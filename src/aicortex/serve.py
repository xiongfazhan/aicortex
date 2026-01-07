"""HTTP server for LLM API.

Corresponds to src/serve.rs in the Rust implementation.
"""

import asyncio
from contextlib import asynccontextmanager
from ipaddress import ip_address, IPv4Address, IPv6Address
from typing import Any, Optional

try:
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import JSONResponse, StreamingResponse, HTMLResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

try:
    from .config import Config
    from .client import Model, Message, MessageRole, ChatCompletionsData
except ImportError:
    Config = None
    Model = None
    Message = None
    MessageRole = None
    ChatCompletionsData = None


DEFAULT_MODEL_NAME = "default"


class Server:
    """LLM API server.

    Provides OpenAI-compatible API endpoints for the configured models.
    """

    def __init__(self, config: Any):
        """Initialize the server.

        Args:
            config: Global configuration
        """
        self.config = config
        self.models: list[dict] = []
        self.roles: list[Any] = []
        self.rags: list[str] = []
        self._setup()

    def _setup(self) -> None:
        """Setup server data."""
        if Config:
            # Load models
            all_models = Config.list_all_models(self.config)
            default_model = self.config.current_model()

            # Add default model
            default_data = default_model.data.copy() if hasattr(default_model, "data") else {}
            default_data["id"] = DEFAULT_MODEL_NAME
            default_data["object"] = "model"
            default_data["owned_by"] = default_model.client_name
            self.models.append(default_data)

            # Add other models
            for model in all_models:
                model_data = model.data.copy() if hasattr(model, "data") else {}
                model_data["id"] = model.id()
                model_data["object"] = "model"
                model_data["owned_by"] = model.client_name
                self.models.append(model_data)

            # Load roles and RAGs
            self.roles = Config.all_roles() if hasattr(Config, "all_roles") else []
            self.rags = Config.list_rags() if hasattr(Config, "list_rags") else []


async def run(config: Any, addr: Optional[str] = None) -> None:
    """Run the HTTP server.

    Args:
        config: Global configuration
        addr: Address to bind to (host:port or just port)
    """
    if not FASTAPI_AVAILABLE:
        print("Error: FastAPI and uvicorn are required for server mode")
        print("Install with: pip install fastapi uvicorn")
        return

    # Parse address
    bind_addr = _parse_address(addr, config)

    # Create app
    app = _create_app(config)

    # Print endpoints
    print(f"Chat Completions API: http://{bind_addr}/v1/chat/completions")
    print(f"Models API:            http://{bind_addr}/v1/models")
    print(f"Embeddings API:         http://{bind_addr}/v1/embeddings")
    print(f"LLM Playground:         http://{bind_addr}/playground")
    print(f"LLM Arena:              http://{bind_addr}/arena?num=2")

    # Run server
    config = uvicorn.Config(
        app=app,
        host=bind_addr.split(":")[0] if ":" in bind_addr else "127.0.0.1",
        port=int(bind_addr.split(":")[1]) if ":" in bind_addr else int(bind_addr),
        log_level="info",
    )

    server = uvicorn.Server(config)
    await server.serve()


def _parse_address(addr: Optional[str], config: Any) -> str:
    """Parse bind address.

    Args:
        addr: Address string
        config: Global configuration

    Returns:
            Formatted address (host:port)
    """
    if addr:
        try:
            # Just a port number
            port = int(addr)
            return f"127.0.0.1:{port}"
        except ValueError:
            pass

        try:
            # IP address only
            ip = ip_address(addr)
            return f"{addr}:8000"
        except ValueError:
            pass

        # Full host:port or just a string
        if ":" in addr:
            host, port = addr.rsplit(":", 1)
            try:
                int(port)
                return addr
            except ValueError:
                pass

        return addr

    # Use config default
    if config and hasattr(config, "serve_addr"):
        return config.serve_addr()

    return "127.0.0.1:8000"


