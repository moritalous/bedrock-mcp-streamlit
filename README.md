# Bedrock Chat with MCP tool

This is a chat application built with Streamlit that integrates with MCP (Model Context Protocol) tools.

## Overview

The application uses Langchain and Bedrock to create a chat model and interacts with MCP servers defined in `mcp_config.json` to access various tools.

## Features

- Chat interface using Streamlit
- Integration with MCP tools
- Uses Langchain and Bedrock for chat model
- Reads MCP server configurations from `mcp_config.json`

## Dependencies

- streamlit
- langchain
- langchain_core
- langchain_mcp_adapters
- asyncio
- json

## Setup

1.  Install the dependencies:

    ```bash
    pip install streamlit langchain langchain_core langchain_mcp_adapters
    ```

2.  Configure the MCP servers in `mcp_config.json`.

3.  Run the application:

    ```bash
    streamlit run main.py
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

1.  Run the application using `streamlit run main.py`.
2.  Enter your message in the chat input.
3.  The application will respond using the chat model and MCP tools.

## Notes

- Make sure to configure the MCP servers correctly in `mcp_config.json` before running the application.
- You need to have access to Bedrock to use this application.
