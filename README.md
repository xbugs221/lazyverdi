# lazyverdi


| ![PyPI](https://img.shields.io/pypi/v/lazyverdi)<br>                        | ![Python](https://img.shields.io/pypi/pyversions/lazyverdi)                          | ![Downloads](https://img.shields.io/pypi/dm/lazyverdi)                                    |
| --------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| ![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen) | ![Ruff](https://img.shields.io/badge/lint-ruff-blue)                                 | ![mypy](https://img.shields.io/badge/type%20checker-mypy-blue)                            |
| ![License](https://img.shields.io/github/license/xbugs221/lazyverdi)    | ![CI](https://github.com/xbugs221/lazyverdi/actions/workflows/publish.yml/badge.svg) | ![codecov](https://codecov.io/gh/xbugs221/lazyverdi/graph/badge.svg?token=8C8PVUV6UD) |


[中文文档](README-CN.md)

A keyboard-driven TUI frontend for AiiDA verdi commands, manage AiiDA as elegantly as you use lazygit

<img width="1440" height="869" alt="final" src="https://github.com/user-attachments/assets/e6bcfd73-1caa-4d53-8d23-32ea1d2224af" />


## Why this project

Pain points of verdi command line:

- **Inefficient**: Repeatedly typing `verdi process list` → filtering → `verdi process kill PK` → checking logs
- **Stateless**: Context is constantly lost between commands
- **Difficult batch operations**: Requires writing scripts

A TUI tool designed with reference to [lazygit](https://github.com/jesseduffield/lazygit)/[lazydocker](https://github.com/jesseduffield/lazydocker), achieving:

- Keyboard-driven, responsive operations
- Asynchronous execution, no workflow interruption
- Multi-selection and batch operations (vim keybindings)

## Installation

lazyverdi depends on the aiida-core library, please install it in a virtual environment that contains it

```bash
uv pip install lazyverdi
lazyverdi
```

## Development

```bash
uv pip install -e ".[dev]"
pre-commit install
pytest tests/  # Requires ≥70% coverage
```

## Feature Status

- ✅ 7-panel UI layout + asynchronous command execution
- ✅ Vim-style keyboard navigation
- ✅ Configuration system (`~/.config/lazyverdi/config.yaml`)

**Limitation**: Only supports query commands (list/show/status), does not support interactive commands

## Configuration Rules

Configuration file location: `~/.config/lazyverdi/config.yaml`, follows YAML syntax

| Parameter Name               | Type  | Default | Options           | Description                                                                                |
| ---------------------------- | ----- | ------- | ----------------- | ------------------------------------------------------------------------------------------ |
| theme                        | str   | monokai | Any Textual theme | Color theme                                                                                |
| auto_refresh_interval        | float | 10      | ≥0.1 or ≤0        | Auto-refresh interval in seconds; supports floating point; set to 0 or negative to disable |
| auto_refresh_on_startup      | bool  | true    | true/false        | Whether to enable auto-refresh on application startup                                      |
| left_panel_width_percent     | int   | 40      | 1-99              | Left panel width percentage (right panel automatically occupies remaining space)            |
| results_panel_height_percent | int   | 80      | 1-99              | Results panel (panel-0) height percentage                                                  |
| focused_panel_height_percent | int   | 50      | 1-99              | Height percentage when panel gains focus                                                   |
| show_line_numbers            | bool  | false   | true/false        | Whether to show line numbers in text areas                                                 |
| soft_wrap                    | bool  | true    | true/false        | Whether to enable soft wrapping for long lines                                             |
| scrollbar_vertical_width     | int   | 1       | 1-3               | Vertical scrollbar width (in characters)                                                   |
| scrollbar_horizontal_height  | int   | 1       | 1-3               | Horizontal scrollbar height (in characters)                                                |
| show_welcome_message         | bool  | true    | true/false        | Whether to show welcome message on startup                                                 |
| initial_focus_panel          | int   | 0       | 0-6               | Default focused panel on startup (0=details, 1-5=left panels, 6=status panel)             |

## License

MIT License
