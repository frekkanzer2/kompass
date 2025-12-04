from typing import List, Optional, Dict
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client
from kubernetes.client.exceptions import ApiException

def register_tools(server: FastMCP):
    """
    Retrieve Kubernetes namespaces, optionally filtering by a substring in their names.
    
    Parameters:
        name (Optional[str]): Substring to filter namespace names; if omitted, all namespaces are returned.
    
    Returns:
        List[Dict[str, object]]: List of dictionaries for each namespace with keys:
            - name: namespace name
            - status: namespace phase
            - labels: namespace metadata labels (or None)
            - creation_timestamp: ISO 8601 string of creation time, or None
    """
    """
    Delete Kubernetes namespaces whose names contain the given substring, excluding protected namespaces.
    
    Parameters:
        substring (str): Substring to match namespace names.
    
    Returns:
        List[Dict[str, object]]: List of result dictionaries for each processed namespace with keys:
            - name: namespace name
            - status: "Deleted" on success, or "Failed: <reason>" on failure
            - details: error body returned by the API (present only on failure)
    """
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
        Delete Kubernetes namespaces whose names contain the given substring, excluding protected system namespaces.
        
        Parameters:
            substring (str): Substring to match against namespace names. Names exactly equal to protected namespaces ("kube-system", "kube-public", "default") are never deleted.
        
        Returns:
            List[Dict[str, object]]: A list of result dictionaries, one per attempted namespace. Each dictionary contains:
                - name (str): The namespace name.
                - status (str): "Deleted" on success or "Failed: <reason>" on failure.
                - details (optional, str): Error body returned by the API when deletion fails.
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