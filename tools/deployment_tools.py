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

def register_deployment_tools(server: FastMCP):
    """
    Return deployments matching optional filters such as namespace, name substring, labels, replica counts, readiness counts, or container image substring.
    
    Parameters:
        namespace (Optional[str]): Namespace to search; if omitted searches all namespaces.
        name (Optional[str]): Substring to match against deployment names.
        labels (Optional[Dict[str, str]]): Required key/value pairs that must be present on the deployment.
        min_replicas (Optional[int]): Minimum desired replicas (inclusive).
        max_replicas (Optional[int]): Maximum desired replicas (inclusive).
        min_ready_replicas (Optional[int]): Minimum ready replicas (inclusive).
        max_ready_replicas (Optional[int]): Maximum ready replicas (inclusive).
        ready_replicas (Optional[int]): Exact ready replicas value to match.
        image (Optional[str]): Substring to match against container image names.
    
    Returns:
        List[Dict[str, object]]: One entry per matching deployment with keys:
            - namespace: deployment namespace
            - name: deployment name
            - labels: deployment labels (or None)
            - replicas: desired replica count (int)
            - available_replicas: available replicas count (int)
            - ready_replicas: ready replicas count (int)
            - updated_replicas: updated replicas count (int)
            - images: list of container image strings
            - creation_timestamp: ISO 8601 timestamp string or None
    """
    """
    Return the current container images for a Deployment and a chronological history derived from its owned ReplicaSets.
    
    Parameters:
        namespace (str): Namespace of the Deployment.
        name (str): Name of the Deployment.
    
    Returns:
        Dict[str, object]: Dictionary containing:
            - deployment: the Deployment name
            - namespace: the Deployment namespace
            - current_images: list of images from the Deployment pod template
            - history: list of dicts with keys:
                - replicaset: replicaset name
                - images: list of images from that replicaset
                - creation_timestamp: ISO 8601 timestamp string or None
    """
    """
    Trigger a rollout restart by annotating matching Deployments' pod templates and report per-deployment outcomes.
    
    Parameters:
        namespace (Optional[str]): Namespace to target; if omitted targets all namespaces.
        label_selector (Optional[str]): Kubernetes label selector to pre-filter deployments.
        names (Optional[List[str]]): Optional exact list of deployment names to include.
    
    Returns:
        List[dict[str, object]]: One result per attempted deployment with either:
            - success entries containing status="success", deployment, namespace, restarted_at (ISO timestamp)
            - error entries containing status="error", deployment, namespace, error (error message)
        If listing deployments fails, returns a single-item list with status="error" and an error message.
    """
    """
    Scale the specified Deployment to the requested replica count and return the operation result.
    
    Parameters:
        name (str): Name of the Deployment to scale.
        namespace (str): Namespace of the Deployment.
        replicas (int): Desired number of replicas.
    
    Returns:
        dict[str, object]: Result dictionary with either:
            - on success: status="success", deployment, namespace, scaled_to (int)
            - on error: status="error", deployment, namespace, error (error message)
    """
    @server.tool()
    def list_deployments(
        namespace: Optional[str] = None,
        name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
        min_ready_replicas: Optional[int] = None,
        max_ready_replicas: Optional[int] = None,
        ready_replicas: Optional[int] = None,
        image: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        """
        List Deployments, optionally filtered by:
          - namespace
          - name substring
          - labels
          - desired replicas (min/max)
          - ready replicas (min/max or exact value)
          - container image (exact or substring)

        Returns:
            A list of dicts with deployment details, including container images.
        """
        kubeclient = get_kube_client_apps()

        if namespace:
            deployments = kubeclient.list_namespaced_deployment(namespace=namespace).items
        else:
            deployments = kubeclient.list_deployment_for_all_namespaces().items

        if name:
            deployments = [d for d in deployments if name in d.metadata.name]

        if labels:
            def match_labels(dep):
                dep_labels = dep.metadata.labels or {}
                return all(dep_labels.get(k) == v for k, v in labels.items())
            deployments = [d for d in deployments if match_labels(d)]

        if min_replicas is not None:
            deployments = [d for d in deployments if (d.spec.replicas or 0) >= min_replicas]

        if max_replicas is not None:
            deployments = [d for d in deployments if (d.spec.replicas or 0) <= max_replicas]

        if min_ready_replicas is not None:
            deployments = [d for d in deployments if (d.status.ready_replicas or 0) >= min_ready_replicas]

        if max_ready_replicas is not None:
            deployments = [d for d in deployments if (d.status.ready_replicas or 0) <= max_ready_replicas]

        if ready_replicas is not None:
            deployments = [d for d in deployments if (d.status.ready_replicas or 0) == ready_replicas]

        if image:
            deployments = [
                d for d in deployments
                if any(image in c.image for c in d.spec.template.spec.containers)
            ]

        return [
            {
                "namespace": d.metadata.namespace,
                "name": d.metadata.name,
                "labels": d.metadata.labels,
                "replicas": d.spec.replicas or 0,
                "available_replicas": d.status.available_replicas or 0,
                "ready_replicas": d.status.ready_replicas or 0,
                "updated_replicas": d.status.updated_replicas or 0,
                "images": [c.image for c in d.spec.template.spec.containers],
                "creation_timestamp": d.metadata.creation_timestamp.isoformat()
                if d.metadata.creation_timestamp
                else None,
            }
            for d in deployments
        ]

    @server.tool()
    def get_deployment_images_history(namespace: str, name: str) -> Dict[str, object]:
        """
        Retrieve current and historical container images for a Deployment by inspecting its ReplicaSets.
        
        History entries are ordered by ReplicaSet creation time (oldest first).
        
        Returns:
            result (dict): Mapping with keys:
                - "deployment" (str): the Deployment name.
                - "namespace" (str): the Deployment namespace.
                - "current_images" (List[str]): images from the Deployment's pod template containers.
                - "history" (List[dict]): list of records for owned ReplicaSets, each containing:
                    - "replicaset" (str): ReplicaSet name.
                    - "images" (List[str]): images from the ReplicaSet's pod template containers.
                    - "creation_timestamp" (str|None): ISO-formatted creation timestamp or None.
        """
        kubeclient = get_kube_client_apps()
        d = kubeclient.read_namespaced_deployment(name=name, namespace=namespace)
        current_images = [c.image for c in d.spec.template.spec.containers]
        rs_list = kubeclient.list_namespaced_replica_set(namespace=namespace).items
        owned_rs = [
            rs for rs in rs_list
            if any(owner.kind == "Deployment" and owner.name == name
                   for owner in (rs.metadata.owner_references or []))
        ]
        history: List[Dict[str, object]] = []
        for rs in owned_rs:
            imgs = [c.image for c in rs.spec.template.spec.containers]
            history.append({
                "replicaset": rs.metadata.name,
                "images": imgs,
                "creation_timestamp": rs.metadata.creation_timestamp.isoformat()
                if rs.metadata.creation_timestamp else None,
            })
        history = sorted(history, key=lambda h: h["creation_timestamp"] or "")
        return {
            "deployment": name,
            "namespace": namespace,
            "current_images": current_images,
            "history": history,
        }
    
    @server.tool()
    def rollout_restart_all_deployments(
        namespace: Optional[str] = None,
        label_selector: Optional[str] = None,
        names: Optional[List[str]] = None,
    ) -> List[dict[str, object]]:
        """
        Trigger a rollout restart for matching Deployments by updating their pod template annotation.
        
        Updates the pod template annotation (kubectl.kubernetes.io/restartedAt) to force a restart for Deployments selected by namespace, label_selector, and/or an explicit list of names. Each item in the returned list describes the outcome for a Deployment; if listing deployments fails a single-item list with an error entry is returned.
        
        Parameters:
            namespace (Optional[str]): Namespace to target; if None, all namespaces are considered.
            label_selector (Optional[str]): Kubernetes label selector string to filter Deployments (e.g. "app=myapp").
            names (Optional[List[str]]): Optional list of exact Deployment names to restart; when provided only Deployments with names in this list are affected.
        
        Returns:
            List[dict[str, object]]: Per-deployment result dictionaries. Each success entry contains "status": "success", "deployment", "namespace", and "restarted_at". Each failure entry contains "status": "error", "deployment", "namespace", and "error". On top-level listing failure returns [{"status": "error", "error": "<message>"}].
        """
        try:
            kubeclient = get_kube_client_apps()
            
            # List deployments
            if namespace:
                deployments = kubeclient.list_namespaced_deployment(
                    namespace=namespace,
                    label_selector=label_selector
                )
            else:
                deployments = kubeclient.list_deployment_for_all_namespaces(
                    label_selector=label_selector
                )
            
            items = [
                deployment for deployment in deployments.items
                if (not names or deployment.metadata.name in names)
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
            
            for deployment in items:
                try:
                    kubeclient.patch_namespaced_deployment(
                        name=deployment.metadata.name,
                        namespace=deployment.metadata.namespace,
                        body=patch_body
                    )
                    
                    results.append({
                        "status": "success",
                        "deployment": deployment.metadata.name,
                        "namespace": deployment.metadata.namespace,
                        "restarted_at": restart_time
                    })
                    
                except Exception as e:
                    results.append({
                        "status": "error",
                        "deployment": deployment.metadata.name,
                        "namespace": deployment.metadata.namespace,
                        "error": str(e)
                    })
            
            return results
            
        except Exception as e:
            return [{
                "status": "error",
                "error": f"Failed to list deployments: {str(e)}"
            }]

    @server.tool()
    def scale_deployment(
        name: str,
        namespace: str,
        replicas: int
    ) -> dict[str, object]:
        """
        Scale the specified Kubernetes Deployment to the given replica count.
        
        Returns:
            A dictionary describing the operation result. On success: `{"status": "success", "deployment": <name>, "namespace": <namespace>, "scaled_to": <replicas>}`. On error: `{"status": "error", "deployment": <name>, "namespace": <namespace>, "error": <error message>}`.
        """
        try:
            kubeclient = get_kube_client_apps()

            patch_body = {
                "spec": {
                    "replicas": replicas
                }
            }

            kubeclient.patch_namespaced_deployment(
                name=name,
                namespace=namespace,
                body=patch_body
            )

            return {
                "status": "success",
                "deployment": name,
                "namespace": namespace,
                "scaled_to": replicas
            }

        except Exception as e:
            return {
                "status": "error",
                "deployment": name,
                "namespace": namespace,
                "error": str(e)
            }