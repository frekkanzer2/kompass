import logging

from kubernetes import client, config
from kubernetes.client import CoreV1Api

def get_kube_client() -> CoreV1Api:
    config.load_kube_config()
    return client.CoreV1Api()

def get_kube_client_apps() -> CoreV1Api:
    config.load_kube_config()
    return client.AppsV1Api()