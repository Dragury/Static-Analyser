from io import TextIOWrapper
from os import path
import toml
from staticanalyser.shared.platform_constants import LANGS_DIR
import re


class Directive(object):
    _name: str = None
    _description: str = None
    _regex_match: re.Pattern = None
    _regex_replace: re.Pattern = None

    def __init__(self, name: str, data: dict):
        self._name = name
        self._description = data.get("description")
        self._load_regex(data)

    def _load_regex(self, data: dict):
        if "regex_match" in data.keys():
            self._regex_match = data.get("regex_match")
            self._regex_replace = data.get("regex_replace")
        else:
            print("This directive doesn't have it's regex populated!")

    def __str__(self):
        return "{}: {}".format(self._name, self._description)

    def apply(self, file_contents: str) -> str:
        if self._regex_match is not None:
            return re.sub(self._regex_match, self._regex_replace, file_contents)
        else:
            return file_contents


class Selector(object):
    _description: str = None
    _long_description: str = None
    _regex: str = None
    _subselectors: list = []


class Preprocessor(object):
    _directives: list = []

    def __init__(self, directives: dict):
        for directive in directives.keys():
            self._directives.append(Directive(directive, directives.get(directive)))

    def apply(self, file_contents: str):
        directive: Directive
        for directive in self._directives:
            file_contents = directive.apply(file_contents)
        return file_contents


class Descriptor(object):
    _lang: str = None
    _syntax_descriptor: dict = {}
    _preprocessor: Preprocessor = None
    _selectors: list = []

    def __init__(self, language_name: str):
        if language_name is None:
            return
        else:
            self._lang = language_name
            # TODO loading from lang files

            language_file = open(path.join(LANGS_DIR, "{}.toml".format(language_name)),
                                 "r")  # TODO push this into config or something
            language_config = toml.load(language_file)

            self._load_preprocessor(language_config.get("directives"))
            pass

    def _load_preprocessor(self, directives: dict):
        self._preprocessor = Preprocessor(directives)

    def _load_selectors(self, selectors: dict):
        pass

    def preprocess(self, file_contents: str) -> str:
        return self._preprocessor.apply(file_contents)

    def select(self, file_contents: str) -> list:
        pass

    def __str__(self):
        return self._lang

    def parse(self, file: TextIOWrapper):
        file_contents: str = file.read()
        print("File before:")
        print(file_contents)
        file_contents = self.preprocess(file_contents)
        print("File after:")
        print(file_contents)
        selected_entities: list = self.select(file_contents)
