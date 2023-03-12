import os
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
            # self.logger.debug(
            #     "Function: '%s' running ",
            #     func.__name__,
            # )

            ret = func(*args, **kwargs)

            self.logger.debug("Function: '%s' return: '%s'", func.__name__, ret)
            return ret

        return inner
