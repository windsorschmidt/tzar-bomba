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
# For each schematic component, the value of custom field "internal_part" is
# an index to that component's detail record in the sqlite3 database.
#
# Following a successful run, exported BOMs in CSV and HTML should be waiting
# for you in your project folder (e.g. project.csv, project.html).

import os
from shutil import copyfile
from collections import defaultdict
from lxml import etree
import sqlite3
import csv
import sys

# Print some basic information about this exporter

print('Setting us up the BOM...')
print('Add DB reference field "internal_part" to schematic symbols.')

# Using argpase would be safer, but hey, who wants to live forever!

infile = sys.argv[1]   # XML bill-of-materials, exported from KiCad
outfile = sys.argv[2]  # The base name of the output files we'll write to
dbfile = sys.argv[3]   # A sqlite3 database holding component information
datasheet_dir = sys.argv[4]  # Where I squirrel away my datasheets

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
header = ['Qty.', 'Reference(s)'] + \
         [str.title(row[0].replace('_', ' ')) for row in cur.description]

for part in bom:
    line = [str(len(bom[part])), ', '.join(bom[part])]
    query = "SELECT * from parts where internal_part is '" + part + "'"
    cur = db.execute(query)
    for row in cur:
        for col in row:
            line.append(col)
    line_items.append(line)
db.close()

# Print a summary to the console (displayed by EESchema's BOM tool)
print('{} line items'.format(len(line_items)))
print('{} part references'.format(len(components)))
if len(missing_refs):
    print('{} {} {}'.format(len(missing_refs),
                            'References without internal part field:',
                            ', '.join(missing_refs)))

# Save as comma-separated values

with open(outfile + '.csv', 'w') as csvfile:
    w = csv.writer(csvfile, delimiter=',')
    for line in [header] + sorted(line_items, key=lambda line: line[1]):
        w.writerow(line)
    print('BOM written to ' + outfile + '.csv')

# Save as HTML

project = etree.parse(infile).findall('design/sheet/title_block/title')[0].text
version = etree.parse(infile).findall('design/sheet/title_block/rev')[0].text
date = etree.parse(infile).findall('design/sheet/title_block/date')[0].text
source = etree.parse(infile).findall('design/source')[0].text
title = 'Bill of Materials: ' + project + ' v' + version

displayed_fields = range(6)

with open(outfile + '.html', 'w') as f:
    f.write('<!DOCTYPE html>\n')
    f.write('<html lang="en">\n')
    f.write('  <head>\n')
    f.write('    <meta charset="utf-8"/>\n')
    f.write('    <title>' + title + '</title>\n')
    f.write('    <link rel="stylesheet" type="text/css" href="style.css">\n')
    f.write('  </head>\n')
    f.write('  <body>\n')
    f.write('    <h1>' + title + '</h1>\n')
    f.write('    <table>\n')
    f.write('      <tr>\n')
    for i, col in enumerate(header):
        if i in displayed_fields:
            f.write('        <th>'
                    + str(col).replace(' ', '&nbsp;') + '</th>\n')
        else:
            f.write('        <th class="hide">' +
                    str(col).replace(' ', '&nbsp;') + '</th>\n')
    f.write('      </tr>\n')
    for row in sorted(line_items, key=lambda line: line[1]):
        datasheet = datasheet_dir + '/' + row[6] if len(row) >= 6 else '#'
        f.write('      <tr>\n')
        for i, col in enumerate(row):
            if i in displayed_fields:
                f.write('        <td>')
            else:
                f.write('        <td class="hide">')
            if i == 3:
                f.write('<a href="' + datasheet + '">' + str(col) + '</a>')
            else:
                f.write(str(col))
            f.write('        </td>\n')
        f.write('      </tr>\n')
    f.write('    </table>\n')
    f.write('  <p>Line items      : {}'.format(len(line_items)) + '<br>\n')
    f.write('  Part references : {}'.format(len(components)) + '<br>\n')
    if len(missing_refs):
        f.write('  <strong>References without internal part field: ' +
                ''.join(missing_refs) + '</strong><br>\n')
    f.write('  Exported from ' + source + '</p>\n')
    f.write('  </body>\n')
    f.write('</html>\n')
    print('BOM written to ' + outfile + '.html')

css_src = os.path.dirname(os.path.realpath(__file__)) + '/style.css'
css_dst = str.join('/', outfile.split('/')[:-1]) + '/style.css'
copyfile(css_src, css_dst)
