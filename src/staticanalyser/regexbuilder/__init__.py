import re


class FormatString(object):
    _dependencies: list = None
    _string: str = None
    _name: str = None

    def __init__(self, name: str, string: str, dependencies=None):
        if dependencies is None:
            dependencies = []
        self._dependencies = dependencies
        self._name = name
        self._string = string

    def __str__(self):
        return self._string

    def __repr__(self):
        return self.__str__()

    def get_dependencies(self):
        return self._dependencies


class RegexBuilder(object):
    _registered_snippets: dict = None
    _registered_format_strings: dict = None

    def __init__(self):
        self._registered_snippets = {}
        self._registered_format_strings = {}

    def register_snippet(self, name: str, snippet: str):
        self._register(self._registered_snippets, name, snippet, [self._registered_format_strings])

    def register_format_string(self, name: str, format_string: str, dependencies=None):
        self._register(
            self._registered_format_strings,
            name,
            FormatString(name, format_string, dependencies),
            [self._registered_snippets]
        )

    @staticmethod
    def _register(dest: dict, name: str, value: object, namespace_dicts: list = None):
        if namespace_dicts is None:
            namespace_dicts = []
        for d in [*namespace_dicts, dest]:
            if name in d.keys():
                raise KeyError()
        dest[name] = value

    def _check_snippet(self, name: str, alternative_dicts: list = None) -> bool:
        all_keys: list = []
        if alternative_dicts is None:
            alternative_dicts = []
        for d in [*alternative_dicts, self._registered_snippets]:
            all_keys = [*all_keys, *d.keys()]
        if name not in all_keys:
            return False
        return True

    def build(self, format_string: str) -> str:
        if self._check_snippet(format_string):
            return self._registered_snippets.get(format_string)
        if format_string not in self._registered_format_strings.keys():
            raise KeyError()
        selected_string: FormatString = self._registered_format_strings.get(format_string)

        res: str = str(selected_string)
        local_namespace: dict = {}

        for dep in selected_string.get_dependencies():
            local_namespace[dep] = self.build(dep)

        found_patterns = re.findall("{{\s*([a-zA-Z_][-a-zA-Z0-9_]+)\s*}}", str(selected_string))
        for s in found_patterns:
            if not self._check_snippet(s, [local_namespace]):
                pass
            else:
                repl: str = None
                if s in local_namespace.keys():
                    repl = local_namespace[s]
                else:
                    repl = self._registered_snippets.get(s)
                res = re.sub(
                    "{{" + s + "}}",
                    repl.replace("\\", "\\\\"),
                    res
                )
        return res
