import asyncio.locks as locks
from uuid import uuid4 as uuid

DEFAULT_TTL = 86400


def _bucket_key_for(name):
    return f'bucket_{name}'


class BucketStorageError(Exception):
    pass


class DuplicateBucketError(BucketStorageError):
    pass


class DictionaryBucketStorage(object):

    def __init__(self, loop=None):
        self._store = {}
        self._lock = locks.Lock(loop=loop)

    async def create(self, name, ttl=None):
        if ttl is None:
            ttl = DEFAULT_TTL

        bucket_data = dict()
        key = _bucket_key_for(name)

        async with self._lock:
            if key in self._store:
                raise DuplicateBucketError(f'duplicate bucket {name}')
            self._store[key] = bucket_data

        return name

    async def exists(self, name):
        key = _bucket_key_for(name)
        async with self._lock:
            return key in self._store

    async def remove(self, name):
        bucket_key = _bucket_key_for(name)
        async with self._lock:
            ncco_data = self._store.pop(bucket_key, None)

        return ncco_data

    async def add_ncco(self, bucket_name, ncco):
        async with self._lock:
            bucket_data = self._store.get(_bucket_key_for(bucket_name))

            if bucket_data is None:
                raise BucketStorageError(f'non-existing bucket {bucket_name}')

            ncco_id = str(uuid())
            bucket_data[ncco_id] = ncco

            return ncco_id

    async def get_ncco(self, bucket_name, ncco_id):
        async with self._lock:
            bucket_data = self._store.get(_bucket_key_for(bucket_name))
            if bucket_data is None:
                raise BucketStorageError(f'non-existing bucket {bucket_name}')

            return bucket_data.get(ncco_id)

    async def remove_ncco(self, bucket_name, ncco_id):
        async with self._lock:
            bucket_data = self._store.get(_bucket_key_for(bucket_name))
            if bucket_data is None:
                raise BucketStorageError(f'non-existing bucket {bucket_name}')

            return bucket_data.pop(ncco_id, None)


class BucketInfo(object):

    def __init__(self, name, nccos):
        self.name = name
        self.nccos = nccos

    def __len__(self):
        return len(self.nccos)


class BucketOperations(object):

    def __init__(self, storage):
        self.storage = storage

    async def create(self, name, ttl=None):
        ttl = ttl or DEFAULT_TTL
        await self.storage.create(name, ttl=ttl)

        return Bucket(name, self.storage)

    async def lookup(self, name):
        if await self.storage.exists(name):
            return Bucket(name, self.storage)

        return None

    async def remove(self, name):
        ncco_data = await self.storage.remove(name)

        if ncco_data is None:
            return None

        return BucketInfo(name, ncco_data)


class Bucket(object):

    def __init__(self, name, storage):
        self.name = name
        self.storage = storage

    async def add(self, ncco):
        return await self.storage.add_ncco(self.name, ncco)

    async def remove(self, ncco_id):
        return await self.storage.remove_ncco(self.name, ncco_id)

    async def lookup(self, ncco_id):
        return await self.storage.get_ncco(self.name, ncco_id)
