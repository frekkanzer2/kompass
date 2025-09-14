import logging

from mcp.server.fastmcp import FastMCP
from tools.context_tools import register_tools as register_context_tools
from tools.deployment_tools import register_deployment_tools
from tools.pod_tools import register_tools as register_pod_tools
from tools.namespace_tools import register_tools as register_namespace_tools
from tools.hpa_tools import register_hpa_tools
from tools.configmap_tools import register_configmap_tools

server = FastMCP("kompass")

register_context_tools(server)
register_deployment_tools(server)
register_pod_tools(server)
register_namespace_tools(server)
register_hpa_tools(server)
register_configmap_tools(server)
        
if __name__ == "__main__":
    logging.info("🚀 Kompass Server started!")
    try:
        server.run(transport="stdio")
    except KeyboardInterrupt:
        logging.error("🛑 Kompass Server interrupted (KeyboardInterrupt)")
    except Exception as e:
        logging.error(f"💥 Kompass Server crashed: {e}")