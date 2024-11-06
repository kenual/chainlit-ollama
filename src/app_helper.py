import logging
from typing import Any, Dict, List

import chainlit as cl
from chainlit.input_widget import Select
import httpx
import ollama
from ollama import AsyncClient

from config import dump_config, load_config
from text_utils import merge_sentences, sentence_split

APP_SETTINGS = 'app_settings'
CONFIG = {
    APP_SETTINGS: 'settings.toml'
}
MODEL_ID = 'model'

logger = logging.getLogger(__name__)


async def initialize_session_chat_settings() -> None:
    settings = load_config(CONFIG[APP_SETTINGS])
    ollama_model_names = [model_object['model']
                          for model_object in list_models()]
    if MODEL_ID in settings:
        selected_model = settings[MODEL_ID]
        if selected_model not in ollama_model_names:
            new_model = ollama_model_names[0]
            logger.warning(f"Model '{selected_model}' is not available. Default to use '{new_model}'")
            selected_model = new_model
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


async def update_session_chat_settings(settings: dict[str, Any]) -> None:
    dump_config(settings, CONFIG[APP_SETTINGS])
    logger.info(f"{CONFIG[APP_SETTINGS]} changed to: {settings}")


def list_models() -> List[dict]:
    # List available Ollama models
    try:
        response = ollama.list()
        return response['models']

    except httpx.ConnectError as error:
        logger.error(f"Ollama server connect error: {error}")
        return [{'model': 'None'}]


def append_message_to_session_history(message: str) -> List[Dict[str, str]]:
    # get current chat history from session storage
    messages = cl.chat_context.to_openai()
    chunks = merge_sentences(sentence_split(message))
    for chunk in chunks:
        messages.append({"role": "user", "content": chunk})
    logger.info(f'{len(chunks)} user message chunks')
    return messages


async def chat_messages_send_response(model: str, messages: List[Dict[str, str]]) -> None:
    translation_table = str.maketrans({'.': '_', ':': '#'})
    assistant_response = cl.Message(
        content='', author=model.translate(translation_table))
    async for part in await AsyncClient().chat(model=model, messages=messages, stream=True):
        await assistant_response.stream_token(part['message']['content'])

    await assistant_response.send()
