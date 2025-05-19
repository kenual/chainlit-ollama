import json
import logging
from typing import Any

import chainlit as cl
from chainlit.cli import run_chainlit
from mcp import ClientSession

from app_helper import MODEL_ID, append_message_to_session_history, initialize_session_chat_settings, prompt_to_fill_template, update_session_chat_settings
from llm_service import chat_messages_send_response
from template_utils import list_templates

logger = logging.getLogger(__name__)


@cl.on_mcp_connect
async def on_mcp_connect(connection: Any, session: ClientSession):
    # Called when an MCP connection is established
    # npx @playwright/mcp@latest

    name = connection.name
    result = await session.list_tools()

    attributes = vars(connection)
    connection_dict = {k: v for k, v in attributes.items() if not k.startswith(
        '__') and not callable(v) and k != 'name'}
    logger.info(f"Connected to {name}: {connection_dict}")

    tools = [{
        "name": t.name,
        "description": t.description,
        "input_schema": t.inputSchema,
    } for t in result.tools]

    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = tools
    cl.user_session.set("mcp_tools", mcp_tools)
    logger.info(f"{json.dumps(tools, indent=2)}")


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    # Called when an MCP connection is terminated
    mcp_tools = cl.user_session.get("mcp_tools", {})
    if name in mcp_tools:
        del mcp_tools[name]
        cl.user_session.set("mcp_tools", mcp_tools)

    logger.info(f"Disconnected from MCP: {name}")


@cl.step(type="tool")
async def call_tool(tool_use):
    tool_name = tool_use.name
    tool_input = tool_use.input

    current_step = cl.context.current_step
    current_step.name = tool_name

    # Find appropriate MCP connection for this tool
    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_name = None

    for connection_name, tools in mcp_tools.items():
        if any(tool.get("name") == tool_name for tool in tools):
            mcp_name = connection_name
            break

    if not mcp_name:
        current_step.output = json.dumps(
            {"error": f"Tool {tool_name} not found in any MCP connection"})
        return current_step.output

    # Get the MCP session
    mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)
    if not mcp_session:
        current_step.output = json.dumps(
            {"error": f"MCP {mcp_name} not found in any MCP connection"})
        return current_step.output

    # Call the tool
    try:
        current_step.output = await mcp_session.call_tool(tool_name, tool_input)
    except Exception as e:
        current_step.output = json.dumps({"error": str(e)})

    return current_step.output


@cl.on_chat_start
async def start():
    await initialize_session_chat_settings()


@cl.on_settings_update
async def handle_settings_update(new_chat_settings: dict[str, Any]):
    await update_session_chat_settings(settings=new_chat_settings)


@cl.on_message
async def on_message(message: cl.Message):
    chat_settings = cl.user_session.get('chat_settings')

    if 'template' in message.content.lower():
        template_message = await prompt_to_fill_template(command=message.content)
        await cl.Message(content=template_message, type="user_message").send()
        messages = append_message_to_session_history(template_message)
    else:
        messages = append_message_to_session_history(message.content, message.elements)

    model = chat_settings[MODEL_ID]
    await chat_messages_send_response(model=model, messages=messages)


@cl.set_starters
async def set_starters():
    return [
        cl.Starter(
            label=template,
            message=f'Use template "{template}" to {template.lower()}',
        ) for template in list_templates()
    ]


def main():
    run_chainlit(__file__)


if __name__ == '__main__':
    main()
