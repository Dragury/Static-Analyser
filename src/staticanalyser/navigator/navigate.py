from typing import Dict, Union, Tuple
from os import path
from staticanalyser.shared.model import *


class Navigator:
    _loaded_models: Dict[str, Dict[str, Union[
        List[DependencyModel],
        List[FunctionModel],
        List[ClassModel]
    ]]] = None

    def __init__(self):
        self._loaded_models = {}

    def entity_model_is_loaded(self, global_id: str) -> Tuple[bool, str]:
        gid_split: list = global_id.split(".")
        model_id = gid_split[0]
        for part in gid_split[1:]:
            model_id = "{}.{}".format(model_id, part)
            if model_id in self._loaded_models.keys():
                return True, model_id
        return False, ""

    def _search_model_for_gid(self, global_id: str, target: Union[dict, list]) -> (bool, NamedModelGeneric):
        if type(target) is list:
            for e in target:
                res = self._search_model_for_gid(global_id, e)
                if res[0]:
                    return res
        elif type(target) is dict:
            for k in target.keys():
                res = self._search_model_for_gid(global_id, target[k])
                if res[0]:
                    return res
        elif type(target) is str:
            return False, None
        else:
            if "_global_identifier" in target.__dict__.keys():
                if target.__dict__.get("_global_identifier") == global_id:
                    return True, target
            for k in target.__dict__.keys():
                res = self._search_model_for_gid(global_id, target.__dict__[k])
                if res[0]:
                    return res
        return False, None

    def find_references_to_global_id(self, global_id: str) -> List[FunctionModel]:
        entities: List[FunctionModel] = []
        for model in self._loaded_models.values():
            funcs: list = model.get("functions")
            for klazz in model.get("classes"):
                for func in klazz.__dict__.get("_functions"):
                    funcs.append(func)
            for func in funcs:
                for l in func.__dict__.get("_statements"):
                    if type(l) == FunctionModel:
                        funcs.append(l)
            funcs = list(set(funcs))
            for func in funcs:
                if global_id in self._find_all_references(func):
                    entities.append(func)
        return entities

    def lookup_entity(self, global_id: str, fail_out: bool = False) -> (bool, NamedModelGeneric):
        entity_loaded = self.entity_model_is_loaded(global_id)
        if entity_loaded[0]:
            return self._search_model_for_gid(global_id, self._loaded_models[entity_loaded[1]])
        if not fail_out:
            self.load_entity(global_id)
            return self.lookup_entity(global_id, True)
        else:
            return False, None

    def _find_all_references(self, model: Union[dict, list, NamedModelGeneric]) -> Union[
                                                                                        List[str],
                                                                                        List[NamedModelGeneric]
                                                                                    ]:
        ret: Union[List[str], List[NamedModelGeneric]] = []
        if type(model) is list:
            for e in model:
                res: List[str] = self._find_all_references(e)
                ret += res
        elif type(model) is dict:
            for k in model.keys():
                res = self._find_all_references(model[k])
                ret += res
        elif type(model) is str or model is None:
            return []
        else:
            if "_ref" in model.__dict__.keys():
                ret.append(model.__dict__.get("_ref"))
            for k in model.__dict__.keys():
                res = self._find_all_references(model.__dict__[k])
                ret += res
        return ret

    @staticmethod
    def find_assignments(target: FunctionModel, global_id: str) -> List[str]:
        ret: List[str] = []
        for statement in target.get_as_statements():
            ret += Navigator._find_assignments_in_control_flow(statement, global_id)
        return ret

    @staticmethod
    def _find_assignments_in_control_flow(target: ControlFlowGeneric, global_id: str) -> List[str]:
        ret: List[str] = []
        if issubclass(type(target), ControlFlowGeneric):
            for statement in target.get_as_statements():
                statement: ControlFlowGeneric
                ret += Navigator._find_assignments_in_control_flow(statement, global_id)
        elif type(target) == StatementModel:
            target: StatementModel
            if type(target._rhs) == ReferenceModel and target.get_rhs().__dict__.get("_ref") == global_id:
                ret.append(target.get_lhs())
        return ret

    def find_references_in_model(self, global_id: str):
        search_model = ModelOperations.get_base_global_id(global_id)
        return list(set(self._find_all_references(self._loaded_models[search_model])))

    def load_entity(self, global_id: str, load_dependencies: bool = False):
        if global_id.split(".")[0] == "builtin":
            return
        model: dict = {"classes": [], "functions": [], "dependencies": []}
        if ModelOperations.get_base_global_id(global_id) not in self._loaded_models.keys():
            model_file = ModelOperations.get_model_file(global_id)
            if model_file:
                with open(model_file, "r") as fp:
                    model_data: dict = json.load(fp)
                for klazz in model_data.get("classes"):
                    c = ModelOperations.load_model_from_dict(klazz)
                    model["classes"].append(c)
                for func in model_data.get("functions"):
                    f = ModelOperations.load_model_from_dict(func)
                    model["functions"].append(f)
                for dependency in model_data.get("dependencies"):
                    d = ModelOperations.load_model_from_dict(dependency)
                    model["dependencies"].append(d)
                self._loaded_models[ModelOperations.get_base_global_id(global_id)] = model
        if load_dependencies:
            dependencies: List[str] = self._find_all_references(model)
            for dependency in dependencies:
                self.load_entity(dependency, True)

    def find_usages(self, func: FunctionModel, var: str):
        pass

    def __str__(self):
        return str(self._loaded_models)


def navigate(global_id):
    n = Navigator()
    n.load_entity(global_id, load_dependencies=True)
    # print(n.lookup_entity(global_id))
    # print(n.find_references_in_model(global_id))
    res = n.find_references_to_global_id("builtin.print")
    print("references to builtin.print: {}".format(", ".join([func.get_global_identifier() for func in res])))
    res = n.find_references_to_global_id("loads")
    for func in res:
        func: FunctionModel
        vars = n.find_assignments(func, "loads")
        print("found assignments to these vars that match loads: {}".format(", ".join(vars)))
    print("references to json.loads: {}".format(", ".join([func.get_global_identifier() for func in res])))
