import os
import tempfile
import unittest

from tests.integration_tests.test_base import (
    TestBase,
    run_multiple_times,
)


class TestTools(TestBase):

    def create_file(self, fname: str, temp_dir: str, content: str):
        temp_file_path = os.path.join(temp_dir, fname)

        with open(temp_file_path, "w", encoding="utf8") as fp:
            fp.write(content)

        return temp_file_path

    @run_multiple_times
    def test_tool_get_date_and_time(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        response = model.generate_response("What is the current time and date?")

        self.assert_response_is_about(
            response,
            "The response contains a time and a date",
        )

    @run_multiple_times
    def test_tool_nothing(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        response = model.generate_response("Hi, how are you?")

        self.assert_response_is_about(
            response,
            "The response contains a greeting or status update",
        )

    @run_multiple_times
    def test_tool_read_file(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = self.create_file(
                "temp_file.txt", temp_dir, "The secret code is 4512."
            )

            response = model.generate_response(
                "Read the file, what is the secret code?",
                selected_files=[temp_file_path],
            )

            self.assert_response_is_about(
                response, "The response contains the secret code which is 4512"
            )

            self.assert_response_is_not_about(
                response, "The response contains the secret code which is 5713."
            )

    @run_multiple_times
    def test_tool_read_file_select_one(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        with tempfile.TemporaryDirectory() as temp_dir:
            secret_code_path = self.create_file(
                "secrets_file.txt", temp_dir, "The secret code is 4512."
            )

            recipes_path = self.create_file(
                "recipes_file.txt",
                temp_dir,
                "Follow these instructions to make a great strawberry cake...",
            )

            response = model.generate_response(
                "Read the file, what is the secret code?",
                selected_files=[secret_code_path, recipes_path],
            )

            self.assert_response_is_about(
                response, "The response contains the secret code which is 4512"
            )

            response = model.generate_response(
                "Read the file, what is the secret code?",
                selected_files=[recipes_path, secret_code_path],
            )

            self.assert_response_is_about(
                response, "The response contains the secret code which is 4512"
            )

    @run_multiple_times
    def test_tool_read_file_summarization(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = self.create_file(
                "temp_file.txt",
                temp_dir,
                """Turing was born in Maida Vale, London, while his father, Julius Mathison Turing was on
                         leave from his position with the Indian Civil Service (ICS) of the British Raj government at
                         Chatrapur, then in the Madras Presidency and presently in Odisha state, in India.[16][17]
                         Turing's father was the son of a clergyman, the Rev. John Robert Turing, from a Scottish
                         family of merchants that had been based in the Netherlands and included a baronet.
                         Turing's mother, Julius's wife, was Ethel Sara Turing (née Stoney), daughter of
                         Edward Waller Stoney, chief engineer of the Madras Railways.""",
            )

            response = model.generate_response(
                "Can you read and summarize this file for me?",
                selected_files=[temp_file_path],
            )

            self.assert_response_is_about(
                response,
                "The response is a summary containing information about Turing's father and mother",
            )

    @run_multiple_times(1)
    def test_tool_browse_internet(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        response = model.generate_response(
            "Can you return the current week by going to https://www.epochconverter.com/weeknumbers for me?"
        )

        self.assert_response_is_about(
            response,
            "The response contains a week number",
        )

    @run_multiple_times(1)
    def test_tool_search_the_web(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        response = model.generate_response("Who wrote the book Murtagh?")

        self.assert_response_is_about(
            response,
            "The response mentions Christopher Paolini",
        )

    @run_multiple_times
    def test_tool_code_interpreter(self):
        model = self.create_test_model(
            single_message_mode=False,
            use_tools=True,
            use_reflections=False,
            ask_permission_to_run_tools=True,
        )
        self.add_system_message(model)

        response = model.generate_response(
            "Run this code for me: print('Hello World!')"
        )

        self.assert_response_is_about(response, "The response contains 'Hello World!'")

    @run_multiple_times
    def test_list_available_tools(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        response = model.generate_response("What tools are available?")

        self.assert_response_is_about(
            response,
            "The response contains a list of available tools",
        )

    @run_multiple_times
    def test_tools_can_reference_previous_messages(self):
        model = self.create_test_model(
            single_message_mode=False, use_tools=True, use_reflections=False
        )
        self.add_system_message(model)

        response = model.generate_response("Memorize that X=50.")

        response = model.generate_response(
            "Use code interpreter to find out what the X'th prime number is."
        )
        self.assert_response_is_about(
            response,
            "The response contains the 50th prime number, which is 229",
        )


if __name__ == "__main__":
    unittest.main()
