import gradio as gr

import client_api

conversation_id = client_api.start_conversation()

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(lines=5)

    def respond(message, chat_history):
        response = client_api.generate_response(conversation_id, message)

        chat_history.append((message, response))
        return "", chat_history

    with gr.Row():
        clear = gr.ClearButton([msg, chatbot])
        submit = gr.Button("Submit")
        submit.click(respond, [msg, chatbot], [msg, chatbot])

    msg.submit(respond, [msg, chatbot], [msg, chatbot])

demo.launch()
