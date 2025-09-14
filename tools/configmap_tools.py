from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client
from kubernetes.client import V1ConfigMap, V1ObjectMeta

def register_configmap_tools(server: FastMCP):
    @server.tool()
    def list_configmaps(
        namespace: Optional[str] = None,
        name: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        """
        List ConfigMaps, optionally filtered by namespace and/or name substring.
        """
        kubeclient = get_kube_client()

        if namespace:
            cms = kubeclient.list_namespaced_config_map(namespace=namespace).items
        else:
            cms = kubeclient.list_config_map_for_all_namespaces().items

        if name:
            cms = [cm for cm in cms if name in cm.metadata.name]

        return [
            {
                "namespace": cm.metadata.namespace,
                "name": cm.metadata.name,
                "labels": cm.metadata.labels,
                "data": cm.data or {},
                "creation_timestamp": cm.metadata.creation_timestamp.isoformat()
                if cm.metadata.creation_timestamp
                else None,
            }
            for cm in cms
        ]