#!/usr/bin/env python3

"""Write new aliases as python variables in this file.
Aliases should be strings, though non-string-type aliases shouldn't break the code.
Variables for internal use only (i.e. non-public) should start with an underscore (e.g. _example).
Aliases should be called in in the filter with the "$" escape character.
$$ will be replaced with a single $.
e.g $alias, ${alias}, ${alias}suffix"""

from string import Template as _template

class _Aliaser(object):
    def __init__(self):
        """Grabs all public global variables in this file and performs string formatting substitution to expand the references within the namespace."""
        self.aliases = {k:v for k,v in globals().items() if not k.startswith('_')}
        max_depth = 100 # prevent endless loop from undefined alias
        while _has_inner(self.aliases) and max_depth:
            self.aliases = {k:_template(v).safe_substitute(**self.aliases) for k, v in self.aliases.items()}
            max_depth -= 1

    def process(self, text):
        t = _template(text)
        return t.safe_substitute(**self.aliases)
        return text.format(**self.aliases)
        

def _has_inner(aliases):
    """Checks a dictionary-like object for valid substitution identifiers in the values."""
    for v in aliases.values():
        t = _template(v)
        if t.get_identifiers():
            return True
    return False


filterwarn = '%PURPLE%Decrease Your Filter Level in Settings to Display It All The Time%CL%%WHITE%Outside the Town/In the Field it is Going to be %RED%HIDDEN%CL%WARNING%WHITE%: This item is hidden at the current filter level.%CL%%NAME%'

# Locations
town = '(MAPID=1 OR MAPID=40 OR MAPID=75 OR MAPID=103 OR MAPID=109)'
field = '(!EQUIPPED !SHOP !MAPID=1 !MAPID=40 !MAPID=75 !MAPID=103 !MAPID=109)'

# Misc item groups
quest = '(bks OR bkd OR tr1 OR ass OR box OR j34 OR g34 OR xyz OR bbb OR qbr OR qey OR qhr OR mss OR ice OR tr2 OR hdm OR msf OR vip OR hst OR g33 OR qf1 OR qf2 OR hfh OR tes OR ceh OR bet OR fed OR toa OR pk1 OR pk2 OR pk3 OR dhn OR bey OR mbr)'
throwpots = '(opm OR gpm OR opl OR ops OR gps OR gpl OR tpfs OR tpgs OR tpcs OR tpls OR tpfm OR tpgm OR tpcm OR tplm OR tpfl OR tpgl OR tpcl OR tpll)'
knownmap = '(t11 OR t12 OR t13 OR t14 OR t15 OR t16 OR t17 OR t21 OR t22 OR t23 OR t24 OR t25 OR t26 OR t27 OR t28 OR t31 OR t32 OR t33 OR t34 OR t35 OR t36 OR t37 OR t38 OR t39 OR t3a OR t41 OR t42 OR t43 OR t44 OR t51 OR t52 OR t53 OR t54 OR t55)'
varmap = '(t11 OR t12 OR t13 OR t14 OR t15 OR t16 OR t17 OR t21 OR t22 OR t23 OR t24 OR t25 OR t26 OR t27 OR t28 OR t31 OR t32 OR t33 OR t34 OR t35 OR t36 OR t37 OR t38 OR t39 OR t3a)'

# Equipment with random affixes
random ='!(UNI OR RW OR SET)'

# Superior equipment with ED
suped = '(NMAG !RW SUP ED>0)'
EDarmor = '((((CHEST OR (HELM !(BAR OR DRU)) OR (SHIELD !(DIN OR NEC)))ELT) OR (DIN (EXC OR ELT) (RES>19 OR AR>100)) OR (gth OR ful OR aar) OR (xng OR xcl OR xhn OR xrs OR xpl OR xlt OR xld OR xtp) OR ci3 OR xsh OR xpk OR xhm OR (RW ARMOR)) !SOCK=1 !INF SUP NMAG ED~5-15)'
EDweapon = '((((WEAPON !SIN !SOR !WAND !SCEPTER !STAFF !(clb OR 9cl OR 7cl OR spc OR 9sp OR 7sp) !DAGGER) ELT) OR 8rx OR (RW WEAPON)) !SOCK=1 !INF SUP NMAG ED~5-15)'

