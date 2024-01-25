import os
import tempfile
import unittest

from client.client_api import Model


def add_system_message(model: Model):
    model_info = model.get_model_info()
    model_path = model_info["path"]
    print(model_path)

    prompt = f"You are AC, the helpful AI coding assistant. You are currently running through the following model: {model_path}."
    model.add_system_message(prompt)
    print(prompt)


class TestTools(unittest.TestCase):
    def assert_response_is_about(self, response, criteria):
        fact_checker = Model(True)
        fact_checker.add_system_message(
            "You are a response checker, answer with YES if the response fulfills the criteria or NO if it does not. Only answer with YES or NO."
        )

        fact_response = fact_checker.generate_response(
            f"Response to evaluate: {response}\nBased on the following criteria: {criteria}.\nAnswer with YES if the criteria is fulfilled, otherwise answer with NO."
        )

        self.assertTrue(
            fact_response.lower().strip().startswith("yes"),
            msg=f'The response "{response}" did not fulfill criteria "{criteria}". AI motivation: "{fact_response}"',
        )

    def test_tool_nothing(self):
        model = Model(False)
        add_system_message(model)

        response = model.generate_response("Hi, how are you?")

        print(response)

        self.assert_response_is_about(
            response,
            "The response contains a greeting or status update",
        )

    def create_file(self, fname, temp_dir, content):
        temp_file_path = os.path.join(temp_dir, fname)

        with open(temp_file_path, "w", encoding="utf8") as fp:
            fp.write(content)

        return temp_file_path

    def test_tool_read_file(self):
        model = Model(single_message_mode=False, use_tools=True, use_reflections=False)
        add_system_message(model)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file_path = self.create_file(
                "temp_file.txt", temp_dir, "The secret code is 4512."
            )

            response = model.generate_response(
                "Read the file, what is the secret code?",
                selected_files=[temp_file_path],
            )

            print(response)
            self.assert_response_is_about(
                response, "The response contains the secret code which is 4512"
            )

    def test_tool_read_file_select_one(self):
        model = Model(single_message_mode=False, use_tools=True, use_reflections=False)
        add_system_message(model)

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

            print(response)
            self.assert_response_is_about(
                response, "The response contains the secret code which is 4512"
            )

    def test_tool_read_file_summarization(self):
        model = Model(single_message_mode=False, use_tools=True, use_reflections=False)
        add_system_message(model)

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

            print(response)
            self.assert_response_is_about(
                response,
                "The response is a summary containing information about Turing's father and mother",
            )


if __name__ == "__main__":
    unittest.main()
