"""Helper script that automates the process of working with w3strings encoder"""

import getopt
import io
import os
import sys


all_langs = ['an', 'br', 'cn', 'cz', 'de', 'en', 'es', 'esmx', 'fr', 'hu', 'it', 'jp', 'kr', 'pl', 'ru', 'tr', 'zh']

encoder = os.path.join(os.path.split(__file__)[0], 'w3strings.exe')
if not os.path.exists(encoder):
    raise Exception('Encoder not found! Make sure to place the script in the same directory as the encoder')



def decode(w3strings_path):
    cmd = f'{encoder} -d {w3strings_path}'
    print(cmd)
    os.system(cmd)


def encode(csv_path, lang: str | None, force: bool):
    csv_data = []
    with open(csv_path, encoding='utf-8') as f:
        csv_data = f.readlines()

    if lang is not None and lang not in all_langs and lang != 'all':
        raise Exception(f'Language {lang} is invalid')
    else:
        lang = deduce_language(csv_path, csv_data)

    cmd = f'{encoder} -e {csv_path} '
    if force:
        cmd += '--force-ignore-id-space-check-i-know-what-i-am-doing'
    else:
        csv_id_range = None
        last_id = None
        for i, line in enumerate(csv_data):
            if not line.startswith(';'):
                split = line.split('|')
                if len(split) != 4:
                    raise Exception(f'Line {i + 1} contains invalid amount of columns; expected 4, got {len(split)}')
                
                id = 0
                try:
                    id = int(split[0])
                except:
                    raise Exception(f'Failed to parse ID column into a number at line {i + 1}')
                
                if id not in range(2110000000, 2120000000):
                    raise Exception(f'ID at line {i + 1} falls outside of the expected value range for mods. If this is intended, enable the --force flag to ignore the ID check in the encoder')
                
                id_range = (id % 2110000000) // 1000
                if csv_id_range is not None and id_range != csv_id_range:
                    raise Exception(f'Inconsistent ID range at line {i + 1}. Expected {csv_id_range}, got {id_range}')
                csv_id_range = id_range

                if last_id is not None and id != last_id + 1:
                    print(f'Warning: Non sequential ID detected at line {i + 1}. Expected {last_id + 1}, got {id}')
                last_id = id

        cmd += f'-i {csv_id_range}'

    print(cmd)
    os.system(cmd)
    # todo remove garbage


def deduce_language(csv_path, csv_data: list[str]):
    # trying the file name first
    basename = os.path.basename(csv_path)
    split = str.split(basename, '.')
    maybe_lang = split[0]
    if maybe_lang in all_langs:
        return maybe_lang

    # if that doesn't work, check metadata inside
    for line in csv_data:
        line = line.replace(' ', '') # remove all spaces
        if line.startswith(';'):
            if line.startswith(';meta'):
                # in case of a group of langugaes, 'cleartext' is present as the language
                lang = line.lstrip(';meta[language=').rstrip(']')
                if lang in all_langs:
                    return lang
        # read only the header comments
        else:
            break

    raise Exception('No target language could be deduced')



def print_help():
    print('Helper script that automates the process of working with w3strings encoder')
    print()
    print('USAGE:')
    print('\tpython w3stringsx.py [OPTIONS] <INPUT_FILE>')
    print()
    print('ARGS:')
    print('\t<INPUT_FILE>   - path to either .csv file (to encode) or .w3strings (to decode)')
    print()
    print('OPTIONS:')
    print('\t-h, --help     - print help')
    print('\t-l, --lang     - set the target encoding language, "all" will generate w3strings files for all languages; by default deduced from the CSV file')
    print('\t-f, --force    - enables the flag "--force-ignore-id-space-check-i-know-what-i-am-doing"')

def main(argv: list[str]):
    if len(argv) < 2:
        raise Exception('No input arguments provided')

    if argv[1] in ('-h', '--help'):
        print_help()
        return

    file_path = argv[1]
    lang = None
    force = False

    if not os.path.exists(file_path):
        raise Exception(f'Path does not exist: "{file_path}"')
    elif not os.path.isfile(file_path):
        raise Exception(f'Path does not describe a file: "{file_path}"')

    opts, _ = getopt.getopt(argv[2:], 'hl:f', ['help', 'lang=', 'force'])
    for opt, arg in opts:
        if opt in ('-l', '--lang'):
            lang = arg.lstrip(' =')
        elif opt in ('-f', '--force'):
            force = True


    _, ext = os.path.splitext(file_path)
    if ext == '.w3strings':
        decode(file_path)
    elif ext == '.csv':
        encode(file_path, lang, force)
    else:
        raise Exception(f'Unsupported file type: "{ext}"')



if __name__ == '__main__':
    main(sys.argv)
