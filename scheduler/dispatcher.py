import time
import os
import yaml

from scheduler.logger import get_logger
from kubernetes import client, config, utils

logger = get_logger(__name__)

NAMESPACE = os.getenv("POD_NAMESPACE", "default")
JOB_TEMPLATE = os.getenv("JOB_TEMPLATE", None)

assert JOB_TEMPLATE, "JOB_TEMPLATE is not defined"


class DispatcherInterface:
    def dispatch(self, full_repo: str, fork: bool):
        """Dispatch the job to a worker"""
        raise NotImplementedError()


class KubernetesDispatcher(DispatcherInterface):
    """
    A dispatcher that will dispatch the jobs as kubernetes jobs.
    For that it will make sure only a given amount of jobs are concurrently running.
    """

    def __init__(self) -> None:
        super().__init__()
        self._max_jobs = os.getenv("MAX_JOBS", 25)
        config.load_incluster_config()

        batch_v1 = client.BatchV1Api()
        list: client.V1JobList = batch_v1.list_namespaced_job(NAMESPACE)
        logger.info(f"Found {len(list.items)} existing jobs")

        k8s_client = client.ApiClient()
        with open(JOB_TEMPLATE) as f:
            dep = yaml.safe_load(f)
            dep["metadata"]["name"] = str(time.time())
            print(dep)
            utils.create_from_yaml(k8s_client, yaml_objects=[dep])
            # batch_v1.create_namespaced_job(NAMESPACE, dep)

    def dispatch(self, full_repo: str, fork: bool):
        logger.info("Dispatching to Kubernetes")
        k8s_client = client.ApiClient()
        utils.create_from_yaml(k8s_client, JOB_TEMPLATE)


class TestDispatcher(DispatcherInterface):
    def dispatch(self, full_repo: str, fork: bool):
        if not hasattr(self, "_events"):
            self._events = []

        logger.info("Capturing in memory")
        self._events.append([full_repo, fork])
