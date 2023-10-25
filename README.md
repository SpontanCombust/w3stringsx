<img src="doc/banner.png"/>

- [Synopsis](#synopsis)
- [How-To](#how-to)
- [Features](#features)
  - [Input context awareness](#input-context-awareness)
  - [Header optionality](#header-optionality)
  - [Language context awareness](#language-context-awareness)
  - [ID space deduction](#id-space-deduction)
  - [Abbreviated entries](#abbreviated-entries)
  - [Encoding all possible languages](#encoding-all-possible-languages)
  - [Parsing files for localisation keys](#parsing-files-for-localisation-keys)

---

# Synopsis

Script that can be used as an alternative CLI frontend for w3strings encoder while also providing additional functionalities to make working with localized Witcher 3 content easier and faster.

w3stringsx is able to work with the regular form of the CSV file. It is however also capable of reading non-standard data format, which is explained later in this document.


# How-To
Put the encoder in the same folder as this script or somehere in the PATH environment variable. Run commands on the script using shell of your choice like cmd.exe.

Requires [python](https://www.python.org/downloads/) in version >= 3.11 to be installed.
Current CLI specification can be found [here](./doc/cli_specification.md).

You can see some use [here](./examples/) and [here](./tests/).


# Features

## Input context awareness
Script performs a different action based on the type of file given to it.
```shell
# Encodes the file
python w3stringsx.py "path\to\en.csv"

# Decodes the file
python w3stringsx.py "path\to\en.w3strings"
```

**Supported input contexts**:
- .csv file - w3strings encoding
- .w3strings file - w3strings decoding
- .xml file, .ws file or a directory - parsing files for localisation keys (more about it [here](#parsing-files-for-localisation-keys))


## Header optionality
The encoder requires these two lines to be present in the CSV file at the very beginning:
```csv
;meta[language=en]
; id      |key(hex)|key(str)| text
```
w3stringsx takes care of adding these for you, so you don't have to add them yourself.

Script does not modify the file you give it. It creates a temporary one where the final result is saved. Normally it gets deleted after encoding is completed, but you can choose to keep it by adding `-k` or `--keep-csv` flag in the terminal.

## Language context awareness
w3stringsx will specify language metadata automatically based on file name. If it's `en.csv` then it will set `meta[language=en]`, if it's `es.csv` it will set `meta[language=es]`, if `ar.csv` then `meta[language=cleartext]` and so on. 

Files don't have to be named exactly that, only one of the components divided by the dot needs to be the language identifier, for example `w3ee.en.final.csv`.

If the traditional CSV header is still present, it will take the metadata from there. If no language metadata could be deduced in any way it defaults to English (`meta[language=en]`).

## ID space deduction
Script will go through all the records in the CSV file and see what ID space is used. For example
```csv
2115018009|        |panel_Mods|Mods
``` 
yields 5018. This ID will be passed onto the encoder.

If the file contains vanilla IDs it will disable the ID check. The entire process is accompanied by informative messages so you know if everything was read correctly.

## Abbreviated entries
Writing IDs by hand can be tiresome. This is why w3stringsx allows to completely get rid of that step.
At the top of file write a comment that specifies the ID space that should be used:
```csv
;idspace=5018
```
Then you will be able to add records that have only string key and text columns like so:
```csv
panel_Mods|Mods
panel_mod_settings|Mod settings
preset_value_mod_default|Default
```
These entries that contain only string key and text columns are referred to in this project as "abbreviated entries". Entries with all the required columns, that is ID column, hex key, string key and text on the other hand are referred to as "complete entries".

If there exists at least one complete entry in the file with the ID in proper mod ID space, the `;idspace` header can be omitted.

Note that you can still add complete lines with IDs if you want to edit vanilla strings or give some of the entries a predefined ID (for whatever reason). The script ensures that there will be no ID collisions when complete lines are generated from the abbreviated ones.

## Encoding all possible languages
Even if your mod was not made with some languages in mind, their respective w3strings files still need to be created so that modded text appears properly, even if in a different language. This is usually done by first encoding one w3strings file in the language of your choosing, for example English as en.w3strings. Then that file is copied and renamed to es.w3strings, fr.w3strings and so on.

w3stringsx can to this automatically after encoding. The `-l` or `--language` option specifies the target encoding language. It can take `"all"` value, which means it will create w3strings file for every possible language. It is the default value.
```shell
# Creates all possible w3strings files
python w3stringsx.py "path\to\en.csv"

# Creates only en.w3strings
python w3stringsx.py "path\to\en.csv" -l "en"
```

## Parsing files for localisation keys
Aside from providing an alternative way to interact with w3strings program, w3stringsx also allows to a certain degree to search for localisation keys in your project.

Script can search these keys in three types of files:
- user configuration XMLs (*.xml) - looks for `displayName` attribute values in the document (these are the files that get put in `bin/config/r4game/user_config_matrix/pc`)
- definition XMLs (*.xml) - looks for attributes like `localisation_key_name` (these are the files that get packed into .bundle archives)
- WitcherScript (*.ws) - looks for any string literals in the scripts that may be a localisation keys

To not have to parse each file one by one you can just pass a path to the directory containing them all to w3stringsx.

To narrow down the pool of possible candidates, `--search` option is available. It should contain a pattern that will be looked for in these files. Said pattern can be a regular expression if you need the search to be more strict than looking for some singular, simple substring.<br>
Example: if you use `abc_` prefix for localisation keys in your mod you should add `--search "abc_"` argument to the program.
Parsing WitcherScript always requires that option.

Parsed entries are saved to a .csv file that contains abbreviated localisation entries for you to localise.
Entries coming from different sources will be seperate by a `;section` comment, for example `;section=scripts`.

If the output file already exists however, w3stringsx will not overwrite the file. It will only add to it those entries that are not yet contained inside it and leave everything else as it was. This saves you from having to retranslate everything every time you parse your project for localisation keys. It also allows to use the same file for entries that cannot be parsed by w3stringsx, i.e. CR2W files.
