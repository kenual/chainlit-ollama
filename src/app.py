import chainlit as cl
from chainlit.cli import run_chainlit

@cl.on_message
async def on_message(message: cl.Message):
    await cl.Message(content=f"Received: {message.content}").send()

def main():
    run_chainlit(__file__)