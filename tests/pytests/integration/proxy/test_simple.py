"""
Simple Smoke Tests for Connected Proxy Minion
"""

import pytest
from tests.support.helpers import slowTest


@pytest.fixture(scope="package")
def salt_cli(salt_proxy, salt_master):
    return salt_master.get_salt_cli(default_timeout=120)


def test_can_it_ping(salt_cli):
    """
    Ensure the proxy can ping
    """
    ret = salt_cli.run("test.ping", minion_tgt="proxytest")
    assert ret.json is True


def test_list_pkgs(salt_cli):
    """
    Package test 1, really just tests that the virtual function capability
    is working OK.
    """
    ret = salt_cli.run("pkg.list_pkgs", minion_tgt="proxytest")
    assert "coreutils" in ret.json
    assert "apache" in ret.json
    assert "redbull" in ret.json


def test_install_pkgs(salt_cli):
    """
    Package test 2, really just tests that the virtual function capability
    is working OK.
    """
    ret = salt_cli.run("pkg.install", "thispkg", minion_tgt="proxytest")
    assert ret.json["thispkg"] == "1.0"

    ret = salt_cli.run("pkg.list_pkgs", minion_tgt="proxytest")

    assert ret.json["apache"] == "2.4"
    assert ret.json["redbull"] == "999.99"
    assert ret.json["thispkg"] == "1.0"


def test_remove_pkgs(salt_cli):
    ret = salt_cli.run("pkg.remove", "apache", minion_tgt="proxytest")
    assert "apache" not in ret.json


def test_upgrade(salt_cli):
    ret = salt_cli.run("pkg.upgrade", minion_tgt="proxytest")
    assert ret.json["coreutils"]["new"] == "2.0"
    assert ret.json["redbull"]["new"] == "1000.99"


def test_service_list(salt_cli):
    ret = salt_cli.run("service.list", minion_tgt="proxytest")
    assert "ntp" in ret.json


def test_service_stop(salt_cli):
    ret = salt_cli.run("service.stop", "ntp", minion_tgt="proxytest")
    ret = salt_cli.run("service.status", "ntp", minion_tgt="proxytest")
    assert ret.json is False


def test_service_start(salt_cli):
    ret = salt_cli.run("service.start", "samba", minion_tgt="proxytest")
    ret = salt_cli.run("service.status", "samba", minion_tgt="proxytest")
    assert ret.json is True


def test_service_get_all(salt_cli):
    ret = salt_cli.run("service.get_all", minion_tgt="proxytest")
    assert ret.json
    assert "samba" in ret.json


def test_grains_items(salt_cli):
    ret = salt_cli.run("grains.items", minion_tgt="proxytest")
    assert ret.json["kernel"] == "proxy"
    assert ret.json["kernelrelease"] == "proxy"


def test_state_apply(salt_cli):
    ret = salt_cli.run("state.apply", "core", minion_tgt="proxytest")
    for value in ret.json.values():
        assert value["result"] is True


@slowTest
def test_state_highstate(salt_cli):
    ret = salt_cli.run("state.highstate", minion_tgt="proxytest")
    for value in ret.json.values():
        assert value["result"] is True
