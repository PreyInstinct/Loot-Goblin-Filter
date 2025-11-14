#!/usr/bin/env python3
import sys
import importlib

from aliases import _Aliaser
Aliaser = _Aliaser()

bar = '//'+'-'*100

def build_filter(structure):
    lines = []
    for section_name, section_source in structure.items():
        header =  ['',
                  bar,
                  '// '+section_name,
                  bar,
                  '']
        lines.extend(header)
        if type(section_source) == str:
            section = parse_source(section_source)
        elif type(section_source) == dict:
            section = build_filter(section_source)
        else:
            raise ValueError("Unknown datatype in filter structure definition: {}".format(section_source))
        lines.extend(section)
    return lines

def parse_source(sourcefile):
    if sourcefile.endswith('.filter'):
        infh = open(sourcefile, 'r')
        lines = [Aliaser.process(line.strip('\n')) for line in infh]
    elif sourcefile.endswith('.py'):
        module = importlib.import_module(sourcefile[:-3])
        lines = [Aliaser.process(line) for line in module.build()]
    else:
        raise ValueError("Unknown filetype in filter structure definition: {}".format(sourcefile))
    return lines

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
            'Amulets': 'points_amulets.filter',
            'Belts': 'points_belts.filter',
            'Boots': 'points_boots.filter',
            'Charms': 'points_charms.filter',
            'Chests': 'points_chests.filter',
            'Gloves': 'points_gloves.filter',
            'Hats': 'points_hats.filter',
            'Jewels': 'points_jewels.filter',
            'Maps': 'points_maps.filter',
            'Quivers': 'points_quivers.filter',
            'Rings': 'points_rings.filter',
            'Shields': 'points_shields.filter',
            'Weapons, Bludgeoning': 'points_weapons_bludgeoning.filter',
            'Weapons, Edged': 'points_weapons_edged.filter',
            'Weapons, Missile': 'points_weapons_missile.filter',
            'Weapons, Throwing': 'points_weapons_throwing.filter'},
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
# weapons, wands
# weapons, staffs
# weapons, orbs
# crafting for most craftable types


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

outfh = open(sys.argv[1], 'w', encoding='windows-1252')
for l in file_header:
    print(l, file=outfh)
for l in build_filter(structure):
    print(l, file=outfh)
