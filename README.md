<img src="doc/banner.png"/>

<details open>
  <summary>Table of Contents</summary>

- [Synopsis](#synopsis)
- [How-To](#how-to)
- [Features](#features)
  - [Input context awareness](#input-context-awareness)
  - [Header optionality](#header-optionality)
  - [Language context awareness](#language-context-awareness)
  - [ID auto-generation and short entries](#id-auto-generation-and-short-entries)
  - [Multiple ID spaces](#multiple-id-spaces)
  - [Encoding all possible languages](#encoding-all-possible-languages)
  - [Parsing files for localisation keys](#parsing-files-for-localisation-keys)

</details>

---

# Synopsis

Script that can be used as an alternative CLI frontend for w3strings encoder while also providing additional functionalities to make working with localized Witcher 3 content easier and faster.

w3stringsx is able to work with the regular form of the CSV file. It is however also capable of reading non-standard data format, which is explained later in this document.


# How-To
Put the encoder in the same folder as this script or somehere in the PATH environment variable. 
The script can be used by drag-n-dropping .csv or .w3strings files onto the script.
If you want to use the tool to its full advantage however you should use a terminal like cmd.exe.  
Read more about features in the next chapter.

Requires [python](https://www.python.org/downloads/) in version >= 3.11 to be installed.
Current CLI specification can be found [here](./doc/cli_specification.md).

Examples can also be found [here](./examples/) and [here](./tests/).


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

## ID auto-generation and short entries
All string entries need to have a unique ID. w3stringsx can auto-generate them for you.  

Normally for all string entries you need to list the ID, key hash (optional), key string and localization text separated by the '|' character, like so:
```csv
1050180009|        |panel_Mods|Mods
```

With w3stringsx this can be shortened into a version with only key string and localization text:
```csv
panel_Mods|Mods
```

All you have to do to make use of this is to do either of two things:
1. Above your entries add a comment describing the string ID space you want to use:
    ```csv
    ;mod_id=5018
    ```
    This will effectively tell w3stringsx to generate suspequent string IDs starting with `1050180000`, which is a convention suggested by modders on the official Witcher 3 Discord server. It derives this "mod ID" from the number assigned to a modification uploaded to NexusMods website, which is the biggest host of Witcher 3 mods to date.  
    Alternatively if you have used rmemr's w3strings encoder before REDkit in this case you would expect IDs to start from `2115018000`. You can enable this generation method by writing a different comment instead:
    ```csv
    ;mod_id_legacy=5018
    ```
    Note that with this method won't allow you to use mod ID greater than 9999.

2. Before short entries write a complete one:
    ```csv
    1050180000|        |panel_Mods|Mods
    ```
    This will tell w3stringsx that the next short entry after it should have ID `1050180001` and so on. You can put these lines with ID already filled in multiple times to some IDs if you need to. Note that only modded IDs will cause this ID generation context to be set - if you put a string entry with vanilla ID it won't affect the flow of ID generation.

## Multiple ID spaces
With w3stringsx a single CSV file may contain string entries for multiple mods and vanilla strings without a hassle:
```csv
;mod_id=10100
item_name_fireworks|Fireworks
item_desc_firecrackers|Firecrackers
;mod_id=5432
vilgefortz_name|Vilgefortz
;vanilla
350496|43078142||Warrior
302053|67827706||Temple Guard
392738|05dc6a8f||Ghost
```

## Encoding all possible languages
Even if your mod was not made with some languages in mind, their respective w3strings files still need to be created so that modded text appears properly, even if in a different language. This is usually done by first encoding one w3strings file in the language of your choosing, for example English as en.w3strings. Then that file is copied and renamed to es.w3strings, fr.w3strings and so on.

w3stringsx can to this automatically after encoding. The `-l` or `--language` option specifies the target encoding language. Argument may be repeated to encode for more languages. If you want to encode for all possible languages you can simply omit this argument as the default behaviour is to handle all cases. 
```shell
# Creates all possible w3strings files
python w3stringsx.py "path\to\en.csv"

# Creates only en.w3strings and pl.w3strings
python w3stringsx.py "path\to\en.csv" --language "en" --language "pl"
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

Parsed entries are saved to a .csv file that contains short localisation entries for you to localise.
Entries coming from different sources will be seperate by a `;section` comment, for example `;section=scripts`.

If the output file already exists however, w3stringsx will not overwrite the file. It will only add to it those entries that are not yet contained inside it and leave everything else as it was. This saves you from having to retranslate everything every time you parse your project for localisation keys. It also allows to use the same file for entries that cannot be parsed by w3stringsx, i.e. CR2W files.
