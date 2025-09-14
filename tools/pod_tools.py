from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client

def register_tools(server: FastMCP):
    @server.tool()
    def list_pods(
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        status: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
        image: Optional[str] = None,
    ) -> List[dict[str, object]]:
        """
        Get all pods or filter them by namespace, name substring, status, labels, or image.
        
        Args:
            name: substring to match pod name
            namespace: filter pods by namespace
            status: filter pods by status (e.g. 'Running', 'Pending', 'CrashLoopBackOff')
            labels: dict of labels to match (all must match)
            image: substring to match container image
        """
        kubeclient = get_kube_client()

        if namespace:
            pods = kubeclient.list_namespaced_pod(namespace=namespace)
        else:
            pods = kubeclient.list_pod_for_all_namespaces()

        pods = pods.items

        if name:
            pods = [pod for pod in pods if name in pod.metadata.name]

        if labels:
            def match_labels(pod):
                pod_labels = pod.metadata.labels or {}
                return all(pod_labels.get(k) == v for k, v in labels.items())
            pods = [pod for pod in pods if match_labels(pod)]

        if status:
            def pod_matches_status(pod):
                if pod.status.container_statuses:
                    for cs in pod.status.container_statuses:
                        if cs.state.waiting and cs.state.waiting.reason == status:
                            return True
                        if cs.state.terminated and cs.state.terminated.reason == status:
                            return True
                return pod.status.phase == status
            pods = [pod for pod in pods if pod_matches_status(pod)]

        if image:
            pods = [
                pod for pod in pods
                if any(image in c.image for c in (pod.spec.containers or []))
            ]

        return [
            {
                "namespace": pod.metadata.namespace,
                "name": pod.metadata.name,
                "phase": pod.status.phase,
                "reason": next(
                    (
                        cs.state.waiting.reason
                        for cs in (pod.status.container_statuses or [])
                        if cs.state.waiting
                    ),
                    None,
                ),
                "restarts": sum(cs.restart_count for cs in (pod.status.container_statuses or [])),
                "containers": [cs.name for cs in (pod.status.container_statuses or [])],
                "images": [c.image for c in (pod.spec.containers or [])],  # sempre in output
                "node": pod.spec.node_name,
                "labels": pod.metadata.labels,
            }
            for pod in pods
        ]
