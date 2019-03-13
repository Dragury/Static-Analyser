# The shared objects that are used by the translator and navigator entities
from enum import Enum
import json
from hashlib import md5
from staticanalyser.shared.platform_constants import SCHEMA_LOCATION

SCHEMA: dict = None
with open(SCHEMA_LOCATION, "r") as s:
    SCHEMA = json.load(s)


class ReferenceModel(str):
    def lookup(self) -> bool:
        pass


class ModelGeneric(object):
    def flatten(self) -> dict:
        raise NotImplementedError()

    def __str__(self):
        return str(self.flatten())

    def __repr__(self):
        return self.__str__()

    def add_subselection(self, sub_selection: dict):
        pass


class ControlFlowGeneric(ModelGeneric):
    _control_flow: dict = None

    def flatten_dict(self, *targets) -> dict:
        res: dict = {}
        for k in self._control_flow.keys():
            if k in targets:
                res[k] = [l.flatten() for l in self._control_flow[k]]
            else:
                res[k] = self._control_flow[k]
        return res


class NamedModelGeneric(ModelGeneric):
    _global_identifier: ReferenceModel = None
    _name: str = None
    _hash: str = None
    _lang: str = None
    _body: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._name = data.get("name")
        self._global_identifier = "{}.{}".format(prefix, self._name)
        self._body = data.get("body")
        self._hash = md5(self._body.encode("utf-8")).hexdigest()
        self._lang = language

    def get_global_identifier(self):
        return self._global_identifier

    def get_hash(self):
        return self._hash


class ClassModel(NamedModelGeneric):
    _subclasses: list = None
    _attributes: list = None
    _functions: list = None

    def __init__(self, language: str, prefix: str, data: dict):
        super(ClassModel, self).__init__(language, prefix, data)
        self._subclasses = []
        self._attributes = []
        self._functions = []

    def add_subselection(self, sub_selection: dict):
        self._subclasses = sub_selection.get("class".format(self._lang))
        self._attributes = sub_selection.get("attribute".format(self._lang))
        self._functions = sub_selection.get("function".format(self._lang))

    def get_functions(self) -> list:
        return self._functions

    def flatten(self) -> dict:
        flattened_functions: list = [f.flatten() for f in self._functions]
        flattened_subclasses: list = [c.flatten() for c in self._subclasses]
        flattened_attributes: list = [a.flatten() for a in self._attributes]
        return {
            "model_type": "class",
            "name": self._name,
            "global_id": self.get_global_identifier(),
            "hash": self._hash,
            "subclasses": flattened_subclasses,
            "methods": flattened_functions,
            "attributes": flattened_attributes,
            "body": self._body
        }


class OperatorType(Enum):
    OR = 1
    AND = 2
    NOT = 3


class OperatorModel(ModelGeneric):
    _lhs: object = None
    _rhs: object = None
    _type: OperatorType = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._lhs = data.get("lhs")
        self._rhs = data.get("rhs")

    def add_subselection(self, sub_selection: dict):
        self._lhs = OperatorModel(None, None, sub_selection.get())

    def flatten(self) -> dict:
        pass


class StatementModel(ModelGeneric):
    _lhs: ReferenceModel = None
    _rhs: OperatorModel = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._lhs = data.get("lhs")
        self._rhs = data.get("rhs")

    def flatten(self) -> dict:
        return {
            "lhs": self._lhs,
            "rhs": self._rhs  # TODO .flatten()
        }


class ForLoopModel(ControlFlowGeneric):
    _loop: str = None
    _body: str = None  # first body, e.g. if true
    _body_parsed: list = None
    _control_flow: dict = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._loop = data.get("loop")
        self._body = data.get("body")
        self._control_flow = {}

    def flatten(self) -> dict:
        self._control_flow = self.flatten_dict("for", "while", "if")
        return {
            "loop": self._loop,
            "body": self._body,
            "body_parsed": [s.flatten() for s in self._body_parsed],
            "control_flow": self._control_flow
        }

    def add_subselection(self, sub_selection: dict):
        self._body_parsed = sub_selection.get("statement") or []
        self._control_flow["for"] = sub_selection.get("for_loop") or []
        self._control_flow["while"] = sub_selection.get("while_loop") or []


class WhileLoop(ControlFlowGeneric):
    _loop: str = None
    _body: str = None  # first body, e.g. if true
    _body_parsed: list = None
    _condition: str = None
    _control_flow: dict = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._loop = data.get("loop")
        self._body = data.get("body")
        self._condition = data.get("condition")
        self._control_flow = {}
        pass

    def flatten(self) -> dict:
        self._control_flow = self.flatten_dict("for", "while", "if")
        return {
            "loop": self._loop,
            "condition": self._condition,
            "body": self._body,
            "body_parsed": [s.flatten() for s in self._body_parsed],
            "control_flow": self._control_flow
        }

    def add_subselection(self, sub_selection: dict):
        self._body_parsed = sub_selection.get("statement") or []
        self._control_flow["for"] = sub_selection.get("for_loop") or []
        self._control_flow["while"] = sub_selection.get("while_loop") or []


class ConditionModel(ControlFlowGeneric):
    _condition: StatementModel = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._condition = data.get("condition")
        self._control_flow = {
            "true": data.get("true_block") or [],
            "false": data.get("false_block") or []
        }

    def flatten(self) -> dict:
        # self._control_flow = self.flatten_dict("true", "false")
        return {
            "condition": self._condition,
            "blocks": self._control_flow
        }


class FunctionModel(NamedModelGeneric, ControlFlowGeneric):
    _parameters: list = None
    _statements: list = None
    _control_flow: dict = None

    def __init__(self, language: str, prefix: str, data: dict):
        super(FunctionModel, self).__init__(language, prefix, data)
        self._parameters = data.get("parameters")
        self._control_flow = {}

    def add_subselection(self, sub_selection: dict):
        self._parameters = sub_selection.get("parameter") or []
        self._statements = sub_selection.get("statement") or []
        self._control_flow["for"] = sub_selection.get("for_loop") or []
        self._control_flow["while"] = sub_selection.get("while_loop") or []
        self._control_flow["if"] = sub_selection.get("if_condition") or []

    def flatten(self):
        self._control_flow = self.flatten_dict("for", "while", "if")
        return {
            "model_type": "function",
            "name": self._name,
            "global_id": self.get_global_identifier(),
            "hash": self._hash,
            "parameters": [p.flatten() for p in self._parameters],
            "body": self._body,
            "body_parsed": [s.flatten() for s in self._statements],
            "control_flow": self._control_flow
        }


class VariableModel(ModelGeneric):
    _lang: str = None
    _name: str = None
    _type: str = None
    _default: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._default = data.get("initial_value") or data.get("default_value") or ""
        self._name = data.get("name")
        self._type = data.get("type") or ""
        self._lang = language

    def flatten(self):
        return {
            "name": self._name,
            "type": self._type,
            "default_value": self._default
        }


class DependencyModel(ModelGeneric):
    _source: str = None
    _provides: list = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._source = data.get("source")
        self._provides = ["*"]

    def add_subselection(self, sub_selection: dict):
        self._provides = sub_selection.get("provided_dependencies")

    def flatten(self) -> dict:
        return {
            "type": "dependency",
            "source": self._source,
            "provides": [p.flatten() for p in self._provides if type(p) != str]
        }


class BasicString(ModelGeneric):
    _value: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._value = data.get("value")

    def flatten(self):
        return self._value


def load_model(global_id):
    pass
