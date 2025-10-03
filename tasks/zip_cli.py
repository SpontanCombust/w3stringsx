import os
from pathlib import Path
import zipapp
import zipfile
import zlib

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__name__)))

TARGET_DIR= os.path.join(ROOT, 'out')
TARGET_ZIPAPP= os.path.join(TARGET_DIR, 'w3stringsx.pyz')
WHITELIST = [
    "w3stringsx/*.py",
    "w3stringsx/lib/*.py",
    "w3stringsx/svc/*.py",
    "w3stringsx/cli/*.py",
]
BLACKLIST = [
    '*/__pycache__',
    '*/__pycache__/*',
    '*.log'
]
BOOTSTRAP_DIR = os.path.join(ROOT, 'bootstrap', 'cli')
TARGET_ZIP = os.path.join(TARGET_DIR, 'w3stringsx.zip')


if not os.path.isdir(TARGET_DIR):
    os.mkdir(TARGET_DIR)
    print('Created output directory ' + TARGET_DIR)

def source_filter(p: Path):
    is_on_whitelist = any(p.match(pat) for pat in WHITELIST)
    is_on_blacklist = any(p.match(pat) for pat in BLACKLIST)
    if is_on_whitelist and not is_on_blacklist:
        print(p)
        return True
    return False

zipapp.create_archive(
    source=os.path.join(ROOT, 'src'),
    main='w3stringsx.cli.__main__:main',
    target=TARGET_ZIPAPP,
    filter=source_filter
)


with zipfile.ZipFile(TARGET_ZIP, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=zlib.Z_DEFAULT_COMPRESSION) as zip:
    zip.write(TARGET_ZIPAPP, os.path.basename(TARGET_ZIPAPP))
    for bootstrap_file in os.listdir(BOOTSTRAP_DIR):
        print(bootstrap_file)
        zip.write(os.path.join(BOOTSTRAP_DIR, bootstrap_file), bootstrap_file)


print('w3stringsx CLI has been successfully packaged to ' + TARGET_ZIP)