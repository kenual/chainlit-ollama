import json
import logging
from typing import List, Dict, Optional
import litellm
import chainlit as cl

logger = logging.getLogger(__name__)

OLLAMA_API_BASE = "http://localhost:11434"


async def llm_completion(model: str, messages: List[Dict[str, str]],
                         tools: Optional[List[Dict[str, str]]] = None,
                         api_base: Optional[str] = OLLAMA_API_BASE,
                         stream: Optional[bool] = True) -> str:
    response = await litellm.acompletion(
        model=model,
        messages=messages,
        tools=tools,
        tool_choice="auto",
        api_base=api_base,
        stream=stream
    )
    return response


@cl.step(type="tool")
async def call_tool(name: str, input: str) -> str:
    current_step = cl.context.current_step
    current_step.name = name
    tool_input = json.loads(input)

    # Find appropriate MCP connection for this tool
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_name = None

    for connection_name, tools in mcp_tools.items():
        if any(tool.get("name") == name for tool in tools):
            mcp_name = connection_name
            break

    if not mcp_name:
        current_step.output = json.dumps(
            {"error": f"Tool {name} not found in any MCP connection"})
        return current_step.output

    # Get the MCP session
    mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)
    if not mcp_session:
        current_step.output = json.dumps(
            {"error": f"MCP {mcp_name} not found in any MCP connection"})
        return current_step.output

    # Call the tool
    try:
        current_step.output = await mcp_session.call_tool(name, tool_input)
    except Exception as e:
        current_step.output = json.dumps({"error": str(e)})
    finally:
        await current_step.send()

    return current_step.output


async def agent_runner(model: str, messages: List[Dict[str, str]],
                       tools: Optional[List[Dict[str, str]]] = None,
                       api_base: Optional[str] = OLLAMA_API_BASE,
                       stream: Optional[bool] = True):
    while True:
        response = await llm_completion(
            model=model,
            messages=messages,
            tools=tools,
            api_base=api_base,
            stream=stream
        )

        if isinstance(response, litellm.ModelResponse):
            message = response.choices[0].message

            use_tools = message.get('tool_calls', [])
            if use_tools:
                # Call the tools
                for tool in use_tools:
                    tool_id = tool.get('id', '')
                    tool_function = tool.get('function', {})
                    tool_name = tool_function.get('name', '')
                    tool_arguments = tool_function.get('arguments', {})
                    result = await call_tool(
                        name=tool_name,
                        input=tool_arguments
                    )

                    logger.info(
                        f"{tool_name} {tool_arguments} result: {result}")
                    # Append the tool result to the messages
                    messages.append(message)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "name": tool_name,
                        "content": result
                    })
            else:
                return await llm_completion(
                    model=model,
                    messages=messages,
                    api_base=api_base,
                    stream=True
                )


        else:
            return response
