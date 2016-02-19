from functools import wraps
from ptero_common.exceptions import NoSuchEntityError


def handles_no_such_entity_error(target):
    @wraps(target)
    def wrapper(*args, **kwargs):
        try:
            result = target(*args, **kwargs)
        except NoSuchEntityError as e:
            return {'error': e.message}, 404
        return result
    return wrapper
