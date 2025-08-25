import time
from typing import AsyncIterator
import chainlit as cl
from any_llm.types.completion import ChatCompletionChunk


@cl.step(type="llm", name="Thinking")
async def think(llm_response: AsyncIterator[ChatCompletionChunk]) -> None:
    current_step = cl.context.current_step
    start_time = time.time()

    async for part in llm_response:
        choice = part.choices[0]

        token = choice.delta.content
        if token == '</think>':
            elapsed_time = time.time() - start_time
            minutes, seconds = map(round, divmod(elapsed_time, 60))

            duration = f'{seconds} second{"s" if seconds != 1 else ""}'
            if minutes > 0:
                duration = f'{minutes} minute{"s" if minutes != 1 else ""} {duration}'

            current_step.name = f'⚛️ Thought for {duration}'
            await current_step.send()
            return

        else:
            await current_step.stream_token(token)
