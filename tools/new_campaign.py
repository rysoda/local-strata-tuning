"""Create a non-executable campaign scaffold; never overwrite existing campaigns."""
import argparse
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]


def create(campaign_id, title, parent=None):
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}-[a-z0-9]+(?:-[a-z0-9]+)*', campaign_id):
        raise ValueError('Use YYYY-MM-DD-lowercase-hardware-purpose (letters, digits and hyphens).')
    root = (parent or REPO/'campaigns')/campaign_id
    root.mkdir(parents=True, exist_ok=False)
    for folder in ('configs/private', 'configs/shareable', 'results', 'state', 'scripts'):
        (root/folder).mkdir(parents=True)
    for source in (REPO/'templates/campaign').glob('*'):
        if source.suffix == '.md':
            text = source.read_text(encoding='utf-8').replace('{{id}}', campaign_id).replace('{{title}}', title)
            (root/source.name).write_text(text, encoding='utf-8')
    manifest = json.loads((REPO/'templates/campaign/manifest.json').read_text(encoding='utf-8'))
    manifest.update(id=campaign_id, title=title)
    (root/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    (root/'state/queue-state.json').write_text(json.dumps({'phase': 'planned', 'current': None, 'runs': {}}, indent=2)+'\n')
    return root


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('id')
    parser.add_argument('--title', required=True)
    args = parser.parse_args()
    try:
        root = create(args.id, args.title)
    except (ValueError, FileExistsError) as error:
        parser.error(str(error))
    print(f'Created {root.relative_to(REPO)}; planned only, no runnable benchmark. Fill manifest/plan and update the root index.')


if __name__ == '__main__':
    main()
