import json
import logging
import os
import time
from typing import Dict, List
import chainlit as cl
import httpx
from any_llm import ProviderName, list_models

from agent_helper import OLLAMA_API_BASE, agent_runner

logger = logging.getLogger(__name__)

SERVICE_MODELS = [
]
if os.getenv('COHERE_API_KEY'):
    SERVICE_MODELS.insert(
        0, {'name': "cohere", 'model': "Cloud Service: command-r-plus-08-2024"})
if os.getenv('TOGETHERAI_API_KEY'):
    SERVICE_MODELS[:0] = [
        {'name': "DeepSeek-R1-Distill-lama-70B-free",
            'model': "Cloud Service: together_ai/deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free"},
        {'name': "Llama-Vision-Free",
            'model': "Cloud Service: together_ai/meta-llama/Llama-Vision-Free"}
    ]


def get_available_models() -> List[dict]:

    # List available Ollama models (https://github.com/ollama/ollama/blob/main/docs/api.md) and Cloud Service models.
    try:
        list_models_response = list_models(provider=ProviderName.OLLAMA)
        return list_models_response['models'] + SERVICE_MODELS

    except httpx.ConnectError as error:
        logger.error(f"Ollama server connect error: {error}")
        return SERVICE_MODELS


async def chat_messages_send_response(model: str, messages: List[Dict[str, str]]) -> None:
    any_llm_model = None
    if 'Cloud Service: ' in model:
        if 'command-r-plus' in model or "together_ai" in model:
            any_llm_model = model.split("Cloud Service: ")[1]

    # Send chat messages to Ollama and stream the response back to the client.
    translation_table = str.maketrans({'.': '_', ':': '#'})

    if not any_llm_model:
        # Ollama settings
        any_llm_model = f"ollama_chat/{model}"
        any_llm_api_base = OLLAMA_API_BASE
    else:
        # Cloud Service settings
        any_llm_api_base = None

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
        api_base=any_llm_api_base,
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
