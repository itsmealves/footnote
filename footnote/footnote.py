import os
import re
import inspect
import textwrap
import types
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
                p = re.sub(r'\$\{[\ \w \-\+\.\(\)\{\}]+\}', '{}', t)
                q = re.sub(r'^\w+:', '', p).strip()
                return q.replace('\'', '\\\'')
            def find_prefix(t):
                match = re.match(r'^\w+:', full_text)
                if not match: return None
                return match.group(0)[0:-1]
            def find_args(t):
                return [
                    argument.replace('${', '').replace('}', '')
                    for argument in re.findall(r'\$\{[\ \w \-\+\.\(\)\{\}]+\}', t)
                ]
            
            comment_text = replace_args(full_text)
            prefix = find_prefix(full_text)
            args = find_args(full_text)

            if prefix is None:
                return original_text

            return cls.get_format(prefix, comment_text, *args) + os.linesep
        return re.sub(r'#.*\s', replace_fn, source)

    @classmethod
    def remove_decorator(cls, source):
        return re.sub('@{}.inject'.format(cls.__name__), '', source)
        # return re.sub(r'@\w[\w\.]*'.format(cls.__name__), '', source))

    @staticmethod
    def rename_function(source):
        return re.sub(r'def\ \w+', 'def patched_fn', source)

    @classmethod
    def inject(cls, fn, custom_context={}):
        transforms = [
            cls.replace_comments,
            cls.remove_decorator,
            cls.normalize_indentation
        ]

        local_context = {}
        source = inspect.getsource(fn)
        patched_source = reduce(lambda a, b: b(a), transforms, source)
        context = {**fn.__globals__, **custom_context, **cls.get_context()}

        compiled_fn = compile(patched_source, inspect.getsourcefile(fn), 'exec')
        exec(compiled_fn, context, local_context)

        return wraps(fn)(local_context.get(fn.__name__))

    @classmethod
    def spread(cls, global_data):
        def spread_fn(inject_cls):

            def patch_mangle(name):
                prefix = '_' + inject_cls.__name__
                if name.startswith(prefix):
                    return name.replace(prefix, '')
                return name

            def patch_members(member, class_def):
                if type(member) == staticmethod:
                    member = member.__func__
                return cls.inject(member, { inject_cls.__name__: class_def, **global_data })

            body = {
                patch_mangle(member_name): member
                for member_name, member in inject_cls.__dict__.items()
                if not inspect.isroutine(member)
            }

            class_def = type(inject_cls.__name__, inspect.getmro(inject_cls)[1:], body)

            for name, member in inject_cls.__dict__.items():
                if inspect.isroutine(member):
                    setattr(class_def, name, patch_members(member, class_def))

            return class_def
        return spread_fn
