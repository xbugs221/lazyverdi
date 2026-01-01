"""Tests for UI panel widgets."""

import pytest
from lazyverdi.app import LazyVerdiApp
from lazyverdi.ui import StatusPanel
from lazyverdi.ui.panels.command_panel import CommandPanel
from lazyverdi.ui.panels.results_panel import ResultsPanel


@pytest.mark.asyncio
async def test_app_has_all_panels() -> None:
    """Test that app contains all required panels."""
    app = LazyVerdiApp()
    async with app.run_test():
        # Check all 7 panels exist (0-6)
        assert app.query_one("#panel-0")
        assert app.query_one("#panel-1")
        assert app.query_one("#panel-2")
        assert app.query_one("#panel-3")
        assert app.query_one("#panel-4")
        assert app.query_one("#panel-5")
        assert app.query_one("#panel-6")


@pytest.mark.asyncio
async def test_focus_switching() -> None:
    """Test that number keys switch focus to panels."""
    app = LazyVerdiApp()
    async with app.run_test() as pilot:
        # Wait for initial focus to be set (happens in on_mount after refresh)
        await pilot.pause()

        # Initial focus should be on panel-0 (results panel)
        assert app.focused is not None and app.focused.id == "panel-0"

        # Test focus switching with number keys
        await pilot.press("1")
        assert app.query_one("#panel-1").has_focus

        await pilot.press("2")
        assert app.query_one("#panel-2").has_focus

        await pilot.press("0")
        # Panel 0 (ResultsPanel) should be focused again
        focused = app.focused
        assert focused is not None and focused.id == "panel-0"


@pytest.mark.asyncio
async def test_status_panel_update() -> None:
    """Test StatusPanel can update content."""
    app = LazyVerdiApp()
    async with app.run_test():
        panel = app.query_one("#panel-6", StatusPanel)
        panel.update_content("Test status content")
        # Verify update happened without errors
        assert panel is not None


@pytest.mark.asyncio
async def test_status_panel_tabs() -> None:
    """Test StatusPanel tab switching."""
    app = LazyVerdiApp()
    async with app.run_test() as pilot:
        await pilot.pause()

        # Focus on panel-6
        await pilot.press("6")
        panel = app.query_one("#panel-6", StatusPanel)

        # Should start at first tab (status)
        assert panel._current_tab_index == 0
        title = str(panel.border_title)
        assert "[green]status[/green]" in title

        # Switch to next tab (daemon)
        await pilot.press("]")
        await pilot.pause()
        assert panel._current_tab_index == 1
        title = str(panel.border_title)
        assert "[green]daemon[/green]" in title

        # Switch to next tab (storage)
        await pilot.press("]")
        await pilot.pause()
        assert panel._current_tab_index == 2
        title = str(panel.border_title)
        assert "[green]storage[/green]" in title

        # Try to go beyond last tab (should stay at storage)
        await pilot.press("]")
        await pilot.pause()
        assert panel._current_tab_index == 2

        # Go back to previous tab (daemon)
        await pilot.press("[")
        await pilot.pause()
        assert panel._current_tab_index == 1

        # Go back to first tab (status)
        await pilot.press("[")
        await pilot.pause()
        assert panel._current_tab_index == 0


def test_command_panel_compose() -> None:
    """Test CommandPanel composition."""
    panel = CommandPanel()
    widgets = list(panel.compose())
    # Should have 5 command category widgets
    assert len(widgets) == 5


def test_results_panel_compose() -> None:
    """Test ResultsPanel initialization."""
    panel = ResultsPanel()
    assert panel.text == ""
    assert panel.read_only is True


@pytest.mark.asyncio
async def test_results_panel_mount() -> None:
    """Test ResultsPanel mount shows welcome message."""
    app = LazyVerdiApp()
    async with app.run_test():
        panel = app.query_one("#panel-0", ResultsPanel)
        # on_mount should set welcome message
        assert "LazyVerdi" in panel.text
        assert "Welcome" in panel.text


@pytest.mark.asyncio
async def test_results_panel_write() -> None:
    """Test ResultsPanel write method."""
    app = LazyVerdiApp()
    async with app.run_test():
        panel = app.query_one("#panel-0", ResultsPanel)
        initial_text = panel.text

        # Write new text
        panel.write("Test output")
        assert "Test output" in panel.text
        assert len(panel.text) > len(initial_text)

        # Write more text
        panel.write("More output")
        assert "More output" in panel.text
