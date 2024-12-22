# src/open_swarm_mcp/modes/rest_mode.py

from typing import Any, Dict
from swarm import Agent, Swarm
from open_swarm_mcp.utils.logger import setup_logger
from open_swarm_mcp.utils.color_utils import color_text

logger = setup_logger(__name__)

async def run_rest_mode(agent: Agent):
    """
    REST API mode for Open Swarm MCP.
    
    Args:
        agent (Agent): Swarm agent to handle REST API requests.
    """
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from pydantic import BaseModel
        import uvicorn

        app = FastAPI(title="Open Swarm MCP REST API")

        # Configure CORS if needed
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        class Query(BaseModel):
            query: str

        @app.post("/query")
        async def handle_query(query: Query):
            response = await Swarm().run(
                agent=agent,
                messages=[{"role": "user", "content": query.query}],
                stream=False,
            )
            result = next(
                (message.get("content") for message in response.messages if message["role"] == "assistant"),
                "No response."
            )
            return {"response": result}

        logger.info("Starting REST API server on http://0.0.0.0:8000")
        print(color_text("Starting REST API server on http://0.0.0.0:8000", "cyan"))
        uvicorn.run(app, host="0.0.0.0", port=8000)

    except ImportError as e:
        logger.error(f"Failed to import REST mode dependencies: {e}")
        print(f"Failed to import REST mode dependencies: {e}")
    except Exception as e:
        logger.error(f"Error running REST mode: {e}")
        print(f"Error running REST mode: {e}")
