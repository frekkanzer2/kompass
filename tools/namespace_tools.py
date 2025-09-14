from typing import List, Optional, Dict
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client

def register_tools(server: FastMCP):
    @server.tool()
    def list_namespaces(name: Optional[str] = None) -> List[Dict[str, object]]:
        """
        Get all namespaces or filter them by name substring.

        Args:
            name: substring to match namespace name
        """
        kubeclient = get_kube_client()
        namespaces = kubeclient.list_namespace().items

        if name:
            namespaces = [ns for ns in namespaces if name in ns.metadata.name]

        return [
            {
                "name": ns.metadata.name,
                "status": ns.status.phase,
                "labels": ns.metadata.labels,
                "creation_timestamp": ns.metadata.creation_timestamp.isoformat()
                if ns.metadata.creation_timestamp
                else None,
            }
            for ns in namespaces
        ]