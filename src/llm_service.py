import logging
import os
import time
from typing import Dict, List
import chainlit as cl
from dotenv import load_dotenv
from any_llm import ProviderName, list_models
from pydantic import BaseModel

from agent_helper import agent_runner
from llm_tools import think

logger = logging.getLogger(__name__)

CLOUD_SERVICE_PREFIX = "☁️🔗 "


class Model(BaseModel):
    name: str
    provider: ProviderName
    display: str


def list_provider_models(
    provider: ProviderName, api_key: str = None
) -> List[Model]:
    """
    List models for the specified provider.

    Args:
        provider: ProviderName to query (can be local or remote).
        api_key: API key for the provider (may be unused depending on provider).

    Returns:
        List[Model]: List of models provided by the specified provider, or an empty list if there is a connection error.
    """
    if provider == ProviderName.OLLAMA:
        prefix = ""
    else:
        prefix = f"{CLOUD_SERVICE_PREFIX}{provider.value}:"

    try:
        list_models_response = list_models(provider=provider, api_key=api_key)
        provider_models = [
            Model(
                name=model.id,
                provider=provider,
                display=prefix + model.id,
            )
            for model in list_models_response
        ]
        return provider_models
    except Exception as error:
        logger.error(f"{provider} list_models() error: {error}")
        return []


def get_available_models() -> List[Model]:
    load_dotenv()
    cloud_service_models: List[Model] = []
    if os.getenv('CO_API_KEY'):
        cloud_service_models += list_provider_models(
            provider=ProviderName.COHERE)
    if os.getenv('TOGETHERAI_API_KEY'):
        cloud_service_models[:0] = [
            Model(name="DeepSeek-R1-Distill-lama-70B-free", provider=ProviderName.TOGETHER,
                  display=f"{CLOUD_SERVICE_PREFIX}together:DeepSeek-R1-Distill-Llama-70B-free"),
            Model(name="Llama-Vision-Free", provider=ProviderName.TOGETHER,
                  display=f"{CLOUD_SERVICE_PREFIX}together:Llama-Vision-Free")
        ]

    # Local Ollama models
    return list_provider_models(provider=ProviderName.OLLAMA) + cloud_service_models


async def chat_messages_send_response(model: str, messages: List[Dict[str, str]]) -> None:
    if CLOUD_SERVICE_PREFIX in model:
        any_llm_model = model.split(CLOUD_SERVICE_PREFIX)[1]
    else:
        any_llm_model = f"{ProviderName.OLLAMA.value}:{model}"

    # Send chat messages to Ollama and stream the response back to the client.
    translation_table = str.maketrans({'.': '_', ':': '#'})

    # Get tools from all MCP connections
    mcp_tools = cl.user_session.get("mcp_tools", {})
    all_tools = [
        {
            "type": "function",
            "function": {
                "name": tool['name'],
                "description": tool['description'],
                "parameters":  tool['input_schema']
            }
        }
        for connection_tools in mcp_tools.values() for tool in connection_tools
    ]

    response = await agent_runner(
        model=any_llm_model,
        messages=messages,
        tools=all_tools,
        stream=all_tools is not None
    )

    assistant_response = cl.Message(content='', author=model.translate(translation_table))
    async for part in response:
        choice = part.choices[0]

        if choice.finish_reason == 'stop':
            await assistant_response.send()
        else:
            token = choice.delta.content

            match token:
                case '<think>':
                    await think(response)
                case _:
                    await assistant_response.stream_token(token)
