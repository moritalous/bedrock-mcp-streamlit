import json

from langchain.chat_models import init_chat_model
from langchain_core.messages import (
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

    async def _process_chunk(self, chunk, container, out):
        raise NotImplementedError("Subclasses must implement _process_chunk")

    async def _post_process_chunk(self, chunk, container, out):
        raise NotImplementedError("Subclasses must implement _process_chunk")

    async def process_message(self, prompt, messages, container):
        chat_model = init_chat_model(
            model_provider=self.model_provider, model=self.model
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

                    await self._process_chunk(gathered, container, out)

                await self._post_process_chunk(gathered, container, out)

                messages.append(gathered)

                # Execute tool
                if gathered.tool_calls:
                    for tool_call in gathered.tool_calls:
                        selected_tool = {tool.name: tool for tool in tools}[
                            tool_call["name"].lower()
                        ]

                        container.expander("Tool Call", expanded=False).write(tool_call)

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


class BedrockProcessor(MessageProcessor):
    async def _process_chunk(self, gathered, container, out):
        for content in gathered.content:
            if content["type"] == "text":
                index = str(content["index"])

                if index not in out:
                    out[index] = container.chat_message("assistant").empty()

                out[index].write(content["text"])

    async def _post_process_chunk(self, gathered, container, out):
        # Convert input from string to JSON to break through Converse API validation check
        for n, _ in enumerate(gathered.content):
            if gathered.content[n]["type"] == "tool_use" and isinstance(
                gathered.content[n]["input"], str
            ):
                gathered.content[n]["input"] = json.loads(gathered.content[n]["input"])


class OpenAIProcessor(MessageProcessor):
    async def _process_chunk(self, gathered, container, out):
        if gathered.content:
            index = str(gathered.id)
            if index not in out:
                out[index] = container.chat_message("assistant").empty()

            out[index].write(gathered.content)

    async def _post_process_chunk(self, gathered, container, out):
        pass


class MessageProcessorFactory:
    def __init__(self, mcp_config_file="mcp_config.json"):
        self.mcp_config_file = mcp_config_file

    def create_processor(self, model_provider, model):
        if model_provider == "bedrock_converse":
            return BedrockProcessor(model_provider, model, self.mcp_config_file)
        elif model_provider in ["openai", "google_genai", "xai"]:
            return OpenAIProcessor(model_provider, model, self.mcp_config_file)
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")
