from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client
from kubernetes.client import V1ConfigMap, V1ObjectMeta

def register_configmap_tools(server: FastMCP):
    """
    Retrieve metadata and data for Kubernetes ConfigMaps, optionally filtered by namespace and name substring.
    
    Parameters:
    	namespace (Optional[str]): If provided, only ConfigMaps in this namespace are returned.
    	name (Optional[str]): If provided, only ConfigMaps whose metadata.name contains this substring are returned.
    
    Returns:
    	List[Dict[str, object]]: A list of dictionaries representing ConfigMaps with the following keys:
    		- "namespace": namespace of the ConfigMap (str or None)
    		- "name": name of the ConfigMap (str)
    		- "labels": metadata labels (dict or None)
    		- "data": key/value data from the ConfigMap (dict; empty dict if none)
    		- "creation_timestamp": ISO 8601 timestamp string of creation time, or None
    """
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