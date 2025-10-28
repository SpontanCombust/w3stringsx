# w3stringsx-gui

w3stringsx GUI application.


## Development

- Initialize project
```sh
pip install uv
uv sync --frozen
```

- Run the app (on Windows)
```sh
uv run task build windows # required only when doing this for the first time
uv run task dev
```

- Build the app (for Windows), artifacts get saved to *build/windows* directory
```sh
uv run --no-sync --no-editable task build windows
```