"""
Easily create singleton-like classes in a sharable/injectable/decoupled way.


## To Do First

If you have not already, to get a nice high-level overview of library see either:

- project README.md here:
    - https://github.com/xyngular/py-glazy#how-to-use
- Or go to glazy module documentation at here:
    - [glazy, How To Use](./#how-to-use)

## Resource Refrence Summary

Allows you to create sub-classes that act as sharable resources.
Things that should stick around and should be created lazily.

Also allows code to temporarily create, customize and activate a resource if you don't want
the customization to stick around permanently.
You can do it without your or other code needing to be aware of each other.

This helps promote code decoupling, since it's so easy to make a Resource activate it
as the 'current' version to use.

The only coupling that takes place is to the Resource sub-class it's self.

Each separate piece of code can be completely unaware of each other,
and yet each one can take advantage of the shared resource.

This means that Resource can also help with simple dependency injection use-case scenarios.

## Resources
[resources]: #resources

### Get Current
There are various ways to get current resource.
Let's say we have a resource called `SomeResourceType`:

>>> next_identifier = 0
>>> class SomeResourceType(Resource):
...     def __init__(self):
...         global next_identifier
...         self.some_value = "hello!"
...         self.ident = next_identifier
...         next_identifier += 1

.. note:: SomeResourceType's `ident` field get's incremented and set on each newly created object.
    So the first SomeResoureType's `ident` will equal `0`,
    the second one created will be `1` and so forth.

If what you want inherits from `Resource`, it has a nice class method that
returns the current resource.
An easy way to get the current resource for the type in this case is
to call the class method `Resource.resource` on its type like so:

>>> SomeResourceType.resource().some_value
'hello!'
>>> SomeResourceType.resource().ident
0

### Activating New Resource

You can easily create a new resource, configure it however you like and then 'activate' it.
That will make it the current version of that resource.
This allows you to tempoary 'override' and activate your own custimized version of a resource.

You can do it via one of the below listed methods/examples below.

For these examples, say I have this resource defined:

>>> from dataclasses import dataclass
>>> from glazy import Resource
>>>
>>> @dataclass
>>> class MyResource(Resource):
>>>     some_value = 'default-value'
>>>
>>> assert MyResource.resource().some_value == 'default-value'

- Use desired `glazy.resource.Resource` subclass as a method decorator:

        >>> @MyResource(some_value='new-value')
        >>> def my_method():
        >>>     assert MyResource.resource().some_value == 'new-value'


## Active Resource Proxy

You can use `glazy.proxy.ActiveResourceProxy` to create an object that will act
like the current resource.
All non-dunder attributes will be grabbed/set on the current object instead of the proxy.

This means you can call all non-special methods and access normal attributes,
as if the object was really the currently active resource instance.

For more info/details see:

- [Active Resource Proxy - pydoc](./#active-resource-proxy)
- [Active Resource Proxy - github]
  (https://github.com/xyngular/py-glazy#active-resource-proxy)


"""
import functools
from typing import TypeVar, Iterable, Type, List, Generic, Callable, Any
from copy import copy, deepcopy
from guards import Default
from glazy import GlazyContext
from glazy.errors import XynResourceError

T = TypeVar('T')
C = TypeVar('C')
R = TypeVar('R')
ResourceTypeVar = TypeVar('ResourceTypeVar')


