from typing import List
import gradio as gr  # type: ignore

import client_api

conversation_id = client_api.start_conversation()

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    system_message_box = gr.Textbox(lines=2, label="System Message")
    message_box = gr.Textbox(lines=5, label="User Message")

    def respond(message: str, chat_history: List[tuple[str, str]], system_message: str):
        if system_message:
            client_api.add_system_message(conversation_id, system_message)

        response = client_api.generate_response(conversation_id, message)

        chat_history.append((message, response))
        return "", chat_history

    with gr.Row():
        clear = gr.ClearButton([message_box, system_message_box, chatbot])
        submit = gr.Button("Submit")
        submit.click(fn=respond, inputs=[message_box, chatbot, system_message_box], outputs=[message_box, chatbot])  # type: ignore

    message_box.submit(fn=respond, inputs=[message_box, chatbot, system_message_box], outputs=[message_box, chatbot])  # type: ignore

    demo.launch()  # type: ignore
