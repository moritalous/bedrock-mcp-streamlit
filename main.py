import asyncio
import glob
import json
import os
import time
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

load_dotenv()


def select_chat(chat_history_file):
    st.session_state.chat_history_file = chat_history_file


models = {
    "Amazon Nova Micro": {
        "model_provider": "bedrock",
        "model": "us.amazon.nova-micro-v1:0",
    },
    "Amazon Nova Lite": {
        "model_provider": "bedrock",
        "model": "us.amazon.nova-lite-v1:0",
    },
    "Amazon Nova Pro": {
        "model_provider": "bedrock",
        "model": "us.amazon.nova-pro-v1:0",
    },
    "Claude 3.7 Sonnet(Bedrock)": {
        "model_provider": "bedrock",
        "model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    },
    "Gemini 2.5 Pro": {
        "model_provider": "google_genai",
        "model": "gemini-2.5-pro-exp-03-25",
    },
    "Gemini 2.0 Flash": {
        "model_provider": "google_genai",
        "model": "gemini-2.0-flash",
    },
    # Gemini 2.0 Flash Thinking not support tool use.
    # "Gemini 2.0 Flash Thinking": {
    #     "model_provider": "google_genai",
    #     "model": "gemini-2.0-flash-thinking-exp-01-21",
    # },
    "Grok 2": {
        "model_provider": "xai",
        "model": "grok-2-latest",
    },
}
chat_history_dir = "chat_history"
if "chat_history_file" not in st.session_state:
    st.session_state["chat_history_file"] = (
        f"{chat_history_dir}/{int(time.time())}.yaml"
    )
chat_history_file = st.session_state.chat_history_file

st.title("Chat app with MCP tool")

if Path(chat_history_file).exists():
    with open(chat_history_file, mode="rt") as f:
        yaml_msg = yaml.safe_load(f)
        messages: list[BaseMessage] = []
        for m in yaml_msg:
            if m["type"] == "human":
                messages.append(HumanMessage.model_validate(m))
            elif m["type"] == "ai":
                messages.append(AIMessage.model_validate(m))
            elif m["type"] == "tool":
                messages.append(ToolMessage.model_validate(m))

else:
    messages = []


async def main():
    # Display chat messages
    for message in messages:
        if message.type in ["ai", "human"]:
            with st.chat_message(message.type):
                if isinstance(message.content, str):
                    st.write(message.content)
                elif isinstance(message.content, list):
                    for content in message.content:
                        if "text" in content:
                            st.write(content["text"])

    # Process when input in chat box
    if prompt := st.chat_input():
        with st.chat_message("user"):
            st.write(prompt)

        messages.append(HumanMessage(prompt))

        chat_model = init_chat_model(
            model_provider=models[selected_model]["model_provider"],
            model=models[selected_model]["model"],
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

                    if isinstance(gathered.content, str):
                        index = str(gathered.id)
                        if index not in out:
                            out[index] = st.chat_message("assistant").empty()
                        out[index].write(gathered.content)
                    else:
                        for content in gathered.content:
                            index = str(content["index"])
                            if "type" in content:
                                if content["type"] == "text":
                                    if index not in out:
                                        out[index] = st.chat_message(
                                            "assistant"
                                        ).empty()

                                    out[index].write(content["text"])
                            else:
                                if index not in out:
                                    out[index] = st.chat_message("assistant").empty()

                                out[index].write(content["text"])

                # Convert input from string to JSON to break through Converse API validation check
                if isinstance(gathered.content, str):
                    if (
                        "type" in gathered.content
                        and gathered.content["type"] == "tool_use"
                    ):
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
                        try:
                            tool_msg = await selected_tool.ainvoke(tool_call)

                        except Exception as e:
                            tool_msg = ToolMessage(str(e), tool_call_id=tool_call["id"])

                        with st.expander("Tool Result", expanded=False):
                            st.write(tool_msg)

                        messages.append(tool_msg)
                else:
                    break

        with open(chat_history_file, mode="wt") as f:
            yaml.safe_dump([m.model_dump() for m in messages], f, allow_unicode=True)


with st.sidebar:
    selected_model = st.selectbox("LLM", models.keys())
    st.button(
        "New Chat",
        on_click=select_chat,
        args=(f"{int(time.time())}.yaml",),
        use_container_width=True,
        type="primary",
    )

    history_files = glob.glob(os.path.join(chat_history_dir, "*.yaml"))

    for h in sorted(history_files, reverse=True):
        st.button(h, on_click=select_chat, args=(h,), use_container_width=True)


asyncio.run(main())
