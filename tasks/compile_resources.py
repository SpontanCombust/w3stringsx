import os
import subprocess

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__name__)))

RESOURCES_DIR = os.path.join(ROOT, "packages", "gui", "src", "w3stringsx_gui", "resources")


with os.scandir(RESOURCES_DIR) as it:
    for entry in it:
        if entry.is_file():
            stem, ext = os.path.splitext(entry.path)
            if ext == '.qrc':
                qrc_path = entry.path
                py_path = stem + '_rc.py'
                subprocess.run(f"pyside6-rcc -g python {qrc_path} > {py_path}", shell=True, check=True)
                print("%s --> %s" % (qrc_path, py_path))
       
    