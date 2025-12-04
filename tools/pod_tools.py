from typing import List, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client

def register_tools(server: FastMCP):
    """
    Retrieve pod metadata, optionally filtering by namespace, pod name substring, pod status, labels, or container image substring.
    
    Parameters:
        name (Optional[str]): Substring to match against pod metadata.name.
        namespace (Optional[str]): Namespace to scope the pod listing; when omitted, searches all namespaces.
        status (Optional[str]): Pod phase or container state reason to match (e.g., 'Running', 'Pending', 'CrashLoopBackOff').
        labels (Optional[dict[str, str]]): Key/value pairs that must all be present on the pod.
        image (Optional[str]): Substring to match against container image names.
    
    Returns:
        List[dict[str, object]]: A list of pod summaries containing keys: `namespace`, `name`, `phase`, `reason`, `restarts`, `containers`, `images`, `resources`, `node`, and `labels`.
    """
    """
    Delete pods owned by Kubernetes Jobs that are in the 'Succeeded' or 'Failed' phase, with optional filtering by namespace, name substring, or labels.
    
    Parameters:
        name (Optional[str]): Substring to match against pod metadata.name.
        namespace (Optional[str]): Namespace to scope the pod listing and deletions; when omitted, operates across all namespaces.
        labels (Optional[dict[str, str]]): Key/value pairs that must all be present on the pod.
    
    Returns:
        List[dict[str, str]]: A list of result objects for attempted deletions. Each object contains `status` ('deleted' or 'error'), `namespace`, and `name`; error entries include an `error` message.
    """
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
        try:
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
        except Exception as e:
            return [{
                "status": "error",
                "error": f"Failed to list pods: {str(e)}"
            }]

    @server.tool()
    def cleanup_job_pods(
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        labels: Optional[dict[str, str]] = None,
    ) -> List[dict[str, str]]:
        """
        Delete pods created by Kubernetes Jobs that are in the "Succeeded" or "Failed" phase, optionally filtering by namespace, name substring, and labels.
        
        Parameters:
            name (Optional[str]): Substring to match within pod names.
            namespace (Optional[str]): Namespace to restrict the search to; if omitted, all namespaces are searched.
            labels (Optional[dict[str, str]]): Labels that must all match on a pod (every key/value pair must be present and equal).
        
        Returns:
            List[dict[str, str]]: A list of result records for each attempted deletion. Each record contains:
                - "status": "deleted" for successful deletions or "error" if deletion failed.
                - "namespace": namespace of the pod.
                - "name": name of the pod.
                - "error" (present only when status is "error"): the error message describing the failure.
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