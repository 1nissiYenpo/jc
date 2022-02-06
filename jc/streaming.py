"""jc - JSON CLI output utility streaming utils"""

from functools import wraps
from typing import Dict, Iterable


def stream_success(output_line: Dict, ignore_exceptions: bool) -> Dict:
    """Add `_jc_meta` object to output line if `ignore_exceptions=True`"""
    if ignore_exceptions:
        output_line.update({'_jc_meta': {'success': True}})

    return output_line


def stream_error(e: BaseException, line: str) -> Dict:
    """
    Return an error `_jc_meta` field.
    """
    return {
        '_jc_meta':
            {
                'success': False,
                'error': f'{e.__class__.__name__}: {e}',
                'line': line.strip()
            }
    }


def add_jc_meta(func):
    """
    Decorator for streaming parsers to add stream_success and stream_error
    objects. This simplifies the yield lines in the streaming parsers.

    With the decorator on parse():

        # successfully parsed line:
        yield output_line if raw else _process(output_line)

        # unsuccessfully parsed line:
        except Exception as e:
            yield raise_or_yield(ignore_exceptions, e, line)

    Without the decorator on parse():

        # successfully parsed line:
        yield stream_success(output_line, ignore_exceptions) if raw \\
            else stream_success(_process(output_line), ignore_exceptions)

        # unsuccessfully parsed line:
        except Exception as e:
            yield stream_error(raise_or_yield(ignore_exceptions, e, line))

    In all cases above:

        output_line:  (Dict)  successfully parsed line yielded as a dict

        e:            (BaseException)  exception object as the first value
                      of the tuple if the line was not successfully parsed.

        line:         (str)  string of the original line that did not
                      successfully parse.

        ignore_exceptions:  (bool)  continue processing lines and ignore
                            exceptions if True.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        ignore_exceptions = kwargs.get('ignore_exceptions', False)
        gen = func(*args, **kwargs)
        for value in gen:
            # if the yielded value is a dict, then we know it was a
            # successfully parsed line
            if isinstance(value, dict):
                yield stream_success(value, ignore_exceptions)

            # otherwise it will be a tuple and we know it was an error
            else:
                exception_obj = value[0]
                line = value[1]
                yield stream_error(exception_obj, line)

    return wrapper


def streaming_input_type_check(data: Iterable) -> None:
    """
    Ensure input data is an iterable, but not a string or bytes. Raises
    `TypeError` if not.
    """
    if not hasattr(data, '__iter__') or isinstance(data, (str, bytes)):
        raise TypeError("Input data must be a non-string iterable object.")


def streaming_line_input_type_check(line: str) -> None:
    """Ensure each line is a string. Raises `TypeError` if not."""
    if not isinstance(line, str):
        raise TypeError("Input line must be a 'str' object.")


def raise_or_yield(
    ignore_exceptions: bool,
    e: BaseException,
    line: str
) -> tuple:
    ignore_exceptions_msg = '... Use the ignore_exceptions option (-qq) to ignore streaming parser errors.'

    if not ignore_exceptions:
        e.args = (str(e) + ignore_exceptions_msg,)
        raise e

    return e, line
