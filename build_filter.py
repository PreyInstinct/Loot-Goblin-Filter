#!/usr/bin/env python3
import sys
import os
import importlib
import argparse
from pathlib import Path

from aliases import _Aliaser
Aliaser = _Aliaser()

PROJECT_DIR = Path(__file__).parent
TEMPLATE_DIR = PROJECT_DIR / 'templates'
GENERATOR_DIR = PROJECT_DIR / 'generators'

structure = {
    'Filter Levels': TEMPLATE_DIR / 'levels.filter',
    'Item Names': {
        'Abbreviations': TEMPLATE_DIR / 'abbreviations.filter',
        'Miscellaneous Items': TEMPLATE_DIR / 'misc_items.filter'},
        'Inferior & Superior': TEMPLATE_DIR / 'inferior_superior.filter',
        'General Tags and Appearance': TEMPLATE_DIR / 'general_tags_appearance.filter',
        'Base Item Tags': TEMPLATE_DIR / 'base_items.filter',
        'Gold and Sale Prices': TEMPLATE_DIR / 'gold_sales.filter',
        'Non-magic Modifiers': TEMPLATE_DIR / 'nonmagic_mods.filter',
        'Skill Modifying Items (pointmods)': GENERATOR_DIR / 'pointmods.py',
        'Hiding and Highlighting': {
            'Set & Uniques': GENERATOR_DIR / 'sets_uniques.py',
            'Rare and Lower': GENERATOR_DIR / 'hiding_highlighting.py'},
        'Gambling Screen': TEMPLATE_DIR / 'gambling.filter',
        'Scrolls & Potions': TEMPLATE_DIR / 'scrolls_potions.filter',
        'Keys': {
            'General Info': TEMPLATE_DIR / 'key_info.filter',
            'Navigation Hints': TEMPLATE_DIR / 'navigation.filter'},
        'Gems': TEMPLATE_DIR / 'gems.filter',
        'Runes': TEMPLATE_DIR / 'runes.filter',
        'Charms': TEMPLATE_DIR / 'charms.filter',
    'Item Descriptions': {
        'Point System': {
            'Generated': GENERATOR_DIR / 'point_system.py',
            'Maps': TEMPLATE_DIR / 'points_maps.filter'},
        'Resistance Totals': TEMPLATE_DIR / 'resistances.filter',
        'Notes on Socketing Non-magical Items': TEMPLATE_DIR / 'socketing_notes_nmag.filter',
        'Notes on Socketing Magical (or better) Items': TEMPLATE_DIR / 'socketing_notes_mag.filter',
        'Notes on Upgrading': TEMPLATE_DIR / 'upgrade_notes.filter',
        'Notes on Crafting': TEMPLATE_DIR / 'crafting_notes.filter',
        'Notes on CBF/HFD': TEMPLATE_DIR / 'freeze_notes.filter',
        'Notes on Imbuing': TEMPLATE_DIR / 'imbuing_notes.filter',
        'Notes on Rerolling and Destroying Jewels': TEMPLATE_DIR / 'jewel_notes.filter',
        'Shop Highlights': TEMPLATE_DIR / 'shop_hunting.filter',
        'Affix Callouts': TEMPLATE_DIR / 'affix_callouts.filter',
        'Notes on Maps': TEMPLATE_DIR / 'map_notes.filter',
        'Unknown Item Catch-all': TEMPLATE_DIR / 'unknown_items.filter'}}
        
        
# Unused/to-do
#        'Sound Effects': 'sound_effects.filter',

file_header = ["-*- coding: windows-1252 -*-",
             "",
             "//	Loot Goblin Filter",
             "//	https://github.com/PreyInstinct/Loot-Goblin-Filter",
             "//",
             "//	Forked from Kryszard's PD2 Loot Filter",
             "//	https://github.com/Kryszard-POD/Kryszard-s-PD2-Loot-Filter",
             "//",
             "//	Note: This file must be edited and saved using Windows-1225 (ANSI) encoding, otherwise some symbols will not render properly.",
             "//"]


def get_args():
    parser = argparse.ArgumentParser(
        description="Loot Goblin Filter Builder."
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Output progress and logging messages."
    )

    parser.add_argument(
        "target",
        type=str,
        help="Target filename."
    )

    return parser.parse_args()


bar = '//'+'-'*100

def build_filter():
    args = get_args()
    outfh = open(args.target, 'w', encoding='windows-1252')
    outfh.writelines(line+'\n' for line in file_header)
    walk_structure(structure, outfh, verbose=args.verbose)
        
def walk_structure(source, outfh, verbose):
    for section_name, section_source in source.items():
        header =  ['',
                   bar,
                  '// '+section_name,
                  bar,
                  '']
        outfh.writelines(line+'\n' for line in header)
        if isinstance(section_source, (str, os.PathLike)):
            section = parse_source(section_source, verbose=verbose)
            outfh.writelines(line+'\n' for line in section)
        elif isinstance(section_source, dict):
            section = walk_structure(section_source, outfh, verbose)
        else:
            raise ValueError("Unknown datatype in filter structure definition: {}".format(section_source))
        

def parse_source(sourcefile, verbose=False):
    sourcefile = Path(sourcefile)
    
    if sourcefile.suffix == '.filter':
        with sourcefile.open('r') as infh:
            return [Aliaser.process(line.strip('\n')) for line in infh]
    elif sourcefile.suffix == '.py':
        root = sourcefile.parent.parent
        # Add project dir to path -> make generators importable
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))

        modname = f'generators.{sourcefile.stem}'
        module = importlib.import_module(modname)
        
        if not hasattr(module, 'build'):
            raise AttributeError(f'{sourcefile} has no "build" function')
        
        return [Aliaser.process(line) for line in module.build(verbose=verbose)]
    else:
        raise ValueError(f"Unknown filetype in filter structure definition: {sourcefile}")





if __name__ == '__main__':
    build_filter()

