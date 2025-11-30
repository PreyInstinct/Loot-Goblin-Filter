#!/usr/bin/env python

import re
import sys
from copy import copy
from types import SimpleNamespace

from pysat.solvers import Glucose3

def learn_regions(disjoint_config = 'config/item_groups_disjoint.csv',
                  subset_config = 'config/item_groups_subset.csv',
                  composite_config = 'config/item_groups_composites.csv',
                  prefix_config = 'config/prefixes.csv',
                  suffix_config = 'config/suffixes.csv',
                  craft_config = 'config/crafting.csv',
                  point_config = 'config/points.csv',
                  verbose = False):
    """
    Read various configuration files and produce a set of equivalency regions
    (i.e. groupings of items) defined by the filter rules and known disjoint/subset
    relationships, such that the same set of rules are applied to all items within
    a region. In other words, find all possible different combinations of point
    sources that could apply to a given item group.
    """
    # Read various config files
    disjoint_pairs = list(read_disjoint(disjoint_config))
    subset_pairs = list(read_subset(subset_config))
    composite_descriptors = list(read_composites(composite_config))
    rule_based_descriptors = extract_descriptors(prefix_config, 2)
    rule_based_descriptors |= extract_descriptors(suffix_config, 2) 
    rule_based_descriptors |= extract_descriptors(craft_config, 2) 
    rule_based_descriptors |= extract_descriptors(point_config, 0) 
    descriptors = assemble_descriptors(disjoint_pairs, subset_pairs, rule_based_descriptors)

    # Create encoder
    encoder = build_sat_encoder()
    
    # Encode the data from config files
    encoder.add_descriptors(descriptors)
    encoder.encode_global_constraints(disjoint_pairs, subset_pairs, composite_descriptors)

    # Parse the rules
    rules = list(read_affixes(prefix_config, kind='prefix'))
    rules.extend( list(read_affixes(suffix_config, kind='suffix')) )
    rules.extend( list(read_affixes(craft_config, kind='craft')) )
    rules.extend( list(read_points(point_config)) )
    if verbose:
        print(f'{len(rules)} rules input')
    for rule in rules:
        try:
            encoder.encode_rule(rule)
        except ValueError as e:
            print("Fatal exception!", file=sys.stderr)
            print(f"Bad {rule.kind} rule :", rule, file=sys.stderr)
            print('', file=sys.stderr)
            raise e
    if verbose:
        print(f'{len(encoder.var2rule)} rules encoded')

    # Initialize the solver with the encoded data
    solver = encoder.init_solver()

    # Ensure that none of the literals are broke => indicates misconfiguration.
    essentials = ['ARMOR', 'HELM', 'CIRC', 'CHEST', 'SHIELD', 'GLOVES', 'BOOTS',
                  'BELT', 'amu', 'rin', 'WEAPON', '1H', '2H', 'MACE', 'TMACE',
                  'CLUB', 'HAMMER', 'AXE', 'SWORD', 'DAGGER', 'SPEAR', 'POLEARM',
                  'THROWING', 'JAV', 'BOW', 'XBOW', 'STAFF', 'WAND', 'SCEPTER',
                  'CLASS', 'DRU', 'BAR', 'DIN', 'NEC', 'SIN', 'SOR', 'ZON', 'CHARM',
                  'cm1', 'cm2', 'cm3', 'jew', 'QUIVER', 'SCYTHE', 'CRYSTAL']
    for essential in essentials:
        probe_literal_alone(encoder, essential)
    if verbose:
        print('Debug Probes Passed!')
        
    # Start with a single region with now assumptions.
    # The region is still constrained by the global constrains
    # present in config files and encoded in the solver.
    regions = [Region()]

    # Use each rule to split or refine each existing region.
    for rule in rules:
        new_regions = []
        for reg in regions:
            # Test if this rule can either true of false within the existing region.
            # 1. The current rule could be either true or false in this region -> make 2 new regions for each case.
            # 2. The current rule must always be true in this region -> append the true state of this rule as a constraint on the region.
            # 3. The current rule must always be false in this region -> append the false state of this rule as a constraint on the region.       
            base_assumps = list(reg.assumptions)

            # Branch 1: rule evaluates to TRUE in this region
            assume_true = base_assumps + [rule.var]
            if solver.solve(assumptions=assume_true):
                new_region = reg.make_copy()
                new_region.add_assumption(rule.var)
                new_region.add_applicable(rule)
                new_regions.append(new_region)

            # Branch 2: rule evaluates to FALSE in this region
            assume_false = base_assumps + [-rule.var]
            if solver.solve(assumptions=assume_false):
                new_region = reg.make_copy()
                new_region.add_assumption(-rule.var)
                new_regions.append(new_region)

        regions = new_regions # Discard the prior generation of regions

    # Simplify regions by pruning redundant rules
    regions = [simplify_region_literals(solver, region) for region in regions]

    for i, region in enumerate(regions):
        if verbose:
            print(f"Region {i}:")
            print(f"Applicable Rules: {region.count_rules()}")
            print(f"Assumptions: {region.assumptions}")
            for v in region.assumptions:
                if v > 0:
                    print(f"{v}: {encoder.var2cond[v]}")
                else:
                    cond = encoder.var2cond[abs(v)]
                    print(f"{abs(v)}: NOT [{cond}]")

        
                
        # Create a conditional that can be used to write new rules for the region.
        cast = build_characteristic_ast(region, encoder)
        cc = ast_to_filter(cast, implicit_and=True)
        if verbose:
            print('Full Characteristic:', cc)

        # Try simplifying the assumptions using context
        new_assumptions = infer_child_states(encoder, region)
        region.assumptions = new_assumptions
        if verbose:
            print('Expanded Assumptions:', region.assumptions)
        region = simplify_region_literals(solver, region)
        if verbose:
            print('New Assumptions:', region.assumptions)

        simplified_assumptions = reduce_ors(encoder, region)
        cast = conjugate(simplified_assumptions)
        cc = ast_to_filter(cast, implicit_and=True)
        if verbose:
            print('Simplified Characteristic:', cc)
        region.characteristic = cc

        if verbose:
            sanity_check(encoder, region)
            print()

    # Discard the empty region (typically the last region, where all rules are false)
    regions = [r for r in regions if r.count_rules()]
    # Output frozen copy of regions for actually working with
    output_regions = [r.frozen_copy(encoder.var2rule) for r in regions]
    return rules, output_regions


