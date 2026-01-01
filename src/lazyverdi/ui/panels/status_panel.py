"""Status panel for displaying system status with tab support."""

from collections.abc import Callable
from typing import Any

from textual.message import Message
from textual.widgets import TextArea

from lazyverdi.core.config import get_config_value


class StatusPanel(TextArea):
    """Panel [6] for showing profile/daemon/storage status with tab support.

    Uses TextArea for text selection and copy support.
    """

    DEFAULT_CSS = """
    StatusPanel {
        height: 20%;
        border: solid $primary;
    }

    StatusPanel:focus {
        border: $accent;
    }
    """

    class Focused(Message):
        """Posted when panel gains focus."""

        def __init__(self, panel_id: str) -> None:
            """Initialize message.

            Args:
                panel_id: ID of the focused panel
            """
            super().__init__()
            self.panel_id = panel_id

    class TabChanged(Message):
        """Posted when tab is changed."""

        def __init__(self, panel_id: str, tab_index: int) -> None:
            """Initialize message.

            Args:
                panel_id: ID of the panel
                tab_index: Index of the new active tab
            """
            super().__init__()
            self.panel_id = panel_id
            self.tab_index = tab_index

    def __init__(self, tabs: list[tuple[str, Callable[..., Any], list[str]]]) -> None:
        """Initialize status panel with multiple tabs.

        Args:
            tabs: List of (tab_name, command_func, args) tuples
        """
        show_line_numbers = get_config_value("show_line_numbers", False)
        soft_wrap = get_config_value("soft_wrap", True)

        super().__init__(
            "Loading...",
            read_only=True,
            show_line_numbers=show_line_numbers,
            soft_wrap=soft_wrap,
            tab_behavior="focus",
            id="panel-6",
        )
        self._tabs = tabs
        self._current_tab_index = 0
        self._tab_contents: dict[int, str] = {}  # Cache content for each tab
        self._update_title()

    def _update_title(self) -> None:
        """Update border title to show all tabs with current tab highlighted."""
        if not self._tabs:
            return

        # Build title with all tab names, highlighting the current one
        tab_parts = []
        for i, (tab_name, _, _) in enumerate(self._tabs):
            if i == self._current_tab_index:
                tab_parts.append(f"[green]{tab_name}[/green]")
            else:
                tab_parts.append(tab_name)

        # Join tabs with slash separator
        tabs_display = "/".join(tab_parts)
        self.border_title = f"[6] {tabs_display}"

    def get_current_tab_command(self) -> tuple[Callable[..., Any], list[str]]:
        """Get current tab's command function and args.

        Returns:
            Tuple of (command_func, args)
        """
        if not self._tabs:
            raise ValueError("No tabs configured")
        _, cmd_func, args = self._tabs[self._current_tab_index]
        return cmd_func, args

    def update_content(self, text: str) -> None:
        """Update current tab's content.

        Args:
            text: New content to display
        """
        self._tab_contents[self._current_tab_index] = text
        self.text = text

    def next_tab(self) -> bool:
        """Switch to next tab.

        Returns:
            True if tab was changed, False if already at last tab
        """
        if self._current_tab_index < len(self._tabs) - 1:
            self._current_tab_index += 1
            self._update_title()
            # Restore cached content if available
            if self._current_tab_index in self._tab_contents:
                self.text = self._tab_contents[self._current_tab_index]
            else:
                self.text = "Loading..."
            self.post_message(self.TabChanged(self.id or "", self._current_tab_index))
            return True
        return False

    def prev_tab(self) -> bool:
        """Switch to previous tab.

        Returns:
            True if tab was changed, False if already at first tab
        """
        if self._current_tab_index > 0:
            self._current_tab_index -= 1
            self._update_title()
            # Restore cached content if available
            if self._current_tab_index in self._tab_contents:
                self.text = self._tab_contents[self._current_tab_index]
            else:
                self.text = "Loading..."
            self.post_message(self.TabChanged(self.id or "", self._current_tab_index))
            return True
        return False

    def on_focus(self) -> None:
        """Handle focus event."""
        self.post_message(self.Focused(self.id or ""))
