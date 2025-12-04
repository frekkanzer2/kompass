import logging

from kubernetes import client, config
from kubernetes.client import CoreV1Api, AppsV1Api, AutoscalingV2Api, BatchV1Api

def get_kube_client() -> CoreV1Api:
    """
    Return a CoreV1Api client configured from the current kubeconfig.
    
    Loads the active Kubernetes configuration and returns a CoreV1Api instance for interacting with core cluster resources (for example, Pods and Services).
    
    Returns:
        CoreV1Api: A configured client for core Kubernetes API operations.
    """
    config.load_kube_config()
    return client.CoreV1Api()

def get_kube_client_apps() -> AppsV1Api:
    """
    Create and return an AppsV1Api client configured from the current kubeconfig.
    
    Returns:
        AppsV1Api: A Kubernetes AppsV1Api client for managing workload resources such as Deployments, StatefulSets, DaemonSets, and ReplicaSets.
    """
    config.load_kube_config()
    return client.AppsV1Api()

def get_kube_client_scaling() -> AutoscalingV2Api:
    """
    Create an AutoscalingV2Api client configured from the current kubeconfig.
    
    Loads the Kubernetes configuration and returns an AutoscalingV2Api client instance for interacting with autoscaling resources.
    
    Returns:
        AutoscalingV2Api: Configured Kubernetes AutoscalingV2Api client instance.
    """
    config.load_kube_config()
    return client.AutoscalingV2Api()

def get_kube_client_batch() -> BatchV1Api:
    """
    Create and return a Kubernetes BatchV1Api client configured from the current kubeconfig.
    
    Loads the active kubeconfig (using the default kubeconfig lookup) and constructs a BatchV1Api client for interacting with batch resources such as Jobs and CronJobs.
    
    Returns:
        BatchV1Api: A configured Kubernetes BatchV1Api client instance.
    """
    config.load_kube_config()
    return client.BatchV1Api()