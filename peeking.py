#!/usr/bin/env python3

import sys

low_uni = ['ba6', 'dr2', 'ne6', 'ulb', '7cm', '7fb', '7pa', '7bt', 'ltp', 'xcl', '9tw', 'xtp', 'xth', '7kr', 'xpl', 'xld', '7b7', '8hx', '7cs', 'xmb', 'tbt', 'amb', '7sc', '7ha', '7ls', '7bl', '9b8', '6hx', 'uml', 'upk', '7gl', '9gm', '7br', 'ush', 'uul']
low_eth_uni = ['am5', '7ga', 'mau', '9st', 'uvb']
okay_uni = ['drf', 'utp', 'ned', 'ulg', 'ung', 'urg', 'drc', 'paf', 'dr6', 'neg', 'uhc', '7st', 'ame', '7di', '7tw', 'amc', '7xf', 'ztb', 'zlb', 'zvb', 'zhb', 'umc', 'uvc', 'xea', 'uui', 'xhn', 'xlt', 'upl', 'uld', 'utu', 'uvg', 'uhg', 'umg', 'xh9', 'usk', 'ci2', 'baa', 'bac', 'dra', 'dre', 'uh9', 'xhm', 'drd', 'bae', 'ulm', 'lbt', 'xhb', 'uhb', 'xvb', 'nee', 'pa9', 'nea', 'uts', 'uow', 'xsh', 'xow', 'pae', 'nef', 'pac', '7ts', '7s8', '9bw', '7wc', '7bw', '7ws', '7fl', '7cr', '7gm', 'oba', 'ama', 'obc', 'amf', '7wh', '7p7', '7wa', '7lw']
okay_eth_uni = ['xpl', 'uul', '7gi', '7m7', '8ls', '7gl', '7b8', '7bk', '7ha', '7b7', '7sr', '9b8', '9la']
gg_uni = ['uhl', 'uth', 'utb', '7bs', '7qr', 'rar', 'rbe', 'ram', 'baf', '7qs', '6bs', 'utg', 'rin', 'amu', '6ws', 'uar', 'ulc', 'urn', 'uap', 'ci3', 'xtb', 'uit', '6lw', '7gw', '7gd', 'obf', 'uhm']
gg_eth_uni = ['utp', '7st', 'uhc', '7cm', '7fb', '9gm', '7gm', '7s8', '7p7', '7wa', '7wh']
okay_eth_set = ['7fb', '7gd', '7ls', '7m7', '7qr']
okay_set = ['amu', 'rin', 'uar', 'ci3', '7qr', 'uth', 'paf', 'urn', '7ws']

# « ¿ Item Name - Item Type ? »

unid_formatter = '¿ {} ?'
padding = {'S': ('ItemDisplay[{}]: %BORDER-{}%{}«««« {} »»»»', 36),
           'A': ('ItemDisplay[{}]: %MAP-{}%{}««« {} »»»', 38),
           'B': ('ItemDisplay[{}]: %MAP-{}%{}«« {} »»', 34),
           'C': ('ItemDisplay[{}]: %DOT-{}%{}« {} »', 30),
           'D': ('ItemDisplay[{}]: %PX-{}%{}{}', 12)}

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
    else:
        text_color = '%GREEN%'
        map_color = '7D'

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
    

        
    
    
