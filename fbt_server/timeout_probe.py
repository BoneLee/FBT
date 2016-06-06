__author__ = 'bone'
# refer to: http://stackoverflow.com/questions/3467526/attaching-a-decorator-to-all-functions-within-a-class

import types
from tornado.ioloop import TimeoutError


class TimeoutProbe(type):
    def __new__(cls, name, bases, attrs):
        for attr_name, attr_value in attrs.iteritems():
            if isinstance(attr_value, types.FunctionType):
                attrs[attr_name] = cls.check_timeout(attr_value)
        return super(TimeoutProbe, cls).__new__(cls, name, bases, attrs)

    @classmethod
    def check_timeout(cls, func):
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except TimeoutError:
                print "**********************************************"
                print "timeout for run ", func.func_name
                print "**********************************************"
                raise

        return wrapper


if __name__ == "__main__":
    class MyClass(object):
        __metaclass__ = TimeoutProbe

        def func1(self):
            print "timeout...."
            import time
            time.sleep(1)
            raise TimeoutError()

        def func2(self):
            print "not timeout"

    MyClass().func1()
    MyClass().func2()
