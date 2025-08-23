import logging
import os
import time
from typing import Dict, List
import chainlit as cl
from dotenv import load_dotenv
from any_llm import ProviderName, list_models
from pydantic import BaseModel

from agent_helper import agent_runner

logger = logging.getLogger(__name__)

CLOUD_SERVICE_PREFIX = "Cloud Service "


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
    if os.getenv('COHERE_API_KEY'):
        cloud_service_models += list_provider_models(
            provider=ProviderName.COHERE,
            api_key=os.getenv('COHERE_API_KEY'))
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
        stream=all_tools is None
    )

    think_step = None
    assistant_response = cl.Message(
        content='', author=model.translate(translation_table))
    async for part in response:
        choice = part['choices'][0]
        token = choice['delta']['content']

        if choice['finish_reason'] == 'stop' or not token:
            await assistant_response.send()
        else:
            match token:
                case '<think>':
                    start_time = time.time()
                    think_step = cl.Step(name="⚛️ Thinking", type="llm")
                    continue
                case '</think>':
                    elapsed_time = time.time() - start_time
                    minutes, seconds = map(round, divmod(elapsed_time, 60))

                    duration = f'{seconds} second{"s" if seconds > 0 else ""}'
                    if minutes > 0:
                        duration = f'{minutes} minute{"s" if minutes > 1 else ""} {duration}'

                    think_step.name = f'⚛️ Thought for {duration}'
                    await think_step.send()
                    think_step = None
                    continue

            if think_step:
                await think_step.stream_token(token)
            else:
                await assistant_response.stream_token(token)