# Tier levels for armor bases.
# "B" bases have the highest defense of any armor in its strength class.
# "D" and "F" bases have unusually high requirements for their defense.
# "A" and "S" tiers are reserved for superior/ethereal bases with good rolls.
FBase = '(ci0 OR ci2 OR ci3 OR ci1)'
DBase = '(fld OR xld OR uld OR spl OR xpl OR upl OR chn OR xhn OR uhn OR stu OR xtu OR utu OR fhl OR xhl OR uhl OR hlm OR xlm OR ulm)'
CBase = '(mbl OR zmb OR umc OR lbl OR zlb OR ulc OR tbt OR xtb OR utb OR ful OR xul OR uul OR gth OR xth OR uth OR plt OR xlt OR ult OR rng OR xng OR ung OR brs OR xrs OR urs OR hla OR xla OR ula OR lea OR xea OR uea OR mgl OR xmg OR umg OR lgl OR xlg OR ulg OR ghm OR xhm OR uhm OR skp OR xkp OR ukp OR ba4 OR ba9 OR bae OR ba2 OR ba7 OR bac OR ba1 OR ba6 OR bab OR dr4 OR dr9 OR dre OR dr3 OR dr8 OR drd OR dr1 OR dr6 OR drb OR gts OR xts OR uts OR spk OR xpk OR upk OR ne3 OR ne8 OR ned OR ne2 OR ne7 OR neg OR pa4 OR pa9 OR pae OR pa3 OR pa8 OR pad OR pa2 OR pa7 OR pac)'
BBase = '(hbl OR zhb OR uhc OR tbl OR ztb OR utc OR vbl OR zvb OR uvc OR hbt OR xhb OR uhb OR mbt OR xmb OR umb OR vbt OR xvb OR uvb OR lbt OR xlb OR ulb OR aar OR xar OR uar OR scl OR xcl OR ucl OR ltp OR xtp OR utp OR qui OR xui OR uui OR hgl OR xhg OR uhg OR tgl OR xtg OR utg OR vgl OR xvg OR uvg OR crn OR xrn OR urn OR bhm OR xh9 OR uh9 OR msk OR xsk OR usk OR cap OR xap OR uap OR ba5 OR baa OR baf OR ba3 OR ba8 OR bad OR dr5 OR dra OR drf OR dr2 OR dr7 OR drc OR tow OR xow OR uow OR bsh OR xsh OR ush OR kit OR xit OR uit OR lrg OR xrg OR urg OR sml OR xml OR uml OR buc OR xuc OR uuc OR ne5 OR nea OR nef OR ne4 OR ne9 OR nee OR ne1 OR ne6 OR neb OR pa5 OR paa OR paf OR pa1 OR pa6 OR pab)'
ABase = '(hbl OR zhb OR uhc OR tbl OR ztb OR utc OR vbl OR zvb OR uvc OR hbt OR xhb OR uhb OR mbt OR xmb OR umb OR vbt OR xvb OR uvb OR lbt OR xlb OR ulb OR aar OR xar OR uar OR scl OR xcl OR ucl OR ltp OR xtp OR utp OR qui OR xui OR uui OR hgl OR xhg OR uhg OR tgl OR xtg OR utg OR vgl OR xvg OR uvg OR crn OR xrn OR urn OR bhm OR xh9 OR uh9 OR msk OR xsk OR usk OR cap OR xap OR uap OR ba5 OR baa OR baf OR ba3 OR ba8 OR bad OR dr5 OR dra OR drf OR dr2 OR dr7 OR drc OR tow OR xow OR uow OR bsh OR xsh OR ush OR kit OR xit OR uit OR lrg OR xrg OR urg OR sml OR xml OR uml OR buc OR xuc OR uuc OR ne5 OR nea OR nef OR ne4 OR ne9 OR nee OR ne1 OR ne6 OR neb OR pa5 OR paa OR paf OR pa1 OR pa6 OR pab) AND SUP AND ED~1-13)'
SBase = '((hbl OR zhb OR uhc OR tbl OR ztb OR utc OR vbl OR zvb OR uvc OR hbt OR xhb OR uhb OR mbt OR xmb OR umb OR vbt OR xvb OR uvb OR lbt OR xlb OR ulb OR aar OR xar OR uar OR scl OR xcl OR ucl OR ltp OR xtp OR utp OR qui OR xui OR uui OR hgl OR xhg OR uhg OR tgl OR xtg OR utg OR vgl OR xvg OR uvg OR crn OR xrn OR urn OR bhm OR xh9 OR uh9 OR msk OR xsk OR usk OR cap OR xap OR uap OR ba5 OR baa OR baf OR ba3 OR ba8 OR bad OR dr5 OR dra OR drf OR dr2 OR dr7 OR drc OR tow OR xow OR uow OR bsh OR xsh OR ush OR kit OR xit OR uit OR lrg OR xrg OR urg OR sml OR xml OR uml OR buc OR xuc OR uuc OR ne5 OR nea OR nef OR ne4 OR ne9 OR nee OR ne1 OR ne6 OR neb OR pa5 OR paa OR paf OR pa1 OR pa6 OR pab) SUP ED>13)'

