# The shared objects that are used by the translator and navigator entities
from enum import Enum
import json
from hashlib import md5


class ReferenceModel(str):
    def lookup(self) -> bool:
        pass


class ModelGeneric(object):
    _global_identifier: ReferenceModel = None
    _name: str = None
    _hash: str = None

    def __init__(self, body: bytes):
        self._hash = md5(body).hexdigest()

    def get_global_identifier(self):
        return self._global_identifier

    def get_hash(self):
        return self._hash


class ClassModel(ModelGeneric):
    pass


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


class FunctionModel(ModelGeneric):
    _parameters: list = None
    _body: list = None

    def __init__(self, name: str, parameters: list, body: list):
        super(FunctionModel, self).__init__("".join(body).encode("utf-8"))
        self._name = name
        self._paramaters = parameters
        self._body = body

    def __str__(self):
        return json.dumps(
            {
                "name":self._name,
                "global_id": self.get_global_identifier(),
                "hash": self._hash,
                "parameters": self._parameters,
                "body": self._body
            }
        )


def load_model(global_id):
    pass
