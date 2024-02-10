import unittest

from client.client_api import Model

TEST_RUN_COUNT = 3


def run_multiple_times(count=None):
    if callable(count):  # Check if count is a function
        return run_multiple_times()(count)

    def decorator(func):
        def wrapper(*args, **kwargs):
            repetitions = count if count is not None else 3
            for _ in range(repetitions):
                func(*args, **kwargs)

        return wrapper

    return decorator


class TestBase(unittest.TestCase):
    def base_assert_response(self, response, criteria, expected):
        fact_checker = Model(single_message_mode=True)
        fact_checker.add_system_message(
            "You are a response checker, answer with YES if the response fulfills the criteria or NO if it does not. Only answer with YES or NO."
        )

        fact_response = fact_checker.generate_response(
            f"Response to evaluate: {response}\nBased on the following criteria: {criteria}.\nAnswer with YES if the criteria is fulfilled, otherwise answer with NO."
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

    def assert_response_is_about(self, response, criteria):
        self.base_assert_response(response, criteria, True)

    def assert_response_is_not_about(self, response, criteria):
        self.base_assert_response(response, criteria, False)

    def add_system_message(self, model: Model):
        model_info = model.get_model_info()
        model_path = model_info["path"]

        prompt = f"You are AC, the helpful AI coding assistant. You are currently running through the following model: {model_path}."
        model.add_system_message(prompt)
