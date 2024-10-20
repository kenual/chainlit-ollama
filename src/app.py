from typing import List
import logging

import chainlit as cl
from chainlit.cli import run_chainlit
from chainlit.input_widget import Select
import httpx
import ollama
from ollama import AsyncClient

CHAT_SESSION_SETTINGS = "chat_settings"

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def start():
    ollama_model_names = [ollama_model['model']
                          for ollama_model in list_models()]
    chat_settings = await cl.ChatSettings(
        [
            Select(
                id="Model",
                label="Ollama Model",
                values=ollama_model_names,
                initial_index=0
            )
        ]
    ).send()
    model = chat_settings["Model"]
    logger.info(f"Model default to: {model}")
    cl.user_session.set(CHAT_SESSION_SETTINGS, chat_settings)


@cl.on_settings_update
async def handle_settings_update(new_chat_settings):
    model = new_chat_settings["Model"]
    logger.info(f"Model changed to: {model}")
    cl.user_session.set(CHAT_SESSION_SETTINGS, new_chat_settings)


@cl.on_message
async def on_message(message: cl.Message):
    chat_settings = cl.user_session.get(CHAT_SESSION_SETTINGS)
    message = {'role': 'user', 'content': message.content}

    assistant_response = cl.Message(content='')
    async for part in await AsyncClient().chat(model=chat_settings["Model"], messages=[message], stream=True):
        await assistant_response.stream_token(part['message']['content'])

    await assistant_response.send()


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
