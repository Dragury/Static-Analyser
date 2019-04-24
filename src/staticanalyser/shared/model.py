# The shared objects that are used by the translator and navigator entities
import copy
from enum import Enum
import json
from hashlib import md5
from typing import List, Union

from staticanalyser.shared.platform_constants import SCHEMA_LOCATION, MODEL_DIR
import staticanalyser.shared.config as config
import logging
from os import path

with open(SCHEMA_LOCATION, "r") as s:
    SCHEMA: dict = json.load(s)


class ModelOperations(object):
    @staticmethod
    def prune_body(body: list, body_entities: list) -> list:
        logging.debug("Attempting to prune {}".format(body))
        logging.debug("Checking for {}".format(body_entities))
        res: list = copy.copy(body)
        try:
            for entity in body_entities:
                for index, line in enumerate(res):
                    logging.debug("Comparing {} to {}".format(line, entity))
                    # TODO change from first come first served
                    if type(line) is StatementModel and entity.get_as_strings()[0] == line.get_rhs():
                        for i in range(len(entity.get_as_strings()) - 1):
                            res.pop(index + 1)
                        res[index] = entity
            return res
        except NotImplementedError:
            return body

    @staticmethod
    def load_model_from_dict(data: dict):
        entity_type: str = data.get("model_type")
        klazz: type = ModelMap.get_model_class(entity_type)
        if klazz:
            res: Union[FunctionModel, ClassModel, DependencyModel] = klazz(hollow=True)
            res.load_from_dict(data)
            return res
        return None

    @staticmethod
    def get_model_file(global_id: str) -> path:
        res = ModelOperations._find_file_in_dir(global_id, path.abspath(".model"))
        if not res:
            res = ModelOperations._find_file_in_dir(global_id, MODEL_DIR)
        return res

    @staticmethod
    def _find_file_in_dir(global_id: str, search_dir: path, return_gid: bool = False) -> path:
        id_parts: List[str] = global_id.split(".")
        current_search_path: path = search_dir
        _ft = config.get_filetypes()
        possible_filetypes: List[str] = []
        for k in _ft.keys():
            for lang in _ft[k]:
                if lang == id_parts[0]:
                    possible_filetypes.append(k)
        for part in id_parts:
            current_search_path = path.join(current_search_path, part)
            for ft in possible_filetypes:
                test_path = "{}.{}.json".format(current_search_path, ft)
                if path.isfile(test_path):
                    if return_gid:
                        return ".".join(id_parts[:id_parts.index(part)+1])
                    return test_path
        return None

    @staticmethod
    def get_base_global_id(global_id: str):
        res = ModelOperations._find_file_in_dir(global_id, path.abspath(".model"), True)
        if not res:
            res = ModelOperations._find_file_in_dir(global_id, MODEL_DIR, True)
        return res


class ModelGeneric(object):
    def flatten(self) -> dict:
        raise NotImplementedError()

    def __str__(self):
        return str(self.flatten())

    def __repr__(self):
        return self.__str__()

    def add_subselection(self, sub_selection: dict):
        pass

    def load_from_dict(self, data: dict):
        raise NotImplementedError()


class ReferenceModel(ModelGeneric):
    _ref: str = None
    _target: str = None
    _parameters: list = None

    def __init__(self, language: str = "", prefix: str = "", data: dict = None, hollow: bool = False):
        if not hollow:
            self._ref = data.get("call")
            self._target = data.get("target") or ""
            self._parameters = data.get("parameters") or ""

    def lookup(self) -> bool:
        pass

    def flatten(self) -> dict:
        parms = []
        if not type(self._parameters) == str:
            for p in self._parameters:
                if issubclass(type(p), ModelGeneric):
                    parms.append(p.flatten())
                else:
                    parms.append(p)
        return {
            "model_type": ModelMap.REFERENCE.value,
            "ref": self._ref,
            "target": self._target,
            "parameters": parms
        }

    def get_ref(self):
        return self._ref

    def set_ref(self, new_ref: str):
        self._ref = new_ref

    def get_target(self):
        return self._target

    def get_parameters(self):
        return self._parameters

    def add_subselection(self, sub_selection: dict):
        if sub_selection.get("parameter_call"):
            self._parameters = sub_selection.get("parameter_call")

    def load_from_dict(self, data: dict):
        self._ref = data.get("ref")
        self._target = data.get("target")
        self._parameters = []
        for p in data.get("parameters"):
            v = VariableModel(hollow=True)
            v.load_from_dict(p)
            self._parameters.append(v)


