from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client_batch, get_kube_client

def register_job_tools(server: FastMCP):
    @server.tool()
    def list_jobs(
        namespace: Optional[str] = None,
        name: Optional[str] = None,
        labels: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, object]]:
        """
        List Kubernetes Jobs, optionally filtered by namespace, name substring, or labels.

        Args:
            namespace: filter by namespace, if None search all namespaces
            name: substring to match Job name
            labels: dict of labels to match (all must match)

        Returns:
            A list of dicts with Job details.
        """
        kubeclient = get_kube_client_batch()

        if namespace:
            jobs = kubeclient.list_namespaced_job(namespace=namespace).items
        else:
            jobs = kubeclient.list_job_for_all_namespaces().items

        if name:
            jobs = [j for j in jobs if name in j.metadata.name]

        if labels:
            def match_labels(job):
                job_labels = job.metadata.labels or {}
                return all(job_labels.get(k) == v for k, v in labels.items())
            jobs = [j for j in jobs if match_labels(j)]

        results: List[Dict[str, object]] = []
        for j in jobs:
            results.append({
                "namespace": j.metadata.namespace,
                "name": j.metadata.name,
                "labels": j.metadata.labels,
                "completions": j.spec.completions,
                "parallelism": j.spec.parallelism,
                "succeeded": j.status.succeeded or 0,
                "active": j.status.active or 0,
                "failed": j.status.failed or 0,
                "start_time": j.status.start_time.isoformat() if j.status.start_time else None,
                "completion_time": j.status.completion_time.isoformat() if j.status.completion_time else None,
            })

        return results