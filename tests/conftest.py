"""Pytest configuration and fixtures."""

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from lazyverdi.app import LazyVerdiApp


@pytest.fixture
def app() -> "LazyVerdiApp":
    """Create LazyVerdiApp instance for testing."""
    from lazyverdi.app import LazyVerdiApp

    return LazyVerdiApp()
