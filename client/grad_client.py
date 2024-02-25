from typing import List
import gradio as gr  # type: ignore

import client_api

conversation_id = client_api.start_conversation()

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(lines=5)

    def respond(message: str, chat_history: List[tuple[str, str]]):
        response = client_api.generate_response(conversation_id, message)

        chat_history.append((message, response))
        return "", chat_history

    with gr.Row():
        clear = gr.ClearButton([msg, chatbot])
        submit = gr.Button("Submit")
        submit.click(respond, [msg, chatbot], [msg, chatbot])  # type: ignore

    msg.submit(respond, [msg, chatbot], [msg, chatbot])  # type: ignore

    demo.launch()  # type: ignore
