#!/usr/bin/env python3

import sys
from pathlib import Path
from .style import read_config as get_style

HERE = Path(__file__).parent
PROJECT_DIR = HERE / '..'
PROJECT_DIR = PROJECT_DIR.resolve()
CONFIG_DIR = PROJECT_DIR / 'config'
CONFIG_DIR = CONFIG_DIR.resolve()
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR = DATA_DIR.resolve()

CONFIG_FILE = CONFIG_DIR / 'hiding_highlighting.csv'

# Adjust levels so odd levels increment strictness
# and even levels are no-potion versions.
adjusted_levels = [0, 2, 4, 6, 8, 10]

def parse_filter_config():
    with open(CONFIG_FILE, 'r') as fh:
        header = fh.readline()
        for line in fh:
            if line.startswith('#'):
                # Comment lines
                continue
            line = line.strip().split('\t')
            rarity, properties, group, description, filter_level, marker_level, notification_level = line
            filter_level = adjusted_levels[int(filter_level)]
            marker_level = int(marker_level)
            notification_level = adjusted_levels[int(notification_level)]
            yield (rarity, properties, group, filter_level, marker_level, notification_level)

class Tracer(object):
    def __init__(self, active=False):
        self.ID = 0
        self.active = active

    def generate_tag(self):
        if self.active:
            tag = '%CL%Rule {}'.format(self.ID)
            self.ID += 1
            return tag
        else:
            return ''

tracer = Tracer(active=False)

def show(group, rarity, properties, name='%NAME%'):
    conditions = ['GROUND', '!ID', rarity, properties, group]
    conditions = [c for c in conditions if c]
    conditions = ' '.join(conditions)
    tag = tracer.generate_tag()
    rule = 'ItemDisplay['+conditions+']: '+str(name)+'{%NAME%'+tag+'}'
    return [rule]

def hide(group, filter_level, rarity, properties):
    if filter_level >= adjusted_levels[-1]:
        # Never hide, even at max filter level
        return []
    filter_level = 'FILTLVL>{}'.format(filter_level)
    conditions = [c for c in [rarity, properties, group, filter_level] if c]
    conditions = ' '.join(conditions)
    tag = tracer.generate_tag()
    rules = ['ItemDisplay[GROUND !${utility} '+conditions+']: {${filterwarn}'+tag+'}',
             'ItemDisplay[!GROUND !SHOP !${utility} '+conditions+']: %NAME%{${filterwarn}'+tag+'}']
    return rules

def set_style():
    st = get_style()

    def highlight(marker_lvl, notification_lvl, rarity, name='%NAME%'):
        marker_color = st.colors['markers'][rarity]
        marker_style = st.markers[marker_lvl]
        map_marker = f'%{marker_style}-{marker_color}%'
    
        if notification_lvl < 9:
            notify_tag = f'%TIER-{notification_lvl}%'
        else:
            # Notification lvl 10 and up = always notify
            notify_tag = ''

        text_color = st.colors['text'][rarity]
        l_bracket, r_bracket = st.brackets[marker_lvl]
        left_side = f'{text_color}{l_bracket} '
        right_side = f' {text_color}{r_bracket}'

        return ''.join([
            map_marker,
            notify_tag,
            left_side,
            name,
            right_side])

    return highlight

def build(verbose=False):
    highlight = set_style()
    rules = []
    for rarity, properties, group, filter_level, marker_level, notification_level in parse_filter_config():
        if rarity in ['SET', 'UNI']:
            # Handling of sets and uniques is done separately
            continue
        # Create hide rules if necessary
        hide_rules = hide(group, filter_level, rarity, properties)
        rules.extend(hide_rules)
        # Create a notification rule if necessary.
        if marker_level:
            # level 0 is no notify
            marker_index = marker_level - 1
            highlighted = highlight(marker_index, notification_level, rarity)
            notification_rule = show(group, rarity, properties, name=highlighted)
            rules.extend(notification_rule)
    return rules

def main():
    rules = build(verbose=True)
    for r in rules:
        print(r)

if __name__ == '__main__':
    main()
        
        
