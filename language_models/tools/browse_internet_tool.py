from typing import Any, Dict, List
import requests
import bs4
from language_models.api.base import ApiModel
from language_models.model_message import MessageMetadata, ModelMessage
from language_models.tools.base_tool import BaseTool


class BrowseInternetTool(BaseTool):
    def __init__(self):
        super().__init__(
            "browse_internet",
            "Using this tool, you have the ability to browse the internet, download webpages and read their content",
            [
                (
                    "URL",
                    "(MANDATORY) specifies the url of the webpage to download and retrieve content from",
                )
            ],
            True,
        )

    def action(
        self,
        arguments: Dict[str, Any],
        model: ApiModel,
        messages: List[ModelMessage],
        metadata: MessageMetadata,
    ) -> str:
        url = self.get_url_argument(arguments)

        if not url:
            print("No URL specified!")
            return ""

        print(f"BROWSE INTERNET with url {url}!")

        web_response = requests.get(url)
        web_response.raise_for_status()
        soup = bs4.BeautifulSoup(web_response.text, "html.parser")

        text_content = soup.get_text()
        return f"WEBPAGE CONTENT OF URL {url}: {text_content}"

    def ask_permission_message(
        self, arguments: Dict[str, Any], metadata: MessageMetadata
    ) -> str:
        url = self.get_url_argument(arguments)

        if url:
            return f"AC would like to download and read the content of the following webpage:\n\n{url}\n\nDo you want to allow this?"
        else:
            return ""

    def get_url_argument(self, arguments: Dict[str, Any]) -> str:
        if "URL" in arguments:
            return arguments["URL"].replace("<", "").replace(">", "")
        return ""

    def get_example_messages(self) -> List[ModelMessage]:
        return self.get_example_dialogue(
            "What's the title of this webpage? https://www.youtube.com/watch?v=hleHx2Uiqmo",
            '{"tool": "browse_internet", "arguments": {"URL": "https://www.youtube.com/watch?v=hleHx2Uiqmo"}}',
        )
