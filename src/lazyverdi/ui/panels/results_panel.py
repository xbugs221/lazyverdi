"""Results panel for displaying command outputs."""

from typing import Any

from textual.widgets import TextArea

from lazyverdi.core.config import get_config_value


class ResultsPanel(TextArea):
    """Panel [0] for showing command results.

    Uses TextArea for text selection and copy support.
    """

    DEFAULT_CSS = """
    ResultsPanel {
        height: 80%;
        border: solid $primary;
    }

    ResultsPanel:focus {
        border: $accent;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize results panel."""
        show_line_numbers = get_config_value("show_line_numbers", False)
        soft_wrap = get_config_value("soft_wrap", True)

        super().__init__(
            "",
            read_only=True,
            show_line_numbers=show_line_numbers,
            soft_wrap=soft_wrap,
            tab_behavior="focus",
            **kwargs,
        )
        self.border_title = "[0] details"

    def on_mount(self) -> None:
        """Display welcome message on startup."""
        show_welcome = get_config_value("show_welcome_message", True)
        if show_welcome:
            self.text = "LazyVerdi v1.0.0\nWelcome! Press ? for help"

    def write(self, text: str) -> None:
        """Append text to the panel (for compatibility with RichLog interface).

        Args:
            text: Text to append
        """
        if self.text:
            self.text = self.text + "\n" + text
        else:
            self.text = text
