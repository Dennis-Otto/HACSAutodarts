"""Home Assistant fixtures for Autodarts."""

from pathlib import Path

import pytest

import custom_components

# The HA test plugin preloads its own custom_components package.
custom_components.__path__.insert(
    0, str(Path(__file__).parents[1] / "custom_components")
)


@pytest.fixture(autouse=True)
def custom_integration(enable_custom_integrations):
    """Enable discovery of the real integration from this repository."""
