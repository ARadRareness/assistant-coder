import unittest
from datasets import load_dataset  # type: ignore
import os.path
from client.client_api import Model
from language_models.helpers.dangerous_code_detector import DangerousCodeDetector  # type: ignore

from language_models.tools.code_interpreter_tool import CodeInterpreterTool
from typing import Dict


class TestCoding(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code_interpreter_tool: CodeInterpreterTool = CodeInterpreterTool()

        cls.dataset = load_dataset("openai_humaneval")

        cls.code_interpreter_tool = CodeInterpreterTool()
        cls.dangerous_code_detector = DangerousCodeDetector()

    def _parse_code(self, message: str):
        return self.code_interpreter_tool.parse_code(message)

    def _generate_code(self, prompt: str, entrypoint: str):
        system_prompt = "You are an expert at solving problems using python. Fill in the code for the function specified by the entrypoint."
        user_prompt = f"Fill in the code for the function {entrypoint} such that it fulfills the task.\n<CODE>{prompt}</CODE>\nLet's think through the problem step by step before generating the final code!"

        model = Model(single_message_mode=False, use_tools=False, use_reflections=False)

        model.add_system_message(system_prompt)

        response = model.generate_response(user_prompt, max_tokens=10000)

        return response, model

    def _detect_dangerous_code(self, prompt: str, code: str, test: str):
        if self.dangerous_code_detector.detect_potentially_dangerous_code(prompt):
            print("PROMPT:\n", prompt)
            raise ValueError("Dangerous prompt code detected")

        elif self.dangerous_code_detector.detect_potentially_dangerous_code(code):
            print("CODE:\n", code)
            raise ValueError("Dangerous generated code detected")

        elif self.dangerous_code_detector.detect_potentially_dangerous_code(test):
            print("TEST:\n", test)
            raise ValueError("Dangerous test code detected")

    def test_run_all(self):
        success_count = 0
        tries = 3
        retries = 5
        for i in range(0, 164):
            print(f"TEST {i}")
            prompt = ""
            test = ""
            code_to_execute = ""
            result = -1
            for _ in range(tries):
                if retries > 0:
                    prompt, test, code_to_execute, result = (
                        self.test_coding_agent_with_retries(i, retries)
                    )
                else:
                    prompt, test, code_to_execute, result = self.test_coding_agent(i)

                if result == 0:
                    success_count += 1
                    print("GREAT SUCCESS WITH id:", i)
                    break

            output_dir = "test_results"
            if not os.path.exists(output_dir):
                os.mkdir(output_dir)
            if result != 0:
                output_file = os.path.join(output_dir, f"{i}_failed.txt")
            else:
                output_file = os.path.join(output_dir, f"{i}_success.txt")
            with open(output_file, "w") as f:
                f.write(prompt + "\n" + "-----" * 5 + "\n")
                f.write(test + "\n" + "-----" * 5 + "\n")
                f.write(code_to_execute)

        print("SUCCESS COUNT:", success_count)
        print("SUCCESS RATE:", success_count / 164)

    def test_blub(self):
        self.test_coding_agent_with_retries(1, 0)

    def test_coding_agent_with_retries(self, test_number: int, retries: int):
        model, prompt, test, entrypoint, code_to_execute, result, result_code = (
            self.test_coding_agent_base(test_number)
        )

        print("RUN 1:", result_code)
        for r in range(retries):
            if result_code == 0:
                break
            else:
                response = model.generate_response(
                    result, max_tokens=1000
                )  # Idea: add to result "\n\nMake sure to write out the full solution and not just the changes to the code."

                code = self._parse_code(response)
                try:
                    self._detect_dangerous_code(prompt, code, test)
                except Exception as e:
                    result = "DANGEROUS CODE DETECTED: " + str(e)
                    continue

                code_to_execute = code + "\n" + test + "\n" + f"check({entrypoint})"

                result, result_code = self.code_interpreter_tool.execute_python_code(
                    code_to_execute
                )
                print(f"RUN {r+2}:", result_code)

        return prompt, test, code_to_execute, result_code

    def test_coding_agent_base(self, test_number: int):
        task: Dict[str, any] = self.dataset["test"][test_number]  # type: ignore

        prompt: str = task["prompt"]  # type: ignore
        test: str = task["test"]  # type: ignore
        entrypoint: str = task["entry_point"]  # type: ignore

        # Type assertions
        assert isinstance(prompt, str)
        assert isinstance(test, str)
        assert isinstance(entrypoint, str)

        if not prompt or not test or not entrypoint:
            raise ValueError("Missing input")

        test: str = test.replace("candidate", entrypoint)

        response, model = self._generate_code(prompt, entrypoint)

        # print("\nRESPONSE FROM MODEL:\n", response)

        code = self._parse_code(response)

        # print("\nCODE:\n", code)

        try:
            self._detect_dangerous_code(prompt, code, test)
        except Exception as e:
            print("DANGEROUS CODE DETECTED:", e)
            return model, prompt, test, entrypoint, "", str(e), -1

        code_to_execute = code + "\n" + test + "\n" + f"check({entrypoint})"

        # print("\nRUNNING THE FOLLOWING CODE:\n", code_to_execute)

        result, result_code = self.code_interpreter_tool.execute_python_code(
            code_to_execute
        )

        return model, prompt, test, entrypoint, code_to_execute, result, result_code

    def test_coding_agent(self, test_number: int):

        _, prompt, test, _, code_to_execute, _, result_code = (
            self.test_coding_agent_base(test_number)
        )
        return prompt, test, code_to_execute, result_code


if __name__ == "__main__":
    unittest.main()
