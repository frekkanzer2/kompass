import logging

from kubernetes import client, config
from kubernetes.client import CoreV1Api, AppsV1Api, AutoscalingV2Api, BatchV1Api

def get_kube_client() -> CoreV1Api:
    config.load_kube_config()
    return client.CoreV1Api()

def get_kube_client_apps() -> AppsV1Api:
    config.load_kube_config()
    return client.AppsV1Api()

def get_kube_client_scaling() -> AutoscalingV2Api:
    config.load_kube_config()
    return client.AutoscalingV2Api()

def get_kube_client_batch() -> BatchV1Api:
    config.load_kube_config()
    return client.BatchV1Api()