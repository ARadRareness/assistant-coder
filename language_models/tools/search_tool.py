import os

from duckduckgo_search import DDGS
from language_models.model_message import MessageMetadata
from language_models.tools.base_tool import BaseTool


class SearchTool(BaseTool):
    def __init__(self):
        super().__init__(
            "search_the_web",
            "search the web for a specific query",
            [
                (
                    "QUERY",
                    "the query to search for",
                )
            ],
        )

    def action(self, arguments, metadata: MessageMetadata):
        if "QUERY" in arguments:
            search_query = arguments["QUERY"]

            with DDGS() as search_engine:
                results = ["SEARCH RESULTS FOR QUERY: " + search_query + "\n\n"]
                for r in search_engine.text(search_query, max_results=5):
                    results.append(
                        f"<ENTRY><TITLE>{r['title']}</TITLE>\n<URL>{r['href']}</URL>\n<DESCRIPTION>{r['body']}<DESCRIPTION></ENTRY>\n"
                    )

                return "\n".join(results)

        else:
            print("TRIED TO SEARCH WITHOUT QUERY ARGUMENTS")

    def get_example_messages(self):
        return self.get_example_dialogue(
            "Forever and one is a song by...",
            '{"tool": "search_the_web", "arguments": {"QUERY": "\'forever and one\' song"}}',
        )
