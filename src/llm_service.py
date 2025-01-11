import json
import logging
from typing import Dict, List, Optional
import chainlit as cl
import httpx
import litellm


logger = logging.getLogger(__name__)

OLLAMA_API_BASE = "http://localhost:11434"

SERVICE_MODELS = [
    {'name': "claude-3-haiku", 'model': "Cloud Service: claude-3-haiku-20240307"},
    {'name': "gpt-4o-mini", 'model': "Cloud Service: gpt-4o-mini"},
    {'name': "llama-3.1-70b",
        'model': "Cloud Service: meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo"},
    {'name': "mixtral-8x7b", 'model': "Cloud Service: mistralai/Mixtral-8x7B-Instruct-v0.1"}
]
SERVICE_CHAT_CONTINUATION_HEADER_KEY = 'x-vqd-4'
CHAT_SESSION_HEADERS = 'session_http_headers'

def list_models() -> List[dict]:

    # List available Ollama models (https://github.com/ollama/ollama/blob/main/docs/api.md) and Cloud Service models.
    try:
        response = httpx.get(url=f'{OLLAMA_API_BASE}/api/tags').json()
        return response['models'] + SERVICE_MODELS

    except httpx.ConnectError as error:
        logger.error(f"Ollama server connect error: {error}")
        return SERVICE_MODELS


async def llm_completion(model: str, messages: List[Dict[str, str]],
                         api_base: Optional[str] = OLLAMA_API_BASE,
                         stream: Optional[bool] = True) -> str:
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        api_base=api_base,
        stream=stream
    )
    return response


async def chat_messages_send_response(model: str, messages: List[Dict[str, str]]) -> None:
    if 'Cloud Service: ' in model:
        await service_chat_messages_send_response(model=model, messages=messages)
        return
    
    # Send chat messages to Ollama and stream the response back to the client.
    translation_table = str.maketrans({'.': '_', ':': '#'})
    assistant_response = cl.Message(
        content='', author=model.translate(translation_table))

    response = await llm_completion(
        model=f"ollama_chat/{model}", 
        messages=messages,
        api_base=OLLAMA_API_BASE,
        stream=True
    )
    async for part in response:
        choice = part['choices'][0]
        if choice['finish_reason'] == 'stop':
            await assistant_response.send()
        else:
            await assistant_response.stream_token(part['choices'][0]['delta']['content'])


def get_continuation_headers(response: httpx.Response) -> dict:
    return {SERVICE_CHAT_CONTINUATION_HEADER_KEY:
            response.headers.get(SERVICE_CHAT_CONTINUATION_HEADER_KEY, '')}


async def service_chat_messages_send_response(model: str, messages: List[Dict[str, str]]) -> None:
    model = model.rsplit(sep=' ', maxsplit=1)[1] # remove cloud service prefix

    translation_table = str.maketrans({'.': '_', ':': '#'})
    assistant_response = cl.Message(
        content='', author=model.translate(translation_table))

    headers = cl.user_session.get(CHAT_SESSION_HEADERS)
    logging.info(f"Use continuation headers: {headers}")
    if headers is None:
        response = httpx.get(url='https://duckduckgo.com/duckchat/v1/status',
                             headers={'x-vqd-accept': '1'}
                             )
        headers = get_continuation_headers(response)

    client = httpx.AsyncClient()
    part = {
        "model": model,
        "messages": messages
    }
    async with client.stream(method='POST',
                             url='https://duckduckgo.com/duckchat/v1/chat',
                             headers=headers,
                             json=part) as response:
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                data = line[5:].strip()
                if not '[DONE]' in data:
                    part = json.loads(data)
                    if 'message' in part:
                        await assistant_response.stream_token(part['message'])
                else:
                    await assistant_response.send()
                    logger.info(data)

        headers = get_continuation_headers(response)
        cl.user_session.set(CHAT_SESSION_HEADERS, headers)
        logging.info(f"Set continuation headers: {headers}")