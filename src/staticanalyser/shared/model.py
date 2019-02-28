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

    def __init__(self, name: str, body: bytes):
        self._hash = md5(body).hexdigest()
        self._name = name

    def get_global_identifier(self):
        return self._global_identifier

    def get_hash(self):
        return self._hash


class ClassModel(NamedModelGeneric):
    _subclasses: list = None
    _body: str = None

    def __init__(self, name: str, body: list, subclasses: list = []):
        super(ClassModel, self).__init__(name, "banana".encode("utf-8"))
        self._subclasses = subclasses

    def flatten(self) -> dict:
        return {
            "model_type": "class",
            "name": self._name,
            "hash": self._hash,
            "subclasses": self._subclasses,
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

    def __init__(self, name: str, parameters: list, body: list):
        super(FunctionModel, self).__init__(name, "".join(body).encode("utf-8"))
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


class ParameterModel(ModelGeneric):
    _name: str = None
    _type: str = None  # TODO change this to a reference, maybe try to infer from body too
    _default: str = None

    def __init__(self, name: str, type: str = None, default: str = None):
        self._name = name
        self._type = type
        self._default = default

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
