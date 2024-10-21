import logging
from typing import Any, List

import chainlit as cl
from chainlit.input_widget import Select
import httpx
import ollama

from config import dump_config, load_config

CHAT_SETTINGS = 'chat_settings'
CONFIG = {
    CHAT_SETTINGS: 'settings.toml'
}
MODEL_ID = 'model'

logger = logging.getLogger(__name__)


async def initialize_session_chat_settings() -> None:
    settings = load_config(CONFIG[CHAT_SETTINGS])
    ollama_model_names = [model_object['model']
                          for model_object in list_models()]
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


async def update_session_chat_settings(settings: dict[str, Any]) -> None:
    dump_config(settings, CONFIG[CHAT_SETTINGS])
    logger.info(f"{CONFIG[CHAT_SETTINGS]} changed to: {settings}")
    cl.user_session.set(CHAT_SETTINGS, settings)


def list_models() -> List[dict]:
    # List available Ollama models
    try:
        response = ollama.list()
        return response['models']

    except httpx.ConnectError as error:
        logger.error(f"Ollama server connect error: {error}")
        return [{'model': 'None'}]
