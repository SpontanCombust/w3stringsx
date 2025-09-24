import os
import zipapp

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__name__)))

TARGET_DIR= os.path.join(ROOT, 'out')
TARGET= os.path.join(TARGET_DIR, 'w3stringsx.pyz')
WHITELIST = [
    "w3stringsx/*.py",
    "w3stringsx/lib/*.py",
    "w3stringsx/cli/*.py",
]
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
    filter=(lambda p: any(p.match(pat) for pat in WHITELIST) and all(not p.match(pat) for pat in BLACKLIST))
)

print('w3stringsx CLI has been successfully packaged to ' + TARGET)