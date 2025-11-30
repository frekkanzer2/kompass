from typing import List, Optional, Dict
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client
from kubernetes.client.exceptions import ApiException

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

    @server.tool()
    def delete_namespaces_by_substring(substring: str) -> List[Dict[str, object]]:
        """
        Delete all namespaces whose name contains the given substring.

        Args:
            substring: substring to match namespace name

        Returns:
            A list with the results of the deletion attempts.
        """
        protected_namespaces = ["kube-system", "kube-public", "default"]
        kubeclient = get_kube_client()
        namespaces = kubeclient.list_namespace().items

        matched = [ns for ns in namespaces if substring in ns.metadata.name and ns.metadata.name not in protected_namespaces]
        results = []

        for ns in matched:
            try:
                kubeclient.delete_namespace(ns.metadata.name)
                results.append(
                    {
                        "name": ns.metadata.name,
                        "status": "Deleted",
                    }
                )
            except ApiException as e:
                results.append(
                    {
                        "name": ns.metadata.name,
                        "status": f"Failed: {e.reason}",
                        "details": e.body,
                    }
                )

        return results