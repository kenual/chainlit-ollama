import pytest

from agent_helper import llm_completion
from any_llm import ProviderName


@pytest.mark.asyncio
async def test_llm_completion_live_no_mock_stream_gpt_oss_20b():
    # Arrange
    model = f"{ProviderName.OLLAMA}:gpt-oss:20b"
    messages = [{"role": "user", "content": "hello"}]
    stream = True

    # Act
    response_iter = await llm_completion(
        model=model,
        messages=messages,
        stream=stream
    )

    # Assert
    assert hasattr(
        response_iter, "__aiter__"), "Response should be an async iterator"
    chunks = []
    async for chunk in response_iter:
        chunks.append(chunk)
    assert len(chunks) > 0, "Should receive at least one chunk"


@pytest.mark.asyncio
async def test_llm_completion_live_tool_use_stream_gpt_oss_20b():
    """
    Live streaming test for gpt-oss:20b with tool-use scenario.
    """
    # Tool definition (external tool format)
    get_stock_price = {
        "type": "function",
        "function": {
            "name": "get_stock_price",
            "description": "Given a stock ticker, returns the current price of the stock",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticker": {"type": "string", "description": "The stock ticker"}
                },
                "required": ["ticker"]
            },
        },
    }
    tools = [get_stock_price]

    # Message that should trigger tool use
    messages = [
        {"role": "user", "content": "Get the stock price of AAPL. Only use provided functions if helpful"}
    ]

    model = f"{ProviderName.OLLAMA}:gpt-oss:20b"
    stream = True

    response_iter = await llm_completion(
        model=model,
        messages=messages,
        stream=stream,
        tools=tools
    )

    assert hasattr(
        response_iter, "__aiter__"), "Response should be an async iterator"
    chunks = []
    tool_calls = []
    async for chunk in response_iter:
        delta = chunk.choices[0].delta
        if delta.reasoning:
            print(delta.reasoning.content, end='')
        else:
            print(delta.content, end='')
        chunks.append(chunk)
        if delta.tool_calls is not None:
            tool_calls = delta.tool_calls
            break
    print()

    assert len(chunks) > 0, "Should receive at least one chunk"
    assert tool_calls is not None, "Should include a tool call in streamed output"
    assert tool_calls[0].function.name == 'get_stock_price', "Wrong function name"
