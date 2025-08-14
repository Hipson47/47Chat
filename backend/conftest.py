"""Pytest configuration for 47Chat backend tests.

This module configures warning filters and test behavior to ensure
clean CI output while catching genuine issues.
"""

import warnings
import pytest


def pytest_configure(config):
    """Configure pytest with runtime warning filters."""
    # Apply warning filters at runtime (in addition to pytest.ini)
    # This ensures warnings are filtered even when running tests directly
    
    # Known safe warnings that we want to suppress
    warnings.filterwarnings(
        "ignore",
        message=r".*numpy\.core\._multiarray_umath.*",
        category=DeprecationWarning,
    )
    
    warnings.filterwarnings(
        "ignore", 
        message=r".*encoder_attention_mask.*",
        category=FutureWarning,
    )
    
    warnings.filterwarnings(
        "ignore",
        message=r".*is deprecated and will be removed.*",
        category=FutureWarning,
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected test items to add markers or configure behavior."""
    # Could add automatic slow marker detection here if needed
    pass


@pytest.fixture(autouse=True)
def configure_warnings():
    """Auto-use fixture to ensure warning configuration is applied."""
    # This fixture runs for every test, ensuring consistent warning behavior
    # The actual filtering is done in pytest_configure, this just ensures
    # the configuration is applied consistently
    yield
