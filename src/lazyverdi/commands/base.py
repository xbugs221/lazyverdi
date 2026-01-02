"""Base command wrapper for verdi commands."""

from collections.abc import Callable
from typing import Any, Optional

from aiida.cmdline.commands.cmd_calcjob import verdi_calcjob
from aiida.cmdline.commands.cmd_code import code_list
from aiida.cmdline.commands.cmd_computer import computer_list
from aiida.cmdline.commands.cmd_config import verdi_config_list
from aiida.cmdline.commands.cmd_daemon import status as daemon_status
from aiida.cmdline.commands.cmd_group import group_list
from aiida.cmdline.commands.cmd_node import node_list
from aiida.cmdline.commands.cmd_plugin import plugin_list
from aiida.cmdline.commands.cmd_presto import verdi_presto
from aiida.cmdline.commands.cmd_process import process_list
from aiida.cmdline.commands.cmd_profile import profile_list
from aiida.cmdline.commands.cmd_storage import storage_info

from .formatters import (
    format_config_list,
    format_daemon_status,
    format_process_list,
    format_profile_list,
    format_storage_info,
    format_table_output,
    no_format,
)
from .parsers import (
    parse_calcjob_help,
    parse_code_list,
    parse_computer_list,
    parse_group_list,
    parse_node_list,
    parse_plugin_list,
    parse_process_list,
)


def get_aiida_status() -> str:
    """Get AiiDA status information directly from internal APIs.

    This function replicates the behavior of 'verdi status' without using subprocess.

    Returns:
        Formatted status string
    """
    from aiida import __version__

    output_lines = []

    # Version
    output_lines.append(f"✔ version:     AiiDA v{__version__}")

    # Config directory
    try:
        from aiida.manage.configuration.settings import AiiDAConfigDir

        config_dir = AiiDAConfigDir.get()
        output_lines.append(f"✔ config:      {config_dir}")
    except Exception as e:
        output_lines.append(f"✘ config:      {e}")
        return "\n".join(output_lines)

    # Get config and profile - gracefully handle missing config
    try:
        from aiida.manage.configuration import get_config

        config = get_config()
        profile_name = config.default_profile_name
    except Exception:
        # Config file doesn't exist - this is expected for first-time users
        output_lines.append("⚠ profile:     No profile configured")
        output_lines.append("")
        output_lines.append("To set up AiiDA, run:")
        output_lines.append("  verdi quicksetup")
        return "\n".join(output_lines)

    if not profile_name:
        output_lines.append("⚠ profile:     No profile configured")
        output_lines.append("")
        output_lines.append("To set up AiiDA, run:")
        output_lines.append("  verdi quicksetup")
        return "\n".join(output_lines)

    profile = config.get_profile(profile_name)
    output_lines.append(f"✔ profile:     {profile.name}")

    # Load profile
    try:
        from aiida.manage.manager import get_manager

        manager = get_manager()
        manager.load_profile(profile.name)
    except Exception as e:
        output_lines.append(f"✘ error:       Failed to load profile - {e}")
        return "\n".join(output_lines)

    # Storage
    try:
        storage_backend = profile.storage_cls(profile)
        storage_str = str(storage_backend)
        # Truncate if too long
        if len(storage_str) > 60:
            storage_str = storage_str[:57] + "..."
        output_lines.append(f"✔ storage:     {storage_str}")
    except Exception as e:
        output_lines.append(f"✘ storage:     {type(e).__name__}")

    # Broker
    try:
        broker = manager.get_broker()
        if broker:
            broker.get_communicator()
            broker_str = str(broker)
            if len(broker_str) > 60:
                broker_str = broker_str[:57] + "..."
            output_lines.append(f"✔ broker:      {broker_str}")
        else:
            output_lines.append("⚠ broker:      No broker")
    except Exception:
        output_lines.append("✘ broker:      Unable to connect")

    # Daemon
    try:
        daemon_client = manager.get_daemon_client()
        daemon_status = daemon_client.get_status()
        if daemon_status:
            pid = daemon_status.get("pid", "unknown")
            output_lines.append(f"✔ daemon:      Running (PID {pid})")
        else:
            output_lines.append("✘ daemon:      Not running")
    except Exception:
        output_lines.append("✘ daemon:      Error")

    return "\n".join(output_lines)


