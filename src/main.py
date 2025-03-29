import asyncio
import glob
import os
import time
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)

from util import MessageProcessorFactory

load_dotenv()


async def main():
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

    # chat_history_dir = "chat_history"

    def select_chat(chat_history_file):
        st.session_state.chat_history_file = chat_history_file

    with st.sidebar:
        with st.expander(":gear: config", expanded=False):
            selected_model = st.selectbox("LLM", models.keys())
            chat_history_dir = st.text_input("chat_history_dir", value="chat_history")
            mcp_config_file = st.text_input("mcp_config_file", value="mcp_config.json")
        st.button(
            "New Chat",
            on_click=select_chat,
            args=(f"{int(time.time())}.yaml",),
            use_container_width=True,
            type="primary",
        )

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

        message_processor_factory = MessageProcessorFactory(mcp_config_file)
        message_processor = message_processor_factory.create_processor(
            model_provider=models[selected_model]["model_provider"],
            model=models[selected_model]["model"],
        )
        messages = await message_processor.process_message(
            prompt, messages, st.container()
        )

        with open(chat_history_file, mode="wt") as f:
            yaml.safe_dump([m.model_dump() for m in messages], f, allow_unicode=True)

    with st.sidebar:
        history_files = glob.glob(os.path.join(chat_history_dir, "*.yaml"))

        for h in sorted(history_files, reverse=True):
            st.button(h, on_click=select_chat, args=(h,), use_container_width=True)


asyncio.run(main())
