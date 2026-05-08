"""
Main entry point for the Open-Swarm MCP server.

This module provides the entry point for running MCP servers. It handles:
- Command line argument parsing
- Server configuration
- Logging setup
- Graceful shutdown
"""

import os
import sys
import asyncio
import logging
import argparse
import signal
from typing import Optional, List
from swarm.settings import DEBUG
from swarm.extensions.mcp.filesystem_server import FilesystemServer

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Open-Swarm MCP Server")
    parser.add_argument(
        "--server-type",
        choices=["filesystem"],
        default="filesystem",
        help="Type of MCP server to run"
    )
    parser.add_argument(
        "--allowed-paths",
        nargs="+",
        help="Allowed paths for filesystem operations (required for filesystem server)",
    )
    args = parser.parse_args()

    # Validate required arguments
    if args.server_type == "filesystem" and not args.allowed_paths:
        parser.error("--allowed-paths is required for filesystem server")

    return args

async def run_server(server_type: str, allowed_paths: Optional[List[str]] = None) -> None:
    """
    Run the specified MCP server.

    Args:
        server_type: Type of server to run
        allowed_paths: List of allowed paths for filesystem server
    """
    try:
        if server_type == "filesystem":
            if not allowed_paths:
                raise ValueError("allowed_paths required for filesystem server")
            server = FilesystemServer([os.path.abspath(p) for p in allowed_paths])
            logger.info(f"Starting filesystem MCP server with allowed paths: {allowed_paths}")
            
            # Run the server
            try:
                await server.run()
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                loop = asyncio.get_running_loop()
                await shutdown(loop)
        else:
            raise ValueError(f"Unknown server type: {server_type}")
            
    except Exception as e:
        logger.error(f"Error running MCP server: {e}", exc_info=True)
        raise

async def shutdown(loop: asyncio.AbstractEventLoop) -> None:
    """
    Gracefully shutdown the server.
    
    Args:
        loop: The event loop to shutdown
    """
    logger.info("Shutting down MCP server...")
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

def main() -> None:
    """Main entry point."""
    args = parse_args()
    try:
        asyncio.run(run_server(args.server_type, args.allowed_paths))
    except Exception as e:
        if not isinstance(e, KeyboardInterrupt):
            logger.error(f"Fatal error: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    main()
