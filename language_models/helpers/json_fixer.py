from typing import Any, Dict, Optional
from language_models.api.base import ApiModel
from language_models.helpers.json_parser import parse_json
from language_models.model_message import ModelMessage, Role, MessageMetadata


def fix_json_errors(
    model: ApiModel,
    metadata: MessageMetadata,
    broken_json: str,
) -> Optional[Dict[str, Any]]:
    json_fix_attempt = fix_json_errors_manually(broken_json)

    try:
        return parse_json(json_fix_attempt)
    except Exception as e:
        return fix_json_errors_with_model(model, metadata, broken_json, str(e))


def fix_json_errors_manually(broken_json: str) -> str:
    fixed_json = ""

    in_argument = False
    using_single_quote_argument = False

    for c in broken_json:
        if in_argument:
            if using_single_quote_argument:
                if c == "'":
                    in_argument = False
                    using_single_quote_argument = False
                    fixed_json += '"'
                else:
                    fixed_json += c
            elif c == '"':
                in_argument = False
                using_single_quote_argument = False
                fixed_json += c
            else:
                fixed_json += c
        else:
            if c == '"':
                in_argument = True
                fixed_json += c
            elif c == "'":
                in_argument = True
                using_single_quote_argument = True
                fixed_json += '"'
            else:
                fixed_json += c

    return fixed_json


def fix_json_errors_with_model(
    model: ApiModel,
    metadata: MessageMetadata,
    broken_json: str,
    parsing_error: str,
) -> Optional[Dict[str, Any]]:

    # Only try to fix the string if it contains an opening brace
    if not "{" in broken_json:
        return None

    system_message = ModelMessage(
        role=Role.SYSTEM,
        content="You are an expert at fixing broken JSON data. Use the JSON in combination with the provided JSON parsing error in order to fix it.",
        metadata=metadata,
    )

    current_broken_json = broken_json
    current_parsing_error = parsing_error

    tries = 3

    for _ in range(tries):
        print(
            f"Trying to fix JSON {current_broken_json} with error {current_parsing_error}"
        )
        user_message = ModelMessage(
            role=Role.USER,
            content=f"The following json: {current_broken_json} failed to parse with the following error: {current_parsing_error}. Please fix the JSON and send it back to me.",
            metadata=metadata,
        )
        response = model.generate_text([system_message, user_message]).get_text()

        try:
            print(f"Solution attempt: {response}")
            return parse_json(response)

        except Exception as e:
            current_broken_json = response
            current_parsing_error = str(e)

    return None
