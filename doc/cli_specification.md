```
usage: w3stringsx.py [-h] [-o OUTPUT_DIR] [-l LANG] [-k] input_file

w3stringsx v1.0.0
Script meant to provide an alternative CLI frontend for w3strings encoder to make it simpler and faster to create localized Witcher 3 content

positional arguments:
  input_file            path to either .csv file (to encode) or .w3strings (to decode)

options:
  -h, --help            show this help message and exit
  -o OUTPUT_DIR, --output_dir OUTPUT_DIR
                        output directory for resulting files [default is input file's directory]
  -l LANG, --language LANG
                        set the target encoding language, "all" will generate all possible variants; available: ['an', 'br', 'cn', 'cz', 'de', 'en', 'es', 'esmx', 'fr', 'hu', 'it', 'jp', 'kr', 'pl', 'ru', 'tr', 'zh', 'all']
  -k, --keep-csv        keep the final form of the CSV file generated during preperation for encoding
```
