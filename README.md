Rimealogy
=========

Python script to generate family (genealogical) trees from RimWorld save files.

Usage
-----

From a command prompt:

    ./Rimealogy.py InputFileName.rws OutputFileName.dot DrawSelection NameSelection

To avoid spoiling yourself too much, the last two (optional) parameters control which pawns are included and/or named in the tree.

DrawSelection controls which pawns to draw the tree(s) from (so those and *every named character related to them* will be drawn):

 * colony: Your own colonists
 * seen: All characters you've seen (visitors, raiders, etc...)
 * all: All human characters

NameSelection controls which character have their name shown:
 * seen: All characters you've seen will be named
 * related: Characters directly related (parent/child as well as romance or ex-romance) to your own colonists will be named
 * all: Show all names
