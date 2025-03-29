import json

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_mcp_adapters.client import MultiServerMCPClient

from prompts import SYSTEM_PROMPT


class MessageProcessor:
    def __init__(
        self,
        model_provider,
        model,
        mcp_config_file="mcp_config.json",
    ):
        self.model_provider = model_provider
        self.model = model
        self.mcp_config_file = mcp_config_file

    async def process_message(self, prompt, messages, container):
        raise NotImplementedError("Subclasses must implement process_message")


class BedrockProcessor(MessageProcessor):
    async def process_message(self, prompt, messages, container):
        chat_model = init_chat_model(
            model_provider=self.model_provider,
            model=self.model,
        )

        # Read MCP tool definitions
        with open(self.mcp_config_file, "r") as f:
            config = json.load(f)

        # Generate MCP client
        async with MultiServerMCPClient(config["mcpServers"]) as mcp_client:
            tools = mcp_client.get_tools()
            chain = chat_model.bind_tools(tools)

            messages.append(HumanMessage(prompt))
            # Loop until tool_calls disappear
            while True:
                gathered = None
                first = True
                out = {}
                async for chunk in chain.astream(
                    [SystemMessage(SYSTEM_PROMPT)] + messages
                ):
                    if first:
                        gathered = chunk
                        first = False
                    else:
                        gathered = gathered + chunk

                    # Assuming gathered.content is a list
                    for content in gathered.content:
                        index = str(content["index"])

                        if content["type"] == "text":
                            if index not in out:
                                out[index] = container.chat_message("assistant").empty()

                            out[index].write(content["text"])

                # Convert input from string to JSON to break through Converse API validation check
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

                        container.expander("Tool Result", expanded=False).write(
                            tool_msg
                        )

                        messages.append(tool_msg)
                else:
                    break

        return messages


class GeminiProcessor(MessageProcessor):
    async def process_message(self, prompt, messages, container):
        chat_model = init_chat_model(
            model_provider=self.model_provider,
            model=self.model,
        )

        # Read MCP tool definitions
        with open(self.mcp_config_file, "r") as f:
            config = json.load(f)

        # Generate MCP client
        async with MultiServerMCPClient(config["mcpServers"]) as mcp_client:
            tools = mcp_client.get_tools()
            chain = chat_model.bind_tools(tools)

            messages.append(HumanMessage(prompt))
            # Loop until tool_calls disappear
            while True:
                gathered = None
                first = True
                out = {}
                async for chunk in chain.astream(
                    [SystemMessage(SYSTEM_PROMPT)] + messages
                ):
                    if first:
                        gathered = chunk
                        first = False
                    else:
                        gathered = gathered + chunk

                    # ModelProviderB specific processing

                    index = str(gathered.id)
                    if index not in out:
                        out[index] = container.chat_message("assistant").empty()
                    out[index].write(gathered.content)

                # たまにAIが無言（空白）で返答してくるのを制御
                if isinstance(gathered.content, str) and gathered.content == "":
                    gathered.content = "{{empty}}"
                elif isinstance(gathered.content, list):
                    for n, _ in enumerate(gathered.content):
                        if gathered.content[n]["content"] == "":
                            gathered.content[n]["content"] = "{{empty}}"

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

                        container.expander("Tool Result", expanded=False).write(
                            tool_msg
                        )

                        messages.append(tool_msg)
                else:
                    break

        return messages


class GrokProcessor(MessageProcessor):
    async def process_message(self, prompt, messages, container):
        chat_model = init_chat_model(
            model_provider=self.model_provider,
            model=self.model,
        )

        # Read MCP tool definitions
        with open(self.mcp_config_file, "r") as f:
            config = json.load(f)

        # Generate MCP client
        async with MultiServerMCPClient(config["mcpServers"]) as mcp_client:
            tools = mcp_client.get_tools()
            chain = chat_model.bind_tools(tools)

            messages.append(HumanMessage(prompt))
            # Loop until tool_calls disappear
            while True:
                gathered = None
                first = True
                out = {}
                async for chunk in chain.astream(
                    [SystemMessage(SYSTEM_PROMPT)] + messages
                ):
                    if first:
                        gathered = chunk
                        first = False
                    else:
                        gathered = gathered + chunk

                    index = "0"
                    if index not in out:
                        out[index] = container.chat_message("assistant").empty()

                    out[index].write(gathered.content)

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

                        container.expander("Tool Result", expanded=False).write(
                            tool_msg
                        )

                        messages.append(tool_msg)
                else:
                    break

        return messages


class MessageProcessorFactory:
    def __init__(self, mcp_config_file="mcp_config.json"):
        self.mcp_config_file = mcp_config_file

    def create_processor(self, model_provider, model):
        if model_provider == "bedrock":
            return BedrockProcessor(model_provider, model, self.mcp_config_file)
        elif model_provider == "google_genai":
            return GeminiProcessor(model_provider, model, self.mcp_config_file)
        elif model_provider == "xai":
            return GrokProcessor(model_provider, model, self.mcp_config_file)
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")
