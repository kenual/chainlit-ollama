import pytest

from agent_helper import llm_completion
from any_llm import ProviderName

@pytest.mark.asyncio
async def test_llm_completion_live_no_mock_stream_gpt_oss_20b():
    # Arrange
    model = "gpt-oss:20b"
    messages = [{"role": "user", "content": "hello"}]
    provider = ProviderName.OLLAMA
    stream = True

    # Act
    response_iter = await llm_completion(
        model=model,
        messages=messages,
        provider=provider,
        stream=stream
    )

    # Assert
    assert hasattr(response_iter, "__aiter__"), "Response should be an async iterator"
    chunks = []
    async for chunk in response_iter:
        chunks.append(chunk)
    assert len(chunks) > 0, "Should receive at least one chunk"