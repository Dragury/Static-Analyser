from staticanalyser.shared.model import *
import staticanalyser.shared.config as config
from argparse import Namespace
from os import path, getcwd
from _io import TextIOWrapper
import re


def lookup_parser(extension: str) -> str:
    pass


def translate(translate_args: Namespace) -> int:
    # TODO lookup filetypes
    filetype_parser_map: dict = {}
    entity: TextIOWrapper
    for entity in translate_args.input_files:
        extension: str = re.split('\.', entity.name)

        print(path.abspath(entity.name))

    # TODO check current model
    return 0
