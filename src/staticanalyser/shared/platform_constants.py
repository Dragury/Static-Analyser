# Constants for the platform(s) this may be run on. Things such as model storage locations etc.
from os import path, environ, name

GLOBAL_MODEL_DIR: path = None

if name == "nt":
    GLOBAL_MODEL_DIR = path.join(path.abspath(environ['APPDATA']), "static-analyser")
    print (GLOBAL_MODEL_DIR)