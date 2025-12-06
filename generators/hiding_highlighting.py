#!/usr/bin/env python3

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

def hide(group, filter_level, rarity, properties):
    if filter_level >= adjusted_levels[-1]:
        # Never hide, even at max filter level
        return []
    filter_level = 'FILTLVL>{}'.format(filter_level)
    conditions = [c for c in [rarity, properties, group, filter_level] if c]
    conditions = ' '.join(conditions)
    tag = tracer.generate_tag()
    rules = ['ItemDisplay[${field} !${utility} '+conditions+']: {${filterwarn}'+tag+'}',
             'ItemDisplay[!${field} !${utility} '+conditions+']: %NAME%{${filterwarn}'+tag+'}']
    return rules

brackets, name_colors, right_tags, left_tags = get_style()

marker_levels = ['marker level 0 should never be used because it indicates no marker',
                 '%PX-{MC}%{tier}%{TC}%'+brackets['marker_level_1_left']+' {name} %{TC}%'+brackets['marker_level_1_right'],
                 '%DOT-{MC}%{tier}%{TC}%'+brackets['marker_level_2_left']+' {name} %{TC}%'+brackets['marker_level_2_right'],
                 '%MAP-{MC}%{tier}%{TC}%'+brackets['marker_level_3_left']+' {name} %{TC}%'+brackets['marker_level_3_right'],
                 '%BORDER-{MC}%{tier}%{TC}%'+brackets['marker_level_4_left']+' {name} %{TC}%'+brackets['marker_level_4_right'],
                 '%DOT-{MC}%{tier}%{TC}%'+brackets['marker_level_5_left']+' {name} %{TC}%'+brackets['marker_level_5_right'],
                 '%DOT-{MC}%{tier}%{TC}%'+brackets['marker_level_6_left']+' {name} %{TC}%'+brackets['marker_level_6_right'],
                 '%DOT-{MC}%{tier}%{TC}%'+brackets['marker_level_7_left']+' {name} %{TC}%'+brackets['marker_level_7_right']]

color_key = {'NMAG !RW': ('WHITE', '1f'),
             'MAG': ('BLUE', '94'),
             'RARE': ('YELLOW', '6A'),
             'SET': ('GREEN', '7D'),
             'UNI': ('GOLD', 'D3')}

def highlight(group, marker_level, notification_level, rarity, properties, name='%NAME%'):
    if not marker_level:
        # Never notify
        return []
    conditions = [c for c in [rarity, properties, group] if c]
    conditions = ' '.join(conditions)
    text_color, map_color = color_key[rarity]
    if notification_level < 9:
        tier = '%TIER-{}%'.format(notification_level+1)
    else:
        tier = ''
    marker = marker_levels[marker_level].format(MC=map_color, tier=tier, TC=text_color, name=name)
    tag = tracer.generate_tag()
    rule = 'ItemDisplay[${field} !ID '+conditions+']: '+marker+'{%NAME%'+tag+'}'
    return [rule]

# Adjust levels so odd levels increment strictness
# and even levels are no-potion versions.
adjusted_levels = [0, 2, 4, 6, 8, 10]

def parse_filter_config():
    fh = open(CONFIG_FILE, 'r')
    header = fh.readline()
    lines = []
    for line in fh:
        if line.startswith('#'):
            # Comment lines
            continue
        line = line.strip().split('\t')
        rarity, properties, group, description, filter_level, marker_level, notification_level = line
        filter_level = adjusted_levels[int(filter_level)]
        marker_level = int(marker_level)
        notification_level = adjusted_levels[int(notification_level)]
        lines.append((rarity, properties, group, filter_level, marker_level, notification_level))
    fh.close()
    return lines

def build(verbose=False):
    rules = []
    for rarity, properties, group, filter_level, marker_level, notification_level in parse_filter_config():
        if rarity in ['SET', 'UNI']:
            # Handling of sets and uniques is done separately
            continue
        # Create hide rules if necessary
        hide_rules = hide(group, filter_level, rarity, properties)
        rules.extend(hide_rules)
        # Create a notification rule if necessary.
        notification_rule = highlight(group, marker_level, notification_level, rarity, properties)
        rules.extend(notification_rule)
    return rules

def main():
    rules = build(verbose=True)
    for r in rules:
        print(r)

if __name__ == '__main__':
    main()
        
        
