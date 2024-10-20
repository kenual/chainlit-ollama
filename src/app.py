from typing import List
import logging

import chainlit as cl
from chainlit.cli import run_chainlit
from chainlit.input_widget import Select
import httpx
import ollama

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def start():
    ollama_model_names = [ollama_model['model']
                          for ollama_model in list_models()]
    settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="Ollama Model",
                values=ollama_model_names,
                initial_index=0
            )
        ]
    ).send()


@cl.on_settings_update
async def handle_settings_update(settings):
    model = settings["Model"]
    logger.info(f"Model changed to: {model}")


@cl.on_message
async def on_message(message: cl.Message):
    await cl.Message(content=f"Received: {message.content}").send()


def list_models() -> List[dict]:
    # List available Ollama models
    try:
        response = ollama.list()
        return response['models']

    except httpx.ConnectError as error:
        logger.error(f"Ollama server connect error: {error}")
        return [{'model': 'None'}]


def main():
    run_chainlit(__file__)


if __name__ == '__main__':
    main()
