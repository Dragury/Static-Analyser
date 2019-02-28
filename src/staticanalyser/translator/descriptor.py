from io import TextIOWrapper
from enum import Enum
from os import path
import toml
from staticanalyser.shared.platform_constants import LANGS_DIR
import staticanalyser.shared.model as model
import re
from hashlib import md5


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
    _registered_selectors: dict = {}
    _name: str = None
    _selection_name: int = None
    _description: str = None
    _subselectors: list = None
    _regex_match: str = None
    _top_level_selector: bool = None

    @staticmethod
    def get_selector(language: str, name: str, data: dict):
        if "{}.{}".format(language, name) not in Selector._registered_selectors.keys():
            if SelectorType.get_selector_class(name) is not None:
                Selector._registered_selectors["{}.{}".format(language,name)] = SelectorType.get_selector_class(name)(language, name, data)
            # if name == SelectorType.sa_function.value:
            #     Selector._registered_selectors["{}.{}".format(language, name)] = FunctionSelector(language, name, data)
            # elif name == SelectorType.sa_class.value:
            #     Selector._registered_selectors["{}.{}".format(language, name)] = None
            # if
        return Selector._registered_selectors.get("{}.{}".format(language, name))

    @staticmethod
    def get_selector_by_name(name: str):
        return Selector._registered_selectors.get(name)

    def __init__(self, language: str, name: str, data: dict):
        self._name = name
        self._description = data.get("description")
        self._regex_match = data.get("regex_match")
        self._selection_name = data.get("name")
        self._top_level_selector = data.get("top_level_selector") == True
        if data.get("subselectors") is not None:
            self._subselectors = ["{}.{}".format(language, sub) for sub in data.get("subselectors")]
        else:
            self._subselectors = []

    def __str__(self):
        return "{}: {}".format(self._name, self._description)

    def select(self, file_contents: str, prefix: str = None) -> list:
        for selector in self._subselectors:
            s: Selector = Selector.get_selector_by_name(selector)
            if s is not None:
                s.select(file_contents)

    def get_is_top_level_selector(self) -> bool:
        return self._top_level_selector


class FunctionSelector(Selector):
    _parameters: int = None
    _body: int = None

    def __init__(self, language: str, name: str, data: dict):
        super(FunctionSelector, self).__init__(language, name, data)
        self._parameters = data.get("parameters")
        self._body = data.get("body")

    def select(self, file_contents: str, prefix: str = None) -> list:
        functions = re.findall(self._regex_match, file_contents)
        function: dict
        for function in functions:
            function_name = function[self._selection_name]
            function_params: list = function[self._parameters].split(',')
            function_body: list = function[self._body].split('\n')[:-1]
            func: model.FunctionModel = model.FunctionModel(function_name, function_params, function_body)
            sub_entities: list = super(FunctionSelector, self).select(
                function[self._body],
                prefix="{}.{}".format(
                    prefix,
                    function[self._selection_name]
                )
            )  # TODO deal with sub entities
            print(func)


class ParameterSelector(Selector):
    pass


class SelectorType(Enum):
    sa_function = "function"
    sa_class = "class"
    sa_parameter = "parameter"
    _class_map: dict = {
        sa_function: FunctionSelector,
        sa_class: None,  # TODO update for class selector
        sa_parameter: ParameterSelector
    }
    @staticmethod
    def get_selector_class(name: str) -> type:
        res: type = None
        if name in SelectorType._class_map.value.keys():
            res = SelectorType._class_map.value.get(name)
        return res


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
            s: Selector = Selector.get_selector(self._lang, selector, selectors.get(selector))
            if s is not None and s.get_is_top_level_selector():
                self._selectors.append(s)
        pass

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
