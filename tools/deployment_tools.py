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
        Get the current and historical images for a Deployment by inspecting its ReplicaSets.

        Args:
            namespace: namespace of the deployment
            name: deployment name

        Returns:
            dict with current images and history of past images (from ReplicaSets)
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
    def get_deployment_events(namespace: str, name: str) -> List[Dict[str, object]]:
        """
        Get all events related to a specific Deployment.

        Args:
            namespace: namespace of the deployment
            name: deployment name

        Returns:
            A list of events with type, reason, message, and timestamps.
        """
        client = get_kube_client()
        events = client.list_namespaced_event(namespace=namespace).items

        deployment_events = [
            {
                "type": ev.type,
                "reason": ev.reason,
                "message": ev.message,
                "first_timestamp": ev.first_timestamp.isoformat() if ev.first_timestamp else None,
                "last_timestamp": ev.last_timestamp.isoformat() if ev.last_timestamp else None,
                "count": ev.count,
            }
            for ev in events
            if ev.involved_object.kind == "Deployment" and ev.involved_object.name == name
        ]
        deployment_events.sort(key=lambda e: e["first_timestamp"] or "")

        return deployment_events