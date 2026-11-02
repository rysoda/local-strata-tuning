"""Shared GPU-profile construction for topology campaigns; no inference on import."""
import pathlib
from tools import benchmark as tune

REPO = pathlib.Path(__file__).resolve().parents[1]
SOURCE_CAMPAIGN = REPO/'campaigns/2026-10-28-1080ti-tuning'
current = {}


def configure(campaign, control):
    global ROOT, CONTROL
    ROOT = pathlib.Path(campaign)
    CONTROL = pathlib.Path(control)
    tune.configure(ROOT, CONTROL)


def base():
    cfg = tune.read_json(SOURCE_CAMPAIGN/'configs/private/recommended.json')
    cfg['exe'] = str(tune.LOCAL/'components/engine/0.1.55-windows-x86_64-cuda-cuda12/strata.exe')
    cfg['cwd'] = str(CONTROL)
    cfg['vision']['exe'] = str(pathlib.Path(cfg['exe']).with_name('strata-vision.exe'))
    args = cfg['args']
    args[args.index('--expert-profile')+1] = str(CONTROL/'data/expert-profile.bin')
    cfg['gpu'] = current['gpu']
    cfg['gpu_order'] = 'as_given'
    cfg.pop('gpu_roles', None)
    if isinstance(cfg['gpu'], list):
        cfg['layer_split'] = current.get('split', 'auto')
    else:
        cfg.pop('layer_split', None)
    cfg['host'] = '127.0.0.1'
    return cfg


def load(path):
    if pathlib.Path(path) == ROOT/'configs/private/baseline.json':
        return base()
    return tune.read_json(path)
