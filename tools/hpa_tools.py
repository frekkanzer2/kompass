from typing import List, Dict, Optional
from mcp.server.fastmcp import FastMCP
from utils.kubernetes_client import get_kube_client_scaling

def register_hpa_tools(server: FastMCP):
    """
    Retrieve a list of HorizontalPodAutoscalers (HPAs) optionally filtered by namespace, name, replica bounds, target/current CPU or memory utilization, or target reference.
    
    Parameters:
        namespace (Optional[str]): Kubernetes namespace to scope the search; if omitted, all namespaces are searched.
        name (Optional[str]): Substring matched against "namespace/name" to filter HPAs.
        min_replicas (Optional[int]): Minimum allowed configured replicas (filters out HPAs whose configured minReplicas is less than this).
        max_replicas (Optional[int]): Maximum allowed configured replicas (filters out HPAs whose configured maxReplicas is greater than this).
        target_cpu_utilization_pct (Optional[int]): Minimum required configured target average CPU utilization percentage on the HPA.
        target_memory_utilization_pct (Optional[int]): Minimum required configured target average memory utilization percentage on the HPA.
        current_cpu_utilization_pct_min (Optional[int]): Minimum required observed current average CPU utilization percentage.
        current_memory_utilization_pct_min (Optional[int]): Minimum required observed current average memory utilization percentage.
        target_kind (Optional[str]): Required kind of the HPA's scale target (e.g., "Deployment").
        target_name (Optional[str]): Substring matched against the scale target's name.
    
    Returns:
        List[Dict[str, object]]: A list of summary dictionaries for matching HPAs. Each dictionary contains the keys:
            "namespace", "name", "target" (formatted "Kind/Name"), "min_replicas", "max_replicas",
            "current_replicas", and "desired_replicas".
    """
    """
    Return the scaling criteria and observed utilization for a specific HorizontalPodAutoscaler (HPA).
    
    Parameters:
        namespace (str): Namespace of the HPA.
        name (str): Name of the HPA.
    
    Returns:
        Dict[str, object]: A dictionary with the HPA's namespace and name and the following fields:
            "cpu": {"target_utilization_pct": int | None, "current_utilization_pct": int | None},
            "memory": {"target_utilization_pct": int | None, "current_utilization_pct": int | None},
            "current_replicas": int.
    """
    @server.tool()
    def list_hpa(
        namespace: Optional[str] = None,
        name: Optional[str] = None,
        min_replicas: Optional[int] = None,
        max_replicas: Optional[int] = None,
        target_cpu_utilization_pct: Optional[int] = None,
        target_memory_utilization_pct: Optional[int] = None,
        current_cpu_utilization_pct_min: Optional[int] = None,
        current_memory_utilization_pct_min: Optional[int] = None,
        target_kind: Optional[str] = None,
        target_name: Optional[str] = None,
    ) -> List[Dict[str, object]]:
        """
        List HPAs with optional filters (namespace, name, replicas, CPU/memory targets, current usage, target ref).
        Output shows only the most relevant info.
        """
        client = get_kube_client_scaling()

        if namespace:
            hpas = client.list_namespaced_horizontal_pod_autoscaler(namespace=namespace).items
        else:
            hpas = client.list_horizontal_pod_autoscaler_for_all_namespaces().items

        results: List[Dict[str, object]] = []

        for h in hpas:
            if name:
                if name not in f"{h.metadata.namespace}/{h.metadata.name}":
                    continue

            spec = h.spec
            status = h.status

            cpu_target = None
            mem_target = None
            for m in spec.metrics or []:
                if m.type == "Resource" and m.resource:
                    if m.resource.name == "cpu":
                        cpu_target = getattr(m.resource.target, "average_utilization", None)
                    elif m.resource.name == "memory":
                        mem_target = getattr(m.resource.target, "average_utilization", None)

            cpu_current = None
            mem_current = None
            for cm in status.current_metrics or []:
                if cm.type == "Resource" and cm.resource:
                    if cm.resource.name == "cpu":
                        cpu_current = getattr(cm.resource.current, "average_utilization", None)
                    elif cm.resource.name == "memory":
                        mem_current = getattr(cm.resource.current, "average_utilization", None)

            if min_replicas is not None and (spec.min_replicas or 0) < min_replicas:
                continue
            if max_replicas is not None and spec.max_replicas and spec.max_replicas > max_replicas:
                continue
            if target_kind is not None and spec.scale_target_ref.kind != target_kind:
                continue
            if target_name is not None and target_name not in spec.scale_target_ref.name:
                continue
            if target_cpu_utilization_pct is not None and (cpu_target is None or cpu_target < target_cpu_utilization_pct):
                continue
            if target_memory_utilization_pct is not None and (mem_target is None or mem_target < target_memory_utilization_pct):
                continue
            if current_cpu_utilization_pct_min is not None and (cpu_current is None or cpu_current < current_cpu_utilization_pct_min):
                continue
            if current_memory_utilization_pct_min is not None and (mem_current is None or mem_current < current_memory_utilization_pct_min):
                continue

            results.append({
                "namespace": h.metadata.namespace,
                "name": h.metadata.name,
                "target": f"{spec.scale_target_ref.kind}/{spec.scale_target_ref.name}",
                "min_replicas": spec.min_replicas or 0,
                "max_replicas": spec.max_replicas,
                "current_replicas": status.current_replicas or 0,
                "desired_replicas": status.desired_replicas or 0,
            })

        return results

    @server.tool()
    def get_hpa_scaling_criteria(namespace: str, name: str) -> Dict[str, object]:
        """
        Retrieve scaling criteria for a specific HorizontalPodAutoscaler (HPA).
        
        Returns:
        	A dictionary with the HPA's namespace and name, CPU and memory scaling targets and current utilizations, and current replica count. Example structure:
        	{
        		"namespace": str,
        		"name": str,
        		"cpu": {
        			"target_utilization_pct": Optional[int],
        			"current_utilization_pct": Optional[int],
        		},
        		"memory": {
        			"target_utilization_pct": Optional[int],
        			"current_utilization_pct": Optional[int],
        		},
        		"current_replicas": int,
        	}
        """
        client = get_kube_client_scaling()
        h = client.read_namespaced_horizontal_pod_autoscaler(name=name, namespace=namespace)

        spec = h.spec
        status = h.status

        cpu_target = None
        mem_target = None
        for m in spec.metrics or []:
            if m.type == "Resource" and m.resource:
                if m.resource.name == "cpu":
                    cpu_target = getattr(m.resource.target, "average_utilization", None)
                elif m.resource.name == "memory":
                    mem_target = getattr(m.resource.target, "average_utilization", None)

        cpu_current = None
        mem_current = None
        for cm in status.current_metrics or []:
            if cm.type == "Resource" and cm.resource:
                if cm.resource.name == "cpu":
                    cpu_current = getattr(cm.resource.current, "average_utilization", None)
                elif cm.resource.name == "memory":
                    mem_current = getattr(cm.resource.current, "average_utilization", None)

        return {
            "namespace": h.metadata.namespace,
            "name": h.metadata.name,
            "cpu": {
                "target_utilization_pct": cpu_target,
                "current_utilization_pct": cpu_current,
            },
            "memory": {
                "target_utilization_pct": mem_target,
                "current_utilization_pct": mem_current,
            },
            "current_replicas": status.current_replicas or 0,
        }