class ControlFlowGeneric(ModelGeneric):
    _control_flow: dict = None

    def flatten_dict(self, *targets) -> dict:
        res: dict = {}
        for k in self._control_flow.keys():
            if k in targets:
                logging.debug("trying to flatten {}".format(k))
                res[k] = [l.flatten() if type(l) is not dict else l for l in self._control_flow[k]]
            else:
                res[k] = self._control_flow[k]
        return res

    def get_as_statements(self) -> list:
        raise NotImplementedError()

    def get_as_strings(self):
        raise NotImplementedError()


class NamedModelGeneric(ModelGeneric):
    _global_identifier: str = None
    _prefix: str = None
    _name: str = None
    _hash: str = None
    _lang: str = None
    _body: str = None

    def __init__(self, language: str = "", prefix: str = "", data: dict = None, hollow: bool = False):
        if not hollow:
            self._name = data.get("name")
            self._prefix = prefix
            self._global_identifier = "{}.{}".format(prefix, self._name)
            if data.get("body"):
                self._body = data.get("body")
                self._hash = md5(self._body.encode("utf-8")).hexdigest()
            self._lang = language

    def get_global_identifier(self):
        return self._global_identifier

    def get_hash(self):
        return self._hash

    def append_to_prefix(self, name: str):
        self._prefix = "{}.{}".format(self._prefix, name)

    def get_name(self):
        return self._name


class ClassModel(NamedModelGeneric):
    _subclasses: list = None
    _attributes: list = None
    _functions: list = None

    def __init__(self, language: str = "", prefix: str = "", data: dict = None, hollow: bool = False):
        super(ClassModel, self).__init__(language, prefix, data, hollow)
        self._subclasses = []
        self._attributes = []
        self._functions = []

    def add_subselection(self, sub_selection: dict):
        self._subclasses = sub_selection.get("class".format(self._lang))
        self._attributes = sub_selection.get("attribute".format(self._lang))
        self._functions = sub_selection.get("function".format(self._lang))

    def get_functions(self) -> list:
        return self._functions

    def set_functions(self, new_functions: list) -> None:
        self._functions = new_functions

    def flatten(self) -> dict:
        flattened_functions: list = [f.flatten() for f in self._functions]
        flattened_subclasses: list = [c.flatten() for c in self._subclasses]
        flattened_attributes: list = [a.flatten() for a in self._attributes]
        return {
            "model_type": ModelMap.CLASS.value,
            "name": self._name,
            "global_id": self._global_identifier,
            "hash": self._hash,
            "subclasses": flattened_subclasses,  # Umm, this should be parent classes?
            "methods": flattened_functions,
            "attributes": flattened_attributes,
            "body": self._body
        }

    def load_from_dict(self, data: dict):
        self._name = data.get("name")
        self._global_identifier = data.get("global_id")
        self._hash = data.get("hash")
        self._body = data.get("body")
        self._attributes = []
        for attribute in data.get("attributes"):
            a = VariableModel(hollow=True)
            a.load_from_dict(attribute)
            self._attributes.append(a)
        # TODO Function loading
        # TODO *PARENT* class reference loading


class OperatorType(Enum):
    OR = 1
    AND = 2
    NOT = 3


class OperatorModel(ModelGeneric):
    _lhs: object = None
    _rhs: object = None
    _type: OperatorType = None
    _body: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._lhs = data.get("lhs")
        self._rhs = data.get("rhs")
        self._body = data.get("body")

    def add_subselection(self, sub_selection: dict):
        if sub_selection.get("reference"):
            self._rhs = sub_selection.get("reference")
        if sub_selection.get("operation"):
            self._rhs = OperatorModel("", "", sub_selection.get("operation")[0])

    def flatten(self) -> dict:
        pass

    def get_string(self) -> str:
        return self._body


