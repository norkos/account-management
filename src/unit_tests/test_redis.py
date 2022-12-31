import redis


def test_redis():
    key = 'my_key'
    name = 'to_be_cached'
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.set(key, name)
    result = r.get(key)

    assert result == name
