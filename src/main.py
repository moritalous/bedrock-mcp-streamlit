import asyncio
import glob
import json
import os
import time
import trace
from pathlib import Path

import streamlit as st
import yaml
from dotenv import load_dotenv
from langchain_core.messages import (
    AIMessage,
    AIMessageChunk,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)

from util import MessageProcessorFactory

load_dotenv()


@st.dialog("SYSTEM_PROMPT", width="large")
def show_system_prompt(system_prompt):
    st.write("If you like it, please use it by reflecting it in SYSTEM_PROMPT of `prompts.py`.")

    st.markdown(f"""````
        {system_prompt}
        """)


async def main():
    with open("config.json", "r") as f:
        config = json.load(f)

    models = config["models"]

    def select_chat(chat_history_file):
        st.session_state.chat_history_file = chat_history_file

    async def generate_system_prompt():
        from util import generate_system_prompt

        with st.spinner("Generating..."):
            system_prompt = await generate_system_prompt(
                model_provider=models[selected_model]["model_provider"],
                model=models[selected_model]["model"],
                mcp_config_file=mcp_config_file,
            )

            show_system_prompt(system_prompt)

    with st.sidebar:
        with st.expander(":gear: config", expanded=True):
            selected_model = st.selectbox("LLM", models.keys())
            chat_history_dir = st.text_input(
                "chat_history_dir", value=config["chat_history_dir"]
            )
            mcp_config_file = st.text_input(
                "mcp_config_file", value=config["mcp_config_file"]
            )

            if st.button(
                "Generate System Prompt from mcp_config",
            ):
                await generate_system_prompt()

        st.button(
            "New Chat",
            on_click=select_chat,
            args=(f"{chat_history_dir}/{int(time.time())}.yaml",),
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
                elif m["type"] == "AIMessageChunk":
                    messages.append(AIMessageChunk.model_validate(m))
                elif m["type"] == "ai":
                    messages.append(AIMessage.model_validate(m))
                elif m["type"] == "tool":
                    messages.append(ToolMessage.model_validate(m))

    else:
        messages = []

    # Display chat messages
    for message in messages:
        if message.type in ["human", "ai", "AIMessageChunk"]:
            with st.chat_message("human" if message.type == "human" else "assistant"):
                if isinstance(message.content, str) and message.content:
                    st.write(message.content)
                elif isinstance(message.content, list):
                    for content in message.content:
                        if "text" in content and content["text"]:
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

        for h in sorted(history_files, reverse=True)[:20]:  # 最新20件表示
            st.button(h, on_click=select_chat, args=(h,), use_container_width=True)


asyncio.run(main())
