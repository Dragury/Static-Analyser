import datetime
from hashlib import md5
from enum import Enum
from os import path
from pathlib import Path

import sys
from jsonschema import validate

import toml
from staticanalyser.shared.platform_constants import LANGS_DIR, PATH_SEPARATOR
import staticanalyser.shared.model as model
from staticanalyser.regexbuilder import *
import re
import json


class RegexBuilderFactory(object):
    _builders: dict = {}

    @staticmethod
    def get_builder(lang: str, snippets: dict = None, format_strings: dict = None):
        if not snippets:
            snippets = {}
        if not format_strings:
            format_strings = {}
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
            print(self._name)
            try:
                # print(regex)
                # print(file_contents)
                artefacts: list = re.findall(regex, file_contents, flags=re.M)
                # print(artefacts)
                # print(regex)
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
                                for st in self._subselectors[selector]["search_texts"]:
                                    if artefact_info.get(st):
                                        _res = s.select(
                                            artefact_info.get(st),
                                            prefix
                                        )
                                        if not sub_selection.get(selector):
                                            sub_selection[selector] = _res
                                        else:
                                            sub_selection[selector] += _res

                        a.add_subselection(sub_selection)
                        res.append(a)
            except re.error:
                print(self._name, file=sys.stderr)
                print("regex error", file=sys.stderr)
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
    sa_for_loop = "for_loop"
    sa_while_loop = "while_loop"
    sa_if_condition = "if_condition"
    sa_dependency = "dependency"
    sa_basic_string = "basic_string"
    sa_operation = "operation"
    sa_reference = "reference"
    _class_map: dict = {
        sa_function: model.FunctionModel,
        sa_class: model.ClassModel,
        sa_variable: model.VariableModel,
        sa_statement: model.StatementModel,
        sa_for_loop: model.ForLoopModel,
        sa_while_loop: model.WhileLoop,
        sa_dependency: model.DependencyModel,
        sa_if_condition: model.ConditionModel,
        sa_basic_string: model.BasicString,
        sa_operation: model.OperatorModel,
        sa_reference: model.ReferenceModel
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
            file_contents = directive.apply(file_contents)
        return file_contents


class Descriptor(object):
    _language_global_lock: dict = {}
    _descriptors: dict = {}
    _lang: str = None
    _syntax_descriptor: dict = None
    _preprocessor: Preprocessor = None
    _selectors: list = None
    _json_mappings: dict = None
    _global_source_dirs: list = None

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
            self._json_mappings = language_config.get("json_mappings") or {}

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

    def select(self, file_contents: str, prefix=None) -> dict:
        res: dict = {}
        selector: Selector
        for selector in self._selectors:
            if selector is not None:
                res[self._json_mappings.get(selector.get_name()) or selector.get_name()] = selector.select(file_contents, prefix=prefix or self._lang)
        return res

    def __str__(self):
        return self._lang

    def _get_shortest_path(self, input_file: str, source_paths: list) -> str:
        cur_source_path = None
        for p in source_paths:
            if not cur_source_path or len(path.relpath(input_file, p)) < len(
                    path.relpath(input_file, cur_source_path)):
                cur_source_path = p
        return cur_source_path

    def _get_base_prefix(self, filename: str, extension: str, source_paths: list):
        file_path: str = self._get_shortest_path(filename, source_paths)
        return "{}.{}".format(self._lang, path.relpath(filename, file_path)[:-1*len(".{}".format(extension))].replace(PATH_SEPARATOR, '.'))

    def _get_json_path(self, output_path: path, input_file: str, source_paths: list):
        object_path = self._get_shortest_path(input_file, source_paths)

        model_path: path = path.relpath(input_file, object_path)
        return path.join(output_path, self._lang, model_path) + ".json"

    def output_json(self, output_path: path, input_file: str, source_paths: path, sa_model: dict,
                    file_hash: str):
        file_path: path = self._get_json_path(output_path, input_file, source_paths)
        file_dir: path = path.abspath(path.dirname(file_path))
        if not path.exists(file_dir):
            Path(file_dir).mkdir(parents=True, exist_ok=True)
        with open(file_path, "w") as f:
            sa_model["hash"] = file_hash
            sa_model["file_name"] = str(input_file)
            sa_model["date_generated"] = str(datetime.datetime.now())
            group: str
            for group in sa_model.keys():
                se: list = sa_model.get(group)
                if type(se) is list:
                    for i in range(len(se)):
                        se.append(se.pop(0).flatten())
            # k: list = [*sa_model.keys()]
            # for key in self._json_mappings.keys():
            #     if key in sa_model.keys():
            #         sa_model[self._json_mappings[key]] = sa_model[key]
            #         del sa_model[key]

            validate(sa_model, model.SCHEMA)
            json_output = json.dumps(sa_model, indent=4)

            print(json_output, file=f)

    def parse(self, file: str, file_extension: str, local_dir: path, source_paths: path, force: bool):
        # TODO normalise whitespace for better parsing, either \t or 4 spaces
        # TODO check for local file so I know the namespace for where entities live(global vs local)
        # TODO check stored model for existing model + different hash from source
        try:
            with open(file, "r") as f:
                file_contents: str = f.read()
            file_hash: str = md5(file_contents.encode("utf-8")).hexdigest()
            model_expired: bool = True
            if path.exists(self._get_json_path(local_dir, file, source_paths)) and not force:
                with open(self._get_json_path(local_dir, file, source_paths), "r") as m:
                    json_model = json.load(m)
                    if json_model.get("hash") == file_hash:
                        model_expired = False

            # print("File before:")
            # print(file_contents)
            if model_expired:
                print("Translating {}".format(file))
                file_contents = self.preprocess(file_contents)
                # print("File after:")
                # print(file_contents)
                prefix: str = self._get_base_prefix(file, file_extension, source_paths)
                selected_entities: dict = self.select(file_contents, prefix)

                # print(selected_entities)
                # TODO resolve references, cull duplicates
                klazz: model.ClassModel
                for klazz in selected_entities.get("classes") or []:
                    # print(klazz)
                    func: model.FunctionModel
                    for func in klazz.get_functions():
                        function_hash = func.get_hash()
                        tlfunc: model.FunctionModel
                        for tlfunc in selected_entities.get("functions") or []:
                            if tlfunc.get_hash() == function_hash:
                                selected_entities.get("functions").remove(tlfunc)

                self.output_json(local_dir, file, source_paths, selected_entities, file_hash)
                print("Translation done for {}".format(file))
            else:
                print("Skipping {}".format(file))
        except UnicodeDecodeError:
            print("Skipping {} due to decoding error".format(file))
