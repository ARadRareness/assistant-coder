from client.client_api import Model
from tests.integration_tests.test_base import TestBase, run_multiple_times


class TestConversations(TestBase):

    @run_multiple_times
    def test_conversation_with_secret_code(self):
        model = Model(single_message_mode=False, use_tools=False, use_reflections=False)
        self.add_system_message(model)

        response = model.generate_response("Hi, how are you?")
        self.assert_response_is_about(
            response,
            "The response contains a greeting or status update",
        )

        response = model.generate_response(
            "My secret code is 4512, please remember it for me."
        )
        self.assert_response_is_about(
            response,
            "The response acknowledges the secret code",
        )

        response = model.generate_response("Write me a short poem.")
        self.assert_response_is_about(
            response,
            "The response contains a poem",
        )

        response = model.generate_response("What is my secret code?")
        self.assert_response_is_about(
            response,
            "The response contains the secret code 4512",
        )
