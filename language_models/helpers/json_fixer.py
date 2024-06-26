from typing import Any, Dict, List, Optional
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
    result, _ = fix_json_errors_manually_helper(broken_json, 0)
    return result


def fix_json_errors_manually_helper(broken_json: str, start_index: int) -> str:
    parsed_arguments: List[str] = []

    in_argument_name = False
    in_argument_value = False
    using_single_quotes = False
    using_nonstring = False

    argument_name = ""
    argument_value = ""

    i: int = start_index
    while i < len(broken_json):
        c = broken_json[i]
        if in_argument_name or in_argument_value:
            if (using_single_quotes and c == "'") or (
                not using_single_quotes and c == '"'
            ):
                if in_argument_name:
                    in_argument_name = False
                    if not argument_name:
                        argument_name = "NONE"
                elif in_argument_value:
                    in_argument_value = False
                    parsed_arguments.append(f'"{argument_name}": "{argument_value}"')
                    argument_name = ""
                    argument_value = ""
            elif using_nonstring and c in ",}:":
                using_nonstring = False
                if in_argument_name:
                    in_argument_name = False
                    if not argument_name:
                        argument_name = "NONE"
                else:
                    in_argument_value = False
                    parsed_arguments.append(f'"{argument_name}": {argument_value}')
                    argument_name = ""
                    argument_value = ""

                    if c == "}":
                        break

            else:
                if in_argument_name:
                    argument_name += c
                elif in_argument_value:
                    argument_value += c
        else:
            if (
                c == "{" and argument_name
            ):  # Only activate recursion if we have parsed an argument_name
                result, i = fix_json_errors_manually_helper(broken_json, i)
                parsed_arguments.append(f'"{argument_name}": {result}')
                argument_name = ""
                i -= 1

            elif c == '"' or c == "'":
                if not argument_name:
                    in_argument_name = True
                else:
                    in_argument_value = True

                if c == "'":
                    using_single_quotes = True
            elif c in "0123456789nft" and argument_name:  # number, null, true, false
                using_nonstring = True
                in_argument_value = True
                argument_value += c
            elif c.isalpha():
                using_nonstring = True
                in_argument_name = True
                argument_name += c
        i += 1

    if argument_name and argument_value:
        if using_nonstring:
            parsed_arguments.append(f'"{argument_name}": {argument_value}')
        else:
            parsed_arguments.append(f'"{argument_name}": "{argument_value}"')

    fixed_json = "{" + ", ".join(parsed_arguments) + "}"
    return fixed_json, i


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
