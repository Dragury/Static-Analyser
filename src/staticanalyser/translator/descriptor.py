from io import TextIOWrapper
from enum import Enum
from os import path
import toml
from staticanalyser.shared.platform_constants import LANGS_DIR
import staticanalyser.shared.model as model
from staticanalyser.regexbuilder import *
import re
import json


class RegexBuilderFactory(object):
    _builders: dict = {}

    @staticmethod
    def get_builder(lang: str, snippets: dict, format_strings: dict):
        r: RegexBuilder
        if RegexBuilderFactory._builders.get(lang) is None:
            r = RegexBuilder()
            for s in snippets.keys():
                r.register_snippet(s, snippets[s]["regex"])
            for f in format_strings.keys():
                deps = []
                if "dependencies" in format_strings[f].keys():
                    deps = format_strings[f]["dependencies"]
                r.register_format_string(f, format_strings[f]["regex"], deps)
        else:
            r = RegexBuilderFactory._builders.get(lang)
        return r


class Directive(object):
    _name: str = None
    _description: str = None
    _regex_match: str = None
    _regex_replace: str = None

    def __init__(self, name: str, regex_match: str, data: dict):
        self._name = name
        self._description = data.get("description")
        self._regex_replace = data.get("regex_replace")
        self._regex_match = regex_match

    def __str__(self):
        return "{}: {}".format(self._name, self._description)

    def apply(self, file_contents: str) -> str:
        if self._regex_match is not None:
            return re.sub(self._regex_match, self._regex_replace, file_contents)
        else:
            return file_contents


class Selector(object):
    _lang: str = None
    _registered_selectors: dict = {}
    _name: str = None
    _selection_name: int = None
    _description: str = None
    _subselectors: list = None
    _regex_matches: list = None
    _top_level_selector: bool = None
    _model_type: type = None

    @staticmethod
    def get_selector(language: str, name: str, data: dict):
        if "{}.{}".format(language, name) not in Selector._registered_selectors.keys():
            if SelectorType.get_selector_class(name) is not None:
                Selector._registered_selectors["{}.{}".format(language, name)] = Selector(language, name, data)
            # if name == SelectorType.sa_function.value:
            #     Selector._registered_selectors["{}.{}".format(language, name)] = FunctionSelector(language, name, data)
            # elif name == SelectorType.sa_class.value:
            #     Selector._registered_selectors["{}.{}".format(language, name)] = None
            # if
        return Selector._registered_selectors.get("{}.{}".format(language, name))

    @staticmethod
    def get_selector_by_name(name: str):
        return Selector._registered_selectors.get(name)

    def __init__(self, language: str, name: str, format_string: list, data: dict):
        self._model_type = mtype
        self._name = name
        self._lang = language
        self._description = data.get("description")
        self._regex_match = format_string
        self._selection_name = data.get("name")
        self._top_level_selector = data.get("top_level_selector")
        if data.get("subselectors") is not None:
            self._subselectors = ["{}.{}".format(language, sub) for sub in data.get("subselectors")]
        else:
            self._subselectors = []

    def __str__(self):
        return "{}: {}".format("{}.{}".format(self._lang, self._name), self._description)

    def select(self, file_contents: str, prefix: str = "") -> dict:
        res: dict = {}
        for selector in self._subselectors:
            s: Selector = Selector.get_selector_by_name(selector)
            if s is not None:
                res[selector] = s.select(file_contents, prefix)
        return res

    def get_is_top_level_selector(self) -> bool:
        return self._top_level_selector

    def get_name(self) -> str:
        return self._name

    def get_qualified_name(self) -> str:
        return "{}.{}".format(self._lang, self._name)


class FunctionSelector(Selector):
    _parameters: int = None
    _body: int = None

    def __init__(self, language: str, name: str, format_string: str, data: dict):
        super(FunctionSelector, self).__init__(language, name, format_string, data)
        self._parameters = data.get("parameters")
        self._body = data.get("body")

    def select(self, file_contents: str, prefix: str = "") -> list:
        functions = re.findall(self._regex_match, file_contents)
        res: list = []
        function: tuple
        for function in functions:
            function_name = function[self._selection_name]
            ps: ParameterSelector = Selector.get_selector_by_name("{}.{}".format(self._lang, "parameter"))
            function_params: list = ps.select(function[self._parameters])
            function_body: list = function[self._body].split('\n')[:-1]
            sub_entities: dict = super(FunctionSelector, self).select(
                function[self._body],
                prefix="{}.{}".format(
                    prefix,
                    function[self._selection_name]
                )
            )  # TODO deal with sub entities
            func: model.FunctionModel = model.FunctionModel(self._lang, "{}.{}".format(prefix, function_name),
                                                            function_params,
                                                            function_body)
            res.append(func)
            print(func.flatten())
            for sub_group in sub_entities.keys():
                res += sub_entities.get(sub_group)
        return res


class ParameterSelector(Selector):
    _type: int = None
    _default_value: int = None

    def __init__(self, language: str, name: str, format_string: str, data: dict):
        super(ParameterSelector, self).__init__(language, name, format_string, data)
        self._type = data.get("type")
        self._default_value = data.get("default_value")

    def select(self, file_contents: str, prefix: str = "") -> list:
        parameters: list = re.findall(self._regex_match, file_contents)
        res: list = []
        parameter: tuple
        for parameter in parameters:
            parameter_name: str = parameter[self._selection_name]
            parameter_type: str = parameter[self._type]
            parameter_default: str = parameter[self._default_value]

            res.append(model.VariableModel(
                self._lang,
                "{}.{}".format(prefix, parameter_name),
                parameter_type,
                parameter_default
            ))
        return res


