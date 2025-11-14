#!/usr/bin/env python
import re
import sys
import traceback

###FIX: PDR is not distinguished between % and flat

outfh = open('point_system.txt', 'w', encoding='windows-1252')

points = {'Belts': {'prefixes': [('Enhanced Defense', 1),
                                 ('Cold Resist', 1),
                                 ('Fire Resist', 1),
                                 ('Lightning Resist', 1),
                                 ('Poison Resist', 1)],
                    'suffixes': [('Faster Cast Rate', 2),
                                 ('Faster Hit Recovery', 2),
                                 ('Extra Gold', 1),
                                 ('Life', 2),
                                 ('Strength', 1),
                                 ('Physical Damage Taken Reduced', 2)]}

class Affix(Object):
    def __init__(self, name, attributes, magic_only, alvl, rlvl, freq, group, affix_type):
        self.name = name
        if type(attributes[0]) == list:
            # Complex attribute
            self.iscomplex = True
        else:
            self.iscomplex = False
        self.attributes = attributes
        self.magic_only = bool(magic_only)
        self.alvl = int(alvl)
        self.rlvl = int(rlvl)
        self.freq = int(freq)
        self.group = int(group)
        self.type = affix_type

    def __repr__(self):
        return self.name

filter_codes = {}
def read_affix_tables(file_name, affix_type):
    global filter_codes
    infh = open(file_name, 'r')
    # header = ['Item Type', 'Filter Code', 'ID', 'Affix', 'Attributes',
    #           'Magic Only', 'alvl', 'rlvl', 'freq', 'group', 'Changes']
    header = infh.readline()
    affixes = {}
    for line in infh:
        item_class, filter_code, ID, name, attributes, magic_only, alvl, rlvl, freq, group, changes = line.strip('\n').split('\t')
        # Parse the attributes field
        try:
            attributes = parse_attributes(attributes)
            # Learn some generalized forms
            if type(attributes[0]) == list:
                # Complex attribute
                for a in attributes:
                    standard_form(a)
            else:
                # Single attribute
                standard_form(attributes)
        except Exception as e:
            traceback.print_exc()
            print(attributes)
            sys.exit()
        fix = Affix(name, attributes, magic_only, alvl, rlvl, freq, group, affix_type)
        # Sort the parsed affixes by item type.
        try:
            affixes[item_class].append(fix)
        except KeyError:
            affixes[item_class] = [fix]
        filter_codes[item_class] = filter_code
    infh.close()
    return affixes

def parse_attributes(attributes):
    # Split up multi-stat attributes into their components
    if ',' in attributes:
        components = attributes.split(', ')
        complex_attribute = []
        for component in components:
            component = parse_attributes(component)
            complex_attribute.append(component)
        return complex_attribute
    # Separate secondary affects in parentheticals, then combine into single attribute construction
    if ('per Level)' in attributes or \
        'second chill)' in attributes or\
        'charges)' in attributes):
        primary = attributes[:attributes.find('(')-1]
        secondary = attributes[attributes.find('(')+1:attributes.find(')')]
        parts = parse_attributes(primary) + parse_attributes(secondary)
        return parts
    # Separate string into numeric words and non-numeric phrases.
    parts = []
    phrase = []
    for word in attributes.split():
        if bool(re.search(r'\d', word)):
            # Has digits -> is numeric word.
            if phrase:
                parts.append(phrase_to_stat(phrase))
                phrase = []
            # Pop off any leading signs
            if word.startswith('+'):
                sign = '+'
                unsigned = word[1:]
            elif word.startswith('-'):
                sign = '-'
                unsigned = word[1:]
            else:
                sign = None
                unsigned = word
            # Strip any parentheticals and percentage signs
            unsigned = unsigned.strip('()[]%')
            # Split up ranges into min (X) and max (Y)
            if '-' in unsigned:
                X, Y = unsigned.split('-')
            else:
                X = unsigned
                Y = unsigned
            try:
                X = int(X)
                Y = int(Y)
            except ValueError:
                X = float(X)
                Y = float(Y)
            except:
                print('Unable to parse numeric word: {} {}'.format(word, unsigned))
                print('In: {}'.format(attributes))
                sys.exit()
            parts.append((X, Y))
        else:
            # No digits -> part of a stat name.
            phrase.append(word)
    if phrase:
        parts.append(phrase_to_stat(phrase))
    return parts

Forms = set()
def standard_form(parts):
    # Learn some generalized forms
    global Forms
    form = []
    i = 0
    variables = ['x', 'y', 'z', 'p', 'q', 'r', 'a', 'b', 'c']
    for part in parts:
        if type(part) == tuple:
            part = variables[i]
            i += 1
        form.append(part)
    form = ' '.join(form)
    Forms.add(form)
    
Stats = set()
def phrase_to_stat(phrase):
    # Strip out joiner and superflous words, leaving only the relevant stat.
    phrase = ' '.join(phrase)
    prefixes = ['to ', 'Bonus to ']
    for prefix in prefixes:
        if phrase.startswith(prefix):
            phrase = phrase[len(prefix):]
            break
    suffixes = [' by', ' of']
    for suffix in suffixes:
        if phrase.endswith(suffix):
            phrase = phrase[:-len(suffix)]
            break
    global Stats
    Stats.add(phrase)
    return phrase
        

prefixes = read_affix_tables('prefix_tables.tsv', 'prefix')
suffixes = read_affix_tables('suffix_tables.tsv', 'suffix')





for s in Stats:
    print(s)
print()
for f in Forms:
    print(f)



dots = 'test•'

