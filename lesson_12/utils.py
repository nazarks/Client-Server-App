import os
from calendar import timegm
from datetime import datetime
from functools import wraps
from inspect import stack


class FunctionLog:
    def __init__(self, logger):
        self.logger = logger

    def __call__(self, func):
        @wraps(func)
        def inner(*args, **kwargs):
            outer_function_name = stack()[1][3]
            path = stack()[1][1]
            module_name = path.split(os.sep)[-1]
            self.logger.debug(
                "Function: '%s' running from module: '%s' and function: '%s', with params: '%s'",
                func.__name__,
                module_name,
                outer_function_name,
                (args, kwargs),
            )

            ret = func(*args, **kwargs)

            self.logger.debug("Function: '%s' return: '%s'", func.__name__, ret)
            return ret

        return inner


def log(user_logger):
    def inner(func_to_log):
        @wraps(func_to_log)
        def log_saver(*args, **kwargs):
            user_logger.debug(
                f"Function:  {func_to_log.__name__} with params: {args} ,"
                f" {kwargs}. running from module: {func_to_log.__module__}"
            )
            ret = func_to_log(*args, **kwargs)
            user_logger.debug("Function: '%s' return: '%s'", func_to_log.__name__, ret)
            return ret

        return log_saver

    return inner


# Дата Время в часовом поясе пользователя
def datetime_from_utc_to_local(utc_datetime):
    return datetime.fromtimestamp(timegm(utc_datetime.timetuple()))
