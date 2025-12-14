#!/usr/bin/env python3

from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
import warnings
import json

HERE = Path(__file__).parent
PROJECT_DIR = HERE / '..'
PROJECT_DIR = PROJECT_DIR.resolve()
CONFIG_DIR = PROJECT_DIR / 'config'
CONFIG_DIR = CONFIG_DIR.resolve()
DATA_DIR = PROJECT_DIR / 'data'
DATA_DIR = DATA_DIR.resolve()

CONFIG_FILE = CONFIG_DIR / 'style.json'

def read_config(config_file=CONFIG_FILE):
    with open(config_file, 'r') as fh:
        cfg = json.load(fh)

    if not isinstance(cfg, dict):
        raise ValueError("style.json must contain a JSON object")

    return SimpleNamespace(**cfg)

class Padder:
    """
    A small utility that represents a run of padding characters.
    Behaves like a mutable-length string of a single repeated character.
    """
    __slots__ = ("_char", "_length")

    def __init__(self, char=" "):
        if not isinstance(char, str) or len(char) != 1:
            raise ValueError(f"Pad character must be a single-character string, got {char!r}")
        self._char = char
        self._length = 0

    def __repr__(self):
        return f"Padder({self._char!r}, length={self._length})"

    def __str__(self):
        return self._char * self._length

    def __len__(self):
        return self._length

    @property
    def char(self):
        return self._char

    @property
    def length(self):
        return self._length

    @length.setter
    def length(self, value):
        if value < 0:
            raise ValueError("Padding length cannot be negative.")
        self._length = value

    def set_length(self, length):
        """Allow p=Padder.set_length(3)"""
        self.length = length
        return self

class Token(str):
    """
    Used to track render length of filter syntax names.
    %keywords% counta s a single character.
    """
    def __new__(cls, value, marker='%'):
        obj = super().__new__(cls, value)
        obj.marker = marker
        return obj

    @property
    def render_length(self) -> int:
        m = self.marker
        n = 0 # length count
        i = 0 # positional index in string
        L = super().__len__() # Ordinary string length
        while i < L:
            if self[i] == m:
                # Start of a keyword: find the end
                j = self.find(m, i+1)
                if j == -1:
                    # No closing maker found: treat as literal
                    n += 1
                    i += 1
                else:
                    n += 1
                    i = j + 1 # Jump ahead to the character after the closer
            else:
                # Ordinary literal: increment to next character
                n += 1
                i += 1
        return n

class Name:
    """
    Formatting object for names composed of Tokens, Padders, and strings.
    Computes total render_length and can coerce to str to render final filter syntax string.

    Example:
    %MAP-1A%%TIER-9%%GOLD%«««   ¿ %GRAY%e%GOLD%Arcana's Flesh%WHITE%¹%GOLD% ?   »»» 
    {marker}{tier}{text_color}{bracket_left}{pad_left}{unid_left}. . .
    {eth_tag}{name}{tier_tag}{text_color} {unid_right}{pad_right}{bracket_right}
    """
    def __init__(self, parts = []):
        self.parts = parts

    # ---------- Basic list-like methods ----------
    def __len__(self):
        return len(self.parts)

    def __getitem__(self, idx):
        return self.parts[idx]

    def __setitem__(self, idx, value):
        self.parts[idx] = value

    def append(self, item):
        self.parts.append(item)

    def extend(self, items):
        self.parts.extend(items)

    def insert(self, idx, item):
        self.parts.insert(idx, item)
        
    @property
    def render_length(self) -> int:
        total = 0
        for part in self.parts:
            if hasattr(part, "render_length"):
                # Token-like
                total += part.render_length
            elif hasattr(part, "length"):
                # Padder-like
                total += part.length
            else:
                # plain string or other
                total += len(str(part))
        return total

    def set_padding(self, total_len = 52):
        """Distribute total padding between all padders"""
        if total_len > 52:
            raise ValueError(f"Cannot pad name to length {total_len} (exceeds maximum of 52 characters).")
        
        # Get the unpadded length
        # Also grab all the padders for subsequent length distribution.
        padders = []
        for p in self.parts:
            if hasattr(p, 'length'):
                p.length = 0
                padders.append(p)
        unpadded_len = self.render_length
        padding = total_len - unpadded_len
        
        if unpadded_len > 52:
            # This name exceeds the maximum length limit of the filter
            warnings.warn(
                f"Displayed item name exceeds maximum length of 52 characters.\n"
                f"  Length={unpadded_len}\n:"
                f"  {str(self)}",
                UserWarning,
                stacklevel=2
                )
        
        if not padders and padding > 0:
            warings.warn(
                f"No padders available to adjust length.\n"
                f"Current render length: {unpadded_len} -> padded length: {total_len}\n"
                f"{self!r}",
                UserWarning,
                stacklevel=2
                )
            return self

        if padding < 0:
            # Name is already long enough
            return self
        
        # Loop through all padders, distributing length until none remains
        i = 0
        quotient, remainder = divmod(padding, len(padders))
        for i, padder in enumerate(padders):
            padder.length = quotient + (1 if i < remainder else 0)

        return self

    def __repr__(self):
        return f'Name({self.parts!r})'

    def __str__(self):
        return ''.join(str(p) for p in self.parts)
    

def build(verbose=False):
    style = read_config()
    general = []
    
    general.append('// Show filter build date in description of Horadric Cube')
    build_date = datetime.today().strftime('%Y-%m-%d')
    version_info = 'ItemDisplay[box]:%NAME%{%NAME%%NL%%GRAY%Loot Goblin Filter %BLACK%| %GRAY% built: '+build_date+'}%CONTINUE%'
    general.append(version_info)

    general.append('// Coloring for items')
    for cond, color in style.colors['text'].items():
        general.append(f'ItemDisplay[{cond}]: {color}%NAME%%CONTINUE%')

    general.append('// Item tier levels')
    for cond, tag in style.tier_tags:
        general.append(f'ItemDisplay[{cond}]: %NAME%{tag}%CONTINUE%')

    general.append('// Tags on left')
    for cond, tag in style.left_tags.items():
        general.append(f'ItemDisplay[{cond}]: {tag}%NAME%%CONTINUE%')

    general.append('// Tags on right')
    for cond, tag in style.right_tags.items():
        general.append(f'ItemDisplay[{cond}]: %NAME%{tag}%CONTINUE%')

    general.append('// Bracketing for unidentified items')
    unidL, unidR = style.unid_brackets
    for cond, color in style.colors['text'].items():
        general.append(f'ItemDisplay[{cond} !ID]: {color}{unidL} %NAME% {color}{unidR}%CONTINUE%')

    general.append('// Add red "*" Stars on Corrupted items in Unique Stygian Caverns Map')
    general.append('ItemDisplay[(ARMOR OR WEAPON OR QUIVER OR rin OR amu) (MAG OR RARE OR SET OR UNI) !ID (MAPID=181 OR MAPID=182)]: %RED%*%NAME%%RED%*%CONTINUE%')

    general.append('// Show quantitiy of stackables')
    general.append('ItemDisplay[!(ARMOR OR WEAPON OR tbk OR ibk OR QUIVER) QTY>1]: %NAME% %TAN%x %WHITE%%QTY%{%NAME%}%CONTINUE%')

    return general


def main():
    lines = build()
    for l in lines:
        print(l)

if __name__ == '__main__':
    main()
