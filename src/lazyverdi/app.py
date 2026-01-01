"""Main Textual application entry point."""

import asyncio
import time
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical

from lazyverdi.commands import PANEL_TABS, format_error_message
from lazyverdi.core import CommandRunner
from lazyverdi.core.config import get_config_value
from lazyverdi.ui import InfoPanel, ResultsPanel, StatusPanel


class LazyVerdiApp(App):
    """Keyboard-driven TUI for AiiDA verdi commands."""

    TITLE = "LazyVerdi"
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("?", "help", "Help"),
        Binding("escape", "pop_screen", "Back"),
        Binding("r", "refresh", "Refresh"),
        Binding("j", "scroll_down", "Down"),
        Binding("k", "scroll_up", "Up"),
        Binding("h", "scroll_left", "Left"),
        Binding("l", "scroll_right", "Right"),
        Binding("left", "scroll_left", "Left"),
        Binding("right", "scroll_right", "Right"),
        Binding("g", "scroll_home_trigger", "Top (gg)"),
        Binding("G", "scroll_end", "Bottom"),
        Binding("[", "prev_tab", "Prev Tab"),
        Binding("]", "next_tab", "Next Tab"),
        Binding("0", "focus_results", "Results"),
        Binding("1", "focus_panel_1", "Computer/Code"),
        Binding("2", "focus_panel_2", "Process"),
        Binding("3", "focus_panel_3", "Group/Node"),
        Binding("4", "focus_panel_4", "Config"),
        Binding("5", "focus_panel_5", "Presto"),
        Binding("6", "focus_panel_6", "Status"),
        Binding("a", "toggle_auto_refresh", "Auto-refresh"),
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        """Initialize app."""
        super().__init__(*args, **kwargs)
        self._runner = CommandRunner()
        self._last_g_time: float = 0.0
        self._background_tasks: set = set()
        self._auto_refresh_enabled: bool = get_config_value("auto_refresh_on_startup", True)
        self._auto_refresh_task: Optional[asyncio.Task] = None  # type: ignore[type-arg]
        # No longer need _panel_commands as tabs are stored in InfoPanel

    CSS = """
#right-panels {
    width: 60%;
}

#left-panels {
    width: 40%;
}

/* Default heights for left panels */
#panel-1 {
    height: 1fr;
}

#panel-2 {
    height: 2fr;
}

#panel-3 {
    height: 2fr;
}

#panel-4 {
    height: 1fr;
}

#panel-5 {
    height: 1fr;
}

/* Focused panel takes 50% height */
#panel-1.focused {
    height: 50%;
}

#panel-2.focused {
    height: 50%;
}

#panel-3.focused {
    height: 50%;
}

#panel-4.focused {
    height: 50%;
}

#panel-5.focused {
    height: 50%;
}

/* Compressed panels share remaining space equally */
#panel-1.compressed,
#panel-2.compressed,
#panel-3.compressed,
#panel-4.compressed,
#panel-5.compressed {
    height: 1fr;
}
"""

    def compose(self) -> ComposeResult:
        """Compose the UI layout."""
        with Horizontal(id="main"):
            with Vertical(id="left-panels"):
                yield InfoPanel(1, PANEL_TABS["panel-1"])
                yield InfoPanel(2, PANEL_TABS["panel-2"])
                yield InfoPanel(3, PANEL_TABS["panel-3"])
                yield InfoPanel(4, PANEL_TABS["panel-4"])
                yield InfoPanel(5, PANEL_TABS["panel-5"])
            with Vertical(id="right-panels"):
                yield ResultsPanel(id="panel-0")
                yield StatusPanel(PANEL_TABS["panel-6"])

    def action_focus_results(self) -> None:
        self._reset_left_panel_sizes()
        self.query_one("#panel-0").focus()

    def action_focus_panel_1(self) -> None:
        self.query_one("#panel-1").focus()

    def action_focus_panel_2(self) -> None:
        self.query_one("#panel-2").focus()

    def action_focus_panel_3(self) -> None:
        self.query_one("#panel-3").focus()

    def action_focus_panel_4(self) -> None:
        self.query_one("#panel-4").focus()

    def action_focus_panel_5(self) -> None:
        self.query_one("#panel-5").focus()

    def action_focus_panel_6(self) -> None:
        self._reset_left_panel_sizes()
        self.query_one("#panel-6").focus()

    def _reset_left_panel_sizes(self) -> None:
        for i in range(1, 6):
            panel = self.query_one(f"#panel-{i}")
            panel.remove_class("focused", "compressed")

    def _apply_config_styles(self) -> None:
        """Apply dynamic styles from config."""
        # Apply panel width settings
        left_width = get_config_value("left_panel_width_percent", 40)
        right_width = 100 - left_width

        try:
            left_panels = self.query_one("#left-panels")
            left_panels.styles.width = f"{left_width}%"
            right_panels = self.query_one("#right-panels")
            right_panels.styles.width = f"{right_width}%"
        except Exception:
            pass

        # Apply results panel height
        results_height = get_config_value("results_panel_height_percent", 80)
        try:
            results_panel = self.query_one("#panel-0")
            results_panel.styles.height = f"{results_height}%"
        except Exception:
            pass

        # Apply scrollbar settings to all panels
        scrollbar_v_width = get_config_value("scrollbar_vertical_width", 1)
        scrollbar_h_height = get_config_value("scrollbar_horizontal_height", 1)

        for panel_id in [
            "panel-0",
            "panel-1",
            "panel-2",
            "panel-3",
            "panel-4",
            "panel-5",
            "panel-6",
        ]:
            try:
                panel = self.query_one(f"#{panel_id}")
                panel.styles.scrollbar_size_vertical = scrollbar_v_width
                panel.styles.scrollbar_size_horizontal = scrollbar_h_height
            except Exception:
                pass

    def action_scroll_down(self) -> None:
        if self.focused:
            self.focused.scroll_down()

    def action_scroll_up(self) -> None:
        if self.focused:
            self.focused.scroll_up()

    def action_scroll_left(self) -> None:
        if self.focused:
            self.focused.scroll_left()

    def action_scroll_right(self) -> None:
        if self.focused:
            self.focused.scroll_right()

    def action_scroll_home_trigger(self) -> None:
        current_time = time.time()
        if current_time - self._last_g_time < 0.5:
            # Double tap detected
            if self.focused:
                self.focused.scroll_home()
        self._last_g_time = current_time

    def action_scroll_end(self) -> None:
        if self.focused:
            self.focused.scroll_end()

    def action_next_tab(self) -> None:
        if not self.focused or not isinstance(self.focused, (InfoPanel, StatusPanel)):
            return

        if self.focused.next_tab():
            # Load content for new tab
            panel = self.focused
            cmd_func, args = panel.get_current_tab_command()
            task = asyncio.create_task(self._refresh_panel(panel.id or "", cmd_func, args))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    def action_prev_tab(self) -> None:
        if not self.focused or not isinstance(self.focused, (InfoPanel, StatusPanel)):
            return

        if self.focused.prev_tab():
            # Load content for new tab
            panel = self.focused
            cmd_func, args = panel.get_current_tab_command()
            task = asyncio.create_task(self._refresh_panel(panel.id or "", cmd_func, args))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    def action_refresh(self) -> None:
        if not self.focused:
            return

        panel_id = getattr(self.focused, "id", None)
        if not panel_id:
            return

        # Handle InfoPanel with tabs
        if isinstance(self.focused, InfoPanel):
            cmd_func, args = self.focused.get_current_tab_command()
            task = asyncio.create_task(self._refresh_panel(panel_id, cmd_func, args))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        # Handle StatusPanel with tabs
        elif isinstance(self.focused, StatusPanel):
            cmd_func, args = self.focused.get_current_tab_command()
            task = asyncio.create_task(self._refresh_panel(panel_id, cmd_func, args))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    async def action_quit(self) -> None:
        """Override quit action to ensure proper cleanup."""
        # Stop auto-refresh first
        await self._stop_auto_refresh()

        # Cancel all background tasks before quitting
        for task in list(self._background_tasks):
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete/cancel
        if self._background_tasks:
            await asyncio.gather(*list(self._background_tasks), return_exceptions=True)

        self._background_tasks.clear()

        # Call parent's quit action
        await super().action_quit()

    def action_help(self) -> None:
        from lazyverdi.ui import HelpModal

        self.push_screen(HelpModal())

    def on_info_panel_focused(self, message: InfoPanel.Focused) -> None:
        # Remove all focus/compressed classes from panels 1-5
        for i in range(1, 6):
            panel = self.query_one(f"#panel-{i}")
            panel.remove_class("focused", "compressed")

        # Add focused class to the focused panel
        focused_panel = self.query_one(f"#{message.panel_id}")
        focused_panel.add_class("focused")

        # Add compressed class to other panels
        for i in range(1, 6):
            if f"panel-{i}" != message.panel_id:
                panel = self.query_one(f"#panel-{i}")
                panel.add_class("compressed")

    async def on_mount(self) -> None:
        # Apply dynamic styles from config
        self._apply_config_styles()

        # Set initial focus based on config
        initial_panel = get_config_value("initial_focus_panel", 0)

        def set_initial_focus() -> None:
            if initial_panel == 0 or initial_panel == 6:
                self._reset_left_panel_sizes()
            try:
                self.query_one(f"#panel-{initial_panel}").focus()
            except Exception:
                # Fallback to panel-0 if config value is invalid
                self._reset_left_panel_sizes()
                self.query_one("#panel-0").focus()

        self.call_after_refresh(set_initial_focus)

        # Load initial tab for each panel (1-5)
        tasks = []
        for panel_id in ["panel-1", "panel-2", "panel-3", "panel-4", "panel-5"]:
            panel = self.query_one(f"#{panel_id}", InfoPanel)
            cmd_func, args = panel.get_current_tab_command()
            task = asyncio.create_task(self._refresh_panel(panel_id, cmd_func, args))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
            tasks.append(task)

        # Load status panel (6)
        status_panel = self.query_one("#panel-6", StatusPanel)
        cmd_func, args = status_panel.get_current_tab_command()
        task = asyncio.create_task(self._refresh_panel("panel-6", cmd_func, args))
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)
        tasks.append(task)

        await asyncio.gather(*tasks, return_exceptions=True)

        # Start auto-refresh if enabled
        await self._start_auto_refresh()

    async def _start_auto_refresh(self) -> None:
        """Start the auto-refresh background task."""
        interval = get_config_value("auto_refresh_interval", 10)
        if interval > 0 and self._auto_refresh_enabled:
            self._auto_refresh_task = asyncio.create_task(self._auto_refresh_loop())
            self._background_tasks.add(self._auto_refresh_task)
            self._auto_refresh_task.add_done_callback(self._background_tasks.discard)
        elif interval <= 0:
            # Disable auto-refresh if interval is 0 or negative
            self._auto_refresh_enabled = False

    async def _stop_auto_refresh(self) -> None:
        """Stop the auto-refresh background task."""
        if self._auto_refresh_task and not self._auto_refresh_task.done():
            self._auto_refresh_task.cancel()
            try:
                await self._auto_refresh_task
            except asyncio.CancelledError:
                pass
            self._auto_refresh_task = None

    async def _auto_refresh_loop(self) -> None:
        """Background task that periodically refreshes all panels.

        Executes panel refreshes sequentially to avoid SQLAlchemy session conflicts.
        """
        try:
            while True:
                interval = get_config_value("auto_refresh_interval", 10)
                # Stop if interval is 0 or negative
                if interval <= 0:
                    self._auto_refresh_enabled = False
                    break

                await asyncio.sleep(interval)

                # Refresh all panels SEQUENTIALLY to avoid database session conflicts
                # When multiple commands try to access the database concurrently,
                # SQLAlchemy may raise "Instance is not persistent within this Session" errors
                for panel_id in ["panel-1", "panel-2", "panel-3", "panel-4", "panel-5", "panel-6"]:
                    try:
                        if panel_id == "panel-6":
                            status_panel = self.query_one(f"#{panel_id}", StatusPanel)
                            cmd_func, args = status_panel.get_current_tab_command()
                        else:
                            info_panel = self.query_one(f"#{panel_id}", InfoPanel)
                            cmd_func, args = info_panel.get_current_tab_command()

                        # Execute refresh and wait for completion before moving to next panel
                        await self._refresh_panel(panel_id, cmd_func, args)
                    except Exception:
                        # Continue to next panel even if one fails
                        continue
        except asyncio.CancelledError:
            # Task was cancelled - this is expected
            pass

    def action_toggle_auto_refresh(self) -> None:
        """Toggle auto-refresh on/off."""
        self._auto_refresh_enabled = not self._auto_refresh_enabled

        if self._auto_refresh_enabled:
            # Start auto-refresh
            task = asyncio.create_task(self._start_auto_refresh())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            # Show notification in results panel
            try:
                results_panel = self.query_one("#panel-0", ResultsPanel)
                interval = get_config_value("auto_refresh_interval", 10)
                results_panel.write(f"Auto-refresh enabled (interval: {interval}s)")
            except Exception:
                pass
        else:
            # Stop auto-refresh
            task = asyncio.create_task(self._stop_auto_refresh())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            # Show notification in results panel
            try:
                results_panel = self.query_one("#panel-0", ResultsPanel)
                results_panel.write("Auto-refresh disabled")
            except Exception:
                pass

    async def on_unmount(self) -> None:
        """Clean up resources when app is unmounting."""
        # Stop auto-refresh first
        await self._stop_auto_refresh()

        # Cancel all background tasks
        for task in self._background_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to be cancelled
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()

    async def _refresh_panel(self, panel_id: str, command_func: object, args: list[str]) -> None:
        """Refresh panel content by running command.

        Args:
            panel_id: ID of the panel to refresh
            command_func: Command function to execute
            args: Command arguments

        Note:
            - stdout is processed and displayed in the target panel
            - stderr is always written to panel-0 (ResultsPanel)
        """
        try:
            result = await self._runner.run_command(command_func, args)  # type: ignore[arg-type]

            # Process stdout for target panel
            stdout_output = result.stdout.strip() if result.stdout.strip() else "No output"

            # Process stderr - always write to panel-0
            if result.stderr.strip():
                stderr = result.stderr.strip()
                # Skip "configuration file does not exist" warnings
                if not (
                    "configuration file" in stderr.lower() and "does not exist" in stderr.lower()
                ):
                    cmd_name = getattr(command_func, "name", str(command_func))
                    error_msg = format_error_message(cmd_name, stderr)
                    # Write stderr to panel-0
                    try:
                        results_panel = self.query_one("#panel-0", ResultsPanel)
                        results_panel.write(f"Error from {panel_id}:")
                        results_panel.write(error_msg)
                    except Exception:
                        # If panel-0 is not available, ignore
                        pass

            # Update target panel content with stdout only
            if panel_id == "panel-6":
                status_panel = self.query_one(f"#{panel_id}", StatusPanel)
                status_panel.update_content(stdout_output)
            else:
                info_panel = self.query_one(f"#{panel_id}", InfoPanel)
                info_panel.update_content(stdout_output)

        except asyncio.CancelledError:
            # Task was cancelled during shutdown - this is expected
            raise
        except Exception as e:
            # Handle errors gracefully
            error_message = f"Error: {str(e)}"
            try:
                # Write exception to panel-0
                results_panel = self.query_one("#panel-0", ResultsPanel)
                results_panel.write(f"Exception in {panel_id}:")
                results_panel.write(error_message)
            except Exception:
                pass

            # Also update target panel to show error occurred
            try:
                if panel_id == "panel-6":
                    status_panel = self.query_one(f"#{panel_id}", StatusPanel)
                    status_panel.update_content(error_message)
                else:
                    info_panel = self.query_one(f"#{panel_id}", InfoPanel)
                    info_panel.update_content(error_message)
            except Exception:
                # If panel query fails, log error (in production would use logger)
                pass


def main() -> None:
    app = LazyVerdiApp()
    app.run()


if __name__ == "__main__":
    main()