def read_disjoint(config):
    """Reads which item groups overlap from config file, yields all disjoint pairs of item groups."""
    fh = open(config, 'r')
    columns = fh.readline().strip().split('\t')
    for row in fh:
        row = row.strip().split('\t')
        # 1st field is element i (row label)
        # last field is diagonal (i == j)
        # fields in between show where i interesects with column j
        i = row[0]
        intersections = row[1:-1]
        js = columns[:len(intersections)] # will only iterate up to the diagonal
        for j, intersects in zip(js, intersections):
            if not intersects:
                # absence of an intersection implies disjoint
                yield (i, j)
    fh.close()

def read_subset(config):
    """Reads which item groups are subsets from config file, yields all pairs where i is a subset of j."""
    fh = open(config, 'r')
    columns = fh.readline().strip().split('\t')
    for row in fh:
        row = row.strip().split('\t')
        # 1st field is element i (row label)
        # last field is diagonal (i == j)
        # fields in between show where i is a subset of j
        # file must remain sorted to ensure no values beyond the diagonal need to be considered (i.e. each subset follows its superset in order)
        i = row[0]
        memberships = row[1:-1]
        js = columns[:len(memberships)] # will only iterate up to the diagonal
        for j, issubset in zip(js, memberships):
            if issubset:
                yield (i, j)
    fh.close()

def read_composites(config):
    """Reads which item groups are subsets of supersets of others from config file."""
    fh = open(config, 'r')
    for row in fh:
        row = row.strip().split('\t')
        composite = row[0]
        superset = row[1:]
        yield (composite, superset)
    fh.close()
    
def extract_descriptors(rulefile, condition_column):
    descriptors = set()
    fh = open(rulefile, 'r')
    header = fh.readline()
    for line in fh:
        line = line.strip().split('\t')
        condition = line[condition_column]
        new_descriptors = explode(condition)
        descriptors |= new_descriptors
    return descriptors

def explode(condition):
    # Break up terms and strip parenthesis and negation (!).
    descriptors = [p.strip('(!)') for p in condition.split()]
    # Keep only unique terms
    descriptors = set(descriptors)
    # Remove logical operators (OR, AND)
    if 'OR' in descriptors:
        descriptors.remove('OR')
    if 'AND' in descriptors:
        descriptors.remove('AND')
    return descriptors

def assemble_descriptors(disjoint_pairs, subset_pairs, other_descriptors):
    # Assemble the set of all descriptors from various sources: config files or used in rules.
    names = other_descriptors
    for i, j in disjoint_pairs:
        names.add(i)
        names.add(j)
    for i, j in subset_pairs:
        names.add(i)
        names.add(j)

    # Deterministic ordering for fewer headaches troubleshooting
    names = sorted(names)
    return names

