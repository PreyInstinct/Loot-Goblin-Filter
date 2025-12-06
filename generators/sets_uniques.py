#!/usr/bin/env python3

import sys
from pathlib import Path

from .hiding_highlighting import hide, highlight, parse_filter_config
from .style import read_config as get_style

HERE = Path(__file__).parent
PROJECT_DIR = HERE / '..'
PROJECT_DIR = PROJECT_DIR.resolve()
CONFIG_DIR = PROJECT_DIR / 'config'
CONFIG_DIR = CONFIG_DIR.resolve()
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR = DATA_DIR.resolve()

CONFIG_FILE = CONFIG_DIR / 'sets_and_uniques.csv'

# « ¿ Item Name - Item Type ? »

brackets, name_colors, right_tags, left_tags = get_style()
unid_formatter = brackets['unid_left']+' {} '+brackets['unid_right']
padding = {'S': 38,
           'A': 38,
           'B': 34,
           'C': 30,
           'D': 12,
           'F': 0}

def pad(s, l):
    # Pad string s to length l with spaces symetrically
    even = False
    while len(s) < l:
        if even:
            s = ' '+s
        else:
            s = s+' '
        even = not even
    return s

def get_levels():
    levels = {'SET': {},
              'UNI': {}}
    eth_levels = {'SET': {},
                  'UNI': {}}
    for rarity, properties, group, filter_level, marker_level, notification_level in parse_filter_config():
        if rarity in ['SET', 'UNI']:
            if properties == 'ETH':
                eth_levels[rarity][group] = (filter_level, marker_level, notification_level)
            else:
                levels[rarity][group] = (filter_level, marker_level, notification_level)
        else:
            pass
    return levels, eth_levels
        

def parse_sets_uniques():
    infh = open(CONFIG_FILE, 'r')
    header = infh.readline()
    for line in infh:
        fields = line.strip().split('\t')
        order, rarity, base, name, tier, eth_tier, base_tier = line.strip().split('\t')
        if not tier:
            tier = 'D'
        if not eth_tier:
            eth_tier = tier
        yield order, rarity, base, name, tier, eth_tier, base_tier

def build(verbose=False):
    levels, eth_levels = get_levels()
    
    uniques = ['// --- Uniques ---',
               '']
    sets = ['// --- Sets ---',
            '']
    for order, rarity, base, name, tier, eth_tier, base_tier in parse_sets_uniques():
        # Make sure the names will fit within the padding
        # 52 characters max
        # -2 for map dot, TIER notification formatter
        # -2 for text color formatters
        # -10 for highlighting («»)
        # 38 character max padded length
        # -4 for UNID brackets (¿?)
        # -1 for base tier
        # -3 for "%GRAY%e%COLOR%" tag
        max_length = 30
        if len(name) > max_length:
            name = name.split(' - ')[0]
            if len(name) > max_length:
                print("Name too long:")
                print(name)
                sys.exit()

        # Add base tier, ethereal, and unid tags to name
        if base_tier == '1':
            name += '¹'
        elif base_tier == '2':
            name += '²'
        elif base_tier == '3':
            name += '³'
        else:
            pass        
        if rarity == 'UNI':
            target = uniques
            eth_name = "%GRAY%e%GOLD%"+name
        elif rarity == 'SET':
            target = sets
            eth_name = "%GRAY%e%GREEN%"+name
        else:
            sys.exit('Unknown item rarity in config file: {}'.format(rarity))
        name = unid_formatter.format(name)
        eth_name = unid_formatter.format(eth_name)

        # Pad out the name with spaces to make it wider
        pad_length = padding[tier]
        padded = pad(name, pad_length)
        eth_pad_length = padding[eth_tier]
        eth_padded = pad(eth_name, eth_pad_length)

        # Look up the levels for notification/hiding
        filter_level, marker_level, notification_level = levels[rarity][tier]
        eth_filter_level, eth_marker_level, eth_notification_level = eth_levels[rarity][eth_tier]

        # Create hide rules if necessary
        hide_rules = hide(base, filter_level, rarity, '!ETH')
        target.extend(hide_rules)
        eth_hide_rules = hide(base, eth_filter_level, rarity, 'ETH')
        target.extend(eth_hide_rules)

        # Create highlight rules if necessary
        highlight_rules = highlight(base, marker_level, notification_level, rarity, '!ETH', name=padded)
        target.extend(highlight_rules)
        eth_highlight_rules = highlight(base, eth_marker_level, eth_notification_level, rarity, 'ETH', name=eth_padded)
        target.extend(eth_highlight_rules)

    uniques.append('')
    return uniques+sets


def main():
    lines = build(verbose=True)
    for l in lines:
        print(l)

if __name__ == '__main__':
    main()
    
