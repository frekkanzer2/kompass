from typing import List
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client

def register_node_tools(server: FastMCP):
  @server.tool()
  def list_cluster_node_versions() -> List[dict[str, object]]:
    """
    Description
      Returns the kubelet version and additional system details for each node in your Kubernetes cluster.

    Arguments
      This function takes no arguments.

    Returns
      A list of dictionaries, one per node. Each dictionary includes:
      - node: The node name.
      - kubelet_version: The version of the kubelet installed on this node.
      - os_image: The operating system image running on this node.
      - container_runtime: The container runtime version for this node.
    """
    try:
        kubeclient = get_kube_client()
        nodes = kubeclient.list_node()
        results = []
        for node in nodes.items:
            node_name = node.metadata.name
            kubelet_version = node.status.node_info.kubelet_version
            os_image = node.status.node_info.os_image
            container_runtime = node.status.node_info.container_runtime_version

            results.append({
                "node": node_name,
                "kubelet_version": kubelet_version,
                "os_image": os_image,
                "container_runtime": container_runtime,
            })
        return results

    except Exception as e:
        return [{
            "status": "error",
            "error": f"Failed to list nodes: {str(e)}"
        }]
