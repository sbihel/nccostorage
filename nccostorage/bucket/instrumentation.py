from prometheus_async.aio import count_exceptions, time
from prometheus_client import Counter, Gauge, Histogram


# pylint: disable-msg=no-value-for-parameter
LIVE_BUCKETS = Gauge('live_buckets', 'number of live buckets in storage')
# pylint: disable-msg=no-value-for-parameter
LIVE_NCCOS = Gauge('live_nccos', 'number of live nccos in storage')
# pylint: disable-msg=no-value-for-parameter
UPDATE_REQUEST = Counter('update_count', 'storage update method call rate')
# pylint: disable-msg=no-value-for-parameter
UPDATE_ERROR = Counter('update_error', 'storage update error rate')
# pylint: disable-msg=no-value-for-parameter
UPDATE_TIME = Histogram('update_time', 'storage update request latency (in seconds)')
# pylint: disable-msg=no-value-for-parameter
READ_REQUEST = Counter('read_count', 'storage read method call rate')
# pylint: disable-msg=no-value-for-parameter
READ_ERROR = Counter('read_error', 'storage read error rate')
# pylint: disable-msg=no-value-for-parameter
READ_TIME = Histogram('read_time', 'storage read request latency (in seconds)')


class InstrumentedBucketStorage(object):

    def __init__(self, storage):
        self._storage = storage

    @time(UPDATE_TIME)
    async def create(self, name, ttl=None):
        UPDATE_REQUEST.inc()
        with UPDATE_ERROR.count_exceptions():
            result = await self._storage.create(name, ttl)
            LIVE_BUCKETS.inc()
            return result

    async def exists(self, name):
        return await self._storage.exists(name)

    @time(UPDATE_TIME)
    async def remove(self, name):
        UPDATE_REQUEST.inc()
        with UPDATE_ERROR.count_exceptions():
            result = await self._storage.remove(name)
            LIVE_BUCKETS.dec()
            return result

    @time(UPDATE_TIME)
    async def add_ncco(self, bucket_name, ncco):
        UPDATE_REQUEST.inc()
        with UPDATE_ERROR.count_exceptions():
            result = await self._storage.add_ncco(bucket_name, ncco)
            LIVE_NCCOS.inc()
            return result

    @time(READ_TIME)
    async def get_ncco(self, bucket_name, ncco_id):
        READ_REQUEST.inc()
        with READ_ERROR.count_exceptions():
            return await self._storage.get_ncco(bucket_name, ncco_id)

    @time(UPDATE_TIME)
    async def remove_ncco(self, bucket_name, ncco_id):
        UPDATE_REQUEST.inc()
        with UPDATE_ERROR.count_exceptions():
            result = await self._storage.remove_ncco(bucket_name, ncco_id)
            LIVE_NCCOS.dec()
            return result
