#!/usr/bin/env python3

import sys
from pathlib import Path

from .hiding_highlighting import hide, show, parse_filter_config
from .style import read_config as get_style
from .style import Token, Padder, Name

HERE = Path(__file__).parent
PROJECT_DIR = HERE / '..'
PROJECT_DIR = PROJECT_DIR.resolve()
CONFIG_DIR = PROJECT_DIR / 'config'
CONFIG_DIR = CONFIG_DIR.resolve()
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR = DATA_DIR.resolve()

CONFIG_FILE = CONFIG_DIR / 'sets_and_uniques.csv'

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
        base_tier = int(base_tier)
        yield order, rarity, base, name, tier, eth_tier, base_tier

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
        
def set_style():
    st = get_style()
    levels, eth_levels = get_levels()
    
    def construct_name(name, rating, base_tier, rarity, is_eth=False):
        # %MAP-1A%%TIER-9%%GOLD%«««   ¿ %GRAY%e%GOLD%Arcana's Flesh%WHITE%¹%GOLD% ?   »»» 

        # Map marker and Tier level
        # Look up the levels for notification/hiding
        if is_eth:
            filter_lvl, marker_lvl, notification_lvl = eth_levels[rarity][rating]
        else:
            filter_lvl, marker_lvl, notification_lvl = levels[rarity][rating]
        

        if marker_lvl:
            marker_idx = marker_lvl -1
            marker_color = st.colors['markers'][rarity]
            marker_style = st.markers[marker_idx]
            map_marker = Token(f'%{marker_style}-{marker_color}%')
        else:
            # Level 0 is no notify
            map_marker = Token('')
    
        if notification_lvl < 9:
            notify_tag = Token(f'%TIER-{notification_lvl}%')
        else:
            # Notification lvl 10 and up = always notify
            notify_tag = Token('')

        # Displayed Text
        text_color = st.colors['text'][rarity]
        l_bracket, r_bracket = st.brackets[marker_lvl]
        left_outer = Token(f'{text_color}{l_bracket}')
        right_outer = Token(r_bracket)
        l_unid, r_unid = st.unid_brackets
        if l_unid:
            left_inner = Token(l_unid+' ')
        else:
            left_inner = Token('')
        if r_unid:
            right_inner = Token(f'{text_color}{r_unid} ')
        else:
            right_inner = Token(text_color)
        if is_eth:
            eth_tag = Token(st.tags['ETH'])
        else:
            eth_tag = Token('')
        tier_tag = Token(st.tier_tags[base_tier][1])
        basename = Token(f'{text_color}{name}')

        item_name = Name([
            map_marker,
            notify_tag,
            left_outer,
            Padder(),
            left_inner,
            eth_tag,
            basename,
            tier_tag,
            right_inner,
            Padder(),
            right_outer
        ])

        # Pad the name to length depending on rating
        pad_len = st.pad_levels[rating]
        # Shorten the item name if necessary
        if item_name.render_length > 52:
            # Strip the basename
            shortname = name.split('-')[0].strip()
            item_name[6] = Token(f'{text_color}{shortname}')
            # Proceed with the shortened version.
            # If the name is still too long a warning will be thrown by the Name object.
        item_name.set_padding(total_len = pad_len)

        return item_name, filter_lvl

    return construct_name
        
def build(verbose=False):
    construct_name = set_style()
    uniques = [
        '// --- Uniques ---',
        '']
    sets = [
        '// --- Sets ---',
        '']
    for order, rarity, base, basename, rating, eth_rating, base_tier in parse_sets_uniques():
        if rarity == 'UNI':
            target = uniques
        elif rarity == 'SET':
            target = sets
        else:
            raise ValueError(f'Unknown item rarity in sets_and_uniques.csv: {rarity}')

        iname, iFL = construct_name(basename, rating, base_tier, rarity, is_eth=False)
        ename, eFL = construct_name(basename, eth_rating, base_tier, rarity, is_eth=True)
        
        # Create hide rules if necessary
        hide_rules = hide(base, iFL, rarity, '!ETH')
        target.extend(hide_rules)
        eth_hide_rules = hide(base, eFL, rarity, 'ETH')
        target.extend(eth_hide_rules)

        # Create display rules
        show_rules = show(base, rarity, '!ETH', name=iname)
        target.extend(show_rules)
        eth_show_rules = show(base, rarity, 'ETH', name=ename)
        target.extend(eth_show_rules)

    uniques.append('')
    return uniques+sets

def main():
    lines = build(verbose=True)
    for l in lines:
        print(l)

if __name__ == '__main__':
    main()
    
