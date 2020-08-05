"""
    tests.multimaster.conftest
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Multimaster PyTest prep routines
"""

import logging
import os
import shutil

import pytest
import salt.utils.files
from salt.serializers import yaml
from salt.utils.immutabletypes import freeze
from tests.support.runtests import RUNTIME_VARS

log = logging.getLogger(__name__)


@pytest.fixture(scope="package")
def salt_mm_master(salt_factories):
    root_dir = salt_factories._get_root_dir_for_daemon("mm-master")
    with salt.utils.files.fopen(
        os.path.join(RUNTIME_VARS.CONF_DIR, "mm_master")
    ) as rfh:
        config_defaults = yaml.deserialize(rfh.read())

    config_defaults["root_dir"] = str(root_dir)

    config_overrides = {
        "file_roots": {
            "base": [
                RUNTIME_VARS.TMP_STATE_TREE,
                os.path.join(RUNTIME_VARS.FILES, "file", "base"),
            ],
            # Alternate root to test __env__ choices
            "prod": [
                RUNTIME_VARS.TMP_PRODENV_STATE_TREE,
                os.path.join(RUNTIME_VARS.FILES, "file", "prod"),
            ],
        },
        "pillar_roots": {
            "base": [
                RUNTIME_VARS.TMP_PILLAR_TREE,
                os.path.join(RUNTIME_VARS.FILES, "pillar", "base"),
            ],
            "prod": [RUNTIME_VARS.TMP_PRODENV_PILLAR_TREE],
        },
    }
    factory = salt_factories.get_salt_master_daemon(
        "mm-master", config_defaults=config_defaults, config_overrides=config_overrides,
    )
    with factory.started():
        yield factory


@pytest.fixture(scope="package")
def salt_mm_minion(request, salt_mm_master, salt_mm_sub_master):
    with salt.utils.files.fopen(
        os.path.join(RUNTIME_VARS.CONF_DIR, "mm_minion")
    ) as rfh:
        config_defaults = yaml.deserialize(rfh.read())
    config_defaults["hosts.file"] = os.path.join(RUNTIME_VARS.TMP, "hosts")
    config_defaults["aliases.file"] = os.path.join(RUNTIME_VARS.TMP, "aliases")
    config_defaults["transport"] = request.config.getoption("--transport")

    mm_master_port = salt_mm_master.config["ret_port"]
    mm_sub_master_port = salt_mm_sub_master.config["ret_port"]
    config_overrides = {
        "master_port": "",
        "master": [
            "localhost:{}".format(mm_master_port),
            "localhost:{}".format(mm_sub_master_port),
        ],
        "test.foo": "baz",
    }
    factory = salt_mm_master.get_salt_minion_daemon(
        "mm-minion", config_defaults=config_defaults, config_overrides=config_overrides,
    )
    with factory.started():
        yield factory


@pytest.fixture(scope="package")
def salt_mm_sub_master(salt_factories, salt_mm_master):
    with salt.utils.files.fopen(
        os.path.join(RUNTIME_VARS.CONF_DIR, "mm_sub_master")
    ) as rfh:
        config_defaults = yaml.deserialize(rfh.read())
    root_dir = salt_factories._get_root_dir_for_daemon("mm-master")

    config_defaults["root_dir"] = str(root_dir)

    config_overrides = {
        "file_roots": {
            "base": [
                RUNTIME_VARS.TMP_STATE_TREE,
                os.path.join(RUNTIME_VARS.FILES, "file", "base"),
            ],
            # Alternate root to test __env__ choices
            "prod": [
                RUNTIME_VARS.TMP_PRODENV_STATE_TREE,
                os.path.join(RUNTIME_VARS.FILES, "file", "prod"),
            ],
        },
        "pillar_roots": {
            "base": [
                RUNTIME_VARS.TMP_PILLAR_TREE,
                os.path.join(RUNTIME_VARS.FILES, "pillar", "base"),
            ],
            "prod": [RUNTIME_VARS.TMP_PRODENV_PILLAR_TREE],
        },
    }

    factory = salt_factories.get_salt_master_daemon(
        "mm-sub-master",
        config_defaults=config_defaults,
        config_overrides=config_overrides,
    )

    # The secondary salt master depends on the primarily salt master fixture
    # because we need to clone the keys
    for keyfile in ("master.pem", "master.pub"):
        shutil.copyfile(
            os.path.join(salt_mm_master.config["pki_dir"], keyfile),
            os.path.join(factory.config["pki_dir"], keyfile),
        )
    with factory.started():
        yield factory


@pytest.fixture(scope="package")
def salt_mm_sub_minion(request, salt_mm_master, salt_mm_sub_master):
    with salt.utils.files.fopen(
        os.path.join(RUNTIME_VARS.CONF_DIR, "mm_sub_minion")
    ) as rfh:
        config_defaults = yaml.deserialize(rfh.read())
    config_defaults["hosts.file"] = os.path.join(RUNTIME_VARS.TMP, "hosts")
    config_defaults["aliases.file"] = os.path.join(RUNTIME_VARS.TMP, "aliases")
    config_defaults["transport"] = request.config.getoption("--transport")

    mm_master_port = salt_mm_master.config["ret_port"]
    mm_sub_master_port = salt_mm_sub_master.config["ret_port"]
    config_overrides = {
        "master_port": "",
        "master": [
            "localhost:{}".format(mm_master_port),
            "localhost:{}".format(mm_sub_master_port),
        ],
        "test.foo": "baz",
    }
    factory = salt_mm_sub_master.get_salt_minion_daemon(
        "mm-sub-minion",
        config_defaults=config_defaults,
        config_overrides=config_overrides,
    )
    with factory.started():
        yield factory


@pytest.fixture(scope="package", autouse=True)
def bridge_pytest_and_runtests(  # pylint: disable=function-redefined
    reap_stray_processes,
    base_env_state_tree_root_dir,
    prod_env_state_tree_root_dir,
    base_env_pillar_tree_root_dir,
    prod_env_pillar_tree_root_dir,
    salt_mm_master,
    salt_mm_minion,
    salt_mm_sub_master,
    salt_mm_sub_minion,
):
    # Make sure unittest2 uses the pytest generated configuration
    RUNTIME_VARS.RUNTIME_CONFIGS["mm_master"] = freeze(salt_mm_master.config)
    RUNTIME_VARS.RUNTIME_CONFIGS["mm_minion"] = freeze(salt_mm_minion.config)
    RUNTIME_VARS.RUNTIME_CONFIGS["mm_sub_master"] = freeze(salt_mm_sub_master.config)
    RUNTIME_VARS.RUNTIME_CONFIGS["mm_sub_minion"] = freeze(salt_mm_sub_minion.config)

    # Make sure unittest2 classes know their paths
    RUNTIME_VARS.TMP_MM_CONF_DIR = os.path.dirname(salt_mm_master.config["conf_file"])
    RUNTIME_VARS.TMP_MM_MINION_CONF_DIR = os.path.dirname(
        salt_mm_minion.config["conf_file"]
    )
    RUNTIME_VARS.TMP_MM_SUB_CONF_DIR = os.path.dirname(
        salt_mm_sub_master.config["conf_file"]
    )
    RUNTIME_VARS.TMP_MM_SUB_MINION_CONF_DIR = os.path.dirname(
        salt_mm_sub_minion.config["conf_file"]
    )
