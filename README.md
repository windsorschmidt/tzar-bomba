# About

This script assists generating bills-of-materials (BOMs) as comma-delimited data using KiCad's schematic capture tool EESchema. The script looks for a special custom field added to schematic components which represents an internal part number. Details about internal part numbers are injected in to the output file from a sqlite3 database

# Requirements

- Python 3 with (and libraries: lxml, sqlite3, and csv)

# Usage

- Using a tool like [sqlitebrowser](http://sqlitebrowser.org/), create a database with a table named `parts` containing a unique, auto-incrementing, integer primary key named `internal_part` and any additional columns desired. Also see the file `example.sqlite`.

- In your schematic, add a custom field named `internal_part` to components, setting the field value to that of the corresponding part (i.e. primary key value) in the sqlite database.

- In EESchema under *Tools -> Generate Bill of Materials*, add a new plugin, giving the paths to the plugin and database files, e.g. `/path/to/kibom.py "%I" "%O" /path/to/parts.sqlite`

- From the same dialog, click "Generate" and the script will run, saving a `.csv` file (in your KiCad project folder and named after your project if using the `%I` and `%O` tokens).

Note: Any component references in the schematic without an `internal_part` field are printed to stdout and captured in the BOM generation dialog under *"Plugin Info."*

# Disclaimer

I wrote this as a quick proof of concept while considering how to keep track of parts for my electronics projects. It's not intended to be secure, robust, or performant. Pull requests or suggestions are welcome, however. Tested with recent versions of KiCad on Linux.