class Rule(object):
    def __init__(self, kind, condition_str, fields):
        self.kind = kind
        self.condition_str = condition_str
        self.ast = None
        self.fields = fields
        self.var = None

    def __repr__(self):
        return f"{self.condition_str}: {self.fields}"

    def register(self, var):
        self.var = var

    def to_ast(self):
        """Parses the string conditional from filter syntax to AST format."""
        # AST node formats:
        # ('var', 'AXE')
        # ('not', expr)
        # ('and', left, right)
        # ('or', left, right)

        # Example:
        # Filter: (RARE OR CRAFT) AXE !THROWING
        # AST: ('and', ('and', ('or', ('var', 'RARE'), ('var', 'CRAFT')), ('var', 'AXE')), ('not', ('var', 'THROWING')))

        if self.ast:
            return self.ast
        tokens = tokenize(self.condition_str)
        pos = 0

        def peek():
            return tokens[pos] if pos < len(tokens) else None

        def consume(expected=None):
            nonlocal pos
            token = peek()
            if token is None:
                raise ValueError(f"Unexpected end of input parsing {self.condition_str}")
            elif token != expected:
                raise ValueError(f"Expected {expected}, got {token} in {self.condition_str}")
            pos += 1
            return token

        # Grammar with precedence: NOT > AND > OR
        def parse_expression():
            return parse_or()
        
        def parse_or():
            left = parse_and()
            while peek() == 'OR':
                consume('OR')
                right = parse_and()
                left = ('or', left, right)
            return left

        def parse_and():
            left = parse_not()
            while peek() == 'AND':
                consume('AND')
                right = parse_not()
                left = ('and', left, right)
            return left

        def parse_not():
            if peek() == '!':
                consume('!')
                expr = parse_not()
                return ('not', expr)
            else:
                return parse_atom()

        def parse_atom():
            # atom: a part that cannot be broken down further
            next_token = peek()
            if next_token == '(':
                # Not truly an atom, but a parenthetical expression.
                # Recursively parse the contents of the parenthetical and return the result.
                consume('(')
                expr = parse_expression()
                consume(')')
                return expr
            elif next_token in ["AND", "OR", "!"]:
                # There should not be any more operator tokens, this is supposed to be an atom.
                # This might arise when there is a syntax error like "AND AND" or "OR AND" or "(AND".
                raise ValueError(f"Unexpected operator token {next_token} in {self.condition_str}")
            elif re.match(r"\w+", next_token):
                # A valid variable name
                token = consume(next_token)
                atom = ('var', token)
                return atom
            else:
                raise ValueError(f"Unexpected token {next_token} in {self.condition_str}")

        ast = parse_expression()
        if pos != len(tokens):
            raise ValueError("Extra tokens at end")
        self.ast = ast
        return ast        
    

def read_affixes(cfgfile, kind):
    fh = open(cfgfile, 'r')
    header = fh.readline()
    rules = []
    for line in fh:
        line = line.strip().split('\t')
        condition = line[2]
        fields = {'affix': line[0],
                  'affix_item_types': line[1],
                  'magic_only': bool(line[3]),
                  'group': line[4],
                  'stat': line[5],
                  'minval': line[6],
                  'maxval': line[7],
                  'description': line[8]}
        rules.append( Rule(kind, condition, fields) )
    fh.close()
    return rules

def read_points(cfgfile):
    fh = open(cfgfile, 'r')
    header = fh.readline()
    rules = []
    for line in fh:
        line = line.strip().split('\t')
        condition = line[0]
        fields = {'item_description': line[1],
                  'quality_reqs': line[2],
                  'stat': line[3],
                  'description': line[4],
                  'point_color': line[5],
                  'point_category': line[6],
                  'thresholds': sorted([int(t) for t in line[7:]])}
        rules.append( Rule('point', condition, fields) )
    fh.close()
    return rules
    
def tokenize(condition):
    condition = add_and(condition)
    # Add spaces around operators
    condition = condition.replace('(', ' ( ').replace(')', ' ) ').replace('!', ' ! ')
    tokens = condition.split()
    return tokens

def add_and(condition):
    # Make the ANDs explicit
    tokens = condition.split()
    last_literal = False
    new_tokens = []
    for token in tokens:
        if token in ['AND', 'OR']:
            last_literal = False
        elif last_literal:
            # This has a literal and the last token had a literal.
            # Need to add an "AND"
            new_tokens.append('AND')
            last_literal = True
        else:
            # This has a literal but the last token was a binary operator.
            last_literal = True
        new_tokens.append(token)
    return ' '.join(new_tokens)

