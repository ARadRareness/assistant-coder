import datetime
from typing import List, Optional, Sequence

from language_models.api.base import ApiModel
from language_models.constants import JSON_ERROR_MESSAGE, JSON_PARSE_RETRY_COUNT
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

    def add_user_message(self, content: str, metadata: MessageMetadata):
        self.messages.append(ModelMessage(Role.USER, content, metadata))

    def add_assistant_message(self, content: str, metadata: MessageMetadata):
        self.messages.append(ModelMessage(Role.ASSISTANT, content, metadata))

    def add_system_message(self, content: str, metadata: MessageMetadata):
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
    ):
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
            new_message = self.handle_knowledge(messages[-1])
            messages[-1] = new_message

            self.write_to_history(
                "RESPONSE AFTER KNOWLEDGE", model, messages, use_metadata
            )

        response = model.generate_text(messages, max_tokens, use_metadata=use_metadata)

        self.add_assistant_message(response.get_text(), metadata)

        self.write_to_history("RESPONSE", model, self.messages[-1:], use_metadata)

        return response.get_text()

    def generate_suggestions(self, model: ApiModel):
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

        print(response.get_text())

        return parse_json(response.get_text())["suggestions"]

    def handle_reflections(
        self,
        model: ApiModel,
        max_tokens: int,
        messages: List[ModelMessage],
        use_metadata: bool = False,
    ):
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

        messages[-1].append_content(
            f"(Information to the model, this is some reflections that you can use: {response.get_text()})"
        )

    def handle_tool_use(
        self,
        model: ApiModel,
        max_tokens: int,
        messages: list[ModelMessage],
        use_metadata: bool = False,
    ):
        last_message = messages[-1]
        tool_messages = self.tool_manager.get_tool_conversation(last_message)
        response = model.generate_text(
            tool_messages, max_tokens=max_tokens, use_metadata=use_metadata
        )

        output: Optional[str] = None

        for _ in range(JSON_PARSE_RETRY_COUNT):
            output, _ = self.tool_manager.parse_and_execute(
                response, tool_messages[-1].get_metadata()
            )
            if output != JSON_ERROR_MESSAGE:
                break

        if output and output != JSON_ERROR_MESSAGE:
            messages[-1].append_content(f"(Information to the model, {output})")

    def handle_knowledge(self, message: ModelMessage):
        formatted_documents: List[str] = []

        self.memory_manager.refresh_memory()

        for i, document in enumerate(
            self.memory_manager.get_most_relevant_documents(message.get_message(), 3)
        ):
            formatted_documents.append(f"{i+1}. {document}")

        if formatted_documents:
            formatted_document_message = "\n".join(formatted_documents)
            return ModelMessage(
                Role.USER,
                f"(Your knowledge base contains the following information: {formatted_document_message})\n\n{message.get_content()}",
                message.get_metadata(),
            )
        else:
            return message

    def write_to_history(
        self,
        title: str,
        model: ApiModel,
        messages: Sequence[ModelMessage],
        use_metadata: bool = False,
    ):
        with open("history.log", "a", encoding="utf8") as file:
            file.write(f"< {title} >\n")

            prompt = str(model.prompt_formatter.generate_prompt(messages, use_metadata))
            file.write(prompt)
            file.write("\n\n")


def generate_metadata(ask_permission_to_run_tools: bool = False):
    return MessageMetadata(datetime.datetime.now(), [], ask_permission_to_run_tools)
