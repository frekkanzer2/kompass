from typing import List, Dict
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client

def register_event_tools(server: FastMCP):
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