class Resource:
    """
    If you have not already done so, you should also read the glazy project's
    [README.md](https://github.com/xyngular/py-glazy#active-resource-proxy) for an overview
    of the library before diving into the below text, that's more of like reference material.

    ## Summary

    Allows you to create sub-classes that act as sharable resources.
    Things that should stick around and should be created lazily.

    Also allows code to temporarily create, customize and activate a resource if you don't want
    the customization to stick around permanently.
    You can do it without your or other code needing to be aware of each other.

    This helps promote code decoupling, since it's so easy to make a Resource activate it
    as the 'current' version to use.

    The only coupling that takes place is to the Resource sub-class it's self.

    You can also easily have each thread lazily create seperate instance of your Resource,
    by inheriting from `PerThreadResource`.

    Each separate piece of code that uses a particular Resource subclass can be completely
    unaware of each other, and yet each one can take advantage of the shared resource.

    This means that Resource can help cover dependency-injection use-cases.

    ## Overview

    A `Resource` represents an object in a `glazy.context.GlazyContext`.
    Generally, resources that are added/created inside a `GlazyContext` inherit from this abstract base
    `Resource` class, but are not required too. `Resource` just adds some class-level
    conveince methods and configuratino options. Inheriting from Resource also helps
    self-document that it's a Resource.

    See [Resources](#resources) at top of this module for a general overview of how resources
    and `GlazyContext`'s work. You should also read the glazy project's
    [README.md](https://github.com/xyngular/py-glazy#active-resource-proxy) for a high-level
    overview.  The text below is more like plain refrence matrial.


    Get the current resource via `Resource.resource`, you can call it on sub-class/concreate
    resource type, like so:

    >>> from glazy import Resource
    >>> class MyConfig(Resource):
    ...     some_setting: str = "default-setting-string"
    >>>
    >>> MyConfig.resource().some_setting

    By default, Resource's act like a singletons; in that child contexs will simply get the same
    instance of the resource that the parent context has.
    You can override this behavior via `Resource.context_resource_for_child` method.

    If you inherit from this class, when you have `Resource.resource` called on you,
    we will do our best to ensure that the same object instance is returned every time
    (there are two exceptions, keep reading).

    These resources are stored in the current `GlazyContext`'s parent.  What happens is:

    If the current `GlazyContext` and none of their parents have this object and it's asked for
    (like what happens when `Resource.resource` is called on it)...
    It will be created in the deepest/oldest parent GlazyContext.

    This is the first parent `GlazyContext` who's `GlazyContext.parent` is None.
    That way it should be visible to everyone on the current thread since it will normally be
    created in the root-context.

    If we don't already exist in any parent, then we must be created the first time we are asked
    for. Normally it will simply be a direct call the resource-type being requested,
    this is the normal way to create objects in python:

    >>> class MyResource(Resource):
    >>>     pass
    >>>
    >>> MyResource.resource()

    When that last line is executed, and the current or any parent context has a `MyResource`
    resource; `GlazyContext` will simply create one via calling the resource type:

    >>> MyResource()

    You can allocate the resource yourself with custom options and add it to the GlazyContext your self.

    Here are the various ways to do that, via:


    - `GlazyContext.add_resource`
        (you will get an error if that GlazyContext currently has a resource
        of that type, so do that as you create the GlazyContext object).

    - Decorator, ie: `@MyResource()`

            >>> from xny_config import Config, config
            >>>
            >>> @Config(service="override-service-name")
            >>> def my_method():
            >>>    assert config.service == "override-service-name"

    - via a with statement.

            >>> def my_method():
            >>>    with @Config(service="override-service-name")
            >>>         assert config.service == "override-service-name"

    If you need more control over how your allocated by default, you can override the
    `Resource.context_resource_for_child` method to customize it.

    ## Background on Unit Testing

    By default, unit tests always create a new blank `GlazyContext` with `parent=None`.
    THis is done by an autouse fixture (`glazy.fixtures.context`)
    THis forces every unit test run to create new resources when they are asked for (lazily).

    This fixture is used automatically for each unit test, it provides a blank root-context
    for each run of a unit test. That way it will recreated any shared resource each time
    and a unit test can't leak resources it added or changed into the next run.

    One example of why this is good is for `moto` and `xyn_aws.dynamodb.DynamoDB`.
    This ensures that we get a new dynamodb shared resource from `boto` each time
    a unit test executes
    (which helps with `moto`, it needs to be active when a resource is allocated/used).

    What I mean by a new blank root-context is that there is nothing in it and it has not
    parent context.  So there are no pre-existing resource that are visible.
    so the older resources that may have already existed won't be used while that
    blank new root-context is the currently active (or any children of it) the old
    resource will be hidden and not used.

    This is exactly what we want for each unit test run.

    When the application runs for real though, we do generally want to use the resources in a
    shared fashion.  So normally we only allocate a new blank-root `@GlazyContext(parent=None)`
    either at the start of a normal application run, or during a unit-test.
    """

    attributes_to_skip_while_copying: Iterable[str] = None
    """ If subclass sets this to a list/set of attribute names,
        we will skip copying them for you (via `Resource.__copy__` and `Resource.__deepcopy__`).

        We ourselves need to skip copying a specific internal property,
        and there are other resources that need to do the same thing.

        This is an easy way to accomplish that goal.

        As a side note, we will always skip copying `_context_manager_stack` in addition to
        what's set on `Resource.attributes_to_skip_while_copying`.

        This can be dynamic if needed, by default it's consulted on the object each time it's
        copied
        (to see where it's used, look at `glazy.resource.Resource.__copy__` and
        `glazy.resource.Resource.__deepcopy__`)
    """

    resource_thread_safe = True
    """ If True, we can be put in the app-root context, and can be potentially used in
        multiple threads.  If False, we will only be lazily allocated in the pre-thread GlazyContext
        and always be used in a single-thread. If another thread needs us and this is False,
        a new Resource instance will be created for that thread.

        ## Details on Mechanism

        It accomplishes this by the lazy-creation mechanism.
        When something asks for a Resource that does not currently exist,
        the parent-GlazyContext is asked for the resource, and then the parent's parent will be
        asked and so on.

        Eventually the app-root context will be asked for the Resource.

        If the app-root already has the Resource, it will return it.

        When app-root does not have the resource, it potentially needs to lazily create the
        resource depending on if Resource is thread-safe.

        So at this point, if `resource_thread_safe` value is (as a class attribute):

        - `False`: The app-root context will return `None` instead of lazily creating the Resource.
            It's expected a thread-root GlazyContext is the thing that asked the app-root context
            and the thread-root context when getting back a None should just go and lazily create
            it.
            This results in a new Resource being lazily allocated for each thread that needs it.
        - `True`: If it does not have one it will lazily create a new Resource store it in self
            and return it. Other thread-roots that ask for this Resource in the future will
            get the one from the app-root, and therefore the Resource will be shared between
            threads and needs to be thread-safe.

        Each context then stores this value in it's self as it goes up the chain.
        Finally the code that orginally asked for the Resource will have it returned to it
        and they can then use it.

        We store it in each GlazyContext that Resource pases though so in the future it can just
        directly answer the question and return the Resource quickly.


        ## How thread-safe

        This is consulted
    """

    @classmethod
    def resource(cls: Type[T], for_context: GlazyContext = Default) -> T:
        """ Gets a potentially shared resource from the current `GlazyContext`.

            If context is Default/False [default], uses the current context.
            Resource may add additional kwargs when overriding this method if needed [rare]
            to customize things or return alternate resource based on passed-in info
            [example: like passing in a hash-key of some sort]. Although, latley I've been using
            a Manager resource for things like this, example:

            >>> class SomeResourceManager(Resource):
            ...     def get_resource_via(self, some_key: str) -> SomeResourceType:
            ...         # Lookup and return something
            ...         pass
            >>> SomeResourceManager.resource().get_resource_via("some-hash-key")
            SomeResourceType(ident: ...)
        """
        if not for_context:
            for_context = GlazyContext.current()

        return for_context.resource(for_type=cls)

    @classmethod
    def resource_proxy(cls: Type[R]) -> R:
        """ Convenience method to easily get a wrapped ActiveResourceProxy for cls/self. """
        from .proxy import ActiveResourceProxy
        return ActiveResourceProxy.wrap(cls)

    def context_resource_for_child(self, child_context: GlazyContext):
        """
        Called by `Context` when it does not have a resource of a particular type but it does
        have a value from a parent-context (via it's parent-chain).

        Gives opportunity for the `Resource` to do something special if it wants.

        Default implementation of this method is to simply return `self` when we get asked.
        That way by default, we simply use the same object for every `Context` on the same thread.

        This way it will make a `Resource` subclass by default a sort of 'singleton`; where we try
        and reuse the same instance.
        In this way, the child-context will get the same instance of me as the parent normally.

        You can think of this as making a `Resource` act like a singleton by default,
        as only one instance (at the root-context) would ever 'normally' be created.

        It's still possible to get a second instance of the resource, however:

        - If someone created a new resource themselves manually and adds it to a new Context
            and then activates the context,
            that resource they created and added themselves could be a second instance.
            (for more details, see [Activating New Resource](#activating-new-resource))

            THis is because the Resource that was manually created was not given an opportunity
            to reused the parent value.

            However, this is usually desirable as whatever manually created the object probably
            wants to override the resource with it's own configured object.

        - If a new `Context` was created at some point later via `Context(parent=None)`
            and then activated. When a resource is next asked for, it must create a new one as
            any previous `Context` would be unreachable until the context was deactivated.
            (for more details, see [Activating New Context](#activating-new-context))

        Args:
            child_context (GlazyContext): A child context that is needing the resource.
        """
        return self

    def context_resource_for_copy(
            self, *, current_context: GlazyContext, copied_context: GlazyContext
    ) -> "Resource":
        """
        When an existing `GlazyContext` instance is used via a `with` statement or as a function
        decorator it will copy it's self for use during the `with` statement
        (ie: it will act as sort of a `template`).

        It will go though and call this method on each resource in the original 'template' context.
        By default we simply return self
        (by default, GlazyContext resources generally try to maintain themselves as singletons).

        If a `Resource` needs to do more, they can override us

        - `Resource.context_resource_for_copy`: Overridable by a resource if non-singleton
            (or other behavior) is desired.
        """
        return self

    def __copy__(self):
        """
        Basic shallow copy protection
        (I am wondering if I should just remove this default copy code).

        `Resource` overrides the default copy operation to shallow copy everything,
        except it will make a new instance for dict/lists
        (so old an new resources don't share the same list/dict instance).

        If you want different behavior, then override.

        A resource could also use `deepcopy` instead when making a copy, if desirable.

        Copying a resource may be useful if you want activate a new resource but have it's
        configuration similar to a current resource (with some tweaks/modifications).
        """
        clone = type(self)()
        dict_copy = self.__dict__.copy()

        # Pop out of the dict-copy any attributes we should skip.
        attrs_to_skip = self.attributes_to_skip_while_copying or []
        for attr_to_skip in ['_context_manager_stack', *attrs_to_skip]:
            dict_copy.pop(attr_to_skip, None)

        for k, v in dict_copy.items():
            if isinstance(v, (list, dict)):
                dict_copy[k] = copy(v)
        clone.__dict__.update(dict_copy)
        return clone

    def __deepcopy__(self, memo=None):
        # Collect a list of things to skip....
        # We always need to have `_context_manager_stack`, subclasses can set
        # `attributes_to_skip_while_copying` if they have additional ones they want to skip.
        skip_attributes = {
            x for x in ['_context_manager_stack', *(self.attributes_to_skip_while_copying or [])]
        }

        # If we get called without a memo, allocate a blank dict.
        if memo is None:
            memo = {}

        # Check to see if we are already in the memo, if we are then use that instead of
        # making a copy of self again.
        already_copied = memo.get(id(self))
        if already_copied:
            return already_copied

        # Make new object, put it in memo so if we encounter `self` in the future we will reuse it.
        copy = type(self)()
        memo[id(self)] = copy

        # Deepcopy everything except the ones user wants to ignore.
        for k, v in self.__dict__.items():
            try:
                if k in skip_attributes:
                    continue
                copy.__dict__[k] = deepcopy(v, memo)
            except TypeError:
                continue  # Ignore type errors

        return copy

    _context_manager_stack: List[GlazyContext] = None
    """ Keeps track of context's we created when self (ie: `Resource`) is used in a `with`
        statement.  This MUST be reset when doing a copy of the resource.
    """

    def __enter__(self: R) -> R:
        if self._context_manager_stack is None:
            self._context_manager_stack = []

        # We make a new GlazyContext object, and delegate context-management duties to it.
        context = GlazyContext(resources=self)
        self._context_manager_stack.append(context)
        context.__enter__(use_a_copy_of_self=False)
        return self

    def __exit__(self, *args, **kwargs):
        stack = self._context_manager_stack
        if not stack:
            raise XynResourceError(
                f"While using ({self}) as a context manager via a `with` statement,"
                f"somehow we did not have an internal context from the initial entering "
                f"(see `glazy.context.Resource.__enter__`). "
                f"Indicates a very strange bug."
            )

        context = stack.pop()
        context.__exit__(*args, **kwargs)

    def __call__(self, func):
        """
        This makes Resource subclasses have an ability to be used as function decorators
        by default unless this method is overriden to provide some other funcionality.

        If sublcasses do need to override this, I would recemend checking the first positional
        argument for a callable (and no other arguments are passed in) to maintain their ability
        to be function decorators.
        Something like this:

        >>> class MyResource(Resource):
        ...     some_param = None
        ...     def __init__(self, some_param = None):
        ...         self.some_param = some_param
        ...
        ...     def __call__(self, *args, **kwargs):
        ...         if len(args) == 1 and not kwargs and callable(args[0]):
        ...             return super().__call__(args[0])

        This method will check for a callable being passed in as first argument.
        I will raise an error with a descriptive error message if we don't get a callable.

        We should get a callable if Resource subclass is used like in the example below.
        (Config being a resource subclass).

        In this example, a new Config resource is being created and we tell it to only use
        the `EnvironmentalProvider` and we use it as a function decorator.
        This means while the `some_method` function is executing,
        that Config object is made the current one.

        `some_method` and any other method called from within `some_method` will
        only be using the `EnvironmentalProvider` for looking up configuration by default.

        >>> my_resource = MyResource.resource_proxy()
        >>> assert my_resource.some_param is None
        >>>
        >>> @MyResource(some_param="alternate-value")
        >>> def some_method():
        ...     # Only searches: overrides, environ-vars, defaults
        ...     assert my_resource.some_param == 'alternate-value'

        Args:
            func (Callable): decorated function passed in via python decorator syntax.

                >>> @MyResource()
                >>> def some_method():
                ...     pass

        Returns: We execute decorated method and return whatever it returns.
        """
        if not callable(func):
            raise XynResourceError(
                f"Attempt to calling a Resource of type ({self}) as a callable function. "
                f"By default (unless resource subclass does/says otherwise) you need to use "
                f"it as a decorator when calling it. "
                f"When using a Resource subclass as a decorator, Python will call the Resource "
                f"and pass in a callable function. The resource will then make self the current "
                f"resource via `with self` and call the passed in function inside that with "
                f"statement, returning the result of calling the passed in function."
            )

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return wrapper


