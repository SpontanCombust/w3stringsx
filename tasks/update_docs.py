import io
import os
import subprocess

ROOT = os.path.realpath(os.path.dirname(os.path.dirname(__file__)))
ORIG_CWD = os.getcwd()

CLI_DIR = os.path.join(ROOT, "packages", "cli")
DOC_DIR = os.path.join(ROOT, "doc")
CLI_SPEC_PATH = os.path.join(DOC_DIR, "cli_specification.md")

os.chdir(CLI_DIR)
# make sure the packages are setup
subprocess.run('uv sync --locked --no-editable', check=True, shell=True)
# get the spec by envoking the "help" command on CLI
spec = subprocess.run('uv run --no-sync task dev -h', check=True, shell=True, capture_output=True, text=True)

os.chdir(DOC_DIR)
# write spec into a Markdown file in docs
with io.open(CLI_SPEC_PATH, mode='w') as f:
    f.write('```\n')
    f.write(spec.stdout)
    f.write('```\n')

print("CLI spec has been written to " + CLI_SPEC_PATH)

os.chdir(ORIG_CWD)