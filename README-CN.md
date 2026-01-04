# lazyverdi


| ![PyPI](https://img.shields.io/pypi/v/lazyverdi)                            | ![Python](https://img.shields.io/pypi/pyversions/lazyverdi)                               | ![Downloads](https://img.shields.io/pypi/dm/lazyverdi)                               |
| --------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| ![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen) | ![Ruff](https://img.shields.io/badge/lint-ruff-blue)                                      | ![mypy](https://img.shields.io/badge/type%20checker-mypy-blue)                       |
| ![License](https://img.shields.io/github/license/xbugs221/lazyverdi)        | ![codecov](https://codecov.io/gh/xbugs221/lazyverdi/graph/badge.svg?token=8C8PVUV6UD)<br> | ![CI](https://github.com/xbugs221/lazyverdi/actions/workflows/publish.yml/badge.svg) |


[English Documentation](README.md)

键盘驱动的 AiiDA verdi 命令 TUI 前端，让你像用 lazygit 一样优雅地管理 AiiDA

<img width="1440" height="869" alt="final" src="https://github.com/user-attachments/assets/e6bcfd73-1caa-4d53-8d23-32ea1d2224af" />

## 为什么做这个

verdi 命令行的几个痛点：

- **低效**: 反复输入 `verdi process list` → 筛选 → `verdi process kill PK` → 查看日志
- **无状态**: 命令之间不断丢失上下文
- **批量操作困难**: 需要编写脚本

参考 [lazygit](https://github.com/jesseduffield/lazygit)/[lazydocker](https://github.com/jesseduffield/lazydocker) 设计的 TUI 工具，做到：

- 键盘驱动，操作跟手
- 异步执行，不打断心流
- 多选和批量操作（vim 快捷键）

## 安装

lazyverdi 依赖 aiida-core 库，请安装到包含它的虚拟环境

```bash
uv pip install lazyverdi
lazyverdi
```

## 开发

```bash
uv pip install -e ".[dev]"
pre-commit install
pytest tests/  # 需要 ≥70% 覆盖率
```

## 功能状态

- ✅ 7 面板 UI 布局 + 异步命令执行
- ✅ Vim 风格键盘导航
- ✅ 配置系统（`~/.config/lazyverdi/config.yaml`）

**限制**：仅支持查询命令（list/show/status），不支持交互式命令

## 配置规则

配置文件位置 `~/.config/lazyverdi/config.yaml`，遵从 yaml 语法

| 参数名称                     | 类型  | 默认值  | 可选值            | 说明                                                        |
| ---------------------------- | ----- | ------- | ----------------- | ----------------------------------------------------------- |
| theme                        | str   | monokai | 任意 Textual 主题 | 配色主题                                                    |
| auto_refresh_interval        | float | 10      | ≥0.1 或 ≤0        | 自动刷新间隔，单位秒；支持浮点数；设置为 0 或负数表示禁用   |
| auto_refresh_on_startup      | bool  | true    | true/false        | 应用启动时是否启用自动刷新                                  |
| left_panel_width_percent     | int   | 40      | 1-99              | 左侧面板宽度百分比（右侧面板自动占用剩余空间）              |
| results_panel_height_percent | int   | 80      | 1-99              | 结果面板（panel-0）高度百分比                               |
| focused_panel_height_percent | int   | 50      | 1-99              | 面板获得焦点时的高度百分比                                  |
| show_line_numbers            | bool  | false   | true/false        | 是否在文本区域显示行号                                      |
| soft_wrap                    | bool  | true    | true/false        | 是否启用长行软换行                                          |
| scrollbar_vertical_width     | int   | 1       | 1-3               | 垂直滚动条宽度（字符数）                                    |
| scrollbar_horizontal_height  | int   | 1       | 1-3               | 水平滚动条高度（字符数）                                    |
| show_welcome_message         | bool  | true    | true/false        | 启动时是否显示欢迎消息                                      |
| initial_focus_panel          | int   | 0       | 0-6               | 启动时默认聚焦的面板（0=details, 1-5=左侧面板, 6=状态面板） |
## 许可证

MIT 许可证
