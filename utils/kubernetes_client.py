import logging

from kubernetes import client, config
from kubernetes.client import CoreV1Api

def get_kube_client() -> CoreV1Api:
    config.load_kube_config()
    logging.info("🔑 Loaded credentials from kubeconfig")
    return client.CoreV1Api()