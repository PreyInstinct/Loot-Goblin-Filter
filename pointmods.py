#!/usr/bin/env python3

import sys

class Skill(object):
    def __init__(self, ID, cls, name, abrv, parent, role):
        self.ID = ID
        if ID.isdigit():
            self.sID = 'SK'+ID
            self.oID = 'MULTI97,'+ID
            self.mID = 'MULTI107,'+ID
        elif ID.startswith('CLSK'):
            digit = ID[4:]
            self.sID = ID
            self.oID = None
            self.mID = 'MULTI83,'+digit
        elif ID.startswith('TABSK'):
            digit = ID[5:]
            self.sID = ID
            self.oID = None
            self.mID = 'MULTI188,'+digit
        else:
            # All Skills
            self.sID = ID
            self.oID = None
            self.mID = 'STAT127'
        self.cls = cls
        self.name = name
        self.abrv = abrv
        self.parent = parent
        self.children = []
        self.role = role

    def __repr__(self):
        return self.name
        #if self.children:
        #    return '{}: {}'.format(self.name, self.children)
        #else:
        #    return self.name
        
    def __iter__(self):
        yield self
        for child in self.children:
            for descendant in child:
                yield descendant

    def bottom_up(self):
        for child in self.children:
            for descendant in child.bottom_up():
                yield descendant
        yield self

    def get(self, query):
        # Check self
        if self.ID == query:
            return self
        else:
            # Check descendants
            for child in self.children:
                result = child.get(query)
                if result:
                    return result
        return False                
        
    def add(self, new_skill):
        if new_skill.parent == self:
            self.children.append(new_skill)
            return True
        else:
            for child in self.children:
                if child.add(new_skill):
                    return True
        return False
    
    def generate_skillmod_filters(self):
        # Group skills by tab/tree, and separate primary from non-primary.
        groups = {}
        for skill in self.bottom_up():
            if skill.role == 'primary':
                try:
                    groups[skill.parent][0].append(skill)
                except KeyError:
                    groups[skill.parent] = ([skill], [])
            elif skill.role != 'tree':
                try:
                    groups[skill.parent][1].append(skill)
                except KeyError:
                    groups[skill.parent] = ([], [skill])
            else:
                continue

        # Begin constructing different conditions for highlighting/tagging.

        # If there is a non-prime skill bonus AND no prime skill bonus, use gray braces.
        subprime = []
        # If any prime skill is 1 or greater AND no prime skill is 4 or greater, use blue braces.
        prime1 = []
        # If any prime skill is 4 AND no prime skill is 5 or greater, use yellow braces.
        prime4 = []
        # If any prime skill is 5 or greater, use gold braces.
        prime5 = []
        # Else, there are no skills so no need for braces.

        for tree, skills in groups.items():
            primes, nonprimes = skills
            # Get all the parental skills.
            ancestors = []
            while tree:
                ancestors.append(tree)
                tree = tree.parent

            # Construct the summation giving the total of each skill
            sum_ancestors = '+'.join([s.mID for s in ancestors])
            sum_primes = [sum_ancestors+'+'+s.mID for s in primes]
            sum_nonprimes = [sum_ancestors+'+'+s.mID for s in nonprimes]

            # Construct the conditionals for this tree
            if nonprimes:
                subprime.append(' OR '.join([s+'>0' for s in sum_nonprimes]))
            if primes:
                prime1.append(' OR '.join([s+'>0' for s in sum_primes]))
                prime4.append(' OR '.join([s+'>3' for s in sum_primes]))
                prime5.append(' OR '.join([s+'>4' for s in sum_primes]))

        # Combine conditionals for all trees to give a single long chain of ORs
        full_subprime = ' OR '.join(subprime)
        full_prime1 = ' OR '.join(prime1)
        full_prime4 = ' OR '.join(prime4)
        full_prime5 = ' OR '.join(prime5)

        # If there is a non-prime skill bonus AND no prime skill bonus, use gray braces.
        gray_braces = '('+full_subprime+') AND !('+full_prime1+')'
        # If any prime skill is 1 or greater AND no prime skill is 4 or greater, use blue braces.
        blue_braces = '('+full_prime1+') AND !('+full_prime4+')'
        # If any prime skill is 4 AND no prime skill is 5 or greater, use yellow braces.
        yellow_braces = '('+full_prime4+') AND !('+full_prime5+')'
        # If any prime skill is 5 or greater, use gold braces.
        gold_braces = '('+full_prime5+')'
        # Else, there are no skills so no need for braces.

        # Construct the filter statements to open and close braces.
        open_brace_template = 'ItemDisplay[{}]: {}{{%NAME%%CONTINUE%\n'
        close_brace_template = 'ItemDisplay[{}]: {}}}%NAME%%CONTINUE%\n'
        openers = (open_brace_template.format(gray_braces, '%GRAY%') + \
                   open_brace_template.format(blue_braces, '%BLUE%') + \
                   open_brace_template.format(yellow_braces, '%YELLOW%') + \
                   open_brace_template.format(gold_braces, '%GOLD%') )
        closers = (close_brace_template.format(gray_braces, '%GRAY%') + \
                   close_brace_template.format(blue_braces, '%BLUE%') + \
                   close_brace_template.format(yellow_braces, '%YELLOW%') + \
                   close_brace_template.format(gold_braces, '%GOLD%') )
        
        print("// Skill Modifiers (aka pointmods) in a separate bracket")
        print()
        # Start with bracket closers because things are constructed backwards
        print(" // Close bracket")
        print(closers)
        # Fill the space between the brackets with the pointmods, working backwards
        for skill in self.bottom_up():
            skill.print_filter_block()
        # Close the block with the opening brackets
        print(" // Open bracket")
        print(openers)


    def print_filter_block(self):
        template = ("ItemDisplay[{SKID}=1]: %ORANGE%+%BLUE%1{COLOR}{ABRV}%NAME%%CONTINUE%\n" +\
                    "ItemDisplay[{SKID}=2]: %ORANGE%+%YELLOW%2{COLOR}{ABRV}%NAME%%CONTINUE%\n" +\
                    "ItemDisplay[{SKID}=3]: %ORANGE%+%GOLD%3{COLOR}{ABRV}%NAME%%CONTINUE%\n" +\
                    "ItemDisplay[{SKID}>3]: %ORANGE%>%GOLD%3{COLOR}{ABRV}%NAME%%CONTINUE%\n")
        if self.ID.isdigit():
            color = '%WHITE%'
        elif self.ID.startswith('TABSK'):
            color = '%BLUE%'
        elif self.ID.startswith('CLSK'):
            color = '%YELLOW%'
        else:
            color = '%GOLD%'
        print(template.format(SKID=self.sID, COLOR=color, ABRV=self.abrv))        

        
def read_skills(infile = 'All.skills'):
    fh = open(infile, 'r')
    header = fh.readline() # 'CLASS\tID\tDESCRIPTION\tABRV\tPARENT\tTYPE\n'
    for line in fh:
        cls, ID, name, abrv, parent, role = line.strip().split('\t')
        if not abrv:
            abrv = name
        if parent == 'root':
            skill = Skill(ID, cls, name, abrv, None, role)
            skill_tree = skill
        else:
            parent = skill_tree.get(parent)
            skill = Skill(ID, cls, name, abrv, parent, role)
            skill_tree.add(skill)
    fh.close()
    return skill_tree


skill_tree = read_skills()
#skill_tree.generate_point_flags()
skill_tree.generate_skillmod_filters()


