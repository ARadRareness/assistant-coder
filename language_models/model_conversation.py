import datetime
from typing import List, Optional, Sequence

from language_models.api.base import ApiModel
from language_models.constants import JSON_ERROR_MESSAGE, JSON_PARSE_RETRY_COUNT
from language_models.helpers.json_fixer import fix_json_errors
from language_models.helpers.json_parser import parse_json
from language_models.memory_manager import MemoryManager
from language_models.model_message import MessageMetadata, ModelMessage, Role
from language_models.tool_manager import ToolManager


class ModelConversation:
    def __init__(
        self, memory_manager: MemoryManager, single_message_mode: bool = False
    ):
        self.messages: List[ModelMessage] = []
        self.single_message_mode: bool = single_message_mode
        self.tool_manager: ToolManager = ToolManager()
        self.memory_manager: MemoryManager = memory_manager

    def get_messages(self, single_message_mode: bool = False) -> List[ModelMessage]:
        if not self.messages:
            return []

        if single_message_mode:
            messages: List[ModelMessage] = []
            system_message = None
            for message in self.messages:
                if message.is_system_message():
                    system_message = message

            if system_message:
                messages.append(system_message)

            if len(self.messages) > 0 and not system_message == self.messages[-1]:
                messages.append(self.messages[-1])

            return messages

        return self.messages[::]

    def add_user_message(self, content: str, metadata: MessageMetadata) -> None:
        self.messages.append(ModelMessage(Role.USER, content, metadata))

    def add_assistant_message(self, content: str, metadata: MessageMetadata) -> None:
        self.messages.append(ModelMessage(Role.ASSISTANT, content, metadata))

    def add_system_message(self, content: str, metadata: MessageMetadata) -> None:
        full_content = (
            "Unless required, answer briefly in a sentence or two.\n" + content
        )
        self.messages.append(ModelMessage(Role.SYSTEM, full_content, metadata))

    def generate_message(
        self,
        model: ApiModel,
        max_tokens: int,
        single_message_mode: bool,
        use_metadata: bool = False,
        use_tools: bool = False,
        use_reflections: bool = False,
        use_knowledge: bool = False,
        ask_permission_to_run_tools: bool = False,
    ) -> str:
        messages = self.get_messages(single_message_mode)

        metadata = generate_metadata(ask_permission_to_run_tools)

        self.write_to_history("HISTORY", model, self.messages, use_metadata)

        if use_reflections and messages and messages[-1].is_user_message():
            self.handle_reflections(
                model, max_tokens, messages, use_metadata=use_metadata
            )

        if use_tools and messages:
            self.handle_tool_use(model, max_tokens, messages, use_metadata=use_metadata)

            self.write_to_history("RESPONSE AFTER TOOLS", model, messages, use_metadata)

        if use_knowledge and messages:
            self.handle_knowledge(model, messages[-1])

            self.write_to_history(
                "RESPONSE AFTER KNOWLEDGE", model, messages, use_metadata
            )

        response = model.generate_text(messages, max_tokens, use_metadata=use_metadata)

        self.add_assistant_message(response.get_text(), metadata)

        self.write_to_history("RESPONSE", model, self.messages[-1:], use_metadata)

        return response.get_text()

    def generate_suggestions(self, model: ApiModel) -> List[str]:
        messages = self.get_messages(single_message_mode=False)

        messages.append(
            ModelMessage(
                Role.USER,
                (
                    "Suggest 3 reasonable follow up questions or instructions based on the previous conversation."
                    + ' Write them out using JSON notation as following {"suggestions": ["suggestion1", "suggestion2", "suggestion3"]}. Do not write any comments, only the json object.'
                ),
                generate_metadata(),
            )
        )

        response = model.generate_text(messages, max_tokens=200)

        try:
            return parse_json(response.get_text())["suggestions"]
        except Exception as e:
            response = fix_json_errors(
                model, generate_metadata(), response.get_text(), str(e)
            )
            if response:
                return response["suggestions"]

        return []

    def handle_reflections(
        self,
        model: ApiModel,
        max_tokens: int,
        messages: List[ModelMessage],
        use_metadata: bool = False,
    ) -> None:
        last_message = messages.pop(-1)

        reflection_prompt_message = ModelMessage(
            Role.USER,
            "Reflect on the user message below, go step by step through your thoughts how to best fulfill the request of the message.\nMESSAGE: "
            + last_message.get_message(use_metadata=use_metadata),
            last_message.get_metadata(),
        )

        messages.append(reflection_prompt_message)

        response = model.generate_text(messages, max_tokens, use_metadata=use_metadata)

        messages[-1] = last_message  # Restore the old user message

        reflection_text = response.get_text()

        if reflection_text:
            messages[-1].get_metadata().set_reflection_text(reflection_text)

    def handle_tool_use(
        self,
        model: ApiModel,
        max_tokens: int,
        messages: list[ModelMessage],
        use_metadata: bool = False,
    ) -> None:
        last_message = messages[-1]
        tool_messages = self.tool_manager.get_tool_conversation(last_message)
        response = model.generate_text(
            tool_messages, max_tokens=max_tokens, use_metadata=use_metadata
        )

        output: Optional[str] = None

        for _ in range(JSON_PARSE_RETRY_COUNT):
            output, _ = self.tool_manager.parse_and_execute(
                model, response, tool_messages[-1].get_metadata()
            )
            if output != JSON_ERROR_MESSAGE:
                break

        if output and output != JSON_ERROR_MESSAGE:
            messages[-1].get_metadata().set_tool_output(output)

    def handle_knowledge(self, model: ApiModel, message: ModelMessage) -> None:
        formatted_documents: List[str] = []

        self.memory_manager.refresh_memory()

        retrieved_documents = (
            self.memory_manager.get_most_relevant_documents_with_rerank(
                message.get_message(), 3
            )
        )

        relevant_documents = self.get_relevant_documents(
            model, retrieved_documents, message
        )

        for i, document in enumerate(relevant_documents):
            formatted_documents.append(f"{i+1}. {document}")

        if formatted_documents:
            formatted_document_message = "\n".join(formatted_documents)
            message.get_metadata().set_knowledge_information(formatted_document_message)

    def get_relevant_documents(
        self, model: ApiModel, documents: Sequence[str], message: ModelMessage
    ) -> List[str]:
        formatted_documents: List[str] = []

        for i, doc in enumerate(documents):
            if i == 0:
                formatted_documents.append(
                    f"<DOCUMENT_{i+1}>\n{doc}</DOCUMENT_{i+1}>\n"
                )

        formatted_string = "\n".join(formatted_documents)

        system_message = "For the user message below, answer with which of the documents that contains information that could be relevant or related to what the user message is about. Focus on the core meaning of the user message, is any information from one of the documents relevent to the core meaning?"

        system_message = (
            system_message
            + ' Write out the response as a json object with the following structure: {"relevant_documents": [1, 2, 3]}. If none are relevant, write {"relevant_documents": []}.'
        )

        user_message = f"""
        <USER_MESSAGE>
        {message.get_message()}
        </USER_MESSAGE>
        <DOCUMENTS>
        {formatted_string}
        </DOCUMENTS>
        """

        example_message = """
        <USER_MESSAGE>
        What is my favorite color?
        </USER_MESSAGE>
        <DOCUMENTS>
        <DOCUMENT_1>
        There is a monkey.
        </DOCUMENT_1>
        <DOCUMENT_2>
        The user likes the color blue.
        </DOCUMENT_2>
        <DOCUMENT_3>
        The cookies are being baked right now.
        </DOCUMENT_3>
        </DOCUMENTS>
        """

        example_answer = '{"relevant_documents":[2]}'

        messages = [
            ModelMessage(Role.SYSTEM, system_message, message.get_metadata()),
            ModelMessage(Role.USER, example_message, message.get_metadata()),
            ModelMessage(Role.ASSISTANT, example_answer, message.get_metadata()),
            ModelMessage(Role.USER, user_message, message.get_metadata()),
        ]

        for _ in range(JSON_PARSE_RETRY_COUNT):
            response = model.generate_text(
                messages,
                40,
                use_metadata=True,
            )
            response_text = response.get_text().replace("\\", "")

            parsed_json = parse_json(response_text)

            error_in_json: bool = False

            if "relevant_documents" in parsed_json:
                output_documents: List[str] = []

                for document_number in parsed_json["relevant_documents"]:
                    try:
                        document_number = int(document_number)
                    except ValueError:
                        error_in_json = True
                        break

                    if document_number <= 0 or document_number > len(documents):
                        error_in_json = True
                        break

                    output_documents.append(documents[document_number - 1])

                if not error_in_json:
                    return output_documents
        return []

    def write_to_history(
        self,
        title: str,
        model: ApiModel,
        messages: Sequence[ModelMessage],
        use_metadata: bool = False,
    ) -> None:
        with open("history.log", "a", encoding="utf8") as file:
            file.write(f"< {title} >\n")

            prompt = str(model.prompt_formatter.generate_prompt(messages, use_metadata))
            file.write(prompt)
            file.write("\n\n")


def generate_metadata(ask_permission_to_run_tools: bool = False) -> MessageMetadata:
    return MessageMetadata(datetime.datetime.now(), [], ask_permission_to_run_tools, "")
