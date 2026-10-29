"""Publish all local run configurations with API credentials redacted.

Private originals remain in ignored configs/*.json. Run after adding experiments.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def redact(value):
    if isinstance(value, dict):
        return {
            key: '<REDACTED>' if key.lower() in ('api_key', 'authorization', 'access_token', 'password') and item else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def main():
    target = ROOT / 'configs/shareable'
    target.mkdir(parents=True, exist_ok=True)
    count = 0
    for source in sorted((ROOT / 'configs').glob('*.json')):
        if source.name.endswith('.runtime.json'):
            continue
        data = json.loads(source.read_text(encoding='utf-8'))
        (target / source.name).write_text(json.dumps(redact(data), indent=2) + '\n', encoding='utf-8')
        count += 1
    print(f'Published {count} redacted configurations; private originals unchanged.')


if __name__ == '__main__':
    main()
