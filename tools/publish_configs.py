"""Publish redacted profiles for all campaigns (or one selected campaign).
Private originals remain ignored under campaigns/*/configs/private/.
"""
import argparse
import json
import pathlib

REPO = pathlib.Path(__file__).resolve().parents[1]
SECRET_FIELDS = {'api_key', 'authorization', 'access_token', 'password', 'refresh_token', 'client_secret'}


def redact(value):
    if isinstance(value, dict):
        return {key: '<REDACTED>' if key.lower() in SECRET_FIELDS and item else redact(item)
                for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign', help='Campaign directory name; default: all campaigns')
    args = parser.parse_args()
    roots = sorted(p.parent for p in (REPO/'campaigns').glob('*/manifest.json'))
    if args.campaign:
        roots = [p for p in roots if p.name == args.campaign]
        if not roots:
            parser.error('Unknown campaign')
    count = 0
    for root in roots:
        target = root/'configs/shareable'
        target.mkdir(parents=True, exist_ok=True)
        for source in sorted((root/'configs/private').glob('*.json')):
            if source.name.endswith('.runtime.json'):
                continue
            data = json.loads(source.read_text(encoding='utf-8'))
            (target/source.name).write_text(json.dumps(redact(data), indent=2)+'\n', encoding='utf-8')
            count += 1
    print(f'Published {count} redacted configurations; private originals unchanged.')


if __name__ == '__main__':
    main()
