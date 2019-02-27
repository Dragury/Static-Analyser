from io import TextIOWrapper
from enum import Enum
from os import path
import toml
from staticanalyser.shared.platform_constants import LANGS_DIR
import staticanalyser.shared.model as model
import re


class Directive(object):
    _name: str = None
    _description: str = None
    _regex_match: str = None
    _regex_replace: str = None

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
    _name: str = None
    _selection_name: int = None
    _description: str = None
    _subselectors: list = []
    _regex_match: str = None

    @staticmethod
    def get_selector(name: str, data: dict):
        if name == SelectorType.sa_function.value:
            return FunctionSelector(name, data)
        elif name == SelectorType.sa_class.value:
            return None

    def __init__(self, name: str, data: dict):
        self._name = name
        self._description = data.get("description")
        self._regex_match = data.get("regex_match")
        self._selection_name = data.get("name")

    def __str__(self):
        return "{}: {}".format(self._name, self._description)

    def select(self, file_contents: str) -> list:
        pass


class FunctionSelector(Selector):
    _parameters: int = None
    _body: int = None

    def __init__(self, name: str, data: dict):
        super(FunctionSelector, self).__init__(name, data)
        self._parameters = data.get("parameters")
        self._body = data.get("body")

    def select(self, file_contents: str) -> list:
        functions = re.findall(self._regex_match, file_contents)
        for function in functions:
            func: model.FunctionModel = model.FunctionModel(function[self._selection_name], [], [])
            print(func)


class SelectorType(Enum):
    sa_function = "function"
    sa_class = "class"
    _class_map: dict = {
        sa_function: FunctionSelector,
        sa_class: None  # TODO update for class selector
    }


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
            language_config = None
            with open(path.join(LANGS_DIR, "{}.toml".format(language_name)), "r") as language_file:
                language_config = toml.load(language_file)

            self._load_preprocessor(language_config.get("directives"))
            self._load_selectors(language_config.get("selectors"))

    def _load_preprocessor(self, directives: dict):
        self._preprocessor = Preprocessor(directives)

    def _load_selectors(self, selectors: dict):
        for selector in selectors.keys():
            self._selectors.append(Selector.get_selector(selector, selectors.get(selector)))

    def preprocess(self, file_contents: str) -> str:
        return self._preprocessor.apply(file_contents)

    def select(self, file_contents: str) -> list:
        selector: Selector
        for selector in self._selectors:
            if selector is not None:
                selector.select(file_contents)

    def __str__(self):
        return self._lang

    def parse(self, file: TextIOWrapper):
        # TODO check for local file so I know the namespace for where entities live(global vs local)
        file_contents: str = file.read()
        print("File before:")
        print(file_contents)
        file_contents = self.preprocess(file_contents)
        print("File after:")
        print(file_contents)
        selected_entities: list = self.select(file_contents)
        print(selected_entities)
