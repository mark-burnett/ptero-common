from functools import wraps
from os import environ
from ptero_common.exceptions import NoSuchEntityError


no_such_entity_status_code = int(environ.get(
    'PTERO_NO_SUCH_ENTITY_STATUS_CODE', 404))


def handles_no_such_entity_error(target):
    @wraps(target)
    def wrapper(*args, **kwargs):
        try:
            result = target(*args, **kwargs)
        except NoSuchEntityError as e:
            return {'error': e.message}, no_such_entity_status_code
        return result
    return wrapper
