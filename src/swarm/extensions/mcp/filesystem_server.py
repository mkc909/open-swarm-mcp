#!/usr/bin/env python3
import os
import json
import sys
import asyncio
from typing import Dict, List, Optional, Any

class FilesystemServer:
    def __init__(self, allowed_paths: List[str]):
        self.allowed_paths = allowed_paths
        self.methods = {
            "initialize": self.initialize,
            "tools/list": self.list_tools,
            "tools/call": self.call_tool
        }
        self.tools = {
            "list_directory": self.list_directory,
            "read_file": self.read_file,
            "write_file": self.write_file
        }

    async def initialize(self, params: Dict) -> Dict:
        return {
            "server_info": {
                "name": "filesystem-server",
                "version": "1.0.0"
            },
            "capabilities": {}
        }

    async def list_tools(self, params: Dict) -> Dict:
        return {
            "tools": [
                {
                    "name": "list_directory",
                    "description": "List contents of a directory",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Directory path to list"
                            }
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "read_file",
                    "description": "Read contents of a file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to read"
                            }
                        },
                        "required": ["path"]
                    }
                },
                {
                    "name": "write_file",
                    "description": "Write contents to a file",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "File path to write"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            ]
        }

    async def call_tool(self, params: Dict) -> Dict:
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return {
                "isError": True,
                "error": f"Unknown tool: {tool_name}"
            }

        try:
            result = await self.tools[tool_name](arguments)
            if "error" in result:
                return {
                    "isError": True,
                    "error": result["error"]
                }
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result)
                    }
                ]
            }
        except Exception as e:
            return {
                "isError": True,
                "error": str(e)
            }

    def _is_path_allowed(self, path: str) -> bool:
        path = os.path.abspath(path)
        return any(path.startswith(allowed) for allowed in self.allowed_paths)

    async def list_directory(self, params: Dict) -> Dict:
        path = params.get("path")
        if not path or not self._is_path_allowed(path):
            return {"error": "Invalid or unauthorized path"}
        
        try:
            entries = os.listdir(path)
            return {
                "entries": [
                    {
                        "name": entry,
                        "type": "directory" if os.path.isdir(os.path.join(path, entry)) else "file"
                    }
                    for entry in entries
                ]
            }
        except Exception as e:
            return {"error": str(e)}

    async def read_file(self, params: Dict) -> Dict:
        path = params.get("path")
        if not path or not self._is_path_allowed(path):
            return {"error": "Invalid or unauthorized path"}
        
        try:
            with open(path, 'r') as f:
                return {"content": f.read()}
        except Exception as e:
            return {"error": str(e)}

    async def write_file(self, params: Dict) -> Dict:
        path = params.get("path")
        content = params.get("content")
        if not path or not self._is_path_allowed(path) or content is None:
            return {"error": "Invalid parameters"}
        
        try:
            with open(path, 'w') as f:
                f.write(content)
            return {"status": "success"}
        except Exception as e:
            return {"error": str(e)}

    async def handle_request(self, request: Dict) -> Dict:
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")
        
        if method not in self.methods:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        try:
            result = await self.methods[method](params)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32000,
                    "message": str(e)
                }
            }

    async def run(self) -> None:
        """Run the server's main loop, processing JSON-RPC requests from stdin."""
        while True:
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break
                    
                request = json.loads(line)
                response = await self.handle_request(request)
                print(json.dumps(response), flush=True)
                
            except Exception as e:
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": f"Parse error: {str(e)}"
                    }
                }), flush=True)

if __name__ == "__main__":
    allowed_paths = [os.path.abspath(p) for p in sys.argv[1:]]
    server = FilesystemServer(allowed_paths)
    asyncio.run(server.run())
