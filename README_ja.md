# Bedrock Chat with MCP tool

これは、Streamlit で構築され、MCP (Model Context Protocol) ツールと統合されたチャット アプリケーションです。

## 概要

Bedrock Chat with MCP ツールは、Streamlit で構築されたチャット アプリケーションで、MCP (Model Context Protocol) ツールと統合されています。

このアプリケーションは、Langchain と Bedrock を使ってチャットモデルを作成し、`config.json` で指定されたモデルを Langchain の `init_chat_model` 関数のパラメータとして使用します([https://python.langchain.com/docs/how_to/chat_models_universal_init/](https://python.langchain.com/docs/how_to/chat_models_universal_init/))。`mcp_config.json` で定義された MCP (Model Context Protocol) サーバーと対話し、さまざまなツールにアクセスします。MCP は、アプリケーションが LLMにコンテキストを提供する方法を標準化するオープンプロトコルです ([https://modelcontextprotocol.io/](https://modelcontextprotocol.io/))。チャット履歴は YAML ファイルに保存されます。`util.py` モジュールは、`MessageProcessor` とそのサブクラスを定義し、さまざまなモデルを使用してメッセージの処理を処理します。

`config.json` ファイルでは、利用する LLM モデルやチャット履歴ファイルの保存場所などを設定できます。
`mcp_config.json` ファイルには、MCP サーバーの設定を記述します。

Streamlit のサイドバーでは、以下の設定を行うことができます。
- LLMモデルの選択
- チャット履歴ディレクトリの変更
- MCP 設定ファイルの変更
- 過去のチャット履歴の選択

## 特徴

- Streamlitを使用したチャットインターフェース
- MCP ツールとの統合
- チャットモデルにLangchainとBedrockを使用
- `config.json`でLLMモデルなどを設定可能
- MCPツール連携
- ラングチェーンとBedrockを利用
- MCP サーバー設定を `mcp_config.json` から読み込みます
- チャット履歴をYAML形式で保存
- Streamlit サイドバーから設定変更可能

## セットアップ

1. 依存関係をインストールします:

    ```bash
    pip install streamlit langchain langchain-aws langchain_mcp_adapters
    ```

2. `mcp_config.json` で MCP サーバーを構成します。

3. アプリケーションを実行します。 

    ```bash
    streamlit run src/main.py
    ```

## 設定

`config.json` ファイルで、LLMモデルなどを設定します。

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

`mcp_config.json` ファイルには、MCP サーバーの設定を記載します。

`transport`が必須ですので注意してください。

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

## 使い方

Streamlit アプリケーションを実行するには、以下のコマンドを実行します。

```bash
streamlit run src/main.py
```

アプリケーションが起動したら、チャット入力ボックスにメッセージを入力します。
送信後、チャットモデルと MCP ツールが応答を生成します。

サイドバーでは、LLM モデル、チャット履歴ディレクトリ、MCP config ファイルを設定できます。
過去のチャット履歴を選択して、会話を再開することも可能です。

## 注意事項

- MCP サーバーの設定を `mcp_config.json` に記述してください。
- Bedrock を利用するには、AWS アカウントが必要です。
- チャット履歴は YAML ファイルで保存されます。
- `config.json` と `mcp_config.json` は、アプリケーションと同じディレクトリに配置してください。