def build_sat_encoder():
    """
    Returns a closure that can:
    - register descriptors
    - encode global constraints
    - encode rules (Tseitin)
    - build a PySAT solver when ready
    """
    desc2var = {} # Mapping from literal names (e.g. AXE) to variable IDs
    var2cond = {} # Mapping from variable IDs to rule conditional statements (str)
    var2ast = {} # Mapping from variable IDs to AST
    var2rule = {} # Mapping or variable IDs to source rules
    var2children = {}
    next_var_id = 1 # PySAT  uses integers for variables, starting with 1, with negative values indicationg NOT/false
    clauses = [] # Input to the solver
    global_clause_count = 0
    solver = None

    def new_var(ast=None):
        # Defines a new variable for some node.
        nonlocal next_var_id
        v = next_var_id
        next_var_id += 1
        var2ast[v] = ast
        return v

    def add_descriptors(descriptors):
        # Assign variable IDs to each descriptor and add them to the mappings
        for name in descriptors:
            if name not in desc2var:
                # Protect from redundant assignments
                v = new_var(ast=('var', name))
                desc2var[name] = v
                var2cond[v] = name
        return desc2var

    def safe_lookup(desc):
        try:
            v = desc2var[desc]
        except KeyError:
            raise ValueError(f"Descriptor '{desc}' has not been registered."
                             f"Ensure that all descriptors have been registered with add_descriptors() first.")
        return v
    
    def encode_global_constraints(disjoint_pairs, subset_pairs, composite_descriptors):
        # Initialize with known descriptor relationships.
        nonlocal global_clause_count
        
        # Disjoint(A, B): !A OR !B must be true
        for a, b in disjoint_pairs:
            va = safe_lookup(a)
            vb = safe_lookup(b)
            clauses.append([-va, -vb])

        # Recall that Subset(A, B) indicates A is a subset of B
        # Subset(A, B): !A OR B must be true
        for a, b in subset_pairs:
            va = safe_lookup(a)
            vb = safe_lookup(b)
            clauses.append([-va, vb])

        # Descriptors which are defined as the union of other descriptors
        # A = B | C | D: !A OR B OR C OR D. . .
        for a, parts in composite_descriptors:
            va = safe_lookup(a)
            vparts = [safe_lookup(p) for p in parts]
            clauses.append([-va]+vparts)

        global_clause_count = len(clauses)
        return clauses

    def get_global_clauses():
        return clauses[:global_clause_count]
    
    def encode_rule(rule):
        """
        Parse and encode one rule condition.
        Verify that this rule is satisfiable
        under the global constraints.
        Raise ValueError if the rule is UNSAT.
        """
        condition_str = rule.condition_str
        # First convert the filter syntax into AST syntax.
        ast = rule.to_ast()
        # Transform AST logic into CNF form
        v_root, rule_clauses = tseitin_encode(ast, is_root=True)
        rule.register(v_root)
        
        # Store these forms for later use
        if v_root in var2cond or v_root in var2rule:
            raise ValueError(f'new root registered, but variable already used. var2cond {v_root in var2cond}. var2rule {v_root in var2rule}.')
        var2cond[v_root] = condition_str
        var2rule[v_root] = rule

        # Build a temporary solver to test the rule
        # using global_clauses, rule_clauses, and v_root
        s = Glucose3()
        s.append_formula(get_global_clauses()) # Global constraints from disjoint & subset files
        s.append_formula(rule_clauses) # Constraints from rule logic

        # Check to see if this the rule can ever return True
        s.add_clause([v_root])

        if s.solve():
            # Rule is satisfiable. Add it's logic to the growing list of clauses.
            clauses.extend( rule_clauses )
        else:
            # Rule is unsatisfiable. It either contradicts possible combinations or has an internal paradox.
            raise ValueError(f"Condition is unsatisfiable: {condition_str}")
        
        return ast, v_root
    
    def tseitin_encode(node, is_root=False):
        """Converts a boolean circuit/logical formula in AST format into an equisatisfiable formula in CNF format."""
        # AST format: logical operators = nodes in a decision tree = gates in a circuit
        # For each node, create a new variable representing the output of that node.
        # e.g. let v be equivalent to (A AND B)
        # There are only 3 types of nodes: NOT, AND, and OR
        # The clauses (statements which must be true) for the equivalency to hold are simple (known and finite).
        # If all the clauses of each node are satisfiable (i.e. can be true for some set of inputs), then the overall circuit must be satisfiable.
        # Therefore, the conjunction (clauses for node 1 AND clauses for node 2 AND clauses for node 3. . .) of all clauses is equisatisfiable with the input formula.
        # Essentially, break down the logical circuit into its smallest constituent parts and if all of them can be satisfied then the entire circuit can be satisfied.
        node_clauses = []
        
        kind = node[0]
        if kind == 'var':
            # This node is a literal - a leaf on the tree.
            # No clauses because it is assumed to be a proper variable that can be either True or False.
            v_base = safe_lookup(node[1])
            if is_root:
                # Still need a new var for the rule
                # (rules != descriptors, even if they have equivalent conditions)
                v_out = new_var(ast=node)
                # v_out ↔ v_base
                node_clauses.append([-v_out,  v_base])
                node_clauses.append([ v_out, -v_base])
                var2children[v_out] = ('alias', v_base)
                return v_out, node_clauses
            else:
                v_out = v_base
                var2children[v_out] = ('lit', v_out)

            
        elif kind == 'not':
            # Unary operator has a single child.
            child = node[1]
            # Descend the tree first, encoding the child
            v_child, child_clauses = tseitin_encode(child)
            node_clauses.extend( child_clauses )
            v_out = new_var(ast=node) # Variable representing this node
            var2children[v_out] = ('not', v_child)
            # v_out ↔ ¬v_child
            # i.e. v_out is equivalent to NOT v_child
            # CLAUSES: (¬v_out ∨ ¬v_child) ∧ (v_out ∨ v_child)
            # i.e. in order for this equivalency to hold, then one must be false and the other true.
            node_clauses.append( [-v_out, -v_child] )
            node_clauses.append( [ v_out,  v_child] )
        elif kind == 'and':
            # Binary operator has two children
            left, right = node[1], node[2]
            # Descend the tree for both children first
            v_l, l_clauses = tseitin_encode(left)
            v_r, r_clauses = tseitin_encode(right)
            node_clauses.extend( l_clauses )
            node_clauses.extend( r_clauses )
            v_out = new_var(ast=node) # Variable representing this node
            var2children[v_out] = ('and', v_l, v_r)
            # v_out ↔ (v_l ∧ v_r)
            # i.e. v_out is equivalent to v_l AND v_r
            # (¬v_out ∨ v_l) ∧ (¬v_out ∨ v_r) ∧ (¬v_l ∨ ¬v_r ∨ v_out)
            # i.e. in order for this equivalency to hold, then:
            # - if either child is false then the node must be false
            # - if both are true then the node must be true
            node_clauses.append( [-v_out, v_l] )
            node_clauses.append( [-v_out, v_r] )
            node_clauses.append( [-v_l, -v_r, v_out] )
        elif kind == 'or':
            # Binary operator has two children
            left, right = node[1], node[2]
            # Descend the tree for both children first
            v_l, l_clauses = tseitin_encode(left)
            v_r, r_clauses = tseitin_encode(right)
            node_clauses.extend( l_clauses )
            node_clauses.extend( r_clauses )
            v_out = new_var(ast=node) # Variable representing this node
            var2children[v_out] = ('or', v_l, v_r)
            # v_out ↔ (v_l ∨ v_r)
            # i.e. v_out is equivalent to v_l OR v_r
            # (¬v_l ∨ v_out) ∧ (¬v_r ∨ v_out) ∧ (v_l ∨ v_r ∨ ¬v_out)
            # i.e. in order for this equivalency to hold, then:
            # - if either child is true then the node must be true
            # - if both children are false then the node must be false
            node_clauses.append( [-v_l, v_out] )
            node_clauses.append( [-v_r, v_out] )
            node_clauses.append( [v_l, v_r, -v_out] )
        else:
            raise ValueError(f"Unknown AST kind {kind}")

        return v_out, node_clauses

    def init_solver():
        nonlocal solver
        if solver:
            raise ValueError("Solver has already been initialized.")
        solver = Glucose3()
        solver.append_formula(clauses)
        return solver


    
    return SimpleNamespace(
        add_descriptors=add_descriptors,
        encode_global_constraints=encode_global_constraints,
        encode_rule=encode_rule,
        get_global_clauses=get_global_clauses,
        tseitin_encode=tseitin_encode,
        desc2var=desc2var,
        var2cond=var2cond,
        var2ast=var2ast,
        var2rule=var2rule,
        var2children=var2children,
        init_solver=init_solver,
        get_solver=lambda: solver)



