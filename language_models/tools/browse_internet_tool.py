import requests
import bs4
from language_models.model_message import MessageMetadata
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

    def action(self, arguments, metadata: MessageMetadata):
        url = self.get_url_argument(arguments)

        if not url:
            print("No URL specified!")
            return None

        print(f"BROWSE INTERNET with url {url}!")

        response = requests.get(url)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        text_content = soup.get_text()
        return f"WEBPAGE CONTENT OF URL {url}: {text_content}"

    def ask_permission_message(self, arguments, metadata: MessageMetadata):
        url = self.get_url_argument(arguments)

        if url:
            return f"AC would like to download and read the content of the following webpage:\n\n{url}\n\nDo you want to allow this?"
        else:
            return None

    def get_url_argument(self, arguments):
        if "URL" in arguments:
            return arguments["URL"].replace("<", "").replace(">", "")
        return None

    def get_example_messages(self):
        return self.get_example_dialogue(
            "What's the title of this webpage? https://www.youtube.com/watch?v=hleHx2Uiqmo",
            '{"tool": "browse_internet", "arguments": {"URL": "https://www.youtube.com/watch?v=hleHx2Uiqmo"}}',
        )
