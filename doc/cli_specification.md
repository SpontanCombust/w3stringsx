```
usage: w3stringsx.py [-h] [-o OUTPUT_PATH] [-l LANG] [-k] [-p PREFIX]
                     input_path

w3stringsx v1.0.0
Script meant to provide an alternative CLI frontend for w3strings encoder to make it simpler and faster to create localized Witcher 3 content

positional arguments:
  input_path            path to a file [.w3strings, .csv, .xml, .ws] or directory [scripts]

options:
  -h, --help            show this help message and exit
  -o OUTPUT_PATH, --output_path OUTPUT_PATH
                        path to the output; default: [input file's directory]
  -l LANG, --language LANG
                        set the target encoding language, "all" will generate all possible variants; available: ['an', 'br', 'cn', 'cz', 'de', 'en', 'es', 'esmx', 'fr', 'hu', 'it', 'jp', 'kr', 'pl', 'ru', 'tr', 'zh', 'all']
  -k, --keep-csv        keep the final form of the generated CSV file
  -p PREFIX, --prefix PREFIX
                        mod string prefix used to identify localized strings in WitcherScript files

remarks:
  * in the case of CSV file context, the output path must be a directory
  * --language and --keep-csv arguments apply only to CSV file context
  * --prefix option applies only to WitcherScript file and scripts folder context
```
