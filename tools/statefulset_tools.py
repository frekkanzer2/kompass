from utils.kubernetes_client import get_kube_client_apps
from typing import List, Optional
from mcp.server.fastmcp import FastMCP

def register_statefulset_tools(server: FastMCP):
    """
    Restart Kubernetes StatefulSets by updating the pod template annotation `kubectl.kubernetes.io/restartedAt` to trigger a rolling restart.
    
    Parameters:
        namespace (Optional[str]): Namespace to target; if None, operate across all namespaces.
        label_selector (Optional[str]): Label selector to filter StatefulSets (e.g. "app=myapp").
        names (Optional[List[str]]): Exact StatefulSet names to limit the restart to.
    
    Returns:
        List[dict]: A list of result objects for each processed StatefulSet. On success objects contain:
            - "status": "success"
            - "statefulset": the StatefulSet name
            - "namespace": the StatefulSet namespace
            - "restarted_at": ISO8601 UTC timestamp used for the restart annotation
        On per-item failure objects contain:
            - "status": "error"
            - "statefulset": the StatefulSet name
            - "namespace": the StatefulSet namespace
            - "error": error message string
        If listing StatefulSets fails, returns a single-item list with:
            - "status": "error"
            - "error": error message string
    """
    @server.tool()
    def rollout_restart_all_statefulsets(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
        names: Optional[List[str]] = None,
    ) -> List[dict[str, object]]:
        """
        Restart all Kubernetes StatefulSets in a namespace or across all namespaces,
        optionally filtering by name(s).
        
        Args:
            namespace: namespace to restart StatefulSets in (if None, restarts in all namespaces)
            label_selector: optional label selector to filter StatefulSets (e.g. "app=myapp")
            names: optional list of StatefulSet names to restart (exact match)
            
        Returns:
            List of dictionaries with restart operation details for each StatefulSet
        """
        try:
            kubeclient = get_kube_client_apps()
            
            # List StatefulSets
            if namespace:
                statefulsets = kubeclient.list_namespaced_stateful_set(
                    namespace=namespace,
                    label_selector=label_selector
                )
            else:
                statefulsets = kubeclient.list_stateful_set_for_all_namespaces(
                    label_selector=label_selector
                )
            
            items = [
                ss for ss in statefulsets.items
                if (not names or ss.metadata.name in names)
            ]
            
            results = []
            from datetime import datetime
            restart_time = datetime.utcnow().isoformat()
            patch_body = {
                "spec": {
                    "template": {
                        "metadata": {
                            "annotations": {
                                "kubectl.kubernetes.io/restartedAt": restart_time
                            }
                        }
                    }
                }
            }
            
            for ss in items:
                try:
                    kubeclient.patch_namespaced_stateful_set(
                        name=ss.metadata.name,
                        namespace=ss.metadata.namespace,
                        body=patch_body
                    )
                    
                    results.append({
                        "status": "success",
                        "statefulset": ss.metadata.name,
                        "namespace": ss.metadata.namespace,
                        "restarted_at": restart_time
                    })
                    
                except Exception as e:
                    results.append({
                        "status": "error",
                        "statefulset": ss.metadata.name,
                        "namespace": ss.metadata.namespace,
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "status": "error",
                "error": f"Failed to list StatefulSets: {str(e)}"
            }]
