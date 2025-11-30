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
                "images": [c.image for c in (pod.spec.containers or [])],
                "resources": [
                    {
                        "container": c.name,
                        "requests": c.resources.requests if c.resources else {},
                        "limits": c.resources.limits if c.resources else {},
                    }
                    for c in (pod.spec.containers or [])
                ],
                "node": pod.spec.node_name,
                "labels": pod.metadata.labels,
            }
            for pod in pods
        ]

    @server.tool()
    def cleanup_job_pods(
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> List[dict[str, str]]:
        """
        Delete all pods created by Jobs that are in 'Succeeded' or 'Failed' state,
        with optional filters on namespace, name, or labels.

        Args:
            name: substring to match in pod names
            namespace: filter pods by namespace
            labels: dictionary of labels to match (all must match)
        
        Returns:
            A list of deleted pods (namespace and name)
        """
        kubeclient = get_kube_client()
        
        if namespace:
            pods = kubeclient.list_namespaced_pod(namespace=namespace).items
        else:
            pods = kubeclient.list_pod_for_all_namespaces().items
        
        pods_to_delete = []
        
        for pod in pods:
            owner_refs = pod.metadata.owner_references or []
            is_job_pod = any(owner.kind == "Job" for owner in owner_refs)
            
            if not is_job_pod:
                continue
            
            if pod.status.phase not in ("Succeeded", "Failed"):
                continue
            
            if name and name not in pod.metadata.name:
                continue
            
            if labels:
                pod_labels = pod.metadata.labels or {}
                if not all(pod_labels.get(k) == v for k, v in labels.items()):
                    continue
            
            pods_to_delete.append(pod)
        
        deleted_pods_info = []
        for pod in pods_to_delete:
            try:
                kubeclient.delete_namespaced_pod(
                    name=pod.metadata.name,
                    namespace=pod.metadata.namespace,
                )
                deleted_pods_info.append({
                    "status": "deleted",
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name
                })
            except Exception as e:
                deleted_pods_info.append({
                    "status": "error",
                    "namespace": pod.metadata.namespace,
                    "name": pod.metadata.name,
                    "error": str(e)
                })
        
        return deleted_pods_info