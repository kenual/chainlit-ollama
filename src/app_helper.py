import json
import logging
from typing import Any, Dict, List

import chainlit as cl
from chainlit.input_widget import Select

from config import dump_config, load_config
from llm_service import list_models
from template_utils import extract_template_name, extract_template_vars, render_template_with_vars
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


def append_message_to_session_history(message: str, elements: List = None) -> List[Dict[str, str]]:
    # get current chat history from session storage
    messages = cl.chat_context.to_openai()
    # ensure chat history does not duplicate the new message
    last_message = messages[-1]
    if last_message['role'] == 'user' and last_message['content'] == message:
        messages = messages[:-1]

    if elements:
        images = [file.path for file in elements if "image" in file.mime]
    else:
        images = None

    # split message into chunks and append to chat history
    chunks = merge_sentences(sentence_split(message))
    for index, chunk in enumerate(chunks):
        message = {"role": "user", "content": chunk}
        # Add images to the first chunk
        if index == 0 and images:
            message["images"] = images
        messages.append(message)        
    logger.info(f'{len(chunks)} user message chunks')
    logger.info(json.dumps(messages, indent=2))

    return messages


async def prompt_to_fill_template(command: str) -> str:
    template = extract_template_name(command=command)
    params = extract_template_vars(name=template)

    template_params = {}
    for param, value in params.items():
        user_response = await cl.AskUserMessage(content=value, timeout=900).send()
        if user_response:
            template_params[param] = user_response['output']

    return render_template_with_vars(name=template, context=template_params)