```
usage: w3stringsx.exe [-h] [-o OUTPUT_DIR] [-l LANGS] [-k] [-s SEARCH]
                      [-w WARN_LEVEL]
                      input_path

w3stringsx v2.0.0
https://github.com/SpontanCombust/w3stringsx

Script acting as an alternative CLI frontend for w3strings encoder while also providing additional functionalities to make working with localized Witcher 3 content easier and faster.

positional arguments:
  input_path            path to a file [.w3strings, .csv, .xml, .ws] or a directory with [.xml, .ws] files

options:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        output directory to place the output in; default: [input file's directory]
  -l LANGS, --language LANGS
                        set the target encoding language, argument may be passed multiple times; omitting this argument will generate all possible variants; available: ['ar', 'br', 'cn', 'cz', 'de', 'en', 'es', 'esmx', 'fr', 'hu', 'it', 'jp', 'kr', 'pl', 'ru', 'tr', 'zh']
  -k, --keep-csv        keep the final form of the generated CSV file
  -s SEARCH, --search SEARCH
                        text that will be used to search localisation string keys; can accept regular expressions
  -w WARN_LEVEL, --warn WARN_LEVEL
                        logging level that should be used; available: [0 - no logs, 1 - only errors, 2 - errors and warnings, 3 - everything]; default: 3

remarks:
  * --language and --keep-csv arguments apply only to CSV file context
  * --search option applies only to XML, WitcherScript and directory contexts
```
