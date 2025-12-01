from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client_batch, get_kube_client

def register_job_tools(server: FastMCP):
    """
    List Kubernetes Jobs optionally filtered by namespace, name substring, or exact labels.
    
    Parameters:
        namespace (Optional[str]): Namespace to search for Jobs. If None, search all namespaces.
        name (Optional[str]): Substring to match against Job metadata.name.
        labels (Optional[Dict[str, str]]): Exact key/value labels all of which must be present on a Job.
    
    Returns:
        List[Dict[str, object]]: A list of dictionaries, one per Job, containing:
            - namespace: Job namespace (str)
            - name: Job name (str)
            - labels: Job labels (dict or None)
            - completions: desired completions (int or None)
            - parallelism: configured parallelism (int or None)
            - succeeded: number of succeeded pods (int)
            - active: number of active pods (int)
            - failed: number of failed pods (int)
            - start_time: ISO 8601 timestamp string of job start or None
            - completion_time: ISO 8601 timestamp string of job completion or None
    """
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