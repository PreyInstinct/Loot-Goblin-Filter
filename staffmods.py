#!/usr/bin/env python3

import sys

class Skill(object):
    def __init__(self, ID, cls, name, abrv, index):
        self.ID = ID
        if ID.isdigit():
            self.sID = 'SK'+ID
            self.oID = 'OS'+ID
        else:
            self.sID = ID
            self.oID = ID
        self.cls = cls
        self.name = name
        self.abrv = abrv
        self.index = index

        self.order = len(self.index[cls])
        self.index[cls].append(self)

    def has_more_skills(self):
        others = self.index[self.cls][self.order+1:]
        has_another = ['{}>0'.format(other.sID) for other in others]
        return ' OR '.join(has_another)

    def tag_block(self):
        sktemplate = ("ItemDisplay[{SKID}>0 {cls}]: %SAGE%{abrv}%NAME%%CONTINUE%\n"
                      "ItemDisplay[{SKID}>0 !{cls}]: %DARK_GREEN%{abrv}%NAME%%CONTINUE%\n"
                      "ItemDisplay[{SKID}~1-2]: %ORANGE%+%LIGHT_GRAY%%{SKID}%%NAME%%CONTINUE%\n"
                      "ItemDisplay[{SKID}>2]: %ORANGE%+%YELLOW%%{SKID}%%NAME%%CONTINUE%\n")
        return sktemplate.format(SKID=self.sID, cls = self.cls, abrv = self.abrv, other_skills = self.has_more_skills())
        
def read_skills(infile = 'All.skills'):
    skills = {'AMAZON': [],
              'ASSASSIN': [],
              'BARBARIAN': [],
              'DRUID': [],
              'NECROMANCER': [],
              'PALADIN': [],
              'SORCERESS': []}
    fh = open(infile, 'r')
    fh.readline() # header
    for line in fh:
        fields = line.strip().split('\t')
        if len(fields) == 4:
            cls, ID, name, abrv = fields
        elif len(fields) == 3:
            cls, ID, name = fields
            abrv = name
        else:
            sys.exit('Invalid entry in {}:{}'.format(infile, line))
        Skill(ID, cls, name, abrv, skills)
    fh.close()
    return skills

def bonus_skills(skills):
    has_skills = "ALIAS[SKILLS]: (ALLSK>0 OR {})"
    allskills = " OR ".join([skill.sID+">0" for cls in skills.keys() for skill in skills[cls]])
    print(has_skills.format(allskills))
    print()
    print("ItemDisplay[ALLSK>0]: %SAGE%ALL%NAME%%CONTINUE%")
    print("ItemDisplay[ALLSK=1]: %ORANGE%+%BLUE%1%NAME%%CONTINUE%")
    print("ItemDisplay[ALLSK=2]: %ORANGE%+%YELLOW%2%NAME%%CONTINUE%")
    print("ItemDisplay[ALLSK=3]: %ORANGE%+%GOLD%3%NAME%%CONTINUE%")
    print()
    
    for cls in skills.keys():
        for skill in skills[cls]:
            print(skill.tag_block())


skills = read_skills()
bonus_skills(skills)        

