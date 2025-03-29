# Bedrock Chat with MCP tool

This is a chat application built with Streamlit that integrates with MCP (Model Context Protocol) tools.

## Overview

The application uses Langchain and Bedrock to create a chat model, using the model specified in `config.json` as a parameter for Langchain's `init_chat_model` function (see [https://python.langchain.com/docs/how_to/chat_models_universal_init/](https://python.langchain.com/docs/how_to/chat_models_universal_init/)). It interacts with MCP (Model Context Protocol) servers defined in `mcp_config.json` to access various tools. MCP is an open protocol that standardizes how applications provide context to LLMs (see [https://modelcontextprotocol.io/](https://modelcontextprotocol.io/)). The chat history is saved in YAML files. The `util.py` module defines `MessageProcessor` and its subclasses, which handle the processing of messages using different models.

## Features

- Chat interface using Streamlit
- Integration with MCP tools
- Uses Langchain and Bedrock for chat model
- Reads MCP server configurations from `mcp_config.json`

## Dependencies

- streamlit
- langchain
- langchain-aws
- langchain_mcp_adapters

## Setup

1.  Install the dependencies:

    ```bash
    pip install streamlit langchain langchain-aws langchain_mcp_adapters
    ```

2.  Configure the MCP servers in `mcp_config.json`.

3.  Run the application:

    ```bash
    streamlit run src/main.py
    ```

## Configuration

The `mcp_config.json` file should contain the configuration for the MCP servers.  For example:

```json
{
  "mcpServers": {
    "server1": {
      "command": "...",
      "args": ["..."],
      "env": {
        "API_KEY": "..."
      }
    }
  }
}
```

## Usage

1.  Run the application using `streamlit run src/main.py`.
2.  Enter your message in the chat input.
3.  The application will respond using the chat model and MCP tools.

## Notes

- Make sure to configure the MCP servers correctly in `mcp_config.json` before running the application.
- You need to have access to Bedrock to use this application.
