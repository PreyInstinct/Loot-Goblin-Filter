#!/usr/bin/env python3

# Warning: Multiprocessing in this module may not work right under Windows or MacOS
# Best to develop in a Linux environment, but top level execution of build_filter.py should work fine.

import sys

from itertools import groupby, product, combinations
from math import prod, factorial
from bisect import bisect_left
from multiprocessing import Pool, cpu_count

from .point_engine import learn_regions

### TO DO
# the following aliases are ESSENTIAL for this to work
necessary_aliases = ['Alias[SCYTHE]: (scy OR 9s8 OR 7s8 OR wsc OR 9wc OR 7wc)',
                     'Alias[CRYSTAL]: (crs OR 9cr OR 7cr)',
                     'Alias[ARROWS]: (aqv OR aqv2 OR aqv3)',
                     'Alias[BOLTS]: (cqv OR cqv2 OR cqv3)']

POINT_RAINBOW = ['GRAY', 'RED', 'CORAL', 'ORANGE', 'GOLD', 'YELLOW', 'SAGE', 'DARK_GREEN', 'TEAL', 'BLUE', 'PURPLE']

def write_points(rules):
    rainbow_lines = {c:[] for c in POINT_RAINBOW}
    # rarity_cond won't be entirely applicable to all rules
    # (e.g. there are no rare or crafted charms)
    # but I don't care enough to try to predict when a shorter conditional will suffice
    rarity_cond ='(MAG OR RARE OR CRAFT)'
    for rule in rules:
        if rule.kind != 'point':
            continue
        for threshold in rule.fields['thresholds']:
            stat_cond = f"{rule.fields['stat']}>{threshold}"
            if rule.fields['quality_reqs']:
                condition = f"({rarity_cond}) {rule.condition_str} {rule.fields['quality_reqs']} {stat_cond}"
            else:
                condition = f"({rarity_cond}) {rule.condition_str} {stat_cond}"
            point_line = "ItemDisplay["+condition+"]: %NAME%{%NAME%•}%CONTINUE%"
            rainbow_lines[rule.fields['point_color']].append(point_line)
    lines = []
    for color in POINT_RAINBOW:
        formating_line = "ItemDisplay[(MAG OR RARE OR CRAFT)]: %NAME%{%NAME%%"+color+"%}%CONTINUE%"
        lines.append(formating_line)
        lines.extend(rainbow_lines[color])
        lines.append('')
    return lines


def write_max_points(regions, item_type, verbose=False):
    """Brute force algorithm to calculate the theoretical maximum number of points for each region."""
    if item_type == 'RARE':
        Nprefixes = 3
        Nsuffixes = 3
        Naffixes = 0
        include_crafts = False
    elif item_type == 'CRAFT':
        Nprefixes = 1
        Nsuffixes = 1
        Naffixes = 2
        include_crafts = True
    elif item_type == 'MAG':
        Nprefixes = 1
        Nsuffixes = 1
        Naffixes = 0
        include_crafts = False
    else:
        raise ValueError(f"Unknown item_type {item_type} (should be either CRAFT, RARE, or MAG)")

    nprocs = max(1, cpu_count()-1)
    
    scale_bars = []
    for i, region in enumerate(regions):
        # Some regions will represent items that can't be a particular type.
        # (e.g. no crafted jewels or charms)
        # Deciding which regions certain rarity types apply to is Work though.
        # So just waste some computation time calculating the theoretical
        # maximum point value of these nonexistant item classes.
        if verbose:
            print(f'Computing max points for region {i}')
            print('   Characteristic:', region.characteristic)

        # Assemble affixes by group (with or without magic only)
        magic_grouped_affixes, rare_grouped_affixes = group_affixes(region)
        if item_type == 'MAG':
            grouped_affixes = magic_grouped_affixes
        else:
            grouped_affixes = rare_grouped_affixes

        # Print worst case shape of affix categories to help estimate effort required
        if verbose:
            for category, groups in grouped_affixes.items():
                if groups:
                    longest_group = max(groups, key=len)
                else:
                    longest_group = []
                print(f'   {len(groups)}x{len(longest_group)} {category} groups')
            
        # Iterating over all possible combinations (especially for crafted items) can take a non-negligible amount of time.
        # Parallelize this step as much as possibe.
        max_points = 0
        best = ({}, [])
        effort = 0
        with Pool(nprocs) as p:
            for points, total_stats, affix_names in p.imap_unordered(
                    calculate_points,
                    ((affixes, region.applicable_points)
                     for affixes in iter_affixes(Nprefixes, Nsuffixes, Naffixes, include_crafts, grouped_affixes)),
                    chunksize=128
            ):
                effort += 1
                max_points = max(max_points, points)
                if points == max_points:
                    best = total_stats, affix_names            

        # Summarize results
        if verbose:
            print(f'{effort} possible items explored')
            print(f'max points = {max_points}:')
            print(f'   {', '.join(best[1])}')
            for s, v in best[0].items():
                print(f'   {s} = {v}')

        # Formulate the filter scale bar
        scale_condition = f"{item_type} {region.characteristic}"
        scale_bar = ("ItemDisplay[" +
                     scale_condition +
                     "]: %NAME%{%LIGHT_GRAY%" +
                     '•'*max_points +
                     "%CL%%NAME%}%CONTINUE%")
        scale_bars.append(scale_bar)
        if verbose:
            print(scale_bar)
            print()
        
    scale_bars.append('') # Blank line before start of next code block
    return scale_bars

