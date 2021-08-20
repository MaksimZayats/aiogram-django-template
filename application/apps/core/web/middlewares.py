import inspect
from typing import Any, Dict

from django.utils.deprecation import MiddlewareMixin


class InjectMiddleware(MiddlewareMixin):
    """
    Adds arguments to views.\n

    To add an argument, you need to add it to the "inject_params".\n
    To take an argument in views, you just need specify it in the function arguments.
    """

    inject_params: Dict[str, Any] = {}

    def process_view(self, request, view_func, view_args, view_kwargs):
        for arg_name in inspect.getfullargspec(view_func).args:
            if arg_name in self.inject_params.keys():
                view_kwargs[arg_name] = self.inject_params[arg_name]
