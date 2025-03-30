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
                            tool_msg = ToolMessage(
                                str(e), tool_call_id=tool_call["id"], status="error"
                            )

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


async def generate_system_prompt(
    model_provider, model, mcp_config_file="mcp_config.json"
):
    with open(mcp_config_file, "r") as f:
        config = json.load(f)

    async with MultiServerMCPClient(config["mcpServers"]) as mcp_client:
        tools = mcp_client.get_tools()

    tool_definition = [
        {"name": tool.name, "description": tool.description, "args": tool.args}
        for tool in tools
    ]

    chat_model = init_chat_model(model_provider=model_provider, model=model)

    prompt = f"""
    You are an expert in generative AI, particularly large language models.  
    The user is struggling with creating appropriate prompts. Do your best to help them.  

    **User's concern:**  
        They are building an application that calls external tools, but the tools are not being invoked as expected.
        For example, when a user inputs, *"Tell me how to make curry,"* the AI attempts to answer using only its built-in capabilities. However, the expected behavior is for the AI to use the web search tool before responding.
        When the user explicitly inputs, *"Search the web for how to make curry and tell me,"* the AI behaves as expected. But the goal is for the AI to determine the appropriate tool to call even when the user does not explicitly specify it.
        
        (The application is a general-purpose AI chatbot, so the questions will not be limited to recipes but will cover a wide range of topics.)

        The following tools are defined:  

        <tool_definition>
        {json.dumps(tool_definition, indent=1, ensure_ascii=False)}
        </tool_definition>

        Generate a **system prompt** that ensures the tools are invoked appropriately as expected.

    Wrap the system prompt with `<SYSTEM_PROMPT></SYSTEM_PROMPT>` tags.  
        
    Do you understand the user's concern?  
    Think step by step before responding.
    """.strip()

    response = chat_model.invoke(prompt)

    content = response.content

    return content
