#! /usr/bin/env python3
from setuptools import setup
from setuptools.command.install import install
from sys import path
from os import path as opath
from os import mkdir, environ
from shutil import rmtree

path.append(opath.join(opath.dirname(__file__), "src"))

import staticanalyser.shared.platform_constants as consts


class SAInstaller(install):
    def __init__(self, *args, **kwargs):
        super(SAInstaller, self).__init__(*args, **kwargs)
        self.setup_config()

    def _create_directories(self, directories: list):
        for directory in directories:
            try:
                mkdir(directory)
            except FileExistsError:
                pass

    def copy_file(self, src, dest):
        with open(src, "r") as src_f:
            with open(dest, "w") as dest_f:
                dest_f.writelines(src_f.readlines())
                print("written config!")

    def setup_config(self) -> None:
        if not opath.exists(consts.GLOBAL_DATA_DIR):
            self._create_directories([consts.GLOBAL_DATA_DIR, consts.LANGS_DIR, consts.MODEL_DIR])
        defaults_dir = opath.join(opath.dirname(__file__), "src", "staticanalyser", "defaults")

        self.copy_file(opath.join(defaults_dir, "default_config.toml"), consts.CONFIG_LOCATION)
        self.copy_file(opath.join(defaults_dir, "python3.toml"), opath.join(consts.LANGS_DIR, "python3.toml"))


setup(
    name="staticanalyser",
    version="0.1",
    description="A static analysis program",
    license="MIT",
    install_requires=[
        "click",
        "toml",
        "jsonschema"
    ],
    package_dir={
        '': 'src'
    },
    package_data={
        '': ['*.toml', '*.json']
    },
    zip_safe=False,
    packages=[
        "staticanalyser.hunter",
        "staticanalyser.shared",
        "staticanalyser.navigator",
        "staticanalyser.translator",
        "staticanalyser.regexbuilder",
        "staticanalyser"
    ],
    cmdclass={
        'install': SAInstaller
    },
    test_suite="staticanalysertest"
)
