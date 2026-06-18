"""Tests for monitor registry."""

import pytest


def test_get_all_monitors():
    """Test getting all monitors."""
    from src.monitors import get_all_monitors

    monitors = get_all_monitors()

    assert len(monitors) == 7

    service_names = [m.service_name for m in monitors]
    assert "github" in service_names
    assert "cloudflare" in service_names
    assert "okta" in service_names
    assert "aws" in service_names
    assert "athena" in service_names
    assert "google_workspace" in service_names
    assert "zscaler" in service_names


def test_get_monitor_by_name():
    """Test getting monitor by service name."""
    from src.monitors import get_monitor_by_name

    github = get_monitor_by_name("github")
    assert github is not None
    assert github.service_name == "github"
    assert github.display_name == "GitHub"

    invalid = get_monitor_by_name("nonexistent")
    assert invalid is None