class Region(object):
    """
    A logical partition of items defined by assumptions.
    Rules which apply to the region are stored by reference
    as their integer variables to ensure immutability (uniqueness).
    """
    def __init__(self, ass=[], pre=set(), suf=set(), cra=set(), pts=set(), char=''):
        self.assumptions = ass
        self.applicable_prefixes = pre
        self.applicable_suffixes = suf
        self.applicable_crafts = cra
        self.applicable_points = pts
        self.characteristic = char

    def add_assumption(self, var):
        self.assumptions.append(var)

    def add_applicable(self, rule):
        if rule.kind == 'prefix':
            self.applicable_prefixes.add(rule.var)
        elif rule.kind == 'suffix':
            self.applicable_suffixes.add(rule.var)
        elif rule.kind == 'craft':
            self.applicable_crafts.add(rule.var)
        elif rule.kind == 'point':
            self.applicable_points.add(rule.var)
        else:
            raise ValueError(f'Unknown rule type: {rule.kind}')

    def test_applicability(self, rule_var):
        if rule_var in self.applicable_prefixes:
            return True
        elif rule_var in self.applicable_suffixes:
            return True
        elif rule_var in self.applicable_crafts:
            return True
        elif rule_var in self.applicable_points:
            return True
        else:
            return False
        
    def make_copy(self):
        c = Region(ass=copy(self.assumptions),
                   pre=copy(self.applicable_prefixes),
                   suf=copy(self.applicable_suffixes),
                   cra=copy(self.applicable_crafts),
                   pts=copy(self.applicable_points),
                   char=copy(self.characteristic))
        return c
    
    def count_rules(self):
        total_rules = len(self.applicable_prefixes)
        total_rules += len(self.applicable_suffixes)
        total_rules += len(self.applicable_crafts)
        total_rules += len(self.applicable_points)
        return total_rules

    def frozen_copy(self, var2rule):
        # var2rule must be a mapping of variable integers to rule objects
        # copy all applicable rules as tuples of rule objects
        # output faccimile of the region without methods
        # Will be nicer form for working with, as I won't need to pass around mappings
        assumps = (a for a in self.assumptions)
        APre = [var2rule[p] for p in self.applicable_prefixes]
        ASuf = [var2rule[p] for p in self.applicable_suffixes]
        ACra = [var2rule[p] for p in self.applicable_crafts]
        APts = [var2rule[p] for p in self.applicable_points]

        return SimpleNamespace(assumptions=assumps,
                               applicable_prefixes=APre,
                               applicable_suffixes=ASuf,
                               applicable_crafts=ACra,
                               applicable_points=APts,
                               characteristic=copy(self.characteristic))


