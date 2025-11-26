from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client_apps, get_kube_client
from kubernetes.client import (
    V1Deployment,
    V1DeploymentSpec,
    V1ObjectMeta,
    V1PodTemplateSpec,
    V1PodSpec,
    V1Container,
    V1LabelSelector,
)

def register_statefulset_tools(server: FastMCP):
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
            
            # Filtro opzionale ulteriormente per nome
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

