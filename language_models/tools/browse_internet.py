import requests
import bs4
from language_models.model_message import MessageMetadata
from language_models.tools.base_tool import BaseTool


class BrowseInternetTool(BaseTool):
    def __init__(self):
        super().__init__(
            "browse_internet",
            "browse the internet by downloading a webpage and reading its content",
            [
                (
                    "URL",
                    "(MANDATORY) specifies the url of the webpage to download and read its content",
                )
            ],
        )

    def action(self, arguments, metadata: MessageMetadata):
        if not "URL" in arguments:
            print("No URL specified!")
            return None

        url = arguments["URL"].replace("<", "").replace(">", "")
        print(f"BROWSE INTERNET with url {url}!")

        response = requests.get(url)
        response.raise_for_status()
        soup = bs4.BeautifulSoup(response.text, "html.parser")

        text_content = soup.get_text()
        return f"CONTENT OF URL {url}: {text_content}"
