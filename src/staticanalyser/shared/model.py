# The shared objects that are used by the translator and navigator entities
import copy
from enum import Enum
import json
from hashlib import md5
from staticanalyser.shared.platform_constants import SCHEMA_LOCATION
import logging

with open(SCHEMA_LOCATION, "r") as s:
    SCHEMA: dict = json.load(s)


class ModelOperations(object):
    @staticmethod
    def prune_body(body: list, body_entities: list) -> list:
        res: list = copy.copy(body)
        try:
            for entity in body_entities:
                for index, line in enumerate(res):
                    if type(line) is StatementModel and entity.get_as_strings()[0] == line.get_rhs():
                        for i in range(len(entity.get_as_strings()) - 1):
                            res.pop(index + 1)
                        res[index] = entity
            return res
        except NotImplementedError:
            return body


class ModelGeneric(object):
    def flatten(self) -> dict:
        raise NotImplementedError()

    def __str__(self):
        return str(self.flatten())

    def __repr__(self):
        return self.__str__()

    def add_subselection(self, sub_selection: dict):
        pass


class ReferenceModel(ModelGeneric):
    _ref: str = None
    _target: str = None
    _parameters: list = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._ref = data.get("call")
        self._target = data.get("target") or ""
        self._parameters = data.get("parameters") or ""

    def lookup(self) -> bool:
        pass

    def flatten(self) -> dict:
        parms = self._parameters
        if not type(parms) == str:
            parms = [p.flatten() for p in parms]
        return {
            "model_type": "reference",
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
        if sub_selection.get("parameter"):
            self._parameters = sub_selection.get("parameter")


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
    _global_identifier: ReferenceModel = None
    _prefix: str = None
    _name: str = None
    _hash: str = None
    _lang: str = None
    _body: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._name = data.get("name")
        self._prefix = prefix
        self._global_identifier = "{}.{}".format(prefix, self._name)
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

    def set_functions(self, new_functions: list) -> None:
        self._functions = new_functions

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

    def __init__(self, language: str, prefix: str, data: dict):
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
            "model_type": "statement",
            "lhs": self._lhs,
            "rhs": rhs
        }


class ForLoopModel(ControlFlowGeneric):
    _loop: str = None
    _body: str = None
    _body_parsed: list = None
    _control_flow: dict = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._loop = data.get("loop")
        self._body = data.get("body")
        self._control_flow = {}

    def flatten(self) -> dict:
        self._control_flow = self.flatten_dict("for", "while", "if")
        return {
            "model_type": "for_loop",
            "loop": self._loop,
            "body": self._body,
            "body_parsed": [s.flatten() for s in self._body_parsed],
            "control_flow": self._control_flow
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


class WhileLoop(ControlFlowGeneric):
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
            "model_type": "while_loop",
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

    def get_as_strings(self) -> list:
        res: list = [self._loop]
        res += [l.strip() for l in self._body.split("\n")]
        return res

    def get_as_statements(self) -> list:
        return self._body_parsed


class ConditionModel(ControlFlowGeneric):
    _condition: OperatorModel = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._condition = data.get("condition")
        self._control_flow = {
            "true": data.get("true_block") or "",
            "false": data.get("false_block") or ""
        }

    def flatten(self) -> dict:
        # self._control_flow = self.flatten_dict("true", "false")
        return {
            "model_type": "condition",
            "condition": self._condition,
            "blocks": self._control_flow
        }

    def get_as_strings(self) -> list:
        res: list = ["if {}:".format(self._condition)]  # .get_string()
        res += [l.strip() for l in self._control_flow["true"].split("\n")]
        if self._control_flow["false"] is not "":
            res.append("else:")
            res += [l.strip() for l in self._control_flow["false"].split("\n")]
        return res

    def get_as_statements(self) -> list:
        res: list = self._control_flow["true"]
        res += self._control_flow.get("false") or []
        return res


class FunctionModel(NamedModelGeneric, ControlFlowGeneric):
    _parameters: list = None
    _statements: list = None
    _control_flow: dict = None
    _declaration: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        super(FunctionModel, self).__init__(language, prefix, data)
        self._parameters = data.get("parameters")
        self._control_flow = {}
        self._declaration = data.get("declaration")

    def add_subselection(self, sub_selection: dict):
        self._parameters = sub_selection.get("parameter") or []
        self._statements = ModelOperations.prune_body(
            sub_selection.get("statement") or [],
            [
                *(sub_selection.get("for_loop") or []),
                *(sub_selection.get("while") or []),
                *(sub_selection.get("if") or []),
                *(sub_selection.get("function") or [])
            ]
        )

    def get_as_statements(self) -> list:
        return self._statements

    def flatten(self):
        self._control_flow = self.flatten_dict("while", "if")
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

    def get_as_strings(self) -> list:
        res: list = [self._declaration]
        res += [l.strip() for l in self._body.split('\n')]
        return res


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
            "model_type": "variable",
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

    def get_provided_imports(self):
        return self._provides


class BasicString(ModelGeneric):
    _value: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        self._value = data.get("value")

    def flatten(self):
        return self._value


def load_model(global_id):
    pass
