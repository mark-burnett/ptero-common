import requests
import logging
import os
import sys
import traceback
from requests.models import Request
from requests.exceptions import ConnectionError
from pprint import pformat


try:
    from flask import request
except:
    # Not everybody who uses ptero_common has requires/uses flask
    pass


MAX_DATA_LENGTH = int(os.environ.get("PTERO_LOG_MAX_DATA_LENGTH", "512"))
TRACEBACK_DEPTH = abs(int(os.environ.get(
        "PTERO_LOG_EXCEPTION_TRACEBACK_DEPTH", "3")))


def getLogger(*args, **kwargs):
    logger = logging.getLogger(*args, **kwargs)
    return CustomLogger(logger=logger)


class CustomLogger(object):
    def __init__(self, logger):
        self.logger = logger

    def __getattr__(self, attr):
        return getattr(self.logger, attr)

    def exception(self, *args, **kwargs):
        if 'extra' in kwargs:
            my_extra = kwargs['extra'].copy()
        else:
            my_extra = {}

        my_extra['exception'] = _pformat(sys.exc_info()[1])

        tb_lines = traceback.format_tb(sys.exc_info()[2])
        for i, tb_line in enumerate(tb_lines[-TRACEBACK_DEPTH:]):
            my_extra['traceback-%s' % (i + 1)] = tb_line

        kwargs['extra'] = my_extra
        self.logger.exception(*args, **kwargs)


class CustomFormatter(logging.Formatter):
    def formatException(self, exc_info):
        tb_lines = traceback.format_tb(sys.exc_info()[2])
        return ''.join(tb_lines[-TRACEBACK_DEPTH:]) +\
                _pformat(sys.exc_info()[1])


def logged_response(logger):
    def _log_response(target):
        def wrapper(*args, **kwargs):
            label = '%s %s' % (target.__name__.upper(), request.url)

            logger.debug(
                    "Handling %s from %s", label, request.access_route[0])
            logger.debug("Body of %s: %s", label, _pformat(request.json))

            try:
                result = target(*args, **kwargs)
            except Exception:
                logger.exception(
                        "Exception while handling %s from %s:\n"
                        "Body: %s", label, request.access_route[0],
                        _pformat(request.json))
                raise
            logger.debug("Full response to %s: %s", label, _pformat(result))
            return result
        return wrapper
    return _log_response


def _pformat(data):
    formatted_data = pformat(data, indent=2, width=80)
    if len(formatted_data) > MAX_DATA_LENGTH:
        return formatted_data[:MAX_DATA_LENGTH] + "..."
    else:
        return formatted_data


def _log_request(target, kind):
    def wrapper(*args, **kwargs):

        logger = kwargs.get('logger', getLogger(__name__))
        if 'logger' in kwargs:
            del kwargs['logger']

        kwargs_for_constructor = get_args_for_request_constructor(kwargs)
        request = Request(kind.upper(), *args, **kwargs_for_constructor)

        def log_with_extra(callable, *_args, **_kwargs):
            extra = {"method": kind.upper(), "url": request.url}

            if "extra" in _kwargs:
                extra.update(_kwargs["extra"])

            _kwargs["extra"] = extra
            return callable(*_args, **_kwargs)

        label = '%s %s' % (kind.upper(), request.url)
        log_with_extra(logger.info, "Submitting HTTP %s", label)
        log_with_extra(logger.debug, "Params for %s: %s", label,
                _pformat(request.params))
        log_with_extra(logger.debug, "Headers for %s: %s", label,
                _pformat(request.headers))
        log_with_extra(logger.debug, "Data for %s: %s", label,
                _pformat(request.data))

        try:
            response = target(*args, **kwargs)
        except ConnectionError:
            raise
        except Exception:
            log_with_extra(logger.exception,
                "Exception while sending %s:\n"
                "  Args: %s\n"
                "  Keyword Args: %s",
                label, _pformat(args), _pformat(kwargs))
            raise

        log_with_extra(logger.info, "Got %s from %s", response.status_code,
                label, extra={"status_code": response.status_code})
        log_with_extra(logger.debug, "Body of response from %s: %s", label,
                _pformat(response.text))
        log_with_extra(logger.debug, "Headers in response from %s: %s", label,
                _pformat(response.headers))

        return response
    return wrapper


def get_args_for_request_constructor(kwargs):
    kwargs_for_constructor = kwargs.copy()
    if 'timeout' in kwargs_for_constructor:
        # timout is an argument to requests.get/post/ect but not
        # Request.__init__
        del kwargs_for_constructor['timeout']
    return kwargs_for_constructor


class LoggedRequest(object):
    def __getattr__(self, name):
        return _log_request(getattr(requests, name), name)
logged_request = LoggedRequest()
