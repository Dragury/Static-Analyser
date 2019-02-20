from enum import Enum
from os import path
import re


class PreprocessorDirectiveType(Enum):
    REGEX_REPLACE = 1


class Directive(object):
    _description: str = None
    _long_description: str = None
    _regex: str = None


class Selector(object):
    _description: str = None
    _long_description: str = None
    _regex: str = None
    _subselectors: list = []


class Preprocessor(object):
    _directives: list = []
    _file_path: path = None

    def __init__(self, directives, file_path):
        self._directives = directives
        self._file_path = file_path

    def apply(self):
        pass  # TODO apply the preprocessor directives


class DefaultDescriptor(object):
    _syntax_descriptor: dict = {}
    _preprocess_directives: list = []

    def __init__(self, descriptor_path: path):
        # Load the translation information from the lang file
        pass

    def preprocess(self):
        pass
