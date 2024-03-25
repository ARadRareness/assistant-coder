import datetime
from typing import Any, Callable
import unittest

from client.client_api import Model
from language_models.model_message import MessageMetadata

TEST_RUN_COUNT = 1


def run_multiple_times(count: Any = None) -> Callable[[Any], Any]:
    if callable(count):  # Check if count is a function
        return run_multiple_times()(count)

    def decorator(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
        def wrapper(*args: Any, **kwargs: Any) -> None:
            repetitions = count if count is not None else TEST_RUN_COUNT
            if callable(repetitions):
                repetitions = TEST_RUN_COUNT
            for _ in range(repetitions):
                func(*args, **kwargs)

        return wrapper

    return decorator


class TestBase(unittest.TestCase):
    def base_assert_response(self, response: str, criteria: str, expected: bool):
        fact_checker = Model(single_message_mode=True)
        fact_checker.add_system_message(
            "You are a response checker, answer with YES if the response fulfills the criteria or NO if it does not. Only answer with YES or NO."
        )

        fact_response = fact_checker.generate_response(
            f"Response to evaluate: {response}\nBased on the following criteria: {criteria}.\nAnswer with YES if the criteria is fulfilled, otherwise answer with NO."
        )

        self.assertTrue(
            fact_response, msg="The fact checker did not return a response."
        )

        if expected:
            self.assertTrue(
                fact_response.lower().strip().startswith("yes"),
                msg=f'The response "{response}" did not fulfill criteria "{criteria}". AI motivation: "{fact_response}"',
            )
        else:
            self.assertTrue(
                fact_response.lower().strip().startswith("no"),
                msg=f'The response "{response}" did not fulfill criteria "{criteria}". AI motivation: "{fact_response}"',
            )

    def assert_response_is_about(self, response: str, criteria: str):
        self.base_assert_response(response, criteria, True)

    def assert_response_is_not_about(self, response: str, criteria: str):
        self.base_assert_response(response, criteria, False)

    def add_system_message(self, model: Model):
        model_info = model.get_model_info()
        model_path = model_info["path"]

        prompt = f"You are AC, the helpful AI coding assistant. You are currently running through the following model: {model_path}."
        model.add_system_message(prompt)

    def generate_metadata(
        self, ask_permission_to_run_tools: bool = False
    ) -> MessageMetadata:
        return MessageMetadata(
            datetime.datetime.now(), [], ask_permission_to_run_tools, ""
        )
