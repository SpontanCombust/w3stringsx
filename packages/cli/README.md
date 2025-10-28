# w3stringsx-cli

w3stringsx CLI application.


## Development

- Initialize project
```sh
pip install uv
uv sync --frozen
```

- Run app
```sh
uv run task dev [args]
```

- Build app, artifacts get saved to *dist* directory
```sh
uv run --no-sync --no-editable task build
```