class StatementModel(ModelGeneric):
    _lhs: str = None
    _rhs: OperatorModel = None
    _body: str = None

    def __init__(self, language: str = "", prefix: str = "", data: dict = None, hollow: bool = False):
        if not hollow:
            self._lhs = data.get("lhs")
            self._rhs = data.get("rhs")
            self._body = data.get("body")

    def add_subselection(self, sub_selection: dict):
        if sub_selection.get("reference"):
            self._rhs = sub_selection.get("reference")[0]
        if sub_selection.get("operation"):
            self._rhs = sub_selection.get("operation")[0]

    def get_rhs(self):
        return self._rhs

    def get_lhs(self):
        return self._lhs

    def flatten(self) -> dict:
        rhs = self._rhs
        if not type(rhs) == str:
            rhs = rhs.flatten()
        return {
            "model_type": ModelMap.STATEMENT.value,
            "lhs": self._lhs,
            "rhs": rhs
        }

    def load_from_dict(self, data: dict):
        self._lhs = data.get("lhs")
        rhs_data: dict = data.get("rhs")
        rhs: Union[ModelGeneric, str] = None
        if type(rhs_data) is dict:
            rhs_klazz = ModelMap.get_model_class(rhs_data.get("model_type"))
            rhs = rhs_klazz(hollow=True)
            rhs.load_from_dict(rhs_data)
        else:
            rhs = rhs_data
        self._rhs = rhs


class ForLoopModel(ControlFlowGeneric):
    _loop: str = None
    _body: str = None
    _body_parsed: list = None
    _control_flow: dict = None

    def __init__(self, language: str = "", prefix: str = "", data: dict = None, hollow: bool = False):
        if not hollow:
            self._loop = data.get("loop")
            self._body = data.get("body")
            self._control_flow = {}

    def flatten(self) -> dict:
        return {
            "model_type": ModelMap.FOR_LOOP.value,
            "loop": self._loop,
            "body": self._body,
            "body_parsed": [s.flatten() for s in self._body_parsed]
        }

    def add_subselection(self, sub_selection: dict):
        self._body_parsed = sub_selection.get("statement") or []
        self._control_flow["for"] = sub_selection.get("for_loop") or []
        self._control_flow["while"] = sub_selection.get("while_loop") or []
        self._body_parsed = ModelOperations.prune_body(
            sub_selection.get("statement"),
            [
                *(sub_selection.get("for_loop") or []),
                *(sub_selection.get("if_condition") or []),
                *(sub_selection.get("while_loop") or [])
            ]
        )

    def get_as_strings(self) -> list:
        res: list = [self._loop]
        res += [l.strip() for l in self._body.split("\n")]
        return res

    def get_as_statements(self) -> list:
        return self._body_parsed

    def load_from_dict(self, data: dict):
        self._loop = data.get("loop")
        self._body = data.get("body")
        self._body_parsed = []
        for entity in data.get("body_parsed"):
            klazz = ModelMap.get_model_class(entity.get("model_type"))
            e = klazz(hollow=True)
            e.load_from_dict(entity)
            self._body_parsed.append(e)


class WhileLoopModel(ControlFlowGeneric):
    _loop: str = None
    _body: str = None  # first body, e.g. if true
    _body_parsed: list = None
    _condition: str = None
    _control_flow: dict = None
    _do_while: bool = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._loop = data.get("loop")
        self._body = data.get("body")
        self._condition = data.get("condition")
        self._control_flow = {}
        pass

    def flatten(self) -> dict:
        self._control_flow = self.flatten_dict("for", "while", "if")
        return {
            "model_type": ModelMap.WHILE_LOOP.value,
            "loop": self._loop,
            "condition": self._condition,
            "body": self._body,
            "body_parsed": [s.flatten() for s in self._body_parsed]
        }

    def add_subselection(self, sub_selection: dict):
        self._body_parsed = sub_selection.get("statement") or []
        self._control_flow["for"] = sub_selection.get("for_loop") or []
        self._control_flow["while"] = sub_selection.get("while_loop") or []
        self._body_parsed = ModelOperations.prune_body(
            sub_selection.get("statement") or [],
            sub_selection.get("for_loop") or [] +
            sub_selection.get("while_loop") or []
        )

    def get_as_strings(self) -> list:
        res: list = [self._loop]
        res += [l.strip() for l in self._body.split("\n")]
        return res

    def get_as_statements(self) -> list:
        return self._body_parsed


