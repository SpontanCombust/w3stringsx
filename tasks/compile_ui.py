import os
import subprocess

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__name__)))

UI_DIR = os.path.join(ROOT, "src", "w3stringsx", "gui", "views")


for root, _, files in os.walk(UI_DIR):
    for file in files:
        stem, ext = os.path.splitext(file)
        if ext == '.ui':
            ui_path = os.path.join(root, file)
            py_path = os.path.join(root, stem + '.py')
            subprocess.run(f"pyside6-uic {ui_path} -o {py_path}", shell=True, check=True)
            print("%s --> %s" % (ui_path, py_path))
    