# Armor groups based on strength requirements.
# Very Light: Dusk Shroud or lower
vlight = '(vbl OR zvb OR uvc OR lbt OR xlb OR ulb OR qui OR xui OR uui OR vgl OR xvg OR uvg OR cap OR xap OR uap OR buc OR xuc OR uuc OR ne1 OR ne6 OR neb OR lbl OR zlb OR ulc OR lgl OR xlg OR ulg OR ci0 OR ci2 OR ci3)'
# Light: Archon Plate or lower
light = '(vbt OR xvb OR uvb OR ltp OR xtp OR utp OR msk OR xsk OR usk OR dr2 OR dr7 OR drc OR sml OR xml OR uml OR ne4 OR ne9 OR nee OR pa1 OR pa6 OR pab OR hla OR xla OR ula OR lea OR xea OR uea OR skp OR xkp OR ukp OR dr1 OR dr6 OR drb OR ne3 OR ne8 OR ned OR ne2 OR ne7 OR neg)'
# Medium: Monarch or lower
medium = '(tbl OR ztb OR utc OR mbt OR xmb OR umb OR scl OR xcl OR ucl OR tgl OR xtg OR utg OR bhm OR xh9 OR uh9 OR ba3 OR ba8 OR bad OR dr5 OR dra OR drf OR bsh OR xsh OR ush OR kit OR xit OR uit OR lrg OR xrg OR urg OR ne5 OR nea OR nef OR pa5 OR paa OR paf OR mbl OR zmb OR umc OR rng OR xng OR ung OR brs OR xrs OR urs OR mgl OR xmg OR umg OR ba2 OR ba7 OR bac OR ba1 OR ba6 OR bab OR dr4 OR dr9 OR dre OR dr3 OR dr8 OR drd OR spk OR xpk OR upk OR pa4 OR pa9 OR pae OR pa3 OR pa8 OR pad OR pa2 OR pa7 OR pac OR stu OR xtu OR utu OR fhl OR xhl OR uhl OR hlm OR xlm OR ulm)'
# Heavy: Unlimited strength requirement
heavy = '(hbl OR zhb OR uhc OR hbt OR xhb OR uhb OR aar OR xar OR uar OR hgl OR xhg OR uhg OR crn OR xrn OR urn OR ba5 OR baa OR baf OR tow OR xow OR uow OR tbt OR xtb OR utb OR ful OR xul OR uul OR gth OR xth OR uth OR plt OR xlt OR ult OR ghm OR xhm OR uhm OR ba4 OR ba9 OR bae OR gts OR xts OR uts OR fld OR xld OR uld OR spl OR xpl OR upl OR chn OR xhn OR uhn)'

# Utility items where base stats may not matter.
pointmod = '(STAFF OR WAND OR SCEPTER OR DRU OR BAR OR NEC OR SIN OR SOR OR ZON OR DAGGER OR CLUB)'
CtABase = '(NMAG ((1H AND SOCKETS=5) OR (SOCKETS=0 AND (2ax OR 92a OR 72a OR fla OR 9fl OR 7fl OR wsp OR 9ws OR 7ws))))'
utility = '(${CtABase} OR leg OR 7cr)'