class ConditionModel(ControlFlowGeneric):
    _condition: OperatorModel = None
    _true_condition: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._condition = data.get("condition")
        self._control_flow = {
            "true": data.get("true_block") or "",
            "false": data.get("false_block") or ""
        }

    def flatten(self) -> dict:
        # self._control_flow = self.flatten_dict("true", "false")
        return {
            "model_type": ModelMap.CONDITION.value,
            "condition": self._condition,
            "blocks": {
                "true_block": [s.flatten() for s in self._control_flow.get("true_block")],
                "false_block": [s.flatten() for s in self._control_flow.get("false_block")] if self._control_flow.get(
                    "false_block") else []
            }
        }

    def add_subselection(self, sub_selection: dict):
        self._control_flow["true_block"] = ModelOperations.prune_body(
            sub_selection.get("statement").get("true_block"),
            sub_selection.get("if_condition").get("true_block") if sub_selection.get(
                "if_condition") and sub_selection.get("if_condition").get("true_block") else [] +
                                                                                             sub_selection.get(
                                                                                                 "for_loop").get(
                                                                                                 "true_block") if sub_selection.get(
                "for_loop") and sub_selection.get("for_loop").get("true_block") else [] +
                                                                                     sub_selection.get(
                                                                                         "while_loop").get(
                                                                                         "true_block") if sub_selection.get(
                "while_loop") and sub_selection.get("while_loop").get("true_block") else []
        )
        self._control_flow["false_block"] = ModelOperations.prune_body(
            sub_selection.get("statement").get("false_block"),
            sub_selection.get("if_condition").get("false_block") if sub_selection.get(
                "if_condition") and sub_selection.get("if_condition").get("false_block") else [] +
                                                                                              sub_selection.get(
                                                                                                  "for_loop").get(
                                                                                                  "false_block") if sub_selection.get(
                "for_loop") and sub_selection.get("for_loop").get("false_block") else [] +
                                                                                      sub_selection.get(
                                                                                          "while_loop").get(
                                                                                          "false_block") if sub_selection.get(
                "while_loop") and sub_selection.get("while_loop").get("false_block") else []
        ) if sub_selection.get("statement").get("false_block") else []

    def get_as_strings(self) -> list:
        res: list = ["if {}:".format(self._condition)]  # .get_string()
        res += [l.strip() for l in self._control_flow["true"].split("\n")]
        if self._control_flow["false"] is not "":
            res.append("else:")
            res += [l.strip() for l in self._control_flow["false"].split("\n")]
        return res

    def get_as_statements(self) -> list:
        res: list = self._control_flow.get("true_block")
        res += self._control_flow.get("false_block") or []
        return res


