from typing import List, Tuple
import logging
import staticanalyser.shared.config as config


from staticanalyser.navigator.navigate import navigate


def _prune_tree(global_id: str, tree: List[Tuple]):
    for branch in tree[::-1]:
        if branch[0] == global_id:
            tree.remove(branch)
        else:
            _prune_tree(global_id, branch[1])


def _gid_appears_in_tree(global_id: str, tree: List[Tuple]):
    for branch in tree:
        if branch[0] == global_id or _gid_appears_in_tree(global_id, branch[1]):
            return True
    return False


def _strip_safe_branches(sink_functions: list, tree: List[Tuple]):
    for branch in tree[::-1]:
        sink_function_found = False
        for sink_function in sink_functions:
            if _gid_appears_in_tree(sink_function, branch[1]) or branch[0] == sink_function:
                sink_function_found = True
        if not sink_function_found:
            logging.debug("No sink functions found in {}".format(branch))
            tree.remove(branch)
        else:
            logging.debug("sink function found! narrowing search to {}".format(branch[1]))
            _strip_safe_branches(sink_functions, branch[1])


def hunt(recursion_depth: int, sink_functions: list, dangers: list, clean_funcs: list,
         file_list: list, language: str = ""):
    if language != "":
        if config.get_sink_funcs_for_lang(language):
            sink_functions += config.get_sink_funcs_for_lang(language)
        if config.get_danger_funcs_for_lang(language):
            dangers += config.get_danger_funcs_for_lang(language)
    findings = []
    for danger in dangers:
        res = navigate(danger, recursion_depth, file_list)
        for func in clean_funcs:
            _prune_tree(func, res)
        _strip_safe_branches(sink_functions, res)
        findings.append((danger, res))
    return findings