def calculate_points(args):
    affixes, region_rules = args
    # Stats in affixes should be atomic
    # (i.e. combined with ";" to be split appart)
    # Stats in points can be combined with "+"
    
    # Sum all the stats provided by affixes
    total_stats = {}
    affix_names = []
    for affix in affixes:
        affix_names.append(affix.fields['affix'])
        for stat, value in affix.fields['stats'].items():
            try:
                total_stats[stat] += value
            except KeyError:
                total_stats[stat] = value
                
    # Tally the number of points acheived by those stats
    points = 0
    for point_rule in region_rules:
        sum_stats = point_rule.fields['stat'].split('+')
        acheived = sum([total_stats[stat] for stat in sum_stats if stat in total_stats])
        # rule.fields['thresholds'] is sorted list of integer thresholds
        # Use bisect_left because it tells you how many values the query is >
        # bisect_right (aka bisect) gives you >=
        points += bisect_left(point_rule.fields['thresholds'], acheived)
    return points, total_stats, affix_names

def describe_shape(region):
    region_shape = f'{len(region.applicable_prefixes)} prefixes, '
    region_shape += f'{len(region.applicable_suffixes)} suffixes, '
    region_shape += f'{len(region.applicable_crafts)} crafts, '
    region_shape += f'{len(region.applicable_points)} points'
    return region_shape

def discard_worthless_affixes(regions, verbose=False):
    # Discard any affixes that don't award stats that are worth points
    for i, region in enumerate(regions):
        if verbose:
            print(f'Pruning worthless affixes in region {i}')
            print('   Characteristic:', region.characteristic)
            print('   Initial shape:', describe_shape(region))
        
        relevant_stats = set()
        for rule in region.applicable_points:
            relevant_stats.add(rule.fields['stat'])
            if '+' in rule.fields['stat']:
                [relevant_stats.add(s) for s in rule.fields['stat'].split('+')]
        
        def is_relevant(rule):
            if rule.fields['stat'] in relevant_stats:
                return True
            for stat in rule.fields['stat'].split(';'):
                if stat in relevant_stats:
                    return True
            return False

        region.applicable_prefixes = [r for r in region.applicable_prefixes if is_relevant(r)]
        region.applicable_suffixes = [r for r in region.applicable_suffixes if is_relevant(r)]
        region.applicable_crafts = [r for r in region.applicable_crafts if is_relevant(r)]
        if verbose:
            print('   Reduced shape:', describe_shape(region))
            print()

    return regions

def extract_stats_from_affixes(regions):
    # Extracts stats from the rule and stores in easy to use form
    # This will save a bit of processing time which may add up
    # during the very many iterations of computing point values.
    for region in regions:
        extract_stats(region.applicable_prefixes)
        extract_stats(region.applicable_suffixes)
        extract_stats(region.applicable_crafts)

def extract_stats(rules):
    for rule in rules:
        # Most affixes will just give a single stat,
        # but some give multiple stats combined with ";".
        # Reduce these compound stats to their atomic elements.
        stats = rule.fields['stat'].split(';')
        max_values = rule.fields['maxval'].split(';')
        unequal_message = f"unequal number of stats and values for {rule.kind} {rule.fields['affix']}"
        assert (len(stats) == len(max_values)), unequal_message
        # Convert allres to four individual resistances
        if 'RES' in stats:
            stats , max_values = convert_res(stats, vals)
        rule_stats = {}
        for stat, max_val in zip(stats, max_values):
            if '.' in max_val:
                max_val = float(max_val)
            else:
                max_val = int(max_val)
            try:
                rule_stats[stat] += max_val
            except KeyError:
                rule_stats[stat] = max_val
        rule.fields['stats'] = rule_stats
    