class FunctionModel(NamedModelGeneric, ControlFlowGeneric):
    _parameters: list = None
    _statements: list = None
    _control_flow: dict = None
    _declaration: str = None

    def __init__(self, language: str = "", prefix: str = "", data: dict = None, hollow: bool = False):
        super(FunctionModel, self).__init__(language, prefix, data, hollow)
        if not hollow:
            self._parameters = data.get("parameters")
            self._control_flow = {}
            self._declaration = data.get("declaration")

    def add_subselection(self, sub_selection: dict):
        self._parameters = sub_selection.get("parameter") or []
        self._statements = ModelOperations.prune_body(
            sub_selection.get("statement") or [],
            sub_selection.get("for_loop") or [] +
            sub_selection.get("while_loop") or [] +
            sub_selection.get("if_condition") or [] +
            sub_selection.get("function") or []
        )

    def get_as_statements(self) -> list:
        return self._statements

    def flatten(self):
        return {
            "model_type": ModelMap.FUNCTION.value,
            "name": self._name,
            "global_id": self.get_global_identifier(),
            "hash": self._hash,
            "parameters": [p.flatten() for p in self._parameters],
            "body": self._body,
            "body_parsed": [s.flatten() for s in self._statements]
        }

    def get_as_strings(self) -> list:
        res: list = [self._declaration]
        res += [l.strip() for l in self._body.split('\n')]
        return res

    def load_from_dict(self, data: dict):
        self._name = data.get("name")
        self._hash = data.get("hash")
        self._body = data.get("body")
        self._statements = []
        self._global_identifier = data.get("global_id")
        # TODO load body
        self._parameters = []
        for parameter in data.get("parameters"):
            p = VariableModel(hollow=True)
            p.load_from_dict(parameter)
            self._parameters.append(p)
        body_parsed: List[dict] = data.get("body_parsed")
        for entity in body_parsed:
            klazz = ModelMap.get_model_class(entity.get("model_type"))
            if klazz:
                e = klazz(hollow=True)
                e.load_from_dict(entity)
                self._statements.append(e)


class VariableModel(NamedModelGeneric):
    _name: str = None
    _type: str = None
    _default: str = None

    def __init__(self, language: str = "", prefix: str = "", data: dict = None, hollow: bool = False):
        super(VariableModel, self).__init__(language, prefix, data, hollow)
        if not hollow:
            self._default = data.get("initial_value") or data.get("default_value") or ""
            self._name = data.get("name")
            self._type = data.get("type") or ""

    def flatten(self):
        return {
            "model_type": ModelMap.VARIABLE.value,
            "name": self._name,
            "type": self._type,
            "default_value": self._default
        }

    def load_from_dict(self, data: dict):
        self._name = data.get("name")
        self._type = data.get("type")
        self._default = data.get("default_value")

    def get_type(self):
        return self._type

    def get_default(self):
        return self._default


class DependencyModel(ModelGeneric):
    _source: str = None
    _provides: list = None

    def __init__(self, language: str = "", prefix: str = "", data: dict = None, hollow: bool = False):
        if not hollow:
            self._source = data.get("source")
            self._provides = data.get("provides")
            print(data.get("provides"))

    def add_subselection(self, sub_selection: dict):
        if sub_selection.get("provided_dependencies") != []:
            self._provides = sub_selection.get("provided_dependencies")

    def flatten(self) -> dict:
        return {
            "model_type": ModelMap.DEPENDENCY.value,
            "source": self._source,
            "provides": [p.flatten() for p in self._provides if type(p) != str]
        }

    def get_provided_imports(self):
        return self._provides

    def get_source(self):
        return self._source

    def load_from_dict(self, data: dict):
        self._source = data.get("source")
        self._provides = [BasicString("", "", {"value": p}) for p in data.get("provides")]


class BasicString(ModelGeneric):
    _value: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._value = data.get("value")

    def flatten(self):
        return {
            "type": ModelMap.STRING.value,
            "val": self._value
        }

    def get_value(self):
        return self._value


def load_model(global_id):
    pass


class ModelMap(Enum):
    CLASS = "class"
    FUNCTION = "function"
    WHILE_LOOP = "while_loop"
    FOR_LOOP = "for_loop"
    CONDITION = "if_condition"
    STATEMENT = "statement"
    STRING = "basic_string"
    DEPENDENCY = "dependency"
    VARIABLE = "variable"
    REFERENCE = "reference"
    _type_map = {
        CLASS: ClassModel,
        FUNCTION: FunctionModel,
        WHILE_LOOP: WhileLoopModel,
        FOR_LOOP: ForLoopModel,
        CONDITION: ConditionModel,
        STATEMENT: StatementModel,
        STRING: BasicString,
        DEPENDENCY: DependencyModel,
        VARIABLE: VariableModel,
        REFERENCE: ReferenceModel
    }

    @staticmethod
    def get_model_class(name: str) -> type:
        return ModelMap._type_map.value.get(name)
