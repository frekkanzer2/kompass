from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client_apps
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
                "replicas": d.spec.replicas,
                "available_replicas": d.status.available_replicas,
                "ready_replicas": d.status.ready_replicas,
                "updated_replicas": d.status.updated_replicas,
                "images": [c.image for c in d.spec.template.spec.containers],
                "creation_timestamp": d.metadata.creation_timestamp.isoformat()
                if d.metadata.creation_timestamp
                else None,
            }
            for d in deployments
        ]
