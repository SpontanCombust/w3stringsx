import os
from pathlib import Path
import zipapp

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__name__)))

TARGET_DIR= os.path.join(ROOT, 'out')
TARGET= os.path.join(TARGET_DIR, 'w3stringsx_gui.pyzw')
WHITELIST = [
    "w3stringsx/*.py",
    "w3stringsx/lib/*.py",
    "w3stringsx/svc/*.py",
    "w3stringsx/gui/*.py",
    "w3stringsx/gui/resources/*.py",
    "w3stringsx/gui/resources/*.py",
    "w3stringsx/gui/views/*.py"
]
BLACKLIST = [
    '*/__pycache__',
    '*/__pycache__/*',
    '*.log'
]


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
    main='w3stringsx.gui.application:application',
    target=TARGET,
    filter=source_filter
)

print('w3stringsx GUI has been successfully packaged to ' + TARGET)