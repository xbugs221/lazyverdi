"""Batch data loader for efficient startup loading.

This module provides a mechanism to load all panel data in a single database session,
avoiding SQLAlchemy session conflicts while minimizing startup time.
"""

from typing import Any, Optional

from aiida.cmdline.commands.cmd_calcjob import verdi_calcjob
from aiida.cmdline.commands.cmd_code import code_list
from aiida.cmdline.commands.cmd_computer import computer_list
from aiida.cmdline.commands.cmd_config import verdi_config_list
from aiida.cmdline.commands.cmd_daemon import status as daemon_status
from aiida.cmdline.commands.cmd_group import group_list
from aiida.cmdline.commands.cmd_node import node_list
from aiida.cmdline.commands.cmd_plugin import plugin_list
from aiida.cmdline.commands.cmd_process import process_list
from aiida.cmdline.commands.cmd_profile import profile_list
from aiida.cmdline.commands.cmd_storage import storage_info
from click.testing import CliRunner

from lazyverdi.commands.base import get_aiida_status


def _run_command_in_batch(command_func: Any, args: list[str]) -> tuple[str, str, int]:
    """Run a single command and return its output.

    Args:
        command_func: Command function to execute
        args: Command arguments

    Returns:
        Tuple of (stdout, stderr, exit_code)
    """
    # Handle non-Click commands (pure Python functions)
    if callable(command_func) and not hasattr(command_func, "callback"):
        try:
            output = command_func()
            return str(output) if output else "", "", 0
        except Exception as e:
            return "", str(e), 1

    # Handle Click commands
    cli_runner = CliRunner(mix_stderr=False)

    # Check if this is a VerdiCommand that needs main verdi context
    is_verdi_command = (
        hasattr(command_func, "__class__") and command_func.__class__.__name__ == "VerdiCommand"
    )

    try:
        if is_verdi_command:
            from aiida.cmdline.commands.cmd_verdi import verdi

            from lazyverdi.commands.base import VERDI_COMMAND_PATHS

            # Look up the command path in our mapping
            cmd_path = VERDI_COMMAND_PATHS.get(id(command_func), [])

            if cmd_path:
                verdi_args = cmd_path + args
            else:
                # Fallback: use command's name attribute
                cmd_name = getattr(command_func, "name", "")
                verdi_args = [cmd_name] + args

            cli_result = cli_runner.invoke(verdi, verdi_args, catch_exceptions=True)
        else:
            # For non-VerdiCommand Click commands, invoke directly
            cli_result = cli_runner.invoke(command_func, args, catch_exceptions=True)  # type: ignore[arg-type]

        stdout = cli_result.output
        stderr = cli_result.stderr_bytes.decode() if cli_result.stderr_bytes else ""
        exit_code = cli_result.exit_code or 0

        return stdout, stderr, exit_code
    except Exception as e:
        return "", str(e), 1


def load_all_startup_data() -> dict[str, dict[str, Any]]:
    """Load data for all panels in a single batch operation.

    This function executes all startup commands sequentially in the same thread/session,
    avoiding SQLAlchemy session conflicts while being faster than running commands
    separately in isolated sessions.

    Returns:
        Dictionary mapping panel_id -> tab_name -> command_result
        Example:
        {
            "panel-1": {
                "computer": {"stdout": "...", "stderr": "...", "exit_code": 0}
            },
            ...
        }
    """
    results: dict[str, dict[str, Any]] = {}

    # Define commands for each panel's default tab
    # Only load the first (default) tab for each panel at startup
    commands_to_run = [
        ("panel-1", "computer", computer_list, []),  # -r flag already in VERDI_COMMAND_PATHS
        ("panel-2", "process", process_list, []),
        ("panel-3", "group", group_list, []),
        ("panel-4", "config", verdi_config_list, ["--"]),
        ("panel-5", "status", get_aiida_status, []),
    ]

    # Execute all commands sequentially in the same session
    for panel_id, tab_name, cmd_func, args in commands_to_run:
        try:
            stdout, stderr, exit_code = _run_command_in_batch(cmd_func, args)

            if panel_id not in results:
                results[panel_id] = {}

            results[panel_id][tab_name] = {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": exit_code,
            }
        except Exception as e:
            if panel_id not in results:
                results[panel_id] = {}

            results[panel_id][tab_name] = {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
            }

    return results


def load_tab_data(
    panel_id: str, tab_name: str, command_func: Any, args: list[str]
) -> dict[str, Any]:
    """Load data for a specific tab when user switches to it.

    Args:
        panel_id: Panel identifier (e.g., "panel-1")
        tab_name: Tab name (e.g., "code", "plugin")
        command_func: Command function to execute
        args: Command arguments

    Returns:
        Command result dictionary with stdout, stderr, exit_code
    """
    try:
        stdout, stderr, exit_code = _run_command_in_batch(command_func, args)
        return {
            "stdout": stdout,
            "stderr": stderr,
            "exit_code": exit_code,
        }
    except Exception as e:
        return {
            "stdout": "",
            "stderr": str(e),
            "exit_code": 1,
        }
