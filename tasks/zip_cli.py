import os
import zipapp

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__name__)))

TARGET_DIR= os.path.join(ROOT, 'out')
TARGET= os.path.join(TARGET_DIR, 'w3stringsx.pyz')
BLACKLIST = [
    '*/__pycache__',
    '*/__pycache__/*',
    '*.log'
]


if not os.path.isdir(TARGET_DIR):
    os.mkdir(TARGET_DIR)
    print('Created output directory ' + TARGET_DIR)

zipapp.create_archive(
    source=os.path.join(ROOT, 'src'),
    main='w3stringsx.cli.__main__:main',
    target=TARGET,
    filter=(lambda p: all(not p.match(pat) for pat in BLACKLIST)) # allow only files that do not match any of the patterns in BLACKLIST
)

print('w3stringsx CLI has been successfully packaged to ' + TARGET)