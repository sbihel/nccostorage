import json

from aiohttp import web
from nccostorage.bucket import BucketOperations, DictionaryBucketStorage
from nccostorage.ncco import validate


def error_response(status=None, text=None):
    if not 399 < status < 600:
        raise ValueError('status must be a valid HTTP error code')

    body = json.dumps({'status': 'error', 'text': text})
    content_type = 'application/json'
    return web.Response(status=status, text=body, content_type=content_type)


async def create_bucket(request):
    body = await request.json()
    bucket_name = body.get('id')

    if bucket_name is None:
        return error_response(status=400, text="missing 'id' in request body")

    buckets: BucketOperations = request.app['buckets']
    await buckets.create(bucket_name)

    return web.Response(status=204)


async def add_ncco_to_bucket(request):
    bucket_id = request.match_info['bucket_id']

    buckets: BucketOperations = request.app['buckets']
    bucket = await buckets.lookup(bucket_id)
    if bucket is None:
        return error_response(status=404, text=f'bucket with id {bucket_id} not found')

    ncco = await request.json()
    try:
        ncco = validate(ncco)
    except Exception:
        return web.Response(status=400, text='Failed to validate NCCO')

    ncco_id = await bucket.add(ncco)

    res_body = {
        'ncco_id': ncco_id,
        'ncco': ncco
    }

    return web.Response(status=201, text=json.dumps(res_body), content_type='application/json')


async def lookup_ncco(request):
    bucket_id = request.match_info['bucket_id']

    buckets: BucketOperations = request.app['buckets']
    bucket = await buckets.lookup(bucket_id)
    if bucket is None:
        return error_response(status=404, text=f'bucket with id {bucket_id} not found')

    ncco_id = request.match_info['ncco_id']
    ncco = await bucket.lookup(ncco_id)

    if ncco is None:
        return error_response(status=404, text=f'ncco with id {ncco_id} not found')

    res_body = {
        'ncco_id': ncco_id,
        'ncco': ncco,
    }

    return web.Response(text=json.dumps(res_body), content_type='application/json')


async def remove_ncco(request):
    bucket_id = request.match_info['bucket_id']

    buckets: BucketOperations = request.app['buckets']
    bucket = await buckets.lookup(bucket_id)
    if bucket is None:
        return error_response(status=404, text=f'bucket with id {bucket_id} not found')

    ncco_id = request.match_info['ncco_id']
    await bucket.remove(ncco_id)

    return web.Response(status=204)


def requires_json(handler):
    async def middleware(request):
        if request.content_type != 'application/json':
            return error_response(status=400, text='request body must be json')

        # TODO(lpedrosa): this should be an exception handler middleware
        try:
            return await handler(request)
        except json.decoder.JSONDecodeError:
            return error_response(status=400, text='request body must be json')
    return middleware


def setup_bucket_api(app):
    app.router.add_post('/bucket', requires_json(create_bucket))

    return app

def setup_ncco_api(app):
    app.router.add_post('/bucket/{bucket_id}/ncco', add_ncco_to_bucket)
    app.router.add_get('/bucket/{bucket_id}/ncco/{ncco_id}', lookup_ncco)
    app.router.add_delete('/bucket/{bucket_id}/ncco/{ncco_id}', remove_ncco)

    return app