from client.client_api import Model
from tests.integration_tests.test_base import TestBase, run_multiple_times


class TestConversations(TestBase):

    @run_multiple_times
    def test_conversation_with_secret_code(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=False, use_reflections=False
        )
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

    @run_multiple_times
    def test_suggestions(self):
        model = self.create_test_model(
            single_message_mode=False,
            use_tools=False,
            use_reflections=False,
        )
        self.add_system_message(model)

        response, suggestions = model.generate_response_with_suggestions(
            "Hi, how are you?"
        )
        self.assert_response_is_about(
            response,
            "The response contains a greeting or status update",
        )

        self.assertTrue(
            suggestions,
            msg="The suggestions are empty",
        )

        self.assert_response_is_about(
            suggestions[0],
            "The text contains a topic that is a fitting as a follow up on a greeting",
        )

    @run_multiple_times
    def test_knowledge_retrieval(self):
        model = self.create_test_model(
            single_message_mode=False,
            use_tools=False,
            use_reflections=False,
            use_knowledge=True,
        )
        self.add_system_message(model)

        response = model.generate_response("What is the secret code?")
        self.assert_response_is_about(
            response,
            "The response contains the code 4512",
        )

    @run_multiple_times
    def test_secret_code_in_metadata(self):
        model = self.create_test_model(
            single_message_mode=False,
            use_tools=False,
            use_reflections=False,
            use_knowledge=False,
        )
        self.add_system_message(model)

        response = model.generate_response(
            "What is the secret code?",
            clipboard_content="My secret code is 4512",
        )

        self.assert_response_is_about(
            response,
            f"The response contains the code 4512",
        )
