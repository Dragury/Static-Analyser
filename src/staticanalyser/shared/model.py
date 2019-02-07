# The shared objects that are used by the translator and navigator entities


class ModelGeneric(object):
    _global_identifier: str = None

    def get_global_identifier(self):
        return self._global_identifier


class ClassModel(ModelGeneric):
    pass


class StatementModel(object):
    pass


class FunctionModel(ModelGeneric):
    pass
