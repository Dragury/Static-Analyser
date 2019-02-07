#!/usr/bin/env python3
from arghandler import *
from staticanalyser.translator.translate import translate
import sys


# The 'main' method for the static analyser, runs with a gui or cli
@subcmd('translate')
def translate_cmd(parser: ArgumentHandler, context, args):
    parser.add_argument("input_files")
    args = parser.parse_args(args)
    translate(args)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("GUI MODE!!!")  # GUI MODE
    else:
        top_level_command_handler = ArgumentHandler(use_subcommand_help=True)
        top_level_command_handler.run()

    sys.exit(0)
