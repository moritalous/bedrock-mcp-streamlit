from openinference.instrumentation.langchain import (
    LangChainInstrumentor,
)
from phoenix.otel import register

tracer_provider = register(
    project_name="bedrock-mcp-streamlit",
    endpoint="http://localhost:6006/v1/traces",
)

LangChainInstrumentor().instrument(tracer_provider=tracer_provider)
