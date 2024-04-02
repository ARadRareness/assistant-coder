import unittest

from language_models.helpers.dangerous_code_detector import DangerousCodeDetector


class TestDangerousCodeDetector(unittest.TestCase):
    def test_safe_code(self):
        dangerous_code_detector = DangerousCodeDetector()
        self.assertFalse(
            dangerous_code_detector.detect_potentially_dangerous_code(
                "print('hello world')"
            )
        )

    def test_potentially_unsafe_code_method(self):
        dangerous_code_detector = DangerousCodeDetector()
        self.assertTrue(
            dangerous_code_detector.detect_potentially_dangerous_code(
                "print('hello world')\na=__import__# Do stuff\nprint(a)"
            )
        )

    def test_approved_import(self):
        dangerous_code_detector = DangerousCodeDetector()
        self.assertFalse(
            dangerous_code_detector.detect_potentially_dangerous_code(
                """import typing
                print("Hi!")
                """
            )
        )

    def test_unapproved_import(self):
        dangerous_code_detector = DangerousCodeDetector()
        self.assertTrue(
            dangerous_code_detector.detect_potentially_dangerous_code(
                """import os
                os.system("echo 'hello world'")
                """
            )
        )

    def test_approved_from_import(self):
        dangerous_code_detector = DangerousCodeDetector()
        self.assertFalse(
            dangerous_code_detector.detect_potentially_dangerous_code(
                """from typing import List, Tuple
                print("Hello, world!")
                """
            )
        )

    def test_unapproved_from_import(self):
        dangerous_code_detector = DangerousCodeDetector()
        self.assertTrue(
            dangerous_code_detector.detect_potentially_dangerous_code(
                """from os import system
                system("echo 'hello world'")
                """
            )
        )
