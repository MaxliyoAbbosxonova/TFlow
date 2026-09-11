import importlib
import inspect
import time
from random import randint

import redis
from rest_framework.fields import Field
from rest_framework.serializers import BaseSerializer


def _signature_parameters(func):
    try:
        inspect.signature
    except AttributeError:
        # Python 2.x
        return inspect.getargspec(func).args
    else:
        # Python 3.x
        return inspect.signature(func).parameters.keys()


class RecursiveField(Field):
    """
    A field that gets its representation from its parent.

    This method could be used to serialize a tree structure, a linked list, or
    even a directed acyclic graph. As with all recursive things, it is
    important to keep the base case in mind. In the case of the tree serializer
    example below, the base case is a node with an empty list of children. In
    the case of the list serializer below, the base case is when `next==None`.
    Above all, beware of cyclical references.

    Examples:

    class TreeSerializer(self):
        children = ListField(child=RecursiveField())

    class ListSerializer(self):
        next = RecursiveField(allow_null=True)
    """

    # This list of attributes determined by the attributes that
    # `rest_framework.serializers` calls to on a field object
    PROXIED_ATTRS = (
        # methods
        'get_value',
        'get_initial',
        'run_validation',
        'get_attribute',
        'to_representation',

        # attributes
        'field_name',
        'source',
        'read_only',
        'default',
        'source_attrs',
        'write_only',
    )

    def __init__(self, to=None, **kwargs):
        """
        arguments:
        to - `None`, the name of another serializer defined in the same module
             as this serializer, or the fully qualified import path to another
             serializer. e.g. `ExampleSerializer` or
             `path.to.module.ExampleSerializer`
        """
        self.to = to
        self.init_kwargs = kwargs
        self._proxied = None

        # need to call super-constructor to support ModelSerializer
        super_kwargs = dict(
            (key, kwargs[key])
            for key in kwargs
            if key in _signature_parameters(Field.__init__)
        )
        super(RecursiveField, self).__init__(**super_kwargs)

    def bind(self, field_name, parent):
        # Extra-lazy binding, because when we are nested in a ListField, the
        # RecursiveField will be bound before the ListField is bound
        self.bind_args = (field_name, parent)

    @property
    def proxied(self):
        if not self._proxied:
            if self.bind_args:
                field_name, parent = self.bind_args

                if hasattr(parent, 'child') and parent.child is self:
                    # RecursiveField nested inside of a ListField
                    parent_class = parent.parent.__class__
                else:
                    # RecursiveField directly inside a Serializer
                    parent_class = parent.__class__

                assert issubclass(parent_class, BaseSerializer)

                if self.to is None:
                    proxied_class = parent_class
                else:
                    try:
                        module_name, class_name = self.to.rsplit('.', 1)
                    except ValueError:
                        module_name, class_name = parent_class.__module__, self.to

                    try:
                        proxied_class = getattr(
                            importlib.import_module(module_name), class_name)
                    except Exception as e:
                        raise ImportError(
                            'could not locate serializer %s' % self.to, e)

                proxied = proxied_class(**self.init_kwargs)
                proxied.bind(field_name, parent)
                self._proxied = proxied

        return self._proxied

    def __getattribute__(self, name):
        if name in RecursiveField.PROXIED_ATTRS:
            try:
                proxied = object.__getattribute__(self, 'proxied')
                return getattr(proxied, name)
            except AttributeError:
                pass

        return object.__getattribute__(self, name)


redis_client = redis.StrictRedis(host='redis', port=6379, db=0, decode_responses=True)


def random_code():
    return randint(100_000, 999_999)


def _get_login_key(email):
    return f'login:{email}'


def send_sms_code(email: str, code: int, ttl_seconds=120):
    redis_key = f'login:{email}'
    data = redis_client.hgetall(redis_key)
    if data:
        sent_at = float(data.get("sent_at"))
        passed = time.time() - sent_at
        remain = ttl_seconds - passed

        if remain > 0:
            return {
                "allowed": False,
                "remain_seconds": round(remain)

            }
    print(f"[TEST] Email: {email}, Code: {code}")
    redis_client.hmset(redis_key, {
        "sent_at": time.time(),
        "code": code
    })
    redis_client.expire(redis_key, ttl_seconds)

    return {
        "allowed": True,
        "remain_seconds": 0
    }


def check_sms_code(email: str, code: int):
    redis_key = f"login:{email}"
    data = redis_client.hgetall(redis_key)
    if not data:
        return False
    saved_code = data.get("code")
    print(saved_code, code)

    return str(saved_code) == str(code)
