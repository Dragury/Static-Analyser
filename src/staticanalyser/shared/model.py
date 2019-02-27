# The shared objects that are used by the translator and navigator entities
from enum import Enum
import json


class ReferenceModel(str):
    def lookup(self) -> bool:
        pass


class ModelGeneric(object):
    _global_identifier: ReferenceModel = None
    _name: str = None

    def get_global_identifier(self):
        return self._global_identifier


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
    def __init__(self, name: str, parameters: list, body: list):
        self._name = name

    def __str__(self):
        return json.dumps(
            {
                "name":self._name,
                "global_id": self.get_global_identifier(),
                "parameters": None,
                "body": None
            }
        )


def load_model(global_id):
    pass
