from unittest import TestCase
from os import path
from staticanalyser.translator.translate import translate

SAMPLE_FILE_LOCATION = path.join(path.dirname(__file__), "sample.py")


class TestTranslator(TestCase):
    def test_translate_without_exceptions(self):
        with open(SAMPLE_FILE_LOCATION, "r") as sample:
            translate([sample])
