<img src="doc/banner.png"/>

---

Script that can be used as an alternative CLI frontend for w3strings encoder while also providing additional functionalities to make working with localized Witcher 3 content easier and faster.

w3stringsx is able to work with the regular form of the CSV file. It is however also capable of reading non-standard data format, which is explained later in this document.

## How-To
Put the encoder in the same folder as this script or somehere in the PATH environment variable. Run commands on the script using shell of your choice like cmd.exe.

Requires [python](https://www.python.org/downloads/) in version >= 3.11 to be installed.
Current CLI specification can be found [here](./doc/cli_specification.md).


## Features

### Input context awareness
Script performs a different action based on the type of file given to it.
```shell
# Encodes the file
python w3stringsx.py "path\to\en.csv"

# Decodes the file
python w3stringsx.py "path\to\en.w3strings"
```

#### Supported input contexts:
- .csv file - w3strings encoding
- .w3strings file - w3strings decoding
- .xml file - parsing menu XML file for displayName attributes or bundled XML file for localisation keys
- .ws file - parsing WitcherScript file for localisation keys
- directory - scanning a directory recursively for WitcherScript or XML files to parse


### Header optionality
The encoder requires these two lines to be present in the CSV file at the very beginning:
```csv
;meta[language=en]
; id      |key(hex)|key(str)| text
```
w3stringsx takes care of adding these for you, so you don't have to add them yourself.

Script does not modify the file you give it. It creates a temporary one where the final result is saved. Normally it gets deleted after it is done, but you can choose to keep it by adding `-k` or `--keep-csv` flag in the terminal.

### Language context awareness
w3stringsx will specify language metadata automatically based on file name. If it's `en.csv` then it will set `meta[language=en]`, if it's `es.csv` it will set `meta[language=es]`, if `ar.csv` then `meta[language=cleartext]` and so on. 

Files don't have to be named exactly that, only one of the components divided by the dot needs to be the language identifier, for example `w3ee.en.final.csv`.

If the traditional CSV header is still present, it will take the metadata from there. If no language metadata could be deduced in any way it defaults to English (`meta[language=en]`).

### ID space deduction
Script will go through all the records in the CSV file and see what ID space is used. For example
```csv
2115018009|        |panel_Mods|Mods
``` 
yields 5018. This ID will be passed onto the encoder.

If the file contains vanilla IDs it will disable the ID check. The entire process is accompanied by informative messages so you know if everything was read correctly.

### Abbreviated entries
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

If there exists at least one complete entry in the file with the ID in proper mod ID space, the `;idspace` header is no longer needed.

Note that you can still add complete lines with IDs if you want to edit vanilla strings or give some of the entries a predefined ID (for whatever reason). The script ensures that there will be no ID collisions when complete lines are generated from abbreviated ones.

### Encoding all possible languages
Even if your mod was not made with some languages in mind, their respective w3strings files still need to be created so that modded text appears properly, even if in a different language. This is usually done by first encoding one w3strings file in the language of your choosing, for example English as en.w3strings. Then that file is copied and renamed to es.w3strings, fr.w3strings and so on.

w3stringsx can to this automatically after encoding. The `-l` or `--language` option specifies the target encoding language. It can take `"all"` value, which means it will create w3strings file for every possible language. It is the default value.
```shell
# Creates all possible w3strings files
python w3stringsx.py "path\to\en.csv"

# Creates only en.w3strings
python w3stringsx.py "path\to\en.csv" -l "en"
```

### XML and WitcherScript parsing
Passing menu XMLs or WitcherScript (.ws) files to the script allows to scan them for string keys. 
In the case of config XMLs they're searched in `displayName` attributes, in bundled XMLs in `localisation_key_name` and other similair attributes that may hold localisation keys. In scripts however, they are looked for in quoted text that appear in the code.

To narrow down the pool of possible candidates, `--search` option. It should contain a pattern that will be looked for in these files. Said pattern can be a regular expression if you need the search to be more strict than looking for some singular, simple substring.

Parsed entries are saved to a .csv file that contains abbreviated localisation entries for you to fill in.