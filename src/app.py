from typing import List
import logging

import chainlit as cl
from chainlit.cli import run_chainlit
from chainlit.input_widget import Select
import httpx
import ollama
from ollama import AsyncClient

from config import load_config, dump_config

CHAT_SETTINGS = "chat_settings"
CONFIG = {
    CHAT_SETTINGS: "settings.toml"
}

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def start():
    MODEL_ID = 'model'

    settings = load_config(CONFIG[CHAT_SETTINGS])
    ollama_model_names = [model_object['model'] for model_object in list_models()]
    if MODEL_ID in settings:
        selected_model = settings[MODEL_ID]
    else:
        selected_model = ollama_model_names[0]

    chat_settings = await cl.ChatSettings(
        [
            Select(
                id=MODEL_ID,
                label="Ollama Model",
                values=ollama_model_names,
                initial_value=selected_model
            )
        ]
    ).send()

    logger.info(f"Chat settings: {chat_settings}")
    cl.user_session.set(CHAT_SETTINGS, chat_settings)


@cl.on_settings_update
async def handle_settings_update(new_chat_settings):
    dump_config(new_chat_settings, CONFIG[CHAT_SETTINGS])
    logger.info(f"{CONFIG[CHAT_SETTINGS]} changed to: {new_chat_settings}")
    cl.user_session.set(CHAT_SETTINGS, new_chat_settings)


@cl.on_message
async def on_message(message: cl.Message):
    chat_settings = cl.user_session.get(CHAT_SETTINGS)
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