# Skill tree bonuses
class1 = '(CLSK0>0 OR CLSK1>0 OR CLSK2>0 OR CLSK3>0 OR CLSK4>0 OR CLSK5>0 OR CLSK6>0)'
class2 = '(CLSK0>1 OR CLSK1>1 OR CLSK2>1 OR CLSK3>1 OR CLSK4>1 OR CLSK5>1 OR CLSK6>1)'
tree2 = '(TABSK0>1 OR TABSK1>1 OR TABSK2>1 OR TABSK8>1 OR TABSK9>1 OR TABSK10>1 OR TABSK16>1 OR TABSK17>1 OR TABSK18>1 OR TABSK24>1 OR TABSK25>1 OR TABSK26>1 OR TABSK32>1 OR TABSK33>1 OR TABSK34>1 OR TABSK40>1 OR TABSK41>1 OR TABSK42>1 OR TABSK48>1 OR TABSK49>1 OR TABSK50>1)'
tree3 = '(TABSK0>2 OR TABSK1>2 OR TABSK2>2 OR TABSK8>2 OR TABSK9>2 OR TABSK10>2 OR TABSK16>2 OR TABSK17>2 OR TABSK18>2 OR TABSK24>2 OR TABSK25>2 OR TABSK26>2 OR TABSK32>2 OR TABSK33>2 OR TABSK34>2 OR TABSK40>2 OR TABSK41>2 OR TABSK42>2 OR TABSK48>2 OR TABSK49>2 OR TABSK50>2)'
tree4 = '(TABSK0>3 OR TABSK1>3 OR TABSK2>3 OR TABSK8>3 OR TABSK9>3 OR TABSK10>3 OR TABSK16>3 OR TABSK17>3 OR TABSK18>3 OR TABSK24>3 OR TABSK25>3 OR TABSK26>3 OR TABSK32>3 OR TABSK33>3 OR TABSK34>3 OR TABSK40>3 OR TABSK41>3 OR TABSK42>3 OR TABSK48>3 OR TABSK49>3 OR TABSK50>3)'
tree5 = '(TABSK0>4 OR TABSK1>4 OR TABSK2>4 OR TABSK8>4 OR TABSK9>4 OR TABSK10>4 OR TABSK16>4 OR TABSK17>4 OR TABSK18>4 OR TABSK24>4 OR TABSK25>4 OR TABSK26>4 OR TABSK32>4 OR TABSK33>4 OR TABSK34>4 OR TABSK40>4 OR TABSK41>4 OR TABSK42>4 OR TABSK48>4 OR TABSK49>4 OR TABSK50>4)'
tree6 = '(TABSK0>5 OR TABSK1>5 OR TABSK2>5 OR TABSK8>5 OR TABSK9>5 OR TABSK10>5 OR TABSK16>5 OR TABSK17>5 OR TABSK18>5 OR TABSK24>5 OR TABSK25>5 OR TABSK26>5 OR TABSK32>5 OR TABSK33>5 OR TABSK34>5 OR TABSK40>5 OR TABSK41>5 OR TABSK42>5 OR TABSK48>5 OR TABSK49>5 OR TABSK50>5)'

# Small Items
# 1x1: Rings, amulets
small1 = '(amu OR rin)'
# 2x1: Belts
# 1x2: Some daggers, wands, most orbs, throwing knives, some throwing axes
small2 = '(BELT OR WAND OR (SOR !(ob5 OR oba OR obf)) OR dgr OR dir OR 9dg OR 9di OR 7dg OR 7di OR tkf OR bkf OR 9tk OR 9bk OR 7tk OR 7bk OR tax OR 9ta OR 7ta)'

hat = '(HELM OR CIRC)'

# Named map icons
def _generate_icons():
    colors = {'white': '20',
              'gray': '1D',
              'light_gray': '1F',
              'blue': '97',
              'royal_blue': '91',
              'sky_blue': '9E',
              'yellow': '6D',
              'light_yellow': 'A8',
              'gold': '53',
              'green': '84',
              'dark_green': '77',
              'keylimepie': 'A9',
              'tan': '5A',
              'black': '21',
              'purple': '9B',
              'royal_purple': '8F',
              'red': '62',
              'dark_red': '0A',
              'vdark_red': '08',
              'redbrown': '05',
              'salmon': '66',
              'orange': '60',
              'light_orange': '68',
              'teal': '9F'}
    dots = {'S': 'PX',
            'M': 'DOT',
            'L': 'MAP',
            'XL': 'BORDER'}
    icons = {}
    for dotname, dot in dots.items():
        for colorname, color in colors.items():
            icon_name = f'{colorname}{dotname}' # e.g. redXL
            icon = f'%{dot}-{color}%' # e.g. %BORDER-0A%
            icons[icon_name] = icon
    return icons

def _export_dict_to_globals(d, prefix='dict_'):
    g = globals()
    for k, v in d.items():
        g[f'{prefix}{k}'] = v

_export_dict_to_globals(_generate_icons(), prefix='icon_')



if __name__ == '__main__':
    Aliaser = _Aliaser()
    for k,v in Aliaser.aliases.items():
        print(k, v)

