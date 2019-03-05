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


class NamedModelGeneric(ModelGeneric):
    _global_identifier: ReferenceModel = None
    _name: str = None
    _hash: str = None
    _lang: str = None

    def __init__(self, language: str, name: str, body: bytes):
        self._hash = md5(body).hexdigest()
        self._global_identifier = name
        self._name = name.split(".")[-1:][0]
        self._lang = language

    def get_global_identifier(self):
        return self._global_identifier

    def get_hash(self):
        return self._hash


class ClassModel(NamedModelGeneric):
    _subclasses: list = None
    _body: str = None
    _attributes: list = None
    _functions: list = None

    def __init__(self, language: str, name: str, body: list, subselections: dict = None):
        if subselections is None:
            subselections = {}
        super(ClassModel, self).__init__(language, name, "banana".encode("utf-8"))
        self._subclasses = subselections.get("{}.class".format(self._lang))
        self._attributes = subselections.get("{}.attribute".format(self._lang))
        self._functions = subselections.get("{}.function".format(self._lang))

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


class StatementModel(object):
    _lhs: ReferenceModel = None


class ConditionModel(object):
    _condition: StatementModel = None
    _true_block: list = None
    _false_block: list = None


class FunctionModel(NamedModelGeneric):
    _parameters: list = None
    _body: list = None

    def __init__(self, language: str, name: str, parameters: list, body: list):
        super(FunctionModel, self).__init__(language, name, "".join(body).encode("utf-8"))
        self._parameters = parameters
        self._body = body

    def flatten(self):
        return {
            "model_type": "function",
            "name": self._name,
            "global_id": self.get_global_identifier(),
            "hash": self._hash,
            "parameters": [p.flatten() for p in self._parameters],
            "body": self._body
        }


class VariableModel(ModelGeneric):
    _lang: str = None
    _name: str = None
    _type: str = None  # TODO change this to a reference, maybe try to infer from body too
    _default: str = None

    def __init__(self, language: str, name: str, type: str = None, default: str = None):
        self._name = name.split(".")[-1:][0]
        self._type = type
        self._default = default
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
