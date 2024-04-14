import logging
from playwright.sync_api import sync_playwright, ElementHandle, Page
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from language_models.helpers.json_parser import parse_json

from client.client_api import Model

logging.basicConfig(level=logging.INFO, format="%(message)s")


class InteractableElement:
    def __init__(self, element: ElementHandle):
        self.element = element

    def get_title(self):
        return self.element.get_attribute("title")

    def get_aria_label(self):
        return self.element.get_attribute("aria-label")

    def get_text(self):
        return self.element.text_content()

    def get_tag(self):
        return self.element.evaluate("element => element.tagName")

    def get_description(self):
        candidates = [self.get_aria_label(), self.get_text(), self.get_title()]
        for candidate in candidates:
            if candidate:
                candidate = candidate.strip()
                if candidate:
                    return candidate
        return f"Unknown"

    def get_type_and_description(self):
        tag = self.get_tag()
        description = self.get_description().replace("\n", " ").replace("\t", " ")
        while "  " in description:
            description = description.replace("  ", " ")

        if tag == "BUTTON":
            return "button", description
        elif tag == "A":
            return "link", description
        else:
            return self.get_tag(), description

    def __repr__(self):
        return f"{self.get_type_and_description()}"

    def __str__(self):
        return self.__repr__()


class Browser:
    def __init__(self):
        self.playwright_context = sync_playwright()
        self.playwright = self.playwright_context.start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def __del__(self):
        self.context.close()
        self.browser.close()
        self.playwright_context.__exit__()

    def open_page(self, url: str) -> Page:
        self.page.goto(url)

    def get_interactable_elements(self):
        return [
            InteractableElement(element)
            for element in self.page.query_selector_all(
                'button, a, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            )
        ]

    def get_element_by_tag_description(self, tag: str, description: str):
        interactable_elements = self.get_interactable_elements()
        for element in interactable_elements:
            if element.get_tag() == tag and element.get_description() == description:
                return element
        return None

    def sleep(self, timeout: int) -> None:
        self.page.wait_for_timeout(timeout)


class AIBrowser:
    def __init__(self):
        self.browser = Browser()
        self.model_click = Model(
            single_message_mode=True,
            use_tools=False,
            use_reflections=False,
            use_knowledge=False,
            ask_permission_to_run_tools=True,
        )

        self.model_click.add_system_message(
            "You are an expert at deciding which element to select given a user query and list of available elements. Respond with the element you want to select."
            ' Answer with a json object with the following format: {"element_type": "link/button", "element_description": "element description"}'
        )

        self.model_url = Model(
            single_message_mode=True,
            use_tools=False,
            use_reflections=False,
            use_knowledge=False,
            ask_permission_to_run_tools=True,
        )

        self.model_url.add_system_message(
            "You are an expert at deciding which URL to go to given a user query. Respond with the URL you want to go to."
            ' Answer with a json object with the following format: {"url": "url"}'
        )

    def goto_url(self, url: str):
        self.browser.open_page(url)

    def goto_url_by_description(self, url_description: str):
        response = self.model_url.generate_response(
            f'Respond with the url that best matches the user description "{url_description}". Go step by step through your reasoning and answer with a json object with the following format: {{"url": "url"}}.',
            temperature=0,
        )

        logging.debug(response)

        parsed_json = parse_json(response)

        if "url" in parsed_json:
            url = parsed_json["url"]
            logging.info(f"Going to url: {url}")
            self.goto_url(url)
            return True

        return False

    def sleep(self, timeout: int) -> None:
        self.browser.sleep(timeout)

    def click_element_by_description(self, element_description: str):
        ai_browser.browser.page.wait_for_load_state("domcontentloaded")

        interactable_elements = self.browser.get_interactable_elements()

        llm_elements = []
        for element in interactable_elements:
            element_type, element_desc = element.get_type_and_description()
            if element_desc != "Unknown":
                current_element = f"{element.get_type_and_description()}"
                llm_elements.append(current_element)

        elements = "\n".join(llm_elements)
        response = self.model_click.generate_response(
            f"<ELEMENTS>{elements}</ELEMENTS>\n\nUSER_QUERY: {element_description}\n\nRespond with the element you should select."
            "Go step by step through your reasoning and answer with a json object with the following format: "
            '{{"element_type": "link/button", "element_description": "element description"}}. It is CRITICAL that you only select elements that exist!',
            temperature=0,
        )

        logging.debug(llm_elements)

        logging.debug("----------")

        logging.debug(interactable_elements)

        logging.debug(response)

        try:
            parsed_json = parse_json(response)
        except:
            logging.error(f"Failed to parse json: {response}")
            return False

        if "element_type" in parsed_json and "element_description" in parsed_json:
            element_type = parsed_json["element_type"]
            element_desc = parsed_json["element_description"]

            for element in interactable_elements:
                element_to_find = (element_type, element_desc)
                if element.get_type_and_description() == element_to_find:
                    logging.info(f"Clicking on element: {element_desc}")
                    element.element.click()
                    return True

            for element in interactable_elements:
                if element_desc in element.get_description():
                    logging.info(f"Clicking on element (type 2): {element_desc}")
                    element.element.click()
                    return True

        logging.info(f"FAILED TO CLICK ON ELEMENT: {element_description}")
        return False


def hugginface_example(ai_browser: AIBrowser):
    assert ai_browser.goto_url_by_description("Go to huggingface")
    assert ai_browser.click_element_by_description("I want to learn!")
    assert ai_browser.click_element_by_description("I would like to learn about NLP!")
    assert ai_browser.click_element_by_description(
        "What are some Bias and limitations?"
    )


def youtube_example(ai_browser: AIBrowser):
    assert ai_browser.goto_url_by_description("Go to youtube")
    assert ai_browser.click_element_by_description("Reject all cookies")
    assert ai_browser.click_element_by_description("Go to shorts")


ai_browser = AIBrowser()

hugginface_example(ai_browser)

ai_browser.sleep(10000)
