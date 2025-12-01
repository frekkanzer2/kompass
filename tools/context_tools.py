from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client
from kubernetes import config

def register_tools(server: FastMCP):
    """
    List available Kubernetes context names.
    
    Returns:
        A list of context name strings; returns an empty list if no contexts are configured.
    """
    """
    Return the currently active Kubernetes context name.
    
    Returns:
        The active context name as a string, or `None` if no active context is configured.
    """
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
        Return the name of the currently active Kubernetes context.
        
        @returns The active context name, or None if no active context is set.
        """
        _, current_context = config.list_kube_config_contexts()
        if not current_context:
            return None
        return current_context["name"]