```
usage: w3stringsx.py [-h] [-o OUTPUT_PATH] [-l LANG] [-k] [-s SEARCH]
                     [-w WARN_LEVEL]
                     input_path

w3stringsx v1.2.0
Script meant to provide an alternative CLI frontend for w3strings encoder to make it simpler and faster to create localized Witcher 3 content

positional arguments:
  input_path            path to a file [.w3strings, .csv, .xml, .ws] or a directory with [.xml, .ws] files

options:
  -h, --help            show this help message and exit
  -o OUTPUT_PATH, --output_path OUTPUT_PATH
                        path to the output; default: [input file's directory]
  -l LANG, --language LANG
                        set the target encoding language, "all" will generate all possible variants; available: ['ar', 'br', 'cn', 'cz', 'de', 'en', 'es', 'esmx', 'fr', 'hu', 'it', 'jp', 'kr', 'pl', 'ru', 'tr', 'zh', 'all']
  -k, --keep-csv        keep the final form of the generated CSV file
  -s SEARCH, --search SEARCH
                        text that will be used to search localisation string keys; can accept regular expressions
  -w WARN_LEVEL, --warn WARN_LEVEL
                        logging level that should be used; available: [0 - no logs, 1 - only errors, 2 - errors and warnings, 3 - everything]; default: 3

remarks:
  * in the case of CSV file context, the output path must be a directory
  * --language and --keep-csv arguments apply only to CSV file context
  * --search option applies only to XML and WitcherScript contexts
```
