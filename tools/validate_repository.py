"""Validate layout, evidence integrity, redaction and links without starting inference.
Use --local to additionally resolve the current installed recommendation.
"""
import argparse
import hashlib
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]
SECRET_FIELDS = {'api_key', 'authorization', 'access_token', 'password', 'refresh_token', 'client_secret'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def secrets(value):
    if isinstance(value, dict):
        for key, item in value.items():
            if key.lower() in SECRET_FIELDS and isinstance(item, str) and item and item != '<REDACTED>':
                yield item
            else:
                yield from secrets(item)
    elif isinstance(value, list):
        for item in value:
            yield from secrets(item)


def validate():
    errors = []
    campaigns = sorted((REPO/'campaigns').glob('*/manifest.json'))
    assert campaigns, 'No campaign manifests'
    known_ids = {p.parent.name for p in campaigns}
    private_secrets = set()
    for path in (REPO/'campaigns').glob('*/configs/private/*.json'):
        private_secrets.update(s for s in secrets(read(path)) if len(s) >= 8)
    for path in campaigns:
        root, manifest = path.parent, read(path)
        if manifest['id'] != root.name:
            errors.append(f'{root.name}: mismatched manifest ID')
        for key in ('workload', 'report', 'state', 'resume_script'):
            value = manifest.get(key)
            if value and not (root/value).is_file():
                errors.append(f'{root.name}: missing {key}: {value}')
        for related in manifest.get('related_campaigns', []):
            if related not in known_ids:
                errors.append(f'{root.name}: unknown related campaign: {related}')
        if manifest['status'].startswith('complete'):
            state = read(root/manifest['state'])
            if state['phase'] != manifest['completed_phase']:
                errors.append(f'{root.name}: final phase changed')
            runs = state['runs']
            complete = sum(r.get('phase') == 'complete' for r in runs.values())
            rejected = sum(r.get('phase') in ('failed', 'invalid', 'sanity-failed') for r in runs.values())
            if complete != manifest['completed_benchmarks'] or rejected != manifest['rejected_configurations']:
                errors.append(f'{root.name}: manifest counts differ from state ({complete} complete, {rejected} rejected)')
        profile = manifest.get('recommended_profile')
        if profile and not (root/'configs/shareable'/profile).is_file():
            errors.append(f'{root.name}: missing redacted recommendation')
        for cfg in (root/'configs/shareable').glob('*.json'):
            if list(secrets(read(cfg))):
                errors.append(f'{cfg.relative_to(REPO)}: unredacted secret field')
    evidence = read(REPO/'docs/migration-evidence-hashes.json')
    for old, item in evidence.items():
        path = REPO/item['path']
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
            errors.append(f'Original evidence changed or missing: {old} -> {item["path"]}')
    # Check repository-owned Markdown, not the pinned upstream submodule or raw reports.
    markdown = [REPO/'README.md', REPO/'AGENTS.md']
    for folder in ('campaigns', 'docs', 'tools', 'templates', 'launchers', 'workloads'):
        markdown.extend((REPO/folder).rglob('*.md'))
    for path in markdown:
        if 'results' in path.relative_to(REPO).parts:
            continue
        for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)', path.read_text(encoding='utf-8')):
            target = target.split('#')[0]
            if not target or '://' in target or target.startswith('mailto:'):
                continue
            if not (path.parent/target).exists():
                errors.append(f'{path.relative_to(REPO)}: broken Markdown link: {target}')
    # Scan all publishable campaign evidence/docs/configs/tools for known local credentials.
    for folder in ('campaigns', 'docs', 'tools', 'templates', 'launchers', 'workloads'):
        for path in (REPO/folder).rglob('*'):
            parts = path.relative_to(REPO).parts
            if not path.is_file() or any(p in parts for p in ('private', 'local-deployment', '__pycache__')):
                continue
            if path.suffix in ('.pyc', '.lock'):
                continue
            data = path.read_bytes()
            if any(secret.encode() in data for secret in private_secrets):
                errors.append(f'{path.relative_to(REPO)}: contains a known private credential')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'Validated {len(campaigns)} campaigns, {len(evidence)} unchanged original artifacts/checkpoints, redaction and Markdown links.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true')
    args = parser.parse_args()
    validate()
    if args.local:
        from launch import resolve
        resolve('2026-11-02-p100-1080ti-x8-x8')
        print('Current installed recommendation resolved; no files written or server started.')


if __name__ == '__main__':
    main()
