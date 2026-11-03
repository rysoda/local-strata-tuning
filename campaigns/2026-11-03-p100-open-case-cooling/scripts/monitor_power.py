"""Read-only NVIDIA power monitor. Does not launch workloads or change GPU settings."""
import argparse
import csv
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import time

RESULTS = Path(__file__).resolve().parents[1] / 'results'
FIELDS = ['uuid', 'name', 'power.draw', 'power.limit', 'temperature.gpu',
          'utilization.gpu', 'clocks.sm']
COLUMNS = ['utc', 'elapsed_seconds', 'power_w', 'power_limit_w',
           'temperature_c', 'utilization_percent', 'sm_clock_mhz']


def query(smi, fields, gpu=None):
    command = [smi, '--query-gpu=' + ','.join(fields),
               '--format=csv,noheader,nounits']
    if gpu is not None:
        command += ['--id=' + gpu]
    result = subprocess.run(command, capture_output=True, text=True, timeout=10,
                            check=True)
    return list(csv.reader(result.stdout.strip().splitlines(), skipinitialspace=True))


def number(value):
    try:
        result = float(value)
        return result if math.isfinite(result) else None
    except ValueError:
        return None


def summary(samples, elapsed):
    """Time-weighted (sample-and-hold) mean; include the final sampling interval."""
    weights = [(samples[i + 1]['elapsed_seconds'] if i + 1 < len(samples) else elapsed)
               - row['elapsed_seconds'] for i, row in enumerate(samples)]
    def mean(key):
        if not samples or elapsed <= 0 or any(row[key] is None for row in samples):
            return None
        return sum(row[key] * w for row, w in zip(samples, weights)) / elapsed
    power = mean('power_w')
    return {
        'duration_seconds': elapsed,
        'sample_count': len(samples),
        'average_power_w': power,
        'energy_wh': power * elapsed / 3600 if power is not None else None,
        'average_temperature_c': mean('temperature_c'),
        'max_temperature_c': max((s['temperature_c'] for s in samples
                                  if s['temperature_c'] is not None), default=None),
        'average_utilization_percent': mean('utilization_percent'),
        'average_sm_clock_mhz': mean('sm_clock_mhz'),
        'max_sample_gap_seconds': max(weights, default=None),
    }


def positive(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError('must be positive and finite')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True, help='Airflow name, e.g. airflow-A')
    parser.add_argument('--gpu', help='NVIDIA GPU index or UUID; default: unique P100')
    parser.add_argument('--seconds', type=positive, default=600, help='default: 600')
    parser.add_argument('--interval', type=positive, default=1, help='seconds; default: 1')
    parser.add_argument('--output-dir', type=Path, default=RESULTS)
    args = parser.parse_args()
    smi = shutil.which('nvidia-smi')
    if not smi:
        parser.error('nvidia-smi was not found on PATH')
    try:
        cards = query(smi, ['uuid', 'name'], args.gpu)
        if args.gpu is None:
            cards = [card for card in cards if 'P100' in card[1]]
        if len(cards) != 1:
            parser.error('Select exactly one GPU using --gpu INDEX or UUID')
        gpu_uuid, gpu_name = cards[0]
    except (subprocess.SubprocessError, OSError, ValueError) as error:
        parser.error(str(error))
    label = re.sub(r'[^a-zA-Z0-9_-]+', '-', args.label).strip('-')
    if not label:
        parser.error('label must contain letters or digits')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    base = args.output_dir / f'{stamp}-{label}'
    csv_path = Path(str(base) + '.csv')
    json_path = Path(str(base) + '.json')
    metadata = dict(label=args.label, gpu_uuid=gpu_uuid, gpu_name=gpu_name,
                    requested_seconds=args.seconds, interval_seconds=args.interval,
                    started_utc=datetime.now(timezone.utc).isoformat(),
                    csv_file=csv_path.name, status='running',
                    method='time-weighted sample-and-hold; NVIDIA board power telemetry')
    json_path.write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(f'{gpu_name} ({gpu_uuid})\n{args.label}: {args.seconds:g}s, every {args.interval:g}s')
    print(f'Samples: {csv_path}\nCtrl+C saves a partial result. Keep the stress test running.')
    samples = []
    start = None
    status, error = 'complete', None
    next_progress = 0
    try:
        with csv_path.open('x', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=COLUMNS)
            writer.writeheader()
            while True:
                rows = query(smi, FIELDS, gpu_uuid)
                now = time.monotonic()
                if len(rows) != 1 or len(rows[0]) != len(FIELDS):
                    raise RuntimeError(f'Unexpected NVIDIA response: {rows!r}')
                values = rows[0]
                power = number(values[2])
                if power is None or power < 0:
                    raise RuntimeError(f'Power reading unavailable: {values[2]}')
                if start is None:
                    start = now
                elapsed = min(now - start, args.seconds)
                row = dict(zip(COLUMNS, [datetime.now(timezone.utc).isoformat(), elapsed,
                                        power, *[number(v) for v in values[3:]]]))
                samples.append(row)
                writer.writerow(row)
                stream.flush()
                if elapsed >= next_progress:
                    print(f'{elapsed:6.0f}/{args.seconds:g}s  {power:6.1f} W  '
                          f'{row["temperature_c"]} C  GPU {row["utilization_percent"]}%')
                    next_progress = elapsed + 30
                remaining = args.seconds - (time.monotonic() - start)
                if remaining <= 0:
                    break
                # Query overhead does not accumulate into the requested interval.
                time.sleep(min(remaining, max(0, args.interval - (time.monotonic() - now))))
                if time.monotonic() - start >= args.seconds:
                    break
    except KeyboardInterrupt:
        status = 'interrupted'
    except (subprocess.SubprocessError, OSError, RuntimeError, ValueError) as exc:
        status, error = 'failed', str(exc)
    elapsed = min(time.monotonic() - start, args.seconds) if start is not None else 0
    metadata.update(summary(samples, elapsed), status=status, error=error,
                    finished_utc=datetime.now(timezone.utc).isoformat())
    json_path.write_text(json.dumps(metadata, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    average = metadata['average_power_w']
    print(f'\n{status.upper()}: {elapsed:.1f}s, {len(samples)} samples')
    if average is not None:
        print(f'Average board power: {average:.2f} W' +
              (' (PARTIAL — do not compare as a full run)' if status != 'complete' else ''))
    print(f'Summary: {json_path}')
    if error:
        print(f'Error: {error}')
    return 0 if status == 'complete' else 1


if __name__ == '__main__':
    raise SystemExit(main())