# Panel configurations with tabs for TextArea-based panels
# Format: panel_id -> list of (tab_name, command_func, args, formatter)
PANEL_TABS: dict[
    str, list[tuple[str, Callable[..., Any], list[str], Optional[Callable[[str], str]]]]
] = {
    "panel-4": [
        ("config", verdi_config_list, ["--"], format_config_list),
        ("profile", profile_list, [], format_profile_list),
    ],
    "panel-5": [
        ("status", get_aiida_status, [], no_format),
        ("daemon", daemon_status, [], format_daemon_status),
        ("storage", storage_info, [], format_storage_info),
    ],
}

# Table panel configurations for DataTable-based panels
# Format: panel_id -> list of (tab_name, command_func, args, formatter, parser)
TABLE_TABS: dict[
    str,
    list[
        tuple[
            str,
            Callable[..., Any],
            list[str],
            Optional[Callable[[str], str]],
            Callable[[str], dict[str, Any]],
        ]
    ],
] = {
    "panel-1": [
        ("computer", computer_list, [], format_table_output, parse_computer_list),
        ("code", code_list, [], format_table_output, parse_code_list),
        ("plugin", plugin_list, [], format_table_output, parse_plugin_list),
    ],
    "panel-2": [
        ("process", process_list, [], format_process_list, parse_process_list),
        ("calcjob", verdi_calcjob, ["--help"], no_format, parse_calcjob_help),
    ],
    "panel-3": [
        ("group", group_list, [], format_table_output, parse_group_list),
        ("node", node_list, [], format_table_output, parse_node_list),
    ],
}

# Mapping from command objects to their verdi command paths
# This is needed because VerdiCommand objects need to be invoked through
# the main verdi command to have proper context (ctx.obj) set up
VERDI_COMMAND_PATHS: dict[int, list[str]] = {
    id(computer_list): [
        "computer",
        "list",
        "-r",
        "-a",
    ],  # Use -a to avoid session issues with hide lambda
    id(code_list): ["code", "list"],
    id(plugin_list): ["plugin", "list"],
    id(process_list): ["process", "list"],
    id(verdi_calcjob): ["calcjob"],
    id(verdi_config_list): ["config", "list"],
    id(profile_list): ["profile", "list"],
    id(group_list): ["group", "list"],
    id(node_list): ["node", "list"],
    id(verdi_presto): ["presto"],
    id(daemon_status): ["daemon", "status"],
    id(storage_info): ["storage", "info"],
}

# Legacy: Status panel uses separate command (deprecated, use PANEL_TABS instead)
STATUS_COMMAND: tuple[Callable[..., Any], list[str]] = (get_aiida_status, [])

# Legacy compatibility - keep for now but deprecated
STARTUP_COMMANDS: dict[str, tuple[Callable[..., Any], list[str]]] = {
    "panel-1": (computer_list, []),
    "panel-2": (process_list, []),
    "panel-3": (group_list, []),
    "panel-4": (profile_list, []),
    "panel-5": (get_aiida_status, []),
}


def format_error_message(cmd_name: str, error: str) -> str:
    """Format friendly error message for failed commands.

    Args:
        cmd_name: Command name
        error: Error message

    Returns:
        Formatted user-friendly message
    """
    if "profile" in cmd_name.lower() or "profile" in error.lower():
        return (
            "No AiiDA profile configured.\n\n"
            "Please run:\n"
            "  verdi quicksetup  (for quick setup)\n"
            "  verdi setup       (for detailed setup)"
        )

    if "computer" in cmd_name.lower() and "No" in error:
        return "No computers configured.\n\nUse 'verdi computer setup' to add computers."

    if "process" in cmd_name.lower() and "No" in error:
        return "No processes found.\n\nSubmit calculations to see them here."

    return error or "Command failed"
