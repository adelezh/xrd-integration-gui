import re
from pathlib import Path
from collections import defaultdict

STANDARD = re.compile(r'^(?P<sample>.+)_(?P<stamp>\d{8}-\d{6})_(?P<uid>[A-Za-z0-9]{6})_(?P<tail>.+)$')
def natural_key(value):
    return [int(p) if p.isdigit() else p.lower() for p in re.split(r'(\d+)', str(value))]
def parse(path):
    stem = Path(path).stem
    unit = ''
    if stem.endswith(('_tth','_q')): stem, unit = stem.rsplit('_',1)
    m = STANDARD.fullmatch(stem)
    if not m: raise ValueError(f'Unrecognized standard filename: {Path(path).name}. Use Keep original or custom naming.')
    d = m.groupdict(); tail = d['tail']
    frame = re.search(r'(?:image-|primary-)(\d+)(_mean)?$', tail)
    if not frame: raise ValueError(f'Unrecognized acquisition/frame suffix: {tail}')
    d.update(identifier=frame[1] + (frame[2] or ''), unit=unit)
    return d

def output_name(path, mode='Keep original', unit='', extension=None, dimension='', prefix='', suffix='', section='', number=None, preserve_identifier=False):
    p = Path(path); stem = p.stem
    existing = ''
    if stem.endswith(('_tth','_q')): stem, existing = stem.rsplit('_',1)
    if mode == 'Shorten standard':
        d = parse(p); stem = f"{d['sample']}_{d['stamp']}_{d['identifier']}"
    elif mode == 'Custom':
        if section:
            a,b = map(int, section.split(':'))
            if not 0 <= a < b <= len(p.stem): raise ValueError('Custom section uses basename characters: 0-based start:end, end excluded.')
            stem = p.stem[a:b]
        if preserve_identifier and section:
            identifier = parse(p)['identifier']
            if not stem.endswith(identifier): stem += '_' + identifier
        if number is not None: stem = f'{stem}_{number:04d}'
    stem = prefix + stem + suffix
    unit = unit or existing
    name = stem + (('_'+unit) if unit else '') + (('_'+dimension) if dimension else '') + (extension or p.suffix)
    if not name or any(c in name for c in '<>:"/\\|?*') or name.endswith((' ','.')): raise ValueError('Invalid output filename.')
    return name

def check_collisions(paths):
    keys = [str(Path(p).absolute()).casefold() for p in paths]
    if len(keys) != len(set(keys)): raise ValueError('Duplicate output names. Change naming or grouping before writing.')

def group_files(paths, mode='All selected', section=''):
    groups = defaultdict(list)
    for p in paths:
        if mode == 'All selected': key = 'all'
        elif mode == 'Custom section':
            a,b = map(int, section.split(':'))
            if not 0 <= a < b <= len(Path(p).stem): raise ValueError('Invalid basename section (0-based start:end).')
            key = Path(p).stem[a:b]
        else:
            d = parse(p); key = d['sample'] + ('_'+d['stamp'] if mode == 'Sample + timestamp' else '')
        groups[key].append(str(p))
    return dict(groups)