def convert_res(stats, vals):
    new_stats = []
    new_vals = []
    for stat, val in zip(stats, vals):
        if stat == 'RES':
            new_stats.append('FRES')
            new_stats.append('CRES')
            new_stats.append('LRES')
            new_stats.append('PRES')
            new_vals.append(val)
            new_vals.append(val)
            new_vals.append(val)
            new_vals.append(val)
        else:
            new_stats.append(stat)
            new_vals.append(val)
    return new_stats, new_vals
    
def group_affixes(region):
    """Generate list of grouped (in list) affixes."""
    magic_grouped_affixes = {} # All affixes
    rare_grouped_affixes = {} # Only rare
    pm, pr = sort_affixes_by_group(region.applicable_prefixes)
    magic_grouped_affixes['prefixes'] = pm
    rare_grouped_affixes['prefixes'] = pr
    sm, sr = sort_affixes_by_group(region.applicable_suffixes)
    magic_grouped_affixes['suffixes'] = sm
    rare_grouped_affixes['suffixes'] = sr
    cm, cr = sort_affixes_by_group(region.applicable_crafts)
    magic_grouped_affixes['crafts'] = cm
    rare_grouped_affixes['crafts'] = cr
    return magic_grouped_affixes, rare_grouped_affixes

def sort_affixes_by_group(affixes):
    magic = {} # All affixes (including magic only)
    rare = {} # Only rare affixes

    for affix in affixes:
        group = affix.fields['group']
        if group not in magic:
            magic[group] = []
        magic[group].append(affix)

        # If not magic only, also add to rare
        if not affix.fields['magic_only']:
            if group not in rare:
                rare[group] = []
            rare[group].append(affix)

    return list(magic.values()), list(rare.values())
    
def iter_affixes(NP, NS, NA, crafted, grouped_affixes):
    grouped_unfixes = [] # Will remain empty if NA == 0
    if crafted:
        NC = 1
    else:
        NC = 0
    p_idx_range = range(len(grouped_affixes['prefixes']))
    s_idx_range = range(len(grouped_affixes['suffixes']))
    for p_idxs in combinations(p_idx_range, NP):
        PGs = [grouped_affixes['prefixes'][i] for i in p_idxs]
        # Other groups can be used for random craft affixes
        if NA:
            remaining_prefixes = [grouped_affixes['prefixes'][i] for i in p_idx_range if i not in p_idxs]
        else:
            remaining_prefixes = []
        for s_idxs in combinations(s_idx_range, NS):
            SGs = [grouped_affixes['suffixes'][i] for i in s_idxs]
            if NA:
                remaining_suffixes = [grouped_affixes['suffixes'][i] for i in s_idx_range if i not in s_idxs]
            else:
                remaining_suffixes = []
            grouped_unfixes = remaining_prefixes + remaining_suffixes
            for prefixes in product(*PGs):
                for suffixes in product(*SGs):
                    for AGs in combinations(grouped_unfixes, NA):
                        for affixes in product(*AGs):
                            for craftmods in combinations(grouped_affixes['crafts'], NC):
                                if craftmods:
                                    craftmods = tuple(r for r in craftmods[0])
                                else:
                                    craftmods = tuple()
                                yield prefixes+suffixes+affixes+craftmods
                                
                                


def build(verbose=False):
    rules, regions = learn_regions(verbose=verbose)

    point_rules = write_points(rules)

    # Reducing the number of affixes will reduce execution times exponentially
    discard_worthless_affixes(regions, verbose=verbose)
    # Also preprocess the Rules into convenient forms to save processing time
    extract_stats_from_affixes(regions)

    # separate magic-only affixes from rare/magic affixes
    
    scale_bars = (write_max_points(regions, 'MAG', verbose=verbose) + \
                  write_max_points(regions, 'RARE', verbose=verbose) + \
                  write_max_points(regions, 'CRAFT', verbose=verbose) )

    header = 'ItemDisplay[MAG OR RARE OR CRAFT]: %NAME%{%NAME%%CL%%LIGHT_GRAY%Affix Quality:%CL%}%CONTINUE%'

    return necessary_aliases + scale_bars + point_rules + [header, '']


def main():
    lines = build(verbose=True)
    fh = open(sys.argv[1], 'w')
    for l in lines:
        print(l, file=fh)
    

if __name__ == '__main__':
    main()
    
