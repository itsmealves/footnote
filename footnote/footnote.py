import os
import re
import inspect
import textwrap

from functools import wraps
from functools import reduce

from abc import ABC
from abc import abstractmethod


class Footnote(ABC):
    @staticmethod
    @abstractmethod
    def get_format(prefix, text, *args):
        pass

    @staticmethod
    def get_context():
        return {}

    @staticmethod
    def normalize_indentation(source):
        return textwrap.dedent(source)

    @classmethod
    def replace_comments(cls, source):
        def replace_fn(match):
            original_text = match.group(0)
            full_text = original_text.replace('#', '').strip()

            def replace_args(t):
                p = re.sub(r'\$\{.+\}', '{}', t)
                q = re.sub(r'^\w+:', '', p).strip()
                return q.replace('\'', '\\\'')
            def find_prefix(t):
                match = re.match(r'^\w+:', full_text)
                if not match: return None
                return match.group(0)[0:-1]
            def find_args(t):
                return [
                    argument.replace('${', '').replace('}', '')
                    for argument in re.findall(r'\$\{.+\}', t)
                ]
            
            comment_text = replace_args(full_text)
            prefix = find_prefix(full_text)
            args = find_args(full_text)

            if prefix is None:
                return original_text

            return cls.get_format(prefix, comment_text, *args) + os.linesep
        return re.sub(r'#.*\s', replace_fn, source)

    @staticmethod
    def remove_decorators(source):
        return re.sub(r'@\w[\w\.]*', '', source)

    @staticmethod
    def rename_function(source):
        return re.sub(r'def\ \w+', 'def patched_fn', source)

    @classmethod
    def inject(cls, fn, custom_context={}):
        transforms = [
            cls.replace_comments,
            cls.remove_decorators,
            cls.rename_function,
            cls.normalize_indentation
        ]

        local = {}
        source = inspect.getsource(fn)
        patched_source = reduce(lambda a, b: b(a), transforms, source)
        
        context = {**fn.__globals__, **custom_context, **cls.get_context()}
        exec(patched_source, context, local)
        patched_fn = local.get('patched_fn')

        @wraps(fn)
        def wrapper(*args, **kwargs):
            return patched_fn(*args, **kwargs)
        return wrapper

    @classmethod
    def spread(cls, inject_cls):
        for _, fn in inspect.getmembers(inject_cls, predicate=inspect.isfunction):
            cls.inject(fn, { inject_cls.__name__: inject_cls })
        return inject_cls
