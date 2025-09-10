from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from app.client.kubernetes_client import get_kube_client

def register_tools(server: FastMCP):
    @server.tool()
    def list_pods(name: Optional[str] = None, namespace: Optional[str] = None) -> List[str]:
        """Get all pods or filter them by namespace or name substring"""
        kubeclient = get_kube_client()

        if namespace:
            pods = kubeclient.list_namespaced_pod(namespace=namespace)
        else:
            pods = kubeclient.list_pod_for_all_namespaces()

        pods = pods.items

        if name:
            pods = [pod for pod in pods if name in pod.metadata.name]

        return [f"{pod.metadata.namespace}/{pod.metadata.name}" for pod in pods]