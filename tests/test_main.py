from redis import Redis
from scheduler.dispatcher import TestDispatcher
from scheduler.schedule_worker import REDIS_SCHEDULE_KEY, ScheduleThread
from pytest_mock_resources import create_redis_fixture

import time
import json

redis = create_redis_fixture()

def insert_renovate_job(redis: Redis):
    item = json.dumps(["foo/bar", True])
    redis.zadd(REDIS_SCHEDULE_KEY, {item:time.time()}, nx=True)


def test_schedule(redis: Redis):
    # Start the Thread, capture the events
    dispatcher = TestDispatcher()
    t = ScheduleThread(redis=redis, dispatcher=dispatcher)
    t.start()

    insert_renovate_job(redis)
    time.sleep(1)

    t._exit = True
    t.join()

    # check the events
    assert len(dispatcher._events) == 1
    assert dispatcher._events[0][0] == "foo/bar"
    assert dispatcher._events[0][1] == True