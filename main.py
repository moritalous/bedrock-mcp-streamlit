import asyncio
import json

import streamlit as st
from langchain_aws import ChatBedrockConverse
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)
from langchain_mcp_adapters.client import MultiServerMCPClient

st.title("Chat app with MCP tool")

# Manage chat history in session
if "messages" not in st.session_state:
    st.session_state.messages = []
messages = st.session_state.messages


async def main():
    # Display chat messages
    for message in messages:
        if isinstance(message, HumanMessage) or isinstance(message, AIMessage):
            with st.chat_message(message.type):
                if isinstance(message.content, str):
                    st.write(message.content)
                elif isinstance(message.content, list):
                    for c in message.content:
                        if "text" in c:
                            st.write(c["text"])

    # Process when input in chat box
    if prompt := st.chat_input():
        with st.chat_message("user"):
            st.write(prompt)

        messages.append(HumanMessage(prompt))

        chat_model = ChatBedrockConverse(
            model="us.amazon.nova-pro-v1:0",
        )

        # Read MCP tool definitions
        with open("mcp_config.json", "r") as f:
            config = json.load(f)

        # Generate MCP client
        async with MultiServerMCPClient(config["mcpServers"]) as mcp_client:
            tools = mcp_client.get_tools()
            chain = chat_model.bind_tools(tools)

            # Loop until tool_calls disappear
            while True:
                gathered = None
                first = True
                out = {}
                async for chunk in chain.astream(messages):
                    if first:
                        gathered = chunk
                        first = False
                    else:
                        gathered = gathered + chunk

                    for content in gathered.content:
                        type = content["type"]
                        index = str(content["index"])

                        if type == "text":
                            if index not in out:
                                out[index] = st.chat_message("assistant").empty()

                            out[index].write(content["text"])

                # Convert input from string to JSON to break through Converse API validation check
                if isinstance(gathered.content, str):
                    if gathered.content["type"] == "tool_use":
                        gathered.content["input"] = json.loads(
                            gathered.content["input"]
                        )
                elif isinstance(gathered.content, list):
                    for n, _ in enumerate(gathered.content):
                        if gathered.content[n]["type"] == "tool_use":
                            gathered.content[n]["input"] = json.loads(
                                gathered.content[n]["input"]
                            )

                messages.append(AIMessage(gathered.content))

                # Execute tool
                if gathered.tool_calls:
                    for tool_call in gathered.tool_calls:
                        selected_tool = {tool.name: tool for tool in tools}[
                            tool_call["name"].lower()
                        ]
                        tool_msg = await selected_tool.ainvoke(tool_call)

                        with st.expander("Tool Result", expanded=False):
                            st.write(tool_msg)

                        messages.append(tool_msg)
                else:
                    break


asyncio.run(main())
