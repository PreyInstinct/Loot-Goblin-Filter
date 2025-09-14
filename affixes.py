#!/usr/env/bin python3

import sys

# Make lookup tables to figure out what affix types go with which filterable equipment categories, and vice verse.
fh = open('affix_inclusions.tsv', 'r')
affix_types_by_filters = {}
filters_by_affix_types = {}
filters = fh.readline().strip().split('\t')
filter_descriptions = fh.readline().strip().split('\t')
descriptions_by_filter = {f:d for f,d in zip(filters, filter_descriptions)}
for line in fh:
    line = line.strip('\n').split('\t')
    affix_type = line[0]
    inclusions = line[1:]
    for f, included in zip(filters, inclusions):
        if included:
            try:
                affix_types_by_filters[f].append(affix_type)
            except KeyError:
                affix_types_by_filters[f] = [affix_type]
            try:
                filters_by_affix_types[affix_type].append(f)
            except KeyError:
                filters_by_affix_types[affix_type] = [f]
fh.close()

# For fixing some typos/inconsistencies
replacements = {'orbs': 'Orb',
                'staves': 'Staff',
                'amulets': 'Amulet',
                'shields': 'Shield',
                'Helmet': 'Helm'}


# Open the affix table and read the header
fh = open(sys.argv[1], 'r')
header = fh.readline().strip('\n').split('\t')
 # Strip out the item-types column and add a new column for mutually exclusive categories.
new_header = '\t'.join(['Item Type', 'Filter Code']+header[:3]+header[4:])
# [ID, Affix, Attributes, Item Types, Magic Only, alvl, rlvl, freq, group, Changes]

# Create new affix lists specific to each filterable equipment category.
affix_lists = {f:[] for f in filters}

for line in fh:
    line = line.strip('\n').split('\t')
    # Split up the comma-separated list of item-types
    affects = [t.strip() for t in line[3].split(',')]
    # Toss the old item-types column
    new_line = '\t'.join(line[:3]+line[4:])
    for t in affects:
        # Fix typos if necessary
        if t in replacements:
            t = replacements[t]
        # Look up all the filter categories this item-type applies to, and add the affix to its list.
        for f in filters_by_affix_types[t]:
            affix_lists[f].append(new_line)


# Print out the new affix lists.

print(new_header)
for f, affixes in affix_lists.items():
    category = '{}\t{}\t'.format(descriptions_by_filter[f], f)
    for affix in affixes:
        print(category+affix)


sys.exit()



lines = [line.strip('\n').split('\t') for line in fh]

by_type = {}




for line in lines:
    affects = [t.strip() for t in line[3].split(',')]
    new_line = line[:3]+line[4:]
    for t in affects:
        if t in replacements:
            t = replacements[t]
        try:
            by_type[t].append(new_line)
        except KeyError:
            by_type[t] = [new_line]

types = sorted(list(by_type.keys()))
for t in types:
    print(t)
sys.exit()
                
new_header = '\t'.join(header[:3]+header[4:])
for t, affixes in by_type.items():
    print(t)
    print(new_header)
    for affix in affixes:
        print('\t'.join(affix))
    print()

