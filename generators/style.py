#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path

HERE = Path(__file__).parent
PROJECT_DIR = HERE / '..'
PROJECT_DIR = PROJECT_DIR.resolve()
CONFIG_DIR = PROJECT_DIR / 'config'
CONFIG_DIR = CONFIG_DIR.resolve()
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR = DATA_DIR.resolve()

CONFIG_FILE = CONFIG_DIR / 'style.csv'

def read_config(config_file=CONFIG_FILE):
    brackets = {}
    name_colors = {}
    right_tags = {}
    left_tags = {}
    with open(config_file, 'r') as fh:
        header, block = get_block(fh)
        while header:
            if header.startswith('Brackets'):
                for name, left, right, desc in block:
                    brackets[name+'_left'] = left
                    brackets[name+'_right'] = right
            elif header.startswith('Name Colors'):
                for cond, color in block:
                    name_colors[cond] = color
            elif header.startswith('Right of Name'):
                for cond, tag in block:
                    right_tags[cond] = tag
            elif header.startswith('Left of Name'):
                for cond, tag in block:
                    left_tags[cond] = tag
            else:
                raise ValueError(f"Unknown style block: {header}")
            header, block = get_block(fh)

    return brackets, name_colors, right_tags, left_tags

def get_block(fh):
    # Read until non-empty header or EOF
    while True:
        line = fh.readline()
        if not line:
            # EOF
            return None, None
        header = line.strip()
        if header:
            break

    # Read until blank line
    block = []
    while True:
        line = fh.readline()
        if not line:
            # EOF
            break
        line = line.strip()
        if not line:
            # Blank line
            break
        block.append(line.split('\t'))

    return header, block

def build(verbose=False):
    brackets, name_colors, right_tags, left_tags = read_config()
    general = []
    
    general.append('// Show filter build date in description of Horadric Cube')
    build_date = datetime.today().strftime('%Y-%m-%d')
    version_info = 'ItemDisplay[box]:%NAME%{%NAME%%NL%%GRAY%Loot Goblin Filter %BLACK%| %GRAY% built: '+build_date+'}%CONTINUE%'
    general.append(version_info)

    general.append('// Coloring for items')
    for cond, color in name_colors.items():
        general.append(f'ItemDisplay[{cond}]: {color}%NAME%%CONTINUE%')

    general.append('// Tags to right of name')
    for cond, tag in right_tags.items():
        general.append(f'ItemDisplay[{cond}]: %NAME%{tag}%CONTINUE%')

    general.append('// Tags to left of name')
    for cond, tag in left_tags.items():
        general.append(f'ItemDisplay[{cond}]: {tag} %NAME%%CONTINUE%')

    general.append('// Bracketing for unidentified items')
    unidL = brackets['unid_left']
    unidR = brackets['unid_right']
    for cond, color in name_colors.items():
        general.append(f'ItemDisplay[{cond} !ID]: {color}{unidL} %NAME% {color}{unidR}%CONTINUE%')

    general.append('// Add red "*" Stars on Corrupted items in Unique Stygian Caverns Map')
    general.append('ItemDisplay[(ARMOR OR WEAPON OR QUIVER OR rin OR amu) (MAG OR RARE OR SET OR UNI) !ID (MAPID=181 OR MAPID=182)]: %RED%*%NAME%%RED%*%CONTINUE%')

    general.append('// Show quantitiy of stackables')
    general.append('ItemDisplay[!(ARMOR OR WEAPON OR tbk OR ibk OR QUIVER) QTY>1]: %NAME% %TAN%x %WHITE%%QTY%{%NAME%}%CONTINUE%')

    return general
