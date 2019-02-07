# Constants for the platform(s) this may be run on. Things such as model storage locations etc.
from os import path, environ, name

GLOBAL_DATA_DIR: path = None
MODEL_DIR: path = None
LANGS_DIR: path = None
CONFIG_LOCATION: path = None

if name == "nt":
    GLOBAL_DATA_DIR = path.join(environ['APPDATA'], "static-analyser")
else: # name == "posix" must be some variation of linux? if not true then it should be an easy fix if it comes up
    GLOBAL_DATA_DIR = path.join(environ['HOME'], ".static-analyser")

MODEL_DIR = path.join(GLOBAL_DATA_DIR, "models")
LANGS_DIR = path.join(GLOBAL_DATA_DIR, "langs")
CONFIG_LOCATION = path.join(GLOBAL_DATA_DIR, "config.toml")