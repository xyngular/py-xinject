"""
Used to have a normal looking object that can be imported directly into other modules and used.

It will in reality, always lookup currently active version of a Resource and use that each
time it's asked anything.

This makes it 'act' like the current version of some resource,
code and just use it like a normal object.

See one of these for more details:

- [Active Resource Proxy - pydoc](./#active-resource-proxy)
- [Active Resource Proxy - github]
  (https://github.com/xyngular/py-glazy#active-resource-proxy)

"""
from typing import TypeVar, Type, Generic, Callable, Any
from .resource import Resource

R = TypeVar('R')


class ActiveResourceProxy(Generic[R]):
    """
    Used to simplify accessing the current resource class via proxy object,
    so you can use the object like a normal global-object, but every time you access a
    normal (non-private) attribute/method it will grab you the one from the currenly active
    resource.

    >>> class MyClass(Resource):
    ...   def my_method(self):
    ...      pass

    Typically, to access attributes of a particular Rsource subclass you would have to do this:

    >>> MyClass.resource().my_method()

    With ProxyActive you can do this instead:

    >>> my_class = ActiveResourceProxy.wrap(MyClass)
    >>> my_class.my_method()

    This will always call the active/current resource without having to use the boilerplate
    `.resource()` method on the resource class/type.

    >>> # You can use the `resource_proxy`
    >>> # convenience method to also accomplish this:
    >>> my_class = MyClass.resource_proxy()

    It's sometimes useful to put at the top-level of a module the proxy-version of the resource
    so it can be directly imported into other modules, and used directly like a normal object.

    >>> # We are in some other Module;
    >>> # import the 'my_class' we defined above.
    >>> from my_class_module import my_class
    >>>
    >>> my_class.my_method()
    """

    @classmethod
    def wrap(cls, resource_type: Type[R]) -> R:
        """ Just like init'ing a new object with `resource_type`....
            Except this will preserve
            the type-hinting, and tell things that care about the type (like an IDE) that
            what's returned from here should act like an instance of the `resource_type` passed
            into this method.

            A simpler/alternate way to wrap a Resource with a `ActiveResourceProxy` is via the
            `glazy.resource.Resource.resource_proxy` convenience method.
        """
        # noinspection PyTypeChecker
        return cls(resource_type=resource_type)

    def __init__(self, resource_type: Type[R], grabber: Callable[[R], Any] = None):
        """
        See `ActiveResourceProxy` for and overview. Init method doc below.

        ## Init Method

        When you create a ActiveResourceProxy, you pass in the resource_type you want
        it to proxy.

        Will act like the current/active object of Resource type `resource_type`.
        you can optionally provide a grabber function, that will be called with the current
        resource passed to it.  You can then grab something from that resource and return it.
        If you pass in a grabber function, this ProxyActive will act like a proxy of whatever
        is returned from the grabber method.

        Args:
            resource_type: Type of resource to proxy.
            grabber: Optional callable, if you wish to grab a specific attribute off the resource
                and act like a proxy for that, you can pass in a method here to do so.
                Whatever is returned from the grabber is what is used to as the object to 'proxy'.
        """

        # Would give unusual error later on, lets just check right now!
        if not issubclass(resource_type, Resource):
            raise Exception(
                f"Must pass a glazy.Resource subtype to glazy.ProxyActive.wrap, "
                f"I was given a ({resource_type}) instead."
            )

        self._resource_type = resource_type
        self._grabber = grabber
        pass

    def _get_active(self):
        # Get current/active instance of resource type
        value = self._resource_type.resource()
        if self._grabber:
            return self._grabber(value)
        return value

    def __getattribute__(self, name):
        # Anything the starts with a `_` is something that we want to get/set on self,
        # and not on the current config object.
        if name.startswith('_'):
            return super().__getattribute__(name)

        return getattr(self._get_active(), name)

    def __setattr__(self, key, value):
        if key.startswith('_'):
            # Anything the starts with a `_` is something that we want to get/set on self,
            # and not on the current config object.
            return super().__setattr__(key, value)

        # Otherwise, we set it on the current/active resource object.
        return setattr(self._get_active(), key, value)