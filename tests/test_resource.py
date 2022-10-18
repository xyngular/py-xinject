import pytest as pytest

from glazy import ActiveResourceProxy, UContext, Dependency
from glazy.dependency import PerThreadDependency


class MyClass(Dependency):
    def __init__(self):
        self._my_value = "b"

    def my_method(self):
        return self._my_value

    @property
    def my_prop(self):
        return self._my_value

    @my_prop.setter
    def my_prop(self, value):
        self._my_value = value


my_class = ActiveResourceProxy.wrap(MyClass)
my_class_via_proxy_method = MyClass.resource_proxy()


def test_proxy_wrapper():
    for current_class in [my_class, my_class_via_proxy_method]:
        with UContext(resources=[MyClass()]):
            assert_myclass("b")

            current_class.my_prop = "c"
            assert_myclass("c")

            current_class.other = 3
            assert current_class.other == 3

        assert_myclass("b")
        with pytest.raises(AttributeError):
            assert current_class.other == 3


def assert_myclass(param):
    assert my_class.my_prop == param
    assert my_class.my_method() == param
    assert my_class_via_proxy_method.my_prop == param
    assert my_class_via_proxy_method.my_method() == param
    assert MyClass.resource().my_prop == param
    assert MyClass.resource().my_method() == param


def test_shared_threaded_resource():
    # Test to ensure that the app-root and thread-root work correctly with
    # thread safe/unsafe resources.

    class ThreadSharableDependency(Dependency):
        hello = "1"

    class NonThreadSharableResource(PerThreadDependency):
        hello2 = "a"

    ThreadSharableDependency.resource().hello = "3"
    NonThreadSharableResource.resource().hello2 = "b"

    assert ThreadSharableDependency.resource().hello == "3"
    assert NonThreadSharableResource.resource().hello2 == "b"

    thread_out_sharable = None
    thread_out_nonsharable = None

    # This is the root-func for a separate thread.
    def thread_func():
        # Want to write-to these in outer scope.
        nonlocal thread_out_sharable
        nonlocal thread_out_nonsharable

        # This should produce an '3', since resource can be shared between threads.
        thread_out_sharable = ThreadSharableDependency.resource().hello

        # This should produce an 'a', since the resource is NOT shared between threads;
        # the setting of it to 'b' above is in another thread and is NOT shared.
        thread_out_nonsharable = NonThreadSharableResource.resource().hello2

    import threading

    # Create thread
    other_thread = threading.Thread(
        name='TestThread',
        target=thread_func,
        args=[]
    )

    # Startup Thread
    other_thread.start()

    # Wait for thread to finish
    other_thread.join()

    # Check to see if the thread safe/unsafe resources worked correctly.
    assert thread_out_sharable == "3"
    assert thread_out_nonsharable == "a"
