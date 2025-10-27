#!/usr/bin/env python3

import sys

# « ¿ Item Name - Item Type ? »

unid_formatter = '¿ {} ?'
padding = {'S': ('ItemDisplay[{}]: %BORDER-{}%{}«««« {} »»»»', 36),
           'A': ('ItemDisplay[{}]: %MAP-{}%{}««« {} »»»', 38),
           'B': ('ItemDisplay[{}]: %MAP-{}%%TIER-7%{}«« {} »»', 34),
           'C': ('ItemDisplay[{}]: %DOT-{}%%TIER-5%{}« {} »', 30),
           'D': ('ItemDisplay[{}]: %PX-{}%%TIER-3%{}{}', 12)}

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

infh = open('sets_and_uniques.tsv', 'r')
header = infh.readline()
first_uni = True
first_set = True
for line in infh:
    fields = line.strip().split('\t')
    if len(fields) == 5:
        order, code, name, tier, eth_tier = line.strip().split('\t')
    elif len(fields) == 4:
        order, code, name, tier = line.strip().split('\t')
        eth_tier = None
    else:
        order, code, name = line.strip().split('\t')
        tier = 'D'
        eth_tier = None
    code = code.strip('[]').split()
        
    # Make sure the names will fit within the padding
    # 52 characters max
    # -2 for color, map dot
    # -14 for formatting
    # 36 characters max name length
    max_length = 36
    # -6 for "%GRAY%eth %GOLD%" tag
    if eth_tier:
        max_length -= 6
    if len(name) > max_length:
        name = name.split(' - ')[0]
        if len(name) > max_length:
            print("Name too long:")
            print(name)
            sys.exit()

    name = unid_formatter.format(name)
    
    if 'UNI' in code:
        text_color = '%GOLD%'
        map_color = 'D3'
        if first_uni:
            print('// --- 3.3 Uniques (Peeking) ---')
            print()
            first_uni = False
    else:
        text_color = '%GREEN%'
        map_color = '7D'
        if first_set:
            print()
            print('// --- 3.4 Sets (Peeking) ---')
            print()
            first_set = False

    if not eth_tier:
        template, pad_length = padding[tier]
        padded = pad(name, pad_length)
        print(template.format(' '.join(code), map_color, text_color, padded))
    else:
        template, pad_length = padding[tier]
        padded = pad(name, pad_length)
        print(template.format(' '.join(code+['!ETH']), map_color, text_color, padded))
        eth_name = '%GRAY%eth '+text_color+name
        eth_template, eth_pad_length = padding[eth_tier]
        padded = pad(eth_name, eth_pad_length)
        print(eth_template.format(' '.join(code+['ETH']), map_color, text_color, padded))
    

        
    
    
