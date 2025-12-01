from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client

def register_event_tools(server: FastMCP):
    """
    Retrieve Kubernetes events for the specified resource.
    
    Parameters:
        kind (str): Resource kind (e.g., Pod, Job, Deployment).
        namespace (str): Namespace of the resource.
        name (str): Name of the resource.
    
    Returns:
        List[Dict[str, object]]: A list of event dictionaries, each containing:
            - `type`: event type (e.g., Normal, Warning)
            - `reason`: short reason string
            - `message`: human-readable message
            - `first_timestamp`: ISO 8601 timestamp string of first occurrence, or None
            - `last_timestamp`: ISO 8601 timestamp string of last occurrence, or None
            - `count`: number of times the event occurred
        If an error occurs while fetching events, returns a single-element list with a dictionary:
            - `status`: "error"
            - `error`: descriptive error message
    """
    @server.tool()
    def get_resource_events(kind: str, namespace: str, name: str) -> List[Dict[str, object]]:
        """
        Get all events related to a specific Kubernetes resource.

        Args:
            kind: resource kind (e.g., Pod, Job, Deployment, CronJob, ReplicaSet, etc.)
            namespace: resource namespace
            name: resource name

        Returns:
            A list of events with type, reason, message, and timestamps.
        """
        try:
            kubeclient = get_kube_client()

            events = kubeclient.list_namespaced_event(namespace=namespace).items

            resource_events = [
                {
                    "type": ev.type,
                    "reason": ev.reason,
                    "message": ev.message,
                    "first_timestamp": ev.first_timestamp.isoformat() if ev.first_timestamp else None,
                    "last_timestamp": ev.last_timestamp.isoformat() if ev.last_timestamp else None,
                    "count": ev.count,
                }
                for ev in events
                if ev.involved_object.kind == kind and ev.involved_object.name == name
            ]

            return resource_events
        except Exception as e:
            return [{
                "status": "error",
                "error": f"Failed to get events for {kind}/{name} in namespace {namespace}: {str(e)}"
            }]