def infer_child_states(encoder, region):
    s = encoder.get_solver()
    assumps = list(region.assumptions)
    sortable_assumps = [(a, 0) for a in assumps]

    def test_TrueFalse(var):
        ct = s.solve(assumptions=assumps+[var])
        cf = s.solve(assumptions=assumps+[-var])
        if ct and cf:
            # Literal is unconstrained
            return 'unconstrained'
        elif ct:
            # Literal is always true in region
            return var
        elif cf:
            # Literal is always false in region
            return -var
        else:
            # Uh oh, something is wrong
            raise ValueError(f"{encoder.var2cond[var]} cannot be either true or false under {assumps}")
    
    def record(inference, depth):
        if depth == 0:
            # Don't record the root vars
            # They are already included in assumps
            return
        assumps.append(inference)
        sortable_assumps.append((inference, depth))
                                            
    def bottom_up(node_var, depth=0):
        node = encoder.var2children[node_var]
        kind = node[0]
        if (kind == 'lit' or
            kind == 'alias'):
            # Reached a leaf.
            v = node[1]
            # Test if this descriptor can be True/False given current constraints.
            inference = test_TrueFalse(v)
            if inference != 'unconstrained':
                record(inference, depth)
                return inference > 0
            else:
                return 'unconstrained'
        elif kind == 'not':
            bottom_up(node[1], depth=depth+1)
            inference = test_TrueFalse(node_var)
            if inference != 'unconstrained':
                record(inference, depth)
                return inference > 0
            else:
                return 'unconstrained'
        elif (kind == 'and' or kind == 'or'):
            bottom_up(node[1], depth=depth+1)
            bottom_up(node[2], depth=depth+1)
            inference = test_TrueFalse(node_var)
            if inference != 'unconstrained':
                record(inference, depth)
                return inference > 0
            else:
                return 'unconstrained'
        else:
            raise ValueError(f"Unknown node type {kind}")

    for a in region.assumptions:
        bottom_up(abs(a))

    sortable_assumps.sort(key=lambda t: t[1])
    sorted_assumps = [t[0] for t in sortable_assumps]
        
    return sorted_assumps


def reduce_ors(encoder, region):
    s = encoder.get_solver()

    def test_TrueFalse(var, context):
        ct = s.solve(assumptions=context+[var])
        cf = s.solve(assumptions=context+[-var])
        if ct and cf:
            # Literal is unconstrained
            return (False, var)
        elif ct:
            # Literal is always true in region
            return (True, True)
        elif cf:
            # Literal is always false in region
            return (True, False)
        else:
            # Uh oh, something is wrong
            raise ValueError(f"{encoder.var2cond[var]} cannot be either true or false under {assumps}")
    
    def make_ast(node_var):
        # Check if this node's value is implied by the region context
        is_implied, val = test_TrueFalse(node_var, context)
        if is_implied:
            return val

        # The node is undetermined. Will need to descend.
        node = encoder.var2children[node_var]
        kind = node[0]

        if (kind == 'lit' or
            kind == 'alias'):
            # An unconstrained leaf
            return ('var', encoder.var2cond[node_var])
        
        elif kind == 'not':
            child_var = node[1]
            # The child should be unconstrained, but lets double check.
            child_is_implied, child_val = test_TrueFalse(child_var, context)
            if child_is_implied:
                print('Warning! Unexpected unconstrained node! (NOT True or NOT False)')
                infer = not child_val
                return infer
            else:
                child = make_ast(child_var)
                return ('not', child)
            
        elif kind == 'and':
            left_var = node[1]
            right_var = node[2]
            # At least one of the children should be unconstrained.
            # Double check.
            left_is_implied, left_val = test_TrueFalse(left_var, context)
            right_is_implied, right_val = test_TrueFalse(right_var, context)
            if left_is_implied and right_is_implied:
                print('Warning! Unexpected unconstrained node! (constant AND constant)')
                # If either is False, return False.
                infer = not ((not left_val) or (not right_val))
                return infer
            elif left_is_implied:
                # Should be true. Double check.
                if not left_val:
                    print('Warning! Unexpected unconstrained node! (False and X)')
                    return False
                else:
                    right = make_ast(right_var)
                    return right
            elif right_is_implied:
                # Should be true. Double check.
                if not right_val:
                    print('Warning! Unexpected unconstrained node! (X and False)')
                    return False
                else:
                    left = make_ast(left_var)
                    return left
            else:
                left = make_ast(left_var)
                right = make_ast(right_var)
                return ('and', left, right)
            
        elif kind  == 'or':
            left_var = node[1]
            right_var = node[2]
            # Neither child should be known True.
            # Double check.
            left_is_implied, left_val = test_TrueFalse(left_var, context)
            right_is_implied, right_val = test_TrueFalse(right_var, context)
            if ((left_is_implied and left_val) or
                (right_is_implied and right_val)):
                print('Warning! Unexpected unconstrained node!(True OR X)')
                return True
            # Both children should not be False.
            # Double check.
            if ((left_is_implied and not left_val) and
                (right_is_implied and not right_val)):
                print('Warning! Unexpected unconstrained node! (False OR False)')
                return False
            # If one child is known False we can drop it and collapse this node.
            if (left_is_implied and not left_val):
                right = make_ast(right_var)
                return right
            if (right_is_implied and not right_val):
                left = make_ast(left_var)
                return left
            # Both children are unconstrained, so keep this node.
            left = make_ast(left_var)
            right = make_ast(right_var)
            return ('or', left, right)
            
        else:
            raise ValueError(f"Unknown node type {kind}")        

    asts = []
    for i, root_var in enumerate(region.assumptions):
        context = region.assumptions[:i] + region.assumptions[i+1:]
        ast = make_ast(abs(root_var))
        if type(ast) == bool:
            # Should be true, given that this is an assumption.
            if ((ast and root_var > 0) or
                (not ast and root_var < 0)):
                # Assumption is always true -> implied by reduced form of other assumptions
                continue
            else:
                raise ValueError("Assumption evaluates to False after simplification.")
        
        if root_var > 0:
            asts.append(ast)
        else:
            asts.append( ('not', ast) )

    return asts

def conjugate(asts):
    if not asts:
        return tuple()
    else:
        c = asts[0]
        for next_part in asts[1:]:
            c = ('and', c, next_part)
        return c


