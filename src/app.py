import logging
from typing import Any

import chainlit as cl
from chainlit.cli import run_chainlit
from ollama import AsyncClient

from app_helper import MODEL_ID, initialize_session_chat_settings, update_session_chat_settings
from text_utils import sentence_split, merge_sentences

logger = logging.getLogger(__name__)


@cl.on_chat_start
async def start():
    await initialize_session_chat_settings()


@cl.on_settings_update
async def handle_settings_update(new_chat_settings: dict[str, Any]):
    await update_session_chat_settings(settings=new_chat_settings)


@cl.on_message
async def on_message(message: cl.Message):
    chat_settings = cl.user_session.get('chat_settings')

    messages = cl.chat_context.to_openai()
    chunks = merge_sentences(sentence_split(message.content))
    for chunk in chunks:
        messages.append({"role": "user", "content": chunk})
    logger.info(f'{len(chunks)} user message chunks')

    model = chat_settings[MODEL_ID]
    translation_table = str.maketrans({'.': '_', ':': '#'})
    assistant_response = cl.Message(content='', author=model.translate(translation_table))
    async for part in await AsyncClient().chat(model=model, messages=messages, stream=True):
        await assistant_response.stream_token(part['message']['content'])

    await assistant_response.send()


def main():
    run_chainlit(__file__)


if __name__ == '__main__':
    main()