class ClassSelector(Selector):
    _subclasses: int = None
    _body: int = None

    def __init__(self, language: str, name: str, format_string: str, data: dict):
        super(ClassSelector, self).__init__(language, name, format_string, data)
        self._subclasses = data.get("subclasses")
        self._body = data.get("body")

    def select(self, file_contents: str, prefix: str = ""):
        klazzes: list = re.findall(self._regex_match, file_contents)
        res: list = []
        klazz: tuple
        for klazz in klazzes:
            klazz_name: str = klazz[self._selection_name]
            klazz_subclasses: str = klazz[self._subclasses]
            sub_entities: dict = super(ClassSelector, self).select(
                klazz[self._body],
                prefix="{}.{}".format(
                    prefix,
                    klazz_name
                )
            )
            klazz_model: model.ClassModel = model.ClassModel(self._lang, "{}.{}".format(prefix, klazz_name), [],
                                                             sub_entities)
            res.append(klazz_model)
            print(klazz_model.flatten())
        return res


class AttributeSelector(Selector):
    _type: int = None
    _initial_value: int = None

    def __init__(self, language: str, name: str, format_string: str, data: dict):
        super(AttributeSelector, self).__init__(language, name, format_string, data)
        self._type = data.get("type")
        self._initial_value = data.get("initial_value")

    def select(self, file_contents: str, prefix: str = ""):
        attributes: list = re.findall(self._regex_match, file_contents)

        res: list = []
        for attribute in attributes:
            attribute_name: str = attribute[self._selection_name]
            attribute_type: str = attribute[self._type]
            attribute_value: str = attribute[self._initial_value]
            attribute_model: model.VariableModel = model.VariableModel(
                self._lang,
                "{}.{}".format(prefix, attribute_name),
                attribute_type,
                attribute_value
            )
            res.append(attribute_model)
        return res


class SelectorType(Enum):
    sa_function = "function"
    sa_class = "class"
    sa_parameter = "parameter"
    sa_attribute = "attribute"
    _class_map: dict = {
        sa_function: FunctionSelector,
        sa_class: ClassSelector,
        sa_parameter: ParameterSelector,
        sa_attribute: AttributeSelector
    }

    @staticmethod
    def get_selector_class(name: str) -> type:
        res: type = None
        if name in SelectorType._class_map.value.keys():
            res = SelectorType._class_map.value.get(name)
        return res


class Preprocessor(object):
    _lang: str = None
    _directives: list = None

    def __init__(self, lang: str, directives: dict, regex_builder: RegexBuilder):
        self._directives = []
        self._lang = lang
        for directive in directives.keys():
            regex_match: str = regex_builder.build(directives[directive]["regex_format_string"])
            self._directives.append(Directive(directive, regex_match, directives.get(directive)))

    def apply(self, file_contents: str):
        directive: Directive
        for directive in self._directives:
            print(directive)
            file_contents = directive.apply(file_contents)
        return file_contents


class Descriptor(object):
    _descriptors: dict = {}
    _lang: str = None
    _syntax_descriptor: dict = None
    _preprocessor: Preprocessor = None
    _selectors: list = None

    @staticmethod
    def get_descriptor(language: str):
        if language not in Descriptor._descriptors.keys():
            Descriptor._descriptors[language] = Descriptor(language)
        return Descriptor._descriptors[language]

    def __init__(self, language_name: str):
        if language_name is None:
            return
        else:
            self._lang = language_name
            # TODO loading from lang files
            language_config = None
            with open(path.join(LANGS_DIR, "{}.toml".format(language_name)), "r") as language_file:
                language_config = toml.load(language_file)

            self._configure_regex_builder(language_config.get("snippets"), language_config.get("format_strings"))
            self._load_preprocessor(language_config.get("directives"))
            self._load_selectors(language_config.get("selectors"))

    def _configure_regex_builder(self, snippets: dict, format_strings: dict):
        RegexBuilderFactory.get_builder(self._lang, snippets, format_strings)

    def _load_preprocessor(self, directives: dict):
        self._preprocessor = Preprocessor(self._lang, directives)

    def _load_selectors(self, selectors: dict):
        self._selectors = []
        for selector in selectors.keys():
            s: Selector = Selector.get_selector(self._lang, selector, selectors.get(selector))
            if s is not None and s.get_is_top_level_selector():
                self._selectors.append(s)

    def preprocess(self, file_contents: str) -> str:
        return self._preprocessor.apply(file_contents)

    def select(self, file_contents: str) -> dict:
        res: dict = {}
        selector: Selector
        for selector in self._selectors:
            if selector is not None:
                res[selector.get_qualified_name()] = selector.select(file_contents)
        return res

    def __str__(self):
        return self._lang

    def parse(self, file: TextIOWrapper):
        temp_map: dict = {
            "function": "functions",
            "class": "classes"
        }
        # TODO check for local file so I know the namespace for where entities live(global vs local)
        file_contents: str = file.read()
        print("File before:")
        print(file_contents)
        file_contents = self.preprocess(file_contents)
        print("File after:")
        print(file_contents)
        selected_entities: dict = self.select(file_contents)
        print(selected_entities)
        with open("out.json", "w") as f:
            group: str
            for group in selected_entities.keys():
                se: list = selected_entities.get(group)
                for i in range(len(se)):
                    se.append(se.pop(0).flatten())
            k: list = [*selected_entities.keys()]
            for key in k:
                selected_entities[temp_map.get(key.split(".")[-1:][0])] = selected_entities[key]
                del selected_entities[key]
            print(json.dumps(selected_entities), file=f)
