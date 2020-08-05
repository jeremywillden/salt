"""
    tests.pytests.integration.conftest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    PyTest fixtures
"""
import pytest


@pytest.fixture(scope="package")
def salt_master(salt_master_factory):
    """
    We override the fixture so that we have the daemon running
    """
    with salt_master_factory.started():
        yield salt_master_factory


@pytest.fixture(scope="package")
def salt_minion(salt_master, salt_minion_factory):
    """
    We override the fixture so that we have the daemon running
    """
    with salt_minion_factory.started():
        # Sync All
        salt_call_cli = salt_minion_factory.get_salt_call_cli()
        ret = salt_call_cli.run("saltutil.sync_all", _timeout=120)
        assert ret.exitcode == 0, ret
        yield salt_minion_factory


@pytest.fixture(scope="package")
def salt_sub_minion(salt_master, salt_sub_minion_factory):
    """
    We override the fixture so that we have the daemon running
    """
    with salt_sub_minion_factory.started():
        # Sync All
        salt_call_cli = salt_sub_minion_factory.get_salt_call_cli()
        ret = salt_call_cli.run("saltutil.sync_all", _timeout=120)
        assert ret.exitcode == 0, ret
        yield salt_sub_minion_factory


@pytest.fixture(scope="package")
def salt_proxy(salt_master, salt_proxy_factory):
    with salt_proxy_factory.started():
        yield salt_proxy_factory
