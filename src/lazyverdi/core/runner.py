"""Command execution engine for running verdi commands asynchronously."""

import asyncio
import inspect
import traceback
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Optional

from click.testing import CliRunner


def _is_verdi_command(command_func: Callable[..., object]) -> bool:
    """Check if a command is a VerdiCommand that needs the main verdi context.

    Args:
        command_func: Command function to check

    Returns:
        True if this is a VerdiCommand
    """
    return hasattr(command_func, "__class__") and command_func.__class__.__name__ == "VerdiCommand"


@dataclass
class CommandResult:
    """Result of a command execution."""

    cmd: str
    stdout: str = ""
    stderr: str = ""
    exit_code: Optional[int] = None
    status: Literal["running", "done", "cancelled", "failed"] = "running"
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None

    @property
    def duration(self) -> float:
        """Calculate command execution duration in seconds."""
        if self.end_time is None:
            return (datetime.now() - self.start_time).total_seconds()
        return (self.end_time - self.start_time).total_seconds()

    @property
    def success(self) -> bool:
        """Check if command completed successfully."""
        return self.exit_code == 0 and self.status == "done"


class CommandRunner:
    """Async command runner for verdi commands."""

    # Class-level lock shared by all instances
    # Will be initialized on first use to ensure it's in the correct event loop
    _lock: Optional[asyncio.Lock] = None

    def __init__(self) -> None:
        """Initialize command runner."""
        # Note: We create a new CliRunner for each command invocation
        # to avoid state pollution during concurrent execution
        pass

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Get or create the shared asyncio lock.

        Creates the lock lazily to ensure it's created in the correct event loop.
        """
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    async def run_command(
        self,
        command_func: Callable[..., object],
        args: Optional[list[str]] = None,
        callback: Optional[Callable[[CommandResult], None]] = None,
    ) -> CommandResult:
        """Run a verdi command asynchronously.

        Args:
            command_func: Click command function or regular Python function to execute
            args: Command line arguments (ignored for regular Python functions)
            callback: Optional callback function called on completion

        Returns:
            CommandResult with execution details
        """
        cmd_name = getattr(
            command_func, "name", getattr(command_func, "__name__", str(command_func))
        )
        result = CommandResult(cmd=f"verdi {cmd_name} {' '.join(args or [])}")

        try:
            # Check if this is a regular Python function (not a Click command)
            if inspect.isfunction(command_func) and not hasattr(command_func, "callback"):
                # Direct Python function call
                try:
                    output = await asyncio.to_thread(command_func)
                    result.stdout = str(output) if output else ""
                    result.exit_code = 0
                    result.status = "done"
                except asyncio.CancelledError:
                    result.status = "cancelled"
                    raise
            else:
                # Use asyncio lock to ensure only one command runs at a time
                # This prevents race conditions in AiiDA/Alembic's global state
                async with self._get_lock():
                    # Create a new CliRunner for each invocation
                    cli_runner = CliRunner(mix_stderr=False)

                    # Check if this is a VerdiCommand that needs the main verdi context
                    if _is_verdi_command(command_func):
                        # Import here to avoid circular dependency
                        from aiida.cmdline.commands.cmd_verdi import verdi

                        from lazyverdi.commands.base import VERDI_COMMAND_PATHS

                        # Look up the command path in our mapping
                        cmd_path = VERDI_COMMAND_PATHS.get(id(command_func), [])

                        if cmd_path:
                            verdi_args = cmd_path + (args or [])
                        else:
                            # Fallback: use command's name attribute
                            cmd_name = getattr(command_func, "name", "")
                            verdi_args = [cmd_name] + (args or [])

                        # Run in thread pool to allow cancellation
                        cli_result = await asyncio.to_thread(
                            cli_runner.invoke,
                            verdi,
                            verdi_args,
                            catch_exceptions=True,
                        )
                    else:
                        # Direct command invocation for non-VerdiCommand
                        cli_result = await asyncio.to_thread(
                            cli_runner.invoke,
                            command_func,  # type: ignore[arg-type]
                            args or [],
                            catch_exceptions=True,
                        )

                    # Clean up database session after command execution
                    # This prevents "Instance is not persistent within this Session" errors
                    try:
                        from aiida.manage.manager import get_manager

                        manager = get_manager()
                        if manager.profile_storage_loaded:
                            # Get the backend and close the session
                            backend = manager.get_profile_storage()
                            # Close any open sessions to prevent session leakage
                            # Note: _session_factory is a private attribute of
                            # SQLAlchemy storage backend
                            if hasattr(backend, "_session_factory"):  # type: ignore[attr-defined]
                                # For SQLAlchemy backends, remove the scoped session
                                session_factory = backend._session_factory  # type: ignore[attr-defined]
                                if hasattr(session_factory, "remove"):
                                    session_factory.remove()
                    except Exception:
                        # Ignore session cleanup errors - not critical
                        pass

                result.stdout = cli_result.output
                result.stderr = cli_result.stderr_bytes.decode() if cli_result.stderr_bytes else ""
                result.exit_code = cli_result.exit_code
                result.status = "done" if cli_result.exit_code == 0 else "failed"

                # If command failed with exception, include full traceback in stderr
                if cli_result.exception:
                    exc_type = type(cli_result.exception).__name__
                    exc_msg = str(cli_result.exception)
                    exc_tb = "".join(
                        traceback.format_exception(
                            type(cli_result.exception),
                            cli_result.exception,
                            cli_result.exception.__traceback__,
                        )
                    )

                    if not result.stderr:
                        result.stderr = f"{exc_type}: {exc_msg}\n\n{exc_tb}"
                    else:
                        result.stderr += f"\n\n{exc_type}: {exc_msg}\n\n{exc_tb}"

        except asyncio.CancelledError:
            result.status = "cancelled"
            raise
        except Exception as e:
            result.status = "failed"
            result.stderr = str(e)
            result.exit_code = 1
        finally:
            result.end_time = datetime.now()
            if callback:
                callback(result)

        return result
