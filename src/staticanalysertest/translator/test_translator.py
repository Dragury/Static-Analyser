from unittest import TestCase
from os import path
from staticanalyser.translator.translate import translate

SAMPLE_FILE_LOCATION = path.join(path.dirname(__file__), "sample.py")


class TestTranslator(TestCase):
    def test_translate_without_exceptions(self):
        translate([SAMPLE_FILE_LOCATION])
