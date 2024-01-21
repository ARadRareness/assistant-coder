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
    def test_tool_nothing(self):
        model = Model(False)
        add_system_message(model)

        response = model.generate_response("Hi, how are you?")

        print(response)


if __name__ == "__main__":
    unittest.main()
