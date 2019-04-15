from typing import Dict, Union, Tuple
from os import path
from staticanalyser.shared.model import *


class Navigator:
    _loaded_models: Dict[str, Union[Dict[str, Union[
        DependencyModel,
        FunctionModel,
        ClassModel
    ]], str]] = None

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

    def _search_model_for_gid(self, global_id: str, target: Union[dict, list]) -> Tuple[bool, object]:
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

    def lookup_entity(self, global_id: str, failout: bool = False) -> object:
        entity_loaded = self.entity_model_is_loaded(global_id)
        if entity_loaded[0]:
            return self._search_model_for_gid(global_id, self._loaded_models[entity_loaded[1]])
        if not failout:
            self.load_entity(global_id)
            return self.lookup_entity(global_id, True)
        else:
            return None

    def load_entity(self, global_id: str):
        if global_id.split(".")[0] == "builtin":
            return
        model_file = ModelOperations.get_model_file(global_id)
        with open(model_file, "r") as fp:
            model_data:dict = json.load(fp)
        model: dict = {"classes": [], "functions": [], "dependencies": []}
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

    def __str__(self):
        return str(self._loaded_models)


def navigate(global_id):
    n = Navigator()
    n.load_entity(global_id)
    print(n.lookup_entity("python3.staticanalysertest.translator.sample.my_decorator.inner"))
