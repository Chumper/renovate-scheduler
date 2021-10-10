import os
import signal

from redis import Redis
from scheduler.dispatcher import KubernetesDispatcher
from scheduler.logger import get_logger
from scheduler.schedule_worker import ScheduleThread

logger = get_logger(__name__)

REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")
REDIS_HOST = os.getenv("REDIS_HOST")


def main():

    # assert environment variables
    assert REDIS_HOST

    logger.info("Starting up")

    # connect to redis first
    redis = Redis.from_url(f"redis://default:{REDIS_PASSWORD}@{REDIS_HOST}")

    threads = []

    try:
        t = ScheduleThread(redis=redis, dispatcher=KubernetesDispatcher())
        t.start()
        threads.append(t)
    except Exception as e:
        logger.exception(e)
        exit(1)

    def signal_handler(signum, frame):
        logger.info("Shutting down...")
        for t in threads:
            t._exit = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # this will block until we receive either SIGINT or SIGTERM
    for t in threads:
        t.join()

    logger.info("Done.")


if __name__ == "__main__":
    main()
