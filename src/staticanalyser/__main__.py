#!/usr/bin/env python3
from arghandler import *
import argparse
from staticanalyser.translator.translate import translate
import sys


# The 'main' method for the static analyser, runs with a gui or cli
@subcmd('translate')
def translate_cmd(parser: ArgumentHandler, context, args):
    # parser.add_argument('-d', '--working-dir', help="The working directory to run in", required=False)
    # parser.add_argument('-l', '--language', help="The programming language to translate from", required=False)
    parser.add_argument("input_files", type=argparse.FileType('r'), nargs='+')
    # parser.add_argument("input_files", nargs='+')
    args = parser.parse_args(args)
    translate(args.input_files)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("GUI MODE!!!")  # GUI MODE
    else:
        top_level_command_handler = ArgumentHandler(use_subcommand_help=True)
        top_level_command_handler.run()

    sys.exit(0)
