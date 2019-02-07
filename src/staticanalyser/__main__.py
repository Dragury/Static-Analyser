#!/usr/bin/env python3
import arghandler
import sys

# The 'main' method for the static analyser, runs with a gui or cli

if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("GUI MODE!!!") # GUI MODE
    else:
        # ap = argparse.ArgumentParser()
        # subparsers = ap.add_subparsers()
        #
        # config_parser = subparsers.add_parser("config")
        # config_parser.add_argument("field")
        #
        # translate_parser = subparsers.add_parser("translate")
        # translate_parser.add_argument("input_file")
        # translate_parser.add_argument("working_dir")
        #
        # args = ap.parse_args()
        pass

    sys.exit(0)