def probe_literal_alone(encoder, lit):
    s = encoder.get_solver()
    v = encoder.desc2var[lit]
    ct = s.solve(assumptions=[ v])
    cf = s.solve(assumptions=[-v])
    if (ct and cf):
        return True
    print('Dead variable found! Check your config files!', file=sys.stderr)
    print(f'   {lit}: can_true={ct} can_false={cf}', file=sys.stderr)
    probe_core_for_literal(encoder, lit)
    raise ValueError('Dead variable = logical inconsistency.')

def probe_core_for_literal(encoder, lit_name):
    """
    Find and print (to stderr) the minimal UNSAT core of global constraints
    that together with `lit_name` cause a contradiction.
    """

    # --- Build fresh solver with guarded global clauses ---
    s = Glucose3()
    gcs = encoder.get_global_clauses()   # only global disjoint/subset CNF

    selectors = []
    clause_info = []   # parallel array describing each clause for debugging
    next_sel = 10_000_000

    def new_sel():
        nonlocal next_sel
        v = next_sel
        next_sel += 1
        return v

    # Make a readable description for each global clause
    def describe_clause(cl):
        # Try mapping back to human meaning
        if len(cl) == 2:
            a, b = cl
            # Detect disjoint pair (¬A ∨ ¬B)
            if a < 0 and b < 0:
                A = encoder.var2cond.get(-a, f"v{-a}")
                B = encoder.var2cond.get(-b, f"v{-b}")
                return f"disjoint({A}, {B})  :: clause {cl}"

            # Detect subset pair (¬A ∨  B)
            if a < 0 and b > 0:
                A = encoder.var2cond.get(-a, f"v{-a}")
                B = encoder.var2cond.get(b,  f"v{b}")
                return f"subset({A} ⊆ {B})  :: clause {cl}"

        # Otherwise just print clause raw
        names = []
        for lit in cl:
            name = encoder.var2cond.get(abs(lit), f"v{abs(lit)}")
            names.append(('' if lit > 0 else '¬') + name)
        return f"clause: {' OR '.join(names)}"

    for cl in gcs:
        s_i = new_sel()
        selectors.append(s_i)

        # Record clause origin
        clause_info.append(describe_clause(cl))

        # Guard: (¬s_i ∨ clause)
        s.add_clause([-s_i] + cl)

    # --- Assumptions: literal true & all selectors true ---
    try:
        v_lit = encoder.desc2var[lit_name]
    except KeyError:
        raise ValueError(f"Unknown descriptor: {lit_name}")

    assumptions = [v_lit] + selectors
    ok = s.solve(assumptions=assumptions)

    # If SAT, literal is not dead
    if ok:
        print(f"[OK] {lit_name} is satisfiable under globals.", file=sys.stderr)
        return

    # --- Extract UNSAT core of assumptions ---
    core = s.get_core()

    print(f"\n[UNSAT] {lit_name} is globally contradictory!", file=sys.stderr)
    print("  Minimal UNSAT core contributors:", file=sys.stderr)

    for lit in core:
        if lit == v_lit:
            print(f"    (literal) {lit_name}", file=sys.stderr)
            continue
        # match selector
        if lit in selectors:
            idx = selectors.index(lit)
            print(f"    (constraint) {clause_info[idx]}", file=sys.stderr)

    print("", file=sys.stderr)
    return

def simplify_region_literals(solver, region):
    """Attempts to simplify region definitions by removing redundant literals with a greedy algorithm."""
    # Regions are defined by the rules (e.g. rule 1 is true in this region, rule 2 is false, rule 3 is true, etc. . .)
    # These assignments are stored in Region.assumptons (positive integers mean true, negative integers mean false).
    # Some rules will be duplicates, or otherwise imply the truth or falseness of another rule.
    # e.g. R1: A, R2: A or B, R3: A or B. If R1 is true in this region, then R2 and R3 must also be true.
    # Assumptions which are implied by other rules are redundant and can be discarded

    # The approach here is to try violating one of the assumptions.
    # Example:
    # region assumptions: R1=True, R2=True, R3=True
    # Test whether it is possible, given the constraints encoded in the solver, to violate R1.
    # Test: R1=False, R2=True, R3=True
    # If R1 is implied by another rule (i.e. it is redundant), then this should not be possible.
    # In this example, though, R1 implies R2 and R3, so it is possible (when B is True and A is False), and R1 is not redundant.
    # Test: R1=True, R2=False, R3=False
    # R2 is implied by both R1 (R2 is a superset of R1) and R3 (R2 and R3 are identical).
    # Thus this set of assumptions should create a logical impossibility and the solver will not return a solution.
    # Specifically, these assumptions will violate the constraints encoded in the solver by the "or" statement:
    # R2 ↔ (A or B); therefore the following must be true...
    #    (A=False OR R2=True) and
    #    (B=False OR R2=True) and
    #    (A=True OR B=True OR R2=False)
    # Assuming that R2=False...
    #    the 1st clause indicates A must be False
    #    the 2nd clause indicates B must be False
    #    the 3rd clause implies nothing about A or B
    # Yet R1=True implies that A=True, thus R1 is in conflict with R2=False
    
    changed = True
    while changed:
        changed = False
        for i, literal in enumerate(region.assumptions):
            others = region.assumptions[:i] + region.assumptions[i+1:]
            if solver.solve(assumptions=others+[-literal]):
                # literal is not redundant
                continue
            else:
                # literal is redundant
                region.assumptions.pop(i)
                changed = True
                break # Restart for loop on modified list of assumpitons

    return region

