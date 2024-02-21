import os

from language_models.tools.base_tool import BaseTool


def load_available_tools(parent_tool_name=None) -> list[BaseTool]:
    tools = []

    # Dynamically load tools from the tools directory
    for file in os.listdir("language_models/tools"):
        if file.endswith(".py") and not file.startswith("__"):
            tool_name = file.split(".")[0]
            tool_module = __import__(
                f"language_models.tools.{tool_name}", fromlist=[tool_name]
            )
            # Get the class from the module if it has BaseTool as parent
            for name, obj in tool_module.__dict__.items():
                if (
                    name != "BaseTool"
                    and name != parent_tool_name
                    and isinstance(obj, type)
                    and issubclass(obj, BaseTool)
                ):
                    tools.append(obj())
    return tools
