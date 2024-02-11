import json


def handle_json(raw_text: str):
    level_count = 0
    start_index = -1
    end_index = -1
    for i, char in enumerate(raw_text):
        if char == "{":
            if start_index == -1:
                start_index = i
            level_count += 1
        elif char == "}":
            level_count -= 1
            if level_count == 0:
                end_index = i + 1
                break

    return raw_text[start_index:end_index]


def parse_json(raw_text: str):
    json_text = handle_json(raw_text)
    return json.loads(json_text)