def _create_app(config: Any) -> FastAPI:
    """Create FastAPI application.

    Args:
        config: Global configuration

    Returns:
        FastAPI application
    """
    app = FastAPI(
        title="AIChat",
        description="All-in-one LLM CLI Tool",
        version="0.1.0",
    )

    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup server
    server = Server(config)

    @app.on_event("startup")
    async def startup():
        """Startup handler."""
        pass

    @app.get("/")
    async def root():
        """Root endpoint."""
        return {
            "name": "AIChat",
            "version": "0.1.0",
            "description": "All-in-one LLM CLI Tool",
        }

    @app.get("/v1/models")
    async def list_models():
        """List available models."""
        return {"object": "list", "data": server.models}

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        """Chat completions endpoint (OpenAI-compatible)."""
        body = await request.json()

        model_id = body.get("model", DEFAULT_MODEL_NAME)
        messages = body.get("messages", [])
        stream = body.get("stream", False)
        temperature = body.get("temperature")
        top_p = body.get("top_p")

        # Convert to internal format
        if config:
            config.set_model(model_id)

        # Build messages
        internal_messages = []
        for msg in messages:
            role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
            content = msg.get("content", "")
            if Message:
                internal_messages.append(Message.new(role, content))

        if stream:
            return StreamingResponse(
                _stream_chat_completions(config, internal_messages, temperature, top_p),
                media_type="text/event-stream",
            )
        else:
            response = await _chat_completions_internal(
                config, internal_messages, temperature, top_p
            )
            return JSONResponse(content=response)

    @app.post("/v1/embeddings")
    async def embeddings(request: Request):
        """Embeddings endpoint."""
        body = await request.json()

        model_id = body.get("model", DEFAULT_MODEL_NAME)
        input_texts = body.get("input", [])

        if isinstance(input_texts, str):
            input_texts = [input_texts]

        # This would need actual embedding model support
        return {
            "object": "list",
            "data": [
                {
                    "object": "embedding",
                    "embedding": [0.0] * 1536,  # Placeholder
                    "index": i,
                }
                for i in range(len(input_texts))
            ],
        }

    @app.get("/playground")
    async def playground():
        """LLM playground interface."""
        html = _get_playground_html()
        return HTMLResponse(content=html)

    @app.get("/arena")
    async def arena(num: int = 2):
        """LLM arena for comparing models."""
        html = _get_arena_html()
        return HTMLResponse(content=html)

    @app.options("/{path:path}")
    async def options(path: str):
        """Handle OPTIONS requests for CORS."""
        return Response(status_code=200)

    return app


async def _stream_chat_completions(
    config: Any,
    messages: list[Any],
    temperature: Optional[float],
    top_p: Optional[float],
):
    """Stream chat completions.

    Args:
        config: Configuration
        messages: Messages
        temperature: Temperature
        top_p: Top P

    Yields:
        SSE chunks
    """
    # This is a placeholder - would need actual LLM integration
    chunk = {
        "id": "chatcmpl-123",
        "object": "chat.completion.chunk",
        "created": 1234567890,
        "model": "gpt-3.5-turbo",
        "choices": [
            {
                "index": 0,
                "delta": {"content": "Hello"},
                "finish_reason": None,
            }
        ],
    }

    import json

    yield f"data: {json.dumps(chunk)}\n\n"
    yield "data: [DONE]\n\n"


async def _chat_completions_internal(
    config: Any,
    messages: list[Any],
    temperature: Optional[float],
    top_p: Optional[float],
) -> dict:
    """Internal chat completions implementation.

    Args:
        config: Configuration
        messages: Messages
        temperature: Temperature
        top_p: Top P

    Returns:
        Response dictionary
    """
    # This is a placeholder - would need actual LLM integration
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "gpt-3.5-turbo",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Hello! This is a placeholder response.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 9,
            "total_tokens": 19,
        },
    }


def _get_playground_html() -> str:
    """Get playground HTML.

    Returns:
        HTML content
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AIChat Playground</title>
    <style>
        body { font-family: system-ui; max-width: 800px; margin: 0 auto; padding: 20px; }
        textarea { width: 100%; min-height: 200px; font-family: monospace; }
        button { padding: 10px 20px; margin: 10px 0; }
        #response { white-space: pre-wrap; border: 1px solid #ccc; padding: 10px; min-height: 100px; }
    </style>
</head>
<body>
    <h1>AIChat Playground</h1>
    <textarea id="prompt" placeholder="Enter your prompt..."></textarea>
    <button onclick="send()">Send</button>
    <div id="response"></div>
    <script>
        async function send() {
            const prompt = document.getElementById('prompt').value;
            const response = await fetch('/v1/chat/completions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: 'default',
                    messages: [{ role: 'user', content: prompt }]
                })
            });
            const data = await response.json();
            document.getElementById('response').textContent =
                data.choices[0].message.content;
        }
    </script>
</body>
</html>
"""


def _get_arena_html() -> str:
    """Get arena HTML.

    Returns:
        HTML content
    """
    return """
<!DOCTYPE html>
<html>
<head>
    <title>AIChat Arena</title>
    <style>
        body { font-family: system-ui; max-width: 1200px; margin: 0 auto; padding: 20px; }
        .models { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        textarea { width: 100%; min-height: 100px; font-family: monospace; }
        .response { white-space: pre-wrap; border: 1px solid #ccc; padding: 10px; min-height: 150px; }
        button { padding: 10px 20px; margin: 10px 0; }
    </style>
</head>
<body>
    <h1>AIChat Arena</h1>
    <textarea id="prompt" placeholder="Enter your prompt..."></textarea>
    <button onclick="compare()">Compare Models</button>
    <div class="models">
        <div>
            <h3>Model 1</h3>
            <div id="response1" class="response"></div>
        </div>
        <div>
            <h3>Model 2</h3>
            <div id="response2" class="response"></div>
        </div>
    </div>
    <script>
        async function compare() {
            const prompt = document.getElementById('prompt').value;
            // Placeholder - would fetch from multiple models
            document.getElementById('response1').textContent = 'Model 1 response';
            document.getElementById('response2').textContent = 'Model 2 response';
        }
    </script>
</body>
</html>
"""


__all__ = ["Server", "run"]
