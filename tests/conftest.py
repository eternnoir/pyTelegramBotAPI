import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--integration", action="store_true", default=False, help="Specify to run integration test in real bot"
    )


def pytest_collection_modifyitems(config, items):
    if config.getoption("--integration"):
        return
    skip_slow = pytest.mark.skip(reason="--integration option is required to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_slow)
