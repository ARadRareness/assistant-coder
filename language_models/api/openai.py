import openai

from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_system_message_param import (
    ChatCompletionSystemMessageParam,
)
from openai.types.chat.chat_completion_user_message_param import (
    ChatCompletionUserMessageParam,
)
from openai.types.chat.chat_completion_assistant_message_param import (
    ChatCompletionAssistantMessageParam,
)

from typing import List, Sequence
from language_models.api.base import ApiModel
from language_models.formatters.base import PromptFormatter
from language_models.model_message import ModelMessage
from language_models.model_response import ModelResponse

import os


class OpenAIModel(ApiModel):
    def __init__(
        self,
        api_key: str,
        model_name: str = "gpt-3.5-turbo",
    ):
        super().__init__(model_name, PromptFormatter())
        # Set the OpenAI API key
        openai.api_key = api_key
        self.model_name = model_name

    def generate_text(
        self,
        messages: Sequence[ModelMessage],
        max_tokens: int = 200,
        temperature: float = 0.2,
        use_metadata: bool = False,
    ) -> ModelResponse:

        client = openai.OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )

        openai_messages: List[ChatCompletionMessageParam] = []
        for message in messages:
            if message.is_system_message():
                openai_messages.append(
                    ChatCompletionSystemMessageParam(
                        content=message.get_content(), role="system"
                    )
                )
            elif message.is_user_message():
                openai_messages.append(
                    ChatCompletionUserMessageParam(
                        content=message.get_content(), role="user"
                    )
                )
            elif message.is_assistant_message():
                openai_messages.append(
                    ChatCompletionAssistantMessageParam(
                        content=message.get_content(), role="assistant"
                    )
                )

        print(openai_messages)

        chat_completion = client.chat.completions.create(
            model=self.model_name,
            messages=openai_messages,
        )

        result = chat_completion.choices[0].message.content

        if result:
            return ModelResponse(result, self.model_name)
        else:
            return ModelResponse("", self.model_name)
