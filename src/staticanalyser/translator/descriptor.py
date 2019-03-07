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
    def get_builder(lang: str, snippets: dict = {}, format_strings: dict = {}):
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
            RegexBuilderFactory._builders[lang] = r
        else:
            r = RegexBuilderFactory._builders.get(lang)
        return r


class Directive(object):
    _name: str = None
    _description: str = None
    _variations: list = None
    _lang: str = None

    def __init__(self, language: str, name: str, data: dict):
        self._name = name
        self._description = data.get("description")
        self._variations = data.get("variations")
        self._lang = language

    def __str__(self):
        return "{}: {}".format(self._name, self._description)

    def apply(self, file_contents: str) -> str:
        r: RegexBuilder = RegexBuilderFactory.get_builder(self._lang)
        for v in self._variations:
            file_contents = re.sub(
                r.build(v.get("regex_format_string")),
                v.get("regex_replace"),
                file_contents
            )
        return file_contents


class Selector(object):
    _lang: str = None
    _registered_selectors: dict = {}
    _name: str = None
    _selection_name: int = None
    _description: str = None
    _subselectors: dict = None
    _variations: list = None
    _top_level_selector: bool = None
    _model_type: type = None

    @staticmethod
    def get_selector(language: str, name: str, data: dict):
        if "{}.{}".format(language, name) not in Selector._registered_selectors.keys():
            Selector._registered_selectors["{}.{}".format(language, name)] = Selector(language, name, data)
        return Selector._registered_selectors.get("{}.{}".format(language, name))

    @staticmethod
    def get_selector_by_name(name: str):
        return Selector._registered_selectors.get(name)

    def __init__(self, language: str, name: str, data: dict):
        self._model_type = SelectorType.get_model_class(data.get("model_element"))
        self._name = name
        self._lang = language
        self._description = data.get("description")
        self._variations = data.get("variations")
        self._selection_name = data.get("name")
        self._top_level_selector = data.get("top_level_selector")
        self._subselectors = {}
        if data.get("subselectors") is not None:
            self._subselectors = data.get("subselectors")

    def __str__(self):
        return "{}: {}".format("{}.{}".format(self._lang, self._name), self._description)

    def select(self, file_contents: str, prefix: str = "") -> list:
        res: list = []
        v: dict
        for v in self._variations:
            r: RegexBuilder = RegexBuilderFactory.get_builder(self._lang)
            regex: str = r.build(v.get("regex_format_string"))
            artefacts: list = re.findall(regex, file_contents)
            for artefact in artefacts:
                artefact_info: dict = {}
                for k in v.keys():
                    if k != "regex_format_string":
                        artefact_info[k] = artefact[v[k]]
                a: model.ModelGeneric
                if self._model_type is not None:
                    a = self._model_type(self._lang, prefix, artefact_info)

                    sub_selection: dict = {}
                    for selector in self._subselectors.keys():
                        s: Selector = Selector.get_selector_by_name("{}.{}".format(self._lang, selector))
                        if s is not None:
                            sub_selection[selector] = s.select(
                                artefact_info.get(self._subselectors[selector]["search_text"]),
                                prefix
                            )

                    a.add_subselection(sub_selection)
                    res.append(a)
        return res

    def get_is_top_level_selector(self) -> bool:
        return self._top_level_selector

    def get_name(self) -> str:
        return self._name

    def get_qualified_name(self) -> str:
        return "{}.{}".format(self._lang, self._name)


class SelectorType(Enum):
    sa_function = "function"
    sa_class = "class"
    sa_variable = "variable"
    sa_statement = "statement"
    _class_map: dict = {
        sa_function: model.FunctionModel,
        sa_class: model.ClassModel,
        sa_variable: model.VariableModel,
        sa_statement: model.StatementModel
    }

    @staticmethod
    def get_model_class(name: str) -> type:
        return SelectorType._class_map.value.get(name)


class Preprocessor(object):
    _lang: str = None
    _directives: list = None

    def __init__(self, lang: str, directives: dict):
        r: RegexBuilder = RegexBuilderFactory.get_builder(lang)
        self._directives = []
        self._lang = lang
        for directive in directives.keys():
            self._directives.append(Directive(lang, directive, directives.get(directive)))

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
                res[selector.get_name()] = selector.select(file_contents)
        return res

    def __str__(self):
        return self._lang

    def parse(self, file: TextIOWrapper):
        temp_map: dict = {
            "top_level_function": "functions",
            "class": "classes",
            "import": "dependencies"
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
