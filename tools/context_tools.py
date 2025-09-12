from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client
from kubernetes import config

def register_tools(server: FastMCP):
    @server.tool()
    def list_contexts() -> List[str]:
        """
        Get all available contexts.
        """
        contexts, _ = config.list_kube_config_contexts()
        if not contexts:
            return []
        return [ctx["name"] for ctx in contexts]

    @server.tool()
    def get_actual_context() -> Optional[str]:
        """
        Get actual active context.
        """
        _, current_context = config.list_kube_config_contexts()
        if not current_context:
            return None
        return current_context["name"]