def build_characteristic_ast(region, encoder):
    """
    Combines all ASTs from rules that define a region to produce a characteristic AST.
    The region is defined by its assumptions = rules that evaluate to True or False within the region.
    So a rule composed of the conjugation of all defining rules should exactly define the region.
    """
    parts = []
    for v in region.assumptions:
        if v > 0:
            # Rule = True
            ast = encoder.var2ast[v]
        else:
            # Rule = False
            ast = ('not', encoder.var2ast[abs(v)])
        parts.append(ast)

    if not parts:
        return tuple()
    else:
        cast = parts[0]
        for next_part in parts[1:]:
            cast = ('and', cast, next_part)
        return cast
    
def ast_to_filter(ast, *, implicit_and=False):
    """
    Convert AST to filter syntax.
    - AST nodes: ('var', name), ('not', X), ('and', L, R), ('or', L, R), ('true',), ('false',)
    - Precedence: NOT > AND > OR
    - Minimal parentheses
    - If implicit_and=True, use space for AND; else output 'AND'
    """
    # ----- helpers -----
    def is_lit(n):
        return isinstance(n, tuple) and (
            (len(n) == 2 and n[0] == 'var') or
            (len(n) == 2 and n[0] == 'not' and isinstance(n[1], tuple) and len(n[1]) == 2 and n[1][0] == 'var')
        )

    def flatten(kind, n):
        """Flatten associative chains of same kind into a list."""
        if isinstance(n, tuple) and n and n[0] == kind:
            return flatten(kind, n[1]) + flatten(kind, n[2])
        return [n]

    # precedence table (higher = binds tighter)
    PREC = {'or': 1, 'and': 2, 'not': 3, 'var': 4, 'true': 4, 'false': 4}

    def prec(n):
        if not isinstance(n, tuple) or not n:
            return 100
        k = n[0]
        return PREC.get(k, 0)

    def wrap(child, parent_op_prec):
        """Parenthesize child if it binds looser than parent context."""
        s = emit(child)
        if prec(child) < parent_op_prec:
            return f"({s})"
        return s

    def emit(node):
        k = node[0]

        if k == 'true':
            return 'TRUE'
        if k == 'false':
            return 'FALSE'

        if k == 'var':
            return node[1]

        if k == 'not':
            c = node[1]
            # Need parens if child has lower precedence than NOT or is another NOT on non-var (cosmetic)
            need_paren = prec(c) < PREC['not']
            inner = emit(c)
            return f"!{inner}" if not need_paren or is_lit(c) else f"!({inner})"

        if k == 'and':
            # Flatten to a list
            terms = [emit(t) for t in map(lambda x: x, flatten('and', node))]
            # Parenthesize children that are ORs
            rendered = [wrap(n, PREC['and']) for n in flatten('and', node)]
            if implicit_and:
                # Join by spaces; ensure grouping around ORs already handled by wrap()
                return " ".join(emit(n) if prec(n) >= PREC['and'] else f"({emit(n)})"
                                for n in flatten('and', node))
            else:
                return " AND ".join(emit(n) if prec(n) >= PREC['and'] else f"({emit(n)})"
                                    for n in flatten('and', node))

        if k == 'or':
            parts = flatten('or', node)
            return " OR ".join(emit(n) if prec(n) >= PREC['or'] else f"({emit(n)})" for n in parts)

        # Fallback (shouldn't happen if AST is well-formed)
        return str(node)

    return emit(ast)

def sanity_check(encoder, region):
    solver = encoder.get_solver()
    # Make sure that at least some descriptor terms apply to this region
    applicable_descriptors = []
    for desc, var in encoder.desc2var.items():
        test = region.assumptions + [var]
        if solver.solve(assumptions=test):
            applicable_descriptors.append(desc)
    print('Applicable Descriptors:', applicable_descriptors)
    # Double check that region is possible
    if solver.solve(assumptions=region.assumptions):
        print('Region confirmed SAT')
    else:
        print('Region is UNSAT!')
    # Make sure the rule vars are pointing to the right rule objects
    for p in region.applicable_prefixes:
        rule = encoder.var2rule[p]
        if rule.kind != 'prefix':
            print(rule.kind, '!= suffix')
            print(f'{rule.var} == {p}?')

    for p in region.applicable_suffixes:
        rule = encoder.var2rule[p]
        if rule.kind != 'suffix':
            print(rule.kind, '!= suffix')
            print(f'{rule.var} == {p}?')
            
    for p in region.applicable_crafts:
        rule = encoder.var2rule[p]
        if rule.kind != 'craft':
            print(rule.kind, '!= craft')
            print(f'{rule.var} == {p}?')

    for p in region.applicable_points:
        rule = encoder.var2rule[p]
        if rule.kind != 'point':
            print(rule.kind, '!= point')
            print(f'{rule.var} == {p}?')

def main():
    rules, regions = learn_regions(verbose=True)

    
if __name__ == '__main__':  
    main()
    
