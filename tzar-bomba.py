#!/bin/env python3
#
# Copyright 2016 Windsor Schmidt <windsor.schmidt@gmail.com>
#
# License: MIT License. Let me know if you find this useful.
#
# This is intended to be called by EESchema's BOM generation tool as a plugin.
# The "Command line" field of the plugin dialog should look something like:
#
# /path/to/tzar-bomba.py "%I" "%O" /path/to/parts.sqlite
#
# For each schematic component, the value of custom field "part" is used to
# extract details associated with that component from the sqlite3 database.
#
# Following a successful run, a new bill-of-materials file should be waiting
# for you in your project folder (e.g. project.csv).

from collections import defaultdict
from lxml import etree
import sqlite3
import csv
import sys

# Using argpase would be safer, but hey, who wants to live forever!

infile = sys.argv[1]   # XML bill-of-materials, exported from KiCad
outfile = sys.argv[2] + '.csv'  # The comma delimited file we'll be writing to
dbfile = sys.argv[3]   # A sqlite3 database holding component information

# Pull our internal part number field from each component in the XML file, and
# use it to build up a dictionary where the keys are unique part numbers, and
# the values are lists of component references sharing those part numbers.

missing_refs = []
bom = defaultdict(list)  # refs grouped by unique internal part numbers
components = etree.parse(infile).findall('.//comp')
for c in components:
    ref = c.attrib['ref']
    pns = c.findall("./fields/field[@name='internal_part']")
    if len(pns) == 1:
        bom[pns[0].text].append(ref)
    else:
        missing_refs.append(ref)

# Gather details about our internal part numbers from our sqlite database, and
# build up a list of line items with that data, along with component quantity
# and associated reference designators.

line_items = []
db = sqlite3.connect(dbfile)
cur = db.execute('select * from parts')
header = [['Quantity'] +
          [str.title(row[0].replace('_', ' ')) for row in cur.description] +
          ['Reference(s)']]
for part in bom:
    line = [str(len(bom[part]))]
    query = "SELECT * from parts where internal_part is '" + part + "'"
    cur = db.execute(query)
    for row in cur:
        for col in row:
            line.append(col)
    line.append(', '.join(bom[part]))
    line_items.append(line)
db.close()

# Print a summary and save our line items as a comma delimited file.

print('Setting us up the BOM...')
print('Part references : ' + str(len(components)))
print('BOM line items  : ' + str(len(line_items)))
if len(missing_refs):
    print('UNRESOLVED REFERENCES : ' + ', '.join(missing_refs))

with open(outfile, 'w') as csvfile:
    w = csv.writer(csvfile, delimiter=',')
    for line in header + line_items:
        w.writerow(line)

print('BOM written to ' + outfile)