class PerThreadResource(Resource):
    """
    Same as `Resource`, except we set the `Resource.resource_thread_safe` flag to False,
    this means when an instance of us is created by the system lazily,
    it will not be shared between threads.

    Basically, when some other thread asks for this resource,
    the system will lazily create another one just for that thread to use.
    This happens when a particular thread asks for the resource for the first time.

    When the same thread asks for the resource a second time, it will not create a new one but
    return the resource instance that was originally created just for that thread.

    ## Details

    Normally, when a new `Resource` subclass needs to be created on-demand for the first time
    the new Resource will be placed in the app's root `glazy.context.GlazyContext`,
    which each thread's root-context has set as its parent.
    This makes the object available to be seen/used by other threads.

    When a resource makes a subclass from `PerThreadResource` or otherwise set's
    the `Resource.resource_thread_safe` to False at the Resource class-level.
    When a thread asks for that resource for first time it will be lazily created like expected,
    but the resulting object is placed in the root-context instead (and NOT the app-root-context).

    That way, only the specific thread the Resource was lazily created on will see the object;
    no other thread will.

    Therefore, when other threads also ask for the resource, they will each create their own
    the first time they ask for it, and place it in their thread-root
    `glazy.context.GlazyContext`.
    """
    resource_thread_safe = False
