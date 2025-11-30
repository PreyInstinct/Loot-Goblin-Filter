#!/usr/bin/env python3
import sys
import importlib
import argparse

from aliases import _Aliaser
Aliaser = _Aliaser()

structure = {
    'Filter Levels': 'levels.filter',
    'Item Names': {
        'Abbreviations': 'abbreviations.filter',
        'Inferior & Superior': 'inferior_superior.filter',
        'General Tags and Appearance': 'general_tags_appearance.filter',
        'Base Item Tags': 'base_items.filter',
        'Gold and Sale Prices': 'gold_sales.filter',
        'Non-magic Modifiers': 'nonmagic_mods.filter',
        'Skill Modifying Items (pointmods)': 'pointmods.py',
        'Hiding and Highlighting': {
            'Set & Uniques': 'sets_uniques.py',
            'Rare and Lower': 'hiding_highlighting.py'},
        'Gambling Screen': 'gambling.filter',
        'Scrolls & Potions': 'scrolls_potions.filter',
        'Keys': {
            'General Info': 'key_info.filter',
            'Navigation Hints': 'navigation.filter'},
        'Gems': 'gems.filter',
        'Runes': 'runes.filter',
        'Charms': 'charms.filter',
        'Miscellaneous Items': 'misc_items.filter'},
    'Item Descriptions': {
        'Point System': {
            'Generated': 'point_system.py',
            'Maps': 'points_maps.filter'},
        'Resistance Totals': 'resistances.filter',
        'Notes on Socketing Non-magical Items': 'socketing_notes_nmag.filter',
        'Notes on Socketing Magical (or better) Items': 'socketing_notes_mag.filter',
        'Notes on Upgrading': 'upgrade_notes.filter',
        'Notes on Crafting': 'crafting_notes.filter',
        'Notes on CBF/HFD': 'freeze_notes.filter',
        'Notes on Imbuing': 'imbuing_notes.filter',
        'Notes on Rerolling and Destroying Jewels': 'jewel_notes.filter',
        'Shop Highlights': 'shop_hunting.filter',
        'Affix Callouts': 'affix_callouts.filter',
        'Notes on Maps': 'map_notes.filter',
        'Unknown Item Catch-all': 'unknown_items.filter'}}
        
        
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
        if type(section_source) == str:
            section = parse_source(section_source, verbose=verbose)
            outfh.writelines(line+'\n' for line in section)
        elif type(section_source) == dict:
            section = walk_structure(section_source, outfh, verbose)
        else:
            raise ValueError("Unknown datatype in filter structure definition: {}".format(section_source))
        

def parse_source(sourcefile, verbose=False):
    if sourcefile.endswith('.filter'):
        infh = open(sourcefile, 'r')
        lines = [Aliaser.process(line.strip('\n')) for line in infh]
    elif sourcefile.endswith('.py'):
        module = importlib.import_module(sourcefile[:-3])
        lines = [Aliaser.process(line) for line in module.build(verbose=verbose)]
    else:
        raise ValueError("Unknown filetype in filter structure definition: {}".format(sourcefile))
    return lines




if __name__ == '__main__':
    build_filter()

