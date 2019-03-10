#!/usr/bin/env python3
import click
from staticanalyser.translator.translate import translate
import sys


# The 'main' method for the static analyser, runs with a gui or cli
@click.group()
def cli():
    pass


@cli.command("translate")
@click.argument("file", nargs=-1, type=click.Path(exists=True))
@click.option("-j", "--jobs", default=4)
def translate_cmd(file: list, jobs: int):
    options: dict = {
        "jobs": jobs
    }
    translate(file, options)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("GUI MODE!!!")  # GUI MODE
    else:
        cli()
        print("YAY!")
    sys.exit(0)
