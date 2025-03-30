# Bedrock Chat with MCP tool

This is a chat application built with Streamlit and integrated with the MCP (Model Context Protocol) tool.

## Overview

Bedrock Chat with MCP tool is a chat application built with Streamlit and integrated with the MCP (Model Context Protocol) tool.

This application uses Langchain and Bedrock to create a chat model and uses the model specified in `config.json` as a parameter in Langchain's `init_chat_model` function ([https://python.langchain.com/docs/how_to/chat_models_universal_init/](https://python.langchain.com/docs/how_to/chat_models_universal_init/)). It interacts with the MCP (Model Context Protocol) server defined in `mcp_config.json` and accesses various tools. MCP is an open protocol that standardizes how applications provide context to LLM ([https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)). Chat history is stored in a YAML file. The `util.py` module defines `MessageProcessor` and its subclasses to handle message processing using different models.

The `config.json` file allows you to configure the LLM model to use, where the chat history files are stored, etc.
The `mcp_config.json` file describes the configuration of the MCP server.

In the Streamlit sidebar, you can configure the following:
- Select LLM model
- Change chat history directory
- Change MCP configuration file
- Select past chat history

## Features

- Chat interface using Streamlit
- Integration with MCP tools
- Use Langchain and Bedrock for chat model
- LLM model etc. can be configured in `config.json`
- MCP tool integration
- Use Langchain and Bedrock
- Read MCP server settings from `mcp_config.json`
- Save chat history in YAML format
- Can change settings from Streamlit sidebar

## Setup

1. Install dependencies:

    ```bash
    pip install streamlit langchain langchain-aws langchain_mcp_adapters
    ```

2. Configure MCP server in `mcp_config.json`.

3. Run the application.

    ```bash
    streamlit run src/main.py
    ```

## Configuration

The `config.json` file is where you configure the LLM model and other settings.

```json
{
  "chat_history_dir": "chat_history",
  "mcp_config_file": "mcp_config.json",
  "models": {
    "Claude 3.7 Sonnet": {
      "model_provider": "bedrock_converse",
      "model": "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
    },
    "Amazon Nova Pro": {
      "model_provider": "bedrock_converse",
      "model": "us.amazon.nova-pro-v1:0"
    },
  },
}
```

The `mcp_config.json` file contains the settings for the MCP server.

Please note that `transport` is required.

```json
{
  "mcpServers": {
    "server1": {
      "command": "...",
      "args": ["..."],
      "env": {
        "API_KEY": "..."
      },
      "transport": "..."
    }
  }
}
```

## Usage

To run the Streamlit application, run the following command.

```bash
streamlit run src/main.py
```

Once the application is running, enter a message in the chat input box.
After sending, the chat model and MCP tool will generate a response.

In the sidebar, you can configure the LLM model, chat history directory, and MCP config file.
You can also select past chat history and resume the conversation.

## Notes

- Write the MCP server configuration in `mcp_config.json`.
- To use Bedrock, you need an AWS account.
- Chat history is stored in a YAML file.
- `config.json` and `mcp_config.json` must be in the same directory as your application.