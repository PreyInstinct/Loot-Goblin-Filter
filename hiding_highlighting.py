#!/usr/bin/env python3

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

tracer = Tracer(active=True)

def hide(group, filter_level, rarity, properties):
    if filter_level >= adjusted_levels[-1]:
        # Never hide, even at max filter level
        return []
    filter_level = 'FILTLVL>{}'.format(filter_level+1)
    conditions = [c for c in [rarity, properties, group, filter_level] if c]
    conditions = ' '.join(conditions)
    tag = tracer.generate_tag()
    rules = ['ItemDisplay[${field} !${utility} '+conditions+']: {${filterwarn}'+tag+'}',
             'ItemDisplay[!${field} !${utility} '+conditions+']: %NAME%{${filterwarn}'+tag+'}']
    return rules

marker_levels = ['marker level 0 should never be used because it indicates no marker',
                 '%PX-{MC}%{tier}%{TC}%« {name} %{TC}%»',
                 '%DOT-{MC}%{tier}%{TC}%«« {name} %{TC}%»»',
                 '%MAP-{MC}%{tier}%{TC}%««« {name} %{TC}%»»»',
                 '%BORDER-{MC}%{tier}%{TC}%«««« {name} %{TC}%»»»»',
                 '%DOT-{MC}%{tier}%PURPLE%- %{TC}%{name} %PURPLE%-',
                 '%DOT-{MC}%{tier}%PURPLE%-= %{TC}%{name} %PURPLE%=-',
                 '%DOT-{MC}%{tier}%PURPLE%-=­¦ %{TC}%{name} %PURPLE%¦=-']

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
adjusted_levels = [-1, 1, 3, 5, 7, 9]

def parse_filter_config():
    fh = open('hiding_highlighting.csv', 'r')
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

def build():
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

if __name__ == '__main__':
    rules = build()
    for r in rules:
        print(r)
        
        
