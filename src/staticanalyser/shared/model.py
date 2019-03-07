# The shared objects that are used by the translator and navigator entities
from enum import Enum
import json
from hashlib import md5


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


class NamedModelGeneric(ModelGeneric):
    _global_identifier: ReferenceModel = None
    _name: str = None
    _hash: str = None
    _lang: str = None
    _body: str = None

    def __init__(self, language:str, prefix: str, data: dict):
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
        self._subclasses = sub_selection.get("class". format(self._lang))
        self._attributes = sub_selection.get("attribute". format(self._lang))
        self._functions = sub_selection.get("function". format(self._lang))

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


class OperatorModel(object):
    _lhs: object = None
    _rhs: object = None
    _type: OperatorType = None


class StatementModel(ModelGeneric):
    _lhs: ReferenceModel = None
    def __init__(self, language: str, prefix: str, data: dict):
        self._lhs = data.get("statement")

    def flatten(self) -> dict:
        return self._lhs


class ConditionModel(object):
    _condition: StatementModel = None
    _true_block: list = None
    _false_block: list = None


class FunctionModel(NamedModelGeneric):
    _parameters: list = None
    _statements: list = None

    def __init__(self, language: str, prefix: str, data: dict):
        super(FunctionModel, self).__init__(language, prefix, data)
        self._parameters = data.get("parameters")

    def add_subselection(self, sub_selection: dict):
        if sub_selection.get("parameter") is not None:
            self._parameters = sub_selection.get("parameter")
        self._statements = sub_selection.get("statement")
        if sub_selection.get("statement") is None:
            self._statements = []
        else:
            self._statements = sub_selection.get("statement")

    def flatten(self):
        return {
            "model_type": "function",
            "name": self._name,
            "global_id": self.get_global_identifier(),
            "hash": self._hash,
            "parameters": [p.flatten() for p in self._parameters],
            "body": self._body,
            "body_parsed": [s.flatten() for s in self._statements]
        }


class VariableModel(ModelGeneric):
    _lang: str = None
    _name: str = None
    _type: str = None
    _default: str = None

    def __init__(self, language: str, prefix: str, data: dict):
        if data.get("initial_value") is not None:
            self._default = data.get("initial_value")
        else:
            self._default = data.get("default_value")
        self._name = data.get("name")
        self._type = data.get("type")
        self._lang = language

    def is_empty(self):
        return self._name == "" and self._type == "" and self._default == ""

    def flatten(self):
        return {
            "name": self._name,
            "type": self._type,
            "default_value": self._default
        }


def load_model(global_id):
    pass
