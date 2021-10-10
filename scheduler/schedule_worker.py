import threading
import time
import json

import redis

from pottery import Redlock
from redis import Redis
from scheduler.dispatcher import DispatcherInterface
from scheduler.logger import get_logger

logger = get_logger(__name__)

REDIS_SCHEDULE_LOCK = "scheduler:schedule"
REDIS_SCHEDULE_KEY = "scheduler:delayed"


class ScheduleThread(threading.Thread):
    def __init__(self, redis: Redis, dispatcher: DispatcherInterface):
        super().__init__()
        self._exit = False
        self._redis = redis
        self._dispatcher = dispatcher

        # create lock for scheduling
        try:
            self._lock = Redlock(
                key=REDIS_SCHEDULE_LOCK,
                masters={self._redis},
                raise_on_redis_errors=True,
            )
        except Exception as e:
            logger.exception(e)
            self._exit = True

    def run(self):
        while not self._exit:
            try:
                with self._lock:
                    self.poll()
            except Exception as e:
                logger.exception("Exception in ScheduleThread")
                self._exit = True

    def poll(self):
        logger.debug("Checking for jobs to schedule")
        # get first item
        item = self._redis.zrange(REDIS_SCHEDULE_KEY, 0, 0, withscores=True)
        # no item or time not reached yet
        if not item or item[0][1] > time.time():
            time.sleep(1)
            return
        full_repo, fork = json.loads(item[0][0])
        logger.info(f"Found task for repo {full_repo}")

        if self._dispatcher:
            self._dispatcher.dispatch(full_repo, fork)
        self._redis.zrem(REDIS_SCHEDULE_KEY, item[0][0])
