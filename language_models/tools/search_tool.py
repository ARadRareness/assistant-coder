from typing import Any, Dict, List

from duckduckgo_search import DDGS  # type: ignore
from language_models.api.base import ApiModel  # type: ignore
from language_models.model_message import MessageMetadata, ModelMessage
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
            True,
        )

    def action(
        self,
        arguments: Dict[str, Any],
        model: ApiModel,
        messages: List[ModelMessage],
        metadata: MessageMetadata,
    ) -> str:
        search_query = self.get_search_query_argument(arguments)

        if search_query:

            with DDGS() as search_engine:
                results = ["SEARCH RESULTS FOR QUERY: " + search_query + "\n\n"]
                for r in search_engine.text(search_query, max_results=5):  # type: ignore
                    results.append(
                        f"<ENTRY><TITLE>{r['title']}</TITLE>\n<URL>{r['href']}</URL>\n<DESCRIPTION>{r['body']}</DESCRIPTION></ENTRY>\n"
                    )

                return "\n".join(results)

        else:
            print("TRIED TO SEARCH WITHOUT QUERY ARGUMENTS")

        return ""

    def ask_permission_message(
        self, arguments: Dict[str, Any], metadata: MessageMetadata
    ) -> str:
        query = self.get_search_query_argument(arguments)

        if query:
            return f"AC would like to search the web for the following query:\n\n{query}\n\nDo you want to allow this?"
        else:
            return ""

    def get_search_query_argument(self, arguments: Dict[str, Any]) -> str:
        if "QUERY" in arguments:
            return arguments["QUERY"]
        return ""

    def get_example_messages(self) -> List[ModelMessage]:
        return self.get_example_dialogue(
            "Forever and one is a song by...",
            '{"tool": "search_the_web", "arguments": {"QUERY": "\'forever and one\' song"}}',
        )
