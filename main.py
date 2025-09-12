import logging

from mcp.server.fastmcp import FastMCP
from tools.context_tools import register_tools as register_context_tools
from tools.pod_tools import register_tools as register_pod_tools

server = FastMCP("kompass")

register_context_tools(server)
register_pod_tools(server)
        
if __name__ == "__main__":
    logging.info("🚀 Kompass Server started!")
    try:
        server.run(transport="stdio")
    except KeyboardInterrupt:
        logging.error("🛑 Kompass Server interrupted (KeyboardInterrupt)")
    except Exception as e:
        logging.error(f"💥 Kompass Server crashed: {e}")