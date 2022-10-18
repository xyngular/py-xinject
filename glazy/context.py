"""
Manage shared resource and dependency injection.


# To Do First:

If you have not already, to get a nice high-level overview of library see either:

- project README.md here:
    - https://github.com/xyngular/py-glazy#how-to-use
- Or go to glazy module documentation at here:
    - [glazy, How To Use](./#how-to-use)


# Quick Start

## Please Read First

If your looking for a simple example/use of singltone-like resources,
go to `glazy.resource.Resource`.

The whole point of the `Context` is to have a place to get shared resources.

Normally, code will use some other convenience methods, as an example:

Most of the time a resource will inherit from `glazy.resource.Resource` and that
class provides a class method `glazy.resource.Resource.resource` to easily get a
resource of the inherited type from the current context as a convenience.

So normally, code would do this to get the current object instance for a Resource:

>>> class SomeResource(Dependency):
>>>    my_attribute = "default-value"
>>>
>>> # Normally code would do this to interact with current resource object:
>>> SomeResource.resource().my_attribute = "change-value"

Another convenient way to get the current resource is via the
`glazy.resource.ActiveResourceProxy`. This class lets you create an object
that always acts like the current/active object for some Resource.
So you can define it at the top-level of some module, and code can import it
and use it directly.

I would start with [Fundamentals](#fundamentals) if you know nothing of how `Context` works
and want to learn more about how it works.

Most of the time, you interact with Context indrectly via
`glazy.resource.Resource`.  So getting familiar with Context is more about
utilize more advance use-cases. I get into some of these advanced use-cases below.

.. important:: The below is for advanced use-cases and understanding.
    Look at `glazy.resource.Resource` or docs just above ^^^ for the normal use-case and
    examples / quick starts.

# Context Overview

Context is used to keep track of a set of resources. The resources are keyed off the class
type. IE: One resource per-context per-resource-type.

Main Classes:

- `Context`: Container of resources, mapped by type.
- For Resource Subclasses:
    - `glazy.resource.Resource`: Nice interface to easily get the current resource.
        Used to implment a something that should shared and not generally duplicated,
        like a soft-singleton.

# Fundamentals

`Context` is like a container, used to store various objects we are calling resources.

Used to store various resources of any type  in general [ie: configs, auths, clients, etc].
All of these resources together represent a sort of "context" from which various pieces of code
can easily get them; that way they can 'share' the resource when appropriate. This is a way
to do dependcy injection in a easier and more reliable way since you don't have to worry
about passing these resources around everywhere manually.

The values are mapped by their type.  When a resource of a specific type is asked for,
the Context will return it if it find it. If not found it will create it, add it to it's self
and return it. Future calls will return this new resource.

`Context` can optionally have a parent. By default, a newly created/used Context will use
 the current context Normally, resources are still normally created even if a
parent has a value, as long as the current context does not have one yet.

This behavior can be customized by the resource, see one of these for details:

- `glazy.resource.Resource`
    - Useful for a shared/soft overridable shared object; where you can easily get the current
        version of it.


## Resources
[resources]: #resources

There are various ways to get resources from the current context. Let's say we have
a resource called `SomeResourceType`:

>>> next_identifier = 0
>>> class SomeResourceType(Dependency):
...     def __init__(self):
...         global next_identifier
...         self.some_value = "hello!"
...         self.ident = next_identifier
...         next_identifier += 1

.. note:: SomeResourceType's `ident` field get's incremented and set on each newly created object.
    So the first SomeResoureType's `ident` will equal `0`,
    the second one created will be `1` and so forth.

If what you want inherits from `glazy.resource.Resource`, it has a nice class method that
returns the current resource.
The easiest way to get the current resource for the type in this case is
to call `glazy.resource.Resource.resource` on it's type like so:

>>> SomeResourceType.resource().some_value
'hello!'
>>> SomeResourceType.resource().ident
0

When a Context does not have the resource, by default it will create it for you, as you
saw in the previous example.

`Context.current()` will return the current Context if no params are passed in, or if a
type is passed in, it will return the current Context's resource for the passed in type.

This means another way to grab resources is to get the current `Context.current`,
and then ask it for the resource like below. This works for any type, including
types that don't inherit from `glazy.resource.Resource`:

>>> UContext.current().resource(SomeResourceType).some_value
'hello!'

If you pass a type into `Context.current`, it will do the above ^ for you:

>>> UContext.current(SomeResourceType).some_value
'hello!'
>>> UContext.current(SomeResourceType).ident
0

As you can see, it still returns the same object [ie: `ident == 0`]

## Activating New Resource

You can easily create a new resource, configure it however you like and then 'activate' it
so it's the current version of that resource.
This allows you to 'override' and activate your own copy of a resource.

You can do it via one of the below listed methods/examples below.

For these examples, say I have this resource defined:

>>> from dataclasses import dataclass
>>> from glazy import Dependency
>>>
>>> @dataclass
>>> class MyResource(Dependency):
>>>     some_value = 'default-value'
>>>
>>> assert MyResource.resource().some_value == 'default-value'

- Use desired `glazy.resource.Resource` subclass as a method decorator:

        >>> @MyResource(some_value='new-value')
        >>> def my_method():
        >>>     assert MyResource.resource().some_value == 'new-value'

## Activating New Context

When you create a new context, you can activate it to make it the current context in three ways
(listed below). Keep in mind that when you make a context current and 'activate' it,
it will implicitly **copy** it's self (so it's unattached from the orginal Context) and
the copy is what is made current/activated (see `Context.__copy__` for more details if intrested).

1. Via the `with` statement.
2. As a method dectorator, ie: `@`.
3. Permently activiating it via `Context.make_current`, making it the new Default/Base
   context in general.
4. When running a unit-test where glazy is installed as a dependcy,
    because the `glazy.ptest_plugin.glazy_test_context` fixture is auto-used in this case.
    This fixture creates a new Context with a None parent;
    that will isolate resources between each run of a unit test method.

### Examples

Here are examples of the four ways to create/activate a new context:

>>> with UContext():
...     SomeResourceType.resource().ident
1

This is stack-able as well; as in this can keep track of a stack of contexts, in a
thread-safe way.

When the context manager or decorated method is exited, it will pop-off the context and it won't
be the default one anymore. Whatever the default one was before you entered the `with` will
be the default once more.

>>> @UContext():
>>> def a_decorated_method():
...     return SomeResourceType.resource().ident
>>> a_decorated_method()
2
>>> a_decorated_method()
3
>>> SomeResourceType.resource().ident
0

As you can see, after the method exits the old context takes over, and it already had the
older version of the resource and so returns that one.

By default, a context will create a resource when it's asked for it and it does not have it
already. As you saw above, every time a blank Context was created, it also created a new
SomeResourceType when it was asked for it because the new blank `Context` did not already
have the resource.


>>> UContext().make_current()
>>> SomeResourceType.resource().ident
4

With the context test fixture, it creates a brand new parent-less context every time a test runs
(see `Context.parent` for more about parents). You can use it like so:

>>> from glazy.fixtures import context
>>> def test_some_text(context):
...    SomeResourceType.resource()



There are ways to share resource in a parent Context that a new blank context would beable
to use. But that's more advanced usage. The above should be enough to get you started quickly.
See below for more advanced usage patterns.

# Parents

A Context can have a parent (`Context.parent`) or event a chain of them (`Context.parent_chain`)

Because it's the safest thing to do by default for naive resources, Context's normally don't
consult parents for basic resources, they will just create them if they don't already have them.

You can customize this behavior. There are some default resource base classes that will implment
a few common patterns for you. You can see how they work to get ideas, and customize the process
for your own resource when needed. See [Resource Base Classes][resource-base-classes] below for
more details on how to do that.

You can make an isolated Context by doing:

>>> UContext(parent=None)

When creating a new context. This will tell the context NOT to use a parent. By default, a
Context will use the current Context as the time the Context was created as it's parent.
See `Context.parent` for more details.

This is also how the Context test fixture works (see `glazy.ptest_plugin.glazy_test_context`). It creates
a new parent-less context and activates it while the fixture is used.

# Resource Base Classes
[resource-base-classes]: #resource-base-classes.

### `glazy.resource.Resource`

You can implment the singleton-pattern easily by inherting from the
`glazy.resource.Resource` class.
This will try it's best to ensure only one resource is used amoung a chain/tree of parents.
It does this by returning `self` when `Context` asks it what it wants to do when a child-context
asks for the resource of a specific type.
Since `glazy.resource.Resource` can be shared amoung many diffrent child Context objects,
and makes the same instance always 'look' like it's the current one;
generally only one is every made or used.

However, you can create a new Context, make it current and put a diffrent instance of the
resource in it to 'override' this behavior.
See [Activating New Resource](#activating-new-resource) for more details.

#### Example

I create a new class that uses our previous [SomeResourceType][resources] but adds in a
`glazy.resource.Resource`.

>>> class MySingleton(SomeResourceType, Dependency):
...     pass
>>> MySingleton.resource().ident
5

Now watch as I do this:

>>> with UContext():
...     MySingleton.resource().ident
5

The same resource is kept when making a child-context. However, if you make a parent-less
context:

>>> with UContext(parent=None):
...     MySingleton.resource().ident
6

The `glazy.resource.Resource` will not see pased the parent-less context,
and so won't see the old resource.
It will create a new one. The `glazy.resource.Resource` will still create it in the
furtherest parent it can... which in this case was the `Context` activated by the with statement.

"""
import contextvars
import itertools
import functools
from typing import TypeVar, Type, Dict, List, Optional, Union, Any, Iterable
from copy import copy
from guards.default import Default, DefaultType, Singleton
from glazy.errors import XynResourceError

T = TypeVar('T')
C = TypeVar('C')
ResourceTypeVar = TypeVar('ResourceTypeVar')
"""
Some sort of resource, I am usuallyemphasizingg with this that you need to pass in the
`Type` or `Class` of the resource you want.
"""


# Tell pdoc3 to document the normally private method __call__.
__pdoc__ = {
    "UContext.__call__": True,
    "UContext.__copy__": True,
    "Dependency.__call__": True,
    "Dependency.__copy__": True
}

# Thread-safe / Lock-Free counter
_ContextCounter = itertools.count()


class _TreatAsRootParentType(Singleton):
    """
    Use `TreatAsRootParent`. This class is an implementation detail,
    to ensure that there is ever only one `TreatAsRootParent` value.
    I based this off how None works in Python [ie: a None + NoneType]
    """
    pass


_TreatAsRootParent = _TreatAsRootParentType()
""" Can be used for the parent of a new `UContext`, it will make the context a root-like
    context. What this means is the parent is treated as if you set it to `None` while at the
    same time altering the copying/activating behavior.

    When you make a copy of a root-like `UContext`, or use it in a `with` or `@` decorator
    which will also copy of the UContext and activate the copy. When this happens the new context
    will use the currently activated context as it's parent.

    Normally when you pass in `None` as the parent of a new context, ie:

    >>> UContext(parent=None)

    New copies of that context object will have their parent set as None.

    For a root-like context created like this:

    >>> UContext(parent=_TreatAsRootParent)

    When activating this context, it will make a copy and have it's parent set as None.
    But if you then make another copy of this root-like context, the new context will
    have it's parent set to the Default/Current context instead of staying as None.

    The idea here is, if you pass in an explicit None, then we should always use None including
    in copied.  But root-like objects are a bit special, they have no parent because they are
    supposed to be the 'first' one, and we don't necessarily want any copies of this
    root-like context to keep using `None`.
"""


# todo: Remove ContextType
class UContext:
    """
    See [Quick Start](#quick-start) in the `glazy.context` module if your new to the UContext
    class.
    """

    @classmethod
    def current(cls, for_type: Union[Type[C], "UContext"] = None) -> Union[C, "UContext"]:
        """ Gets the current context that should be used by default, via the Python 3.7 ContextVar
            feature. Please see UContext class doc [just above] for more details on how this works.
        """
        context = _current_context_contextvar.get()

        # If we are None, we need to create the 'root-context' for current thread.
        if context is None:
            import threading
            context = UContext(name=f'ThreadRoot-{threading.current_thread().name}')
            context._make_current_and_get_reset_token(is_thread_root_context=True)

        if for_type in (None, UContext):
            return context

        return context.resource(for_type=for_type)

    @classmethod
    def _current_without_creating_thread_root(cls):
        return _current_context_contextvar.get()

    def make_current(self) -> 'UContext':
        """
        Read [Quick Start](#quick-start) first if you don't know anything about how `Context`
        works.

        Makes a **copy** of this Context object (which I will return), and makes that copy the
        current one the current thread until:

        1. Another Context object is made current.
        2. If while calling `make_current` the current context is temporary. Once the current
           context is not temporary anymore, the current context reverts back to what it was
           before that change happened. ie:

        .. note:: See `Context.__copy__` for more details on copying aspect.

        Example of this via a 'with'`' statement:
        >>> before_context = UContext.current()
        >>> with UContext() as my_context:
        ...    assert UContext.current() is my_context
        ...    another_context = UContext()
        ...    active_context_copy = another_context.make_current()
        ...    assert UContext.current() is active_context_copy
        >>> assert UContext.current() is before_context

        Example of this via a '@' method decorator statement:

        >>>
        >>> before_int_resource_value = UContext.current(for_type=int)
        >>> method_context = UContext(resources=[20])
        >>>
        >>> # This dectorator will make a copy of `method_context` each time `my_method` is called.
        >>> @method_context
        >>> def my_method():
        ...     assert UContext.current(for_type=int) == 20
        ...     another_context = UContext(resources=[19])
        ...     another_context.make_current()
        ...     assert UContext.current(for_type=int) == 19
        ...     # After method exits, due to `@method_context` the previous context
        ...     # state will be restored.
        >>> assert UContext.current(for_type=int) == before_int_resource_value

        ## Other Notes

        If you want to have a config object only temporarily current for the current thread,
        use it in a with statement:

        >>> with UContext() as my_context:
        ...     assert UContext.current() is my_context
        ... assert UContext.current() is not my_context

        Or as a method decorator:

        >>> some_context = UContext()
        >>> @some_context:
        >>> def my_method()
        ...     # Current context will be copy of `some_context` (with it's resources intact).

        If you use this method, it will make current permanently a copy of the 'current' context.

        Normally you would avoid make a context 'permanet' unless your trying to setup
        something special at the start of the application.

        Normally using the pre-allocated/existing permanet root context, or a temporary one via
        dectorator `@` / `with` statement is the way to go.

        Using `make_current` is more useful for situations where you are setting
        up a new "default" context for entire app, that you want everything in the project to
        generally use that would sit on top of the pre-allocated root-context.
        """
        new_ctx = copy(self)
        new_ctx._make_current_and_get_reset_token()
        return new_ctx

    def _make_current_and_get_reset_token(
        self,
        is_thread_root_context=False,
        is_app_root_context=False
    ) -> Optional[Any]:
        """ See `UContext.make_current` docs for more details.

            This method is called by `UContext.make_current`, but will also pass back the reset
            token (to be used internally in this module).

            Args:
                is_thread_root_context: This is simply a flag. You should have used the
                    `_TreatAsRootParent` as the parent when creating the context
                    and wanting it to be a 'root-context'.

                is_app_root_context: This tells us to NOT add this UContext to the
                    per-thread `_current_context_contextvar`.  Instead, we activate
                    this context as the app-root context that is shared between all threads.
                    We only ever have one of these, and it's always allocated at
                    a module-level attributed called `_app_root_context`.
                    Should never be set to True except for the object allocated at
                    module-import time into that variable.

                    Only returns None when this is True.
        """
        if is_thread_root_context:
            # For debugging purposes, so you know which one was truly the thread-root context
            # if there is another root-like-context made (for unit tests).
            self._is_root_context_for_thread = True
            assert self._parent is Default, "See my methods doc-comment for details."

        if is_app_root_context:
            self._is_root_context_for_app = True
            assert self._parent is _TreatAsRootParent, "See my methods doc-comment for details."

        if self._parent is Default:
            # Side Note: This will be `None` if we are the first UContext on current thread.
            self._parent = UContext._current_without_creating_thread_root()

            if self._parent is None:
                # We set parent to use app-root-context if we are the thread-root-context.
                self._parent = _app_root_context
        elif self._parent is _TreatAsRootParent:
            # When you activate a context who should be treated as root, we have a None
            # parent and we set `_originally_passed_none_for_parent` to False
            # to indicate future activations/copies of the context should NOT be root
            # and should get the 'Default' as their parent.
            self._parent = None
            self._originally_passed_none_for_parent = False

        self._is_active = True

        if is_app_root_context:
            return None

        # This makes my self the current context permanently on the current-thread.
        # This is a special context-var [introduced in Python 3.7].
        #
        # We return the reset token, but it's only used internally when calling this method.
        # outside people should ignore token.
        return _current_context_contextvar.set(self)

    @property
    def parent(self) -> Optional["UContext"]:
        parent = self._parent
        if self._is_active:
            if parent is None:
                return None

            if parent:
                return parent

            raise XynResourceError(
                f"Somehow we have a UContext has been activated "
                f"(ie: has activated via decorator `@` or via `with` or via "
                f"`UContext.make_active` at some point and has not exited yet) "
                f"but still has it's internal parent value set to `Default`. "
                f"This indicates some sort of programming error or bug with UContext. "
                f"An active UContext should NEVER have their parent set at `Default`. "
                f"It should either be None or an explict parent UContext instance "
                # Can't resolve parent, would create infinite recursion.
                f"({self.__repr__(include_parent=False)}). "
                f"A UContext should either have an explicit parent or a parent of `None` after "
                f"UContext has been activated via `@` or `with` or `UContext.make_current()`; "
                f"(side note: you can look at UContext._is_active doc-comment for more internal "
                f"details)."
            )

        # If we are not 'active' (ie: via `with` or `make_current()` or decorator `@`)
        # and we have our internal parent set to `Default`;
        # lookup current active context and make that our 'parent' temporarily (ie: dynamically),
        # next time we are asked it could change. That's fine as long as we are not 'active'.
        #
        # Honestly, looking up resources with a non-active context should be pretty rare,
        # I am allowing it for more of completeness at this point then anything else.
        # However, it might be more useful at some point.
        if parent is Default:
            return UContext.current()

        if parent in (_TreatAsRootParent, None):
            return None

        raise XynResourceError(
            f"Somehow we have a UContext that is not active "
            f"(ie: ever activated via decorator `@` or via `with` or via "
            f"`UContext.make_active`) but has a specific parent "
            f"(ie: not None or _TreatAsRootParent or Default). "
            f"This indicates some sort of programming error or bug with UContext. "
            f"A UContext should only have an explicit parent if they have "
            f"been activated via `@` or `with` or `UContext.make_current()`; "
            f"(side note: you can look at UContext._is_active for more internal details)."
        )

    @property
    def name(self) -> str:
        """ Name of context (for debugging purposes only).
            Right now this defaults to a unique number, that gets incremented each time a
            `UContext` is created (in it's init method).

            May allow customization in the future.
        """
        return self._name

    def __init__(
            self, __func=None, *,
            resources: Union[Dict[Type, Any], List[Any], Any] = None,
            parent: Union[DefaultType, _TreatAsRootParentType, None] = Default,
            name: str = None
    ):
        """
        You can give an initial list of resources
        (if desired, most of the time you just start with a blank context).

        for `parent`, it can be set to `guards.default.Default` (default value); or to `None.

        If you don't pass anything to parent, then the default value of `Default` will cause us
        to lookup the current context and use that for the parent automatically when the
        UContext is activated.
        For more information on activating a context see
        [Activating A UContext](#activating-a-context).

        If you pass in None for parent, no parent will be used/consulted. Normally you'll only
        want to do this for a root context. Also, useful for unit testing to isolate testing
        method resources from other unit tests. Right now, the unit-test resource isolation
        happens automatically via an auto-use fixture (`glazy.ptest_plugin.glazy_test_context`).

        A non-activated context will return `guards.default.Default` as it's `UContext.parent`
        if it was created with the default value;
        otherwise we return `None` (if it was created that way).

        Args:
            resources (Union[Dict[Type, Any], List[Any], Any]): If you wish to have the
                `UContext` your creating have an initial list of resources you can pass them
                in here.

                It can be a single resource, or a list of resources, or a mapping of resources.

                Mainly useful for unit-testing, but could be useful elsewhere too.

                They will be added to use via `UContext.add_resource` for you.

                If you use a dict/mapping, we will use the following for `UContext.add_resource`:

                - Dict-key as the `for_type' method parameter.
                - Dict-value as the `resource` method parameter.

                This allows you to map some standard resource type into a completely different
                type (useful for unit-testing).

                By default, no resources are initially added to a new UContext.

            parent (Union[guards.default.Default, _TreatAsRootParent, None]): If we should use
                `guards.default.Default`, treat this as a root-like UContext, or use None as
                parent.

                Right now the only valid option is to do one of these three options:

                - nothing (ie: leave at `guards.default.Default`): If left as
                    `guards.default.Default`, We lookup current context and use that as the
                    parent in self and in copies or when self is used in a `with` statement or as
                    a decorator.
                - Pass `None`, indicating to not use any parent for current thread,
                    even if copied or used in a decorator/with-statement.
                    This means app-root, and any current thread-root will be ignored.
                - Pass `_TreatAsRootParent`, indicating to not use any parent, but allow copies
                    or when used as decorator/with-statement to use the currently activate
                    UContext as the new copies parent.

                    This option should **ONLY** be used internally in this module.

                    If you use `_TreatAsRootParent` as the value, keep in mind that a root-like
                    UContext is special, as it never has a parent and is also considered to have
                    a default parent if it's copied. A context is shallow copied, and the copy
                    activated when used as a decorator or in a `with` statement.

                    `_TreatAsRootParent ` should only be used INTERNALLY in this module,
                    it's not currently exposed publicly.

                    See `_TreatAsRootParent` for more details on root-like contexts.

            name (str): Optional name.
                If left as None, by default, this will simply assign a unique sequential
                number to the name.

                If name is passed in, it will be appended to the unique sequential number.

                When UContext is printed in a string, it will include
                this as it's name to make debugging easier.

        """

        # This means we were used directly as a function decorator, ie:
        # >>> @UContext
        # >>> def some_method():
        # ...     pass
        #
        # Store the decorated function for later use
        # (for when decorated method get's called).
        if __func and not callable(__func):
            raise XynResourceError(
                "First position argument was NOT a callable function; "
                "The first positional argument `__func` is reserved for a decorated function "
                "when you do use UContext directly as a decorator, "
                "ie: `@UContext` (notice no parens at end)."
            )
        self._func = __func
        if __func:
            # Make our class appear to be '__func', ie: we are wrapping __func
            # due to using UContext like this:
            #
            # >>> @UContext  # <-- notice not parens at end "()"
            # >>> def some_method():
            # ...     pass
            functools.update_wrapper(self, __func)

        # Unique sequential number.
        self._name = str(next(_ContextCounter))
        if name:
            self._name = f'{self._name}-{name}'

        self._reset_token_stack = []
        self._resources = {}
        self._parent = None

        if parent is Default:
            self._parent = Default
            self._originally_passed_none_for_parent = False
        elif parent is None:
            self._parent = None
            self._originally_passed_none_for_parent = True
        elif parent is _TreatAsRootParent:
            self._parent = _TreatAsRootParent
            self._originally_passed_none_for_parent = False
            self._is_root_like_context = True
        else:
            raise XynResourceError(
                "You must only pass in `Default` or `None` or `_TreatAsRootParentType` for parent "
                f"when creating a new UContext, got ({parent}) instead."
            )

        # Add any requested initial resources.
        if isinstance(resources, dict):
            # We have a mapping, use that....
            for for_type, resource in resources.items():
                self.add_resource(resource, for_type=for_type)
        elif isinstance(resources, list):
            # We have one or more resource values, add each one.
            for resource in resources:
                self.add_resource(resource)
        elif resources is not None:
            # Otherwise, we have a single resource value.
            self.add_resource(resources)

    # todo: Make it so if there is a parent context, and the current config has no property
    # todo: it can ask the UContext for the parent config to see if it has what is needed.
    def add_resource(
            self, resource: Any, *, skip_if_present=False, for_type: Type = None
    ) -> "UContext":
        """
        Lets you add a resource to this context, you can only have one-resource per-type.

        Returns self so that you can keep calling more methods on it easily.... this allws you
        to also add a resource and then use it directly as decorator (only works on python 3.9),
        ie:

        >>> # Only works on python 3.9+, it relaxes grammar restrictions
        >>> #    (https://www.python.org/dev/peps/pep-0614/)
        >>>
        >>> @UContext().add_resource(2)
        >>> def some_method()
        ...     print(f"my int resource: {UContext.resource(int)}")
        Output: "my int resource: 2"

        As as side-note, you can easily add resources to a new `Context` via:

        >>> @UContext(resources=[2])
        >>> def some_method()
        ...     print(f"my int resource: {UContext.resource(int)}")
        Output: "my int resource: 2"

        With the `Context.add_resource` method, you can subsitute resource for other
        resource types, ie:

        >>> def some_method()
        ...     context = UContext()
        ...     context.add_resource(3, for_type=str)
        ...     print(f"my str resource: {UContext.resource(str)}")
        Output: "my str resource: 3"

        If you need to override a resource, you can create a new context and set me as it's
        parent. At that point you can add whatever resources you want before anyone else
        uses the new `Context`.

        .. warning:: If you attempt to add a second resource of the same type...
            ...a `glazy.XynResourceError` will be
            raised. This is because other objects have already gotten this resource and are
            relying on it now.  You need to configure any special resources you want to add
            to this context early enough before anything else will need it.

        .. todo:: Consider relaxing this ^ and not producing an error [or at least an option
            to 'replace' an existing resource in an existing Context. I was cautious on this
            at first because it was the safest thing to do and I could always relax it later
            if I found that desirable. Careful consideration would have to be made.

        Args:
            resource (Any): Object to add as a resource, it's type will be mapped to it.

            skip_if_present (bool): If False [default], we raise an exception if resource
                of that type is already in context/self.

                If True, we don't do anything if resource of that type is already in
                context/self.

            for_type: You can force a particular mapping by using this option.
                By default, the `for_type` is set to the type of the passed in resource
                [via `type(resource)`].

                You can override this behavior by passing a type in the `for_type` param.
                We will then map the resource for `for_type` to the `resource` object when
                a resource is requested for `for_type` in the future. Will still raise the
                error if a resource for `for_type` already exists in Context.
        """
        resource_type = type(resource)
        if for_type is not None:
            resource_type = for_type

        if resource_type in self._resources:
            if skip_if_present:
                return self
            # todo: complete/figure out comment!
            # if not rep
            raise XynResourceError(f"Trying to add resource ({resource}), but already have one!")

        self._resources[resource_type] = resource
        return self

    def resource(
            self, for_type: Type[ResourceTypeVar], create: bool = True
    ) -> ResourceTypeVar:
        """

        ## Summary

        The whole point of the `Context` is to have a place to get shared resources. This method
        is the primary way to get a shared resource from a Contet directly

        Normally, code will use some other convenience methods, as an example:

        Normally a resource will inherit from `glazy.resource.Resource` and that
        class provides a class method `glazy.resource.Resource.resource` to easily get a
        resource of the inherited type from the current context as a convenience.

        So normally, code would do this to get a Resource:

        >>> class SomeResource(Dependency):
        >>>    pass
        >>> # Normally code would do this to get current resource object:
        >>> SomeResource.resource()

        Another convenient way to get the current resource is via the
        `glazy.resource.ActiveResourceProxy`. This class lets you create an object
        that always acts like the current/active object for some Resource.
        So you can define it at the top-level of some module, and code can import it
        and use it directly.

        I would start with [Quick Start](#quick-start) if you know nothing of how `Context` works
        and want to learn more about how it works.

        Most of the time, you interact with Context indrectly via
        `glazy.context.Resource`.  So getting familure with Context is more about
        utilize more advance use-cases. I get into some of these advanced use-cases below.

        ## Advanced Usage for Unit Tests

        You can allocate a new Context to inject or customize resources. When the context is
        thrown away or otherwise is not the current context anymore, the idea is whatever
        resource you made temporarily active is forgotten.

        You can inject/replace resources as needed for unit-testing purposes as well by simply
        adding the resource to a new/blank `Context` as a diffrent type, see example below.

        In this example, we add a value of int(20) for the `str` resource type.
        I used built-int types to simplify this, but you can image using your own
        custom-resource-class and placing it in the Context for the normal-resource-type
        the normal code asks for.

        >>> UContext().add_resource(20, for_type=str)
        >>> UContext().resource(str)
        Output: 20

        ## Specific Details

        Given a type of `glazy.resource.Resource`, or any other type;
        we will return an instance of it.

        If we currently don't have one, we will create a new one of type passe in and return that.
        We will continue to return the one created in the future for the type passed in.

        You can customize this process a bit by having your custom resource inherit from
        `glazy.resource.Resource`.

        Otherwise, no other parameters will be sent to init method.

        If you have an `for_type` class of any sort
        that needs extra parameters and you want to use it as a Resource, you can create it
        yourself and add it to the Context via `add_resource`.  I would recommend in this case a
        class-method on the `for_type` class that would accept these extra parameters and then
        check the current Context and allocate or return the existing context resource as needed.

        Args:
            for_type (Type[ResourceTypeVar]): The type of resource you need, and instance of
                this type will be returned.

            create (bool): Whether to create resource if needed or not.
                If `True` [default]: creates the resource if it does not exist in self.
                If `False`: only returns an object if we have it already, otherwise None.

            use_parent (bool): Controls how the parent is used.

                If `False` [default]: we won't check the parent for the resource to return. We may
                still consult the parent in order to create a new resource from it; the use of
                the resource from parent is dependent on the resource. It has the option to decide
                what to do in this case. That's why this is False by default, it gives the option
                of what to do with the parent resource [if any] to the resource it's self. It has
                more knowledge about what it's situation is and can make a more informed decision.

                If `True`: and the resource is not directly in `self`, we will ask the parent
                `Context`; if we have a parent for the resource and return that if it's found.
                If a resource is found this way, we won't add it to `self` directly,
                only return it for you to use.

                If the resource is not in self and is not found in parent, then we will create it
                if `create=True` [default] and add that to `self` and return it.
                Otherwise, we return `None`.
        """

        # If we find it in self, use that; no need to check anything else.
        obj = self._resources.get(for_type, None)
        if obj is not None:
            return obj

        # If we are the root context for the entire app (ie: app-root between all threads)
        # then we check to see if resource is thread-sharable.
        # If it is then we continue as normal.
        # If NOT, then we always return None.
        # This will indicate to the thread-specific UContext that is calling us to allocate
        # the object in it's self.
        # If something else is asking us, we still return None because this Dependency does not
        # belong in us and so we should not accidently auto-create it in us.
        # ie: Whoever is calling is should handle the None case.
        #
        # In Reality, the only thing that should be calling the app-root context
        # is a thread-root context.  Thread root-contexts should never return None when asked
        # for a resource.
        # So, code using a Dependency in general should never have to worry about this None case.
        if self._is_root_context_for_app:
            from glazy import Dependency
            if issubclass(for_type, Dependency) and not for_type.resource_thread_safe:
                return None

        parent_value = None
        parent = self.parent

        # Sanity check: If we are active we should have a None or an explicit, non-default parent.
        if self._is_active and parent is Default:
            XynResourceError(
                "We somehow have a UContext that has been 'activated' but yet has "
                "their parent still set to `Default`. This is a bug. Active UContext's "
                "should NEVER have their parent set at `Default`. It should either be None "
                f"or an explict parent UContext instance, problem instance: {self}"
            )

        # If we have a Default parent, then lookup current parent and use them for our 'Parent'.
        if parent is Default:
            # An active parent's will never have their self._parent set as Default;
            # The current context is `active` along with it's parent-chain....
            # So this should be safe.
            # Doing an assert here to at least minimally double check this.
            parent = UContext.current()
            assert self is not parent, "Somehow have self and parent as same instance."

        if parent:
            parent_value = parent.resource(for_type, create=create)

        # If we can't create the resource, we can ask the resoruce to potetially create more of
        # it's self.
        # We should also not put any value we find in self either.
        # Simply return the parent_value, whatever it is (None or otherwise)
        if not create:
            return parent_value

        # We next create resource if we don't have an existing one.
        obj = self._create_or_reuse_resource(for_type=for_type, parent_value=parent_value)

        # Store in self for future reuse.
        self._resources[for_type] = obj
        return obj

    def _create_or_reuse_resource(
            self,
            *,
            for_type: Type[T],
            parent_value: Union['Dependency', Any, None] = None
    ) -> T:
        """
        This tries to reuse parent_value if possible;
        otherwise will create new resource of `for_type` and returns it.

        Args:
            for_type: A class/type to create if needed.
            parent_value: If `parent_value` is not None and inherits from `Dependency`
                will ask parent_value to decide if it wants to reuse it's self or create a
                new resource object.

                See `glazy.resource.Dependency.context_resource_for_child`
                for more details if you want to customize this behavior.
        """
        from glazy import Dependency
        try:
            # Allocate a blank object if we have no parent-value to use.
            if parent_value is None:
                return for_type()

            # If we have a context-resource AND a parent_value;
            # then ask parent_value Dependency to do whatever it wants to do.
            # By default, `glazy.resource.Dependency.context_resource_for_child`
            # returns `self`
            #   to reuse resource value.
            if parent_value and isinstance(parent_value, Dependency):
                return parent_value.context_resource_for_child(child_context=self)
        except TypeError as e:
            # Python will add the `e` as the `from` exception to this new one.
            raise XynResourceError(
                f"I had trouble creating/getting resource ({for_type}) due to TypeError({e})."
            )

        # If we have a parent value that is not a `glazy.resource.Dependency`;
        # default to reusing it:
        return parent_value

    def resource_chain(
            self, for_type: Type[ResourceTypeVar], create: bool = False
    ) -> Iterable[ResourceTypeVar]:
        """
        Returns a python generator yielding resources in self and in each parent;
        returns them in order.

        This won't create a resource if none exist unless you pass True into `create`, so it's
        possible for no results to be yielded if it's never been created and `create` == False.

        .. warning:: This is mostly used by `glazy.resource.Dependency` subclasses
            (internally).

            Not normally used elsewhere. It can help the glazy.resource.Dependency`
            subclass to find it's
            list of parent resources to consult on it's own.

            Real Example: `xyn_config.config.Config` uses this to construct it's parent-chain.

        Args:
            for_type (Type[ResourceTypeVar]): The resource type to look for.
            create (bool): If we should create resource at each context if it does not already
                exist.
        Yields:
            Generator[ResourceTypeVar, None, None]: Resources that were found in the self/parent
                hierarchy.
        """
        for context in self.parent_chain():
            resource = context.resource(for_type=for_type, create=create)
            if resource:
                yield resource

    def __copy__(self):
        """ Makes a copy of self, gives an opportunity for resources to do something special
            while they are copied if needed via
            `glazy.resource.Dependency.context_resource_for_copy`.

            We copy `UContext` implicitly and make that copy the 'active' context when it's made
            current/activated via a:

            - decorator `@`,
            - `with` statement,
            - or `UContext.make_current`;

            Using one of the above with a UContext also makes it 'active'
            (see UContext._is_active for more internal details, if your interested ).

            When a context is made current, it's sort of used as a 'template'.
            That way it can be used over and over again without accumulating
            resourced between runs. It will be 'fresh' each time with whatever
            you added in the original 'template'.

            Root and root-like contexts are treated special when it comes to copying with regard
            to how their parent values in their copies are treated.
            See `_TreatAsRootParent` for more details on this aspect.
        """
        from glazy import Dependency
        # Use None for parent if we were originally created with a `None` parent.
        parent = Default
        if self._parent is _TreatAsRootParent:
            # When this context is activated, _TreatAsRootParent will be turned into a None
            # on the object automatically, and properly setup to be a root or root-like context.
            parent = _TreatAsRootParent
        elif self._originally_passed_none_for_parent:
            parent = None

        # Blank context with the same parent configuration
        new_context = UContext(parent=parent)

        # Copy current resources from self into new UContext;
        # This uses `self` as a template for the new UContext.
        # See doc comment on: `UContext.__call__` and
        # `glazy.resource.Dependency.context_resource_for_copy`.
        new_resources = {}
        for k, v in self._resources.items():
            if isinstance(v, Dependency):
                v = v.context_resource_for_copy(current_context=self, copied_context=new_context)
            else:
                v = copy(v)
            new_resources[k] = v

        new_context._resources = new_resources
        # Reset context chain cache, if anything was cached in it.
        new_context._reset_caches()
        return new_context

    def __deepcopy__(self, memo):
        """
        Used to make a deepcopy of self via `copy.deepcopy(some_context)`,
        This will in-turn deep-copy all resources currently in self.

        At the moment, this is not really used. I considered using this for
        unit tests but decided to use an autouse context to setup the needed resources
        instead.

        for now I am just making this method private, as it still works just fine in
        case it's handy to make public and start using again someday.
        Args:
            memo: Memo from `copy.deepcopy`, used to hook up already deep-copied objects
                that have multiple ways/paths to get to in a graph.

        Returns:
            Deep copied object.
        """
        raise XynResourceError(
            "Deepcopy is currently disabled for glazy.context.UContext. "
            "If there is a desire to use it again in the future, remove this exception "
            "as it should still work."
        )
        # return self.__copy__(deepcopy_resources=True, deepcopy_memo=memo)

    def copy(self):
        """ Convenience method to easily shallow-copy a UContext, calls `return copy.copy(self)`.
            Used when you activate a UContext via a decorator or `with` statement.

            When a UContext is activate, it is copied and then the copy is set to active.
        """
        return copy(self)

    def __enter__(self, use_a_copy_of_self: bool = True):
        """ Used to make a Context usable as a ContextManager via `with` statement.
            We will copy self and then activate the copy, returning the copy as the
            output of the with statement.

            >>> # Some pre-existing UContext object.
            >>> some_context: UContext
            >>>
            >>> # Use it in `with` statement:
            >>> with some_context as copied_and_activated_context:
            ...     assert UContext.current() is copied_and_activated_context
            ...     assert UContext.current() is not some_context

            Args:
                use_a_copy_of_self: If True (default): will make a copy of self,
                    activate that and return that context

                    If False: Will activate self, and return self,
                        You MUST ensure that a context that is directly activated and with no
                        copy made is not currently active right now.

                    Generally, `glazy.resource.Dependency.__enter__` will set to this
                    False because it always creates a blank context just for it's self.
                    No need to create two context's.
        """
        # We copy by default, but if requested we can use current context.
        # It's safer to Copy, but if you know what your doing you can use current context
        # instead of activating a copy of it.
        new_ctx = self.copy() if use_a_copy_of_self else self
        token = new_ctx._make_current_and_get_reset_token()
        self._reset_token_stack.append(token)
        return new_ctx

    def __exit__(self, *args, **kwargs):
        # Makes it possible to use a UContext object in a `with UContext():` statement.
        token = self._reset_token_stack.pop()
        current_context = UContext.current()

        # Doing this to be extra-cautious, UContext should dynamically lookup current
        # context if it's not active anymore
        # (ie: outside of / not in python ContextVar: `_current_context_contextvar`).
        #
        # Reset context that is not active anymore back to Default if it had a parent.
        # if the parent is None, it should remain as None.
        # A `Default` parent means it looks up parent dynamically each time (to the current one).
        if current_context._parent:
            current_context._parent = Default
            current_context._reset_caches()

        _current_context_contextvar.reset(token)

    def __call__(self, *args, **kwargs):
        """
        This allows us to support using `Context` as a function decorator in a few ways:

        >>> @UContext
        >>> def some_method():
        ...     pass

        OR

        >>> my_context = UContext()
        >>> my_context.add_resource(Dependency())
        >>>
        >>> @my_context
        >>> def some_method():
        ...     pass

        In either case, we will create and activate NEW context each time `some_method` is called.
        It will be thrown away after the method is finished executing.

        This allows you to make whatever changes you wish to the Context while method is
        is running and it will start fresh again next time it runs.

        In the case of a pre-allocated context, such as `my_context` in the above example;
        we will use that as the template/starting-point each time `some_method` is called;

        What this means is that when `some_method` is called, and we create this new `Context`
        to use. The next `Context` will get the same resources that are/were assigned to it;
        whatever it is at the time `some_method` is called.

        This allows for more fine-control of what is in the `template` context, without
        worrying about taking other changes into it that come later.
        """
        _func = self._func

        def wrapper(*args, **kwargs):
            # If we already have `self._func`,
            # it means we were used directly as a function decorator, ie:
            #
            # >>> @UContext
            # >>> def some_method():
            # ...     pass
            # We always start with a new-blank context in this state
            with copy(self):
                # Use the out-scope `_func` var; which should have the original/decorated method
                # that is being called.
                return _func(*args, **kwargs)

        if _func:
            # If we have a `self._func`, that means we were used as a decorator without
            # using parens, like so:
            #
            # @UContext
            # def some_method():
            #    pass
            #
            # In this case, we just use the stored method we already have.
            # Currently, the decorated method is being called so we execute the call immediately.
            return wrapper(*args, **kwargs)

        # If we don't already have an assigned self._func;
        # we have this situation:
        #
        # @UContext()
        # def some_func():
        #     pass
        #
        # OR
        #
        # some_context = UContext()
        # @some_context
        # def some_func():
        #     pass
        #
        #
        # In the above cases Python will call us to give us the originally decorated func
        # which in the above cases would be `some_func`.
        #
        # Our objective is to wrap a decorated function; such that when decorated method is called
        # we will activate a new context, keeping whatever objects are in `some_context`.
        # After function is done, we will throwaway the new context because it may have
        # objects while `some_func` was running. We don't want to bring any resources
        # created while function was running into future runs of the function.
        # We want to start fresh each time.

        fail_reason = ""
        if len(args) != 1:
            fail_reason = "zero arguments"
        elif not callable(args[0]):
            fail_reason = "one non-callable argument"

        if fail_reason:
            raise XynResourceError(
                f"Used directly as decorator `@UContext` (without ending parens) which is"
                f"normally fine. This normally makes "
                f"Python pass decorated function into `__init__` method and I don;t "
                f"one of those. "
                f"In this case Python should call us with exactly one callable argument; "
                f"But instead we got called with {fail_reason}. "
                f"This should not be possible; something very strange is afoot!"
            )

        # Store the function for later use by the wrapper closure method we are returning.
        # This should be the originally decorated method;
        # ie: It should be `some_method` in the below small example:
        #
        # @UContext()
        # def some_method():
        #    pass

        _func = args[0]
        # This makes our `wrapper` method look like `_func` to the outside world.
        functools.update_wrapper(wrapper, _func)
        return wrapper

    # todo: rename this to just 'chain' ?? or context_chain? [it includes 'self' is why].
    def parent_chain(self) -> List["UContext"]:
        """ A list of self + all parents in priority order.

            This is cached the first time we are called if we are currently active
            since the `UContext.parent` can't be changed after `UContext` creation while active.

            See `UContext._is_active` internal/private var for a bit more detail on what is 'active'
            but suffice to say that active means UContext is currently being used via a
            decorator '@' or via `with` or via `UContext.make_current` and the `with` or `@` has
            not been exited yet, we are active.

            If we are not current active, we won't cache the list and the parent chain will
            start with `self` as the first item, and if the parent passed in to us when self
            was created was left/set at:

            - `guards.default.Default`: Lookup current context via `UContext.current` and that's
                our next parent (and we grab their parent and so forth and return the full list).
            - `None`: We don't look for more parents.
        """
        chain = self._cached_context_chain
        if chain is not None:
            return chain

        chain = [self]

        # This will resolve Default parent if needed, or give us back out explicit parent;
        # or a None if we originally got passed a None for our parent when we were created.
        current_context = self.parent

        while current_context:
            chain.append(current_context)
            current_context = current_context.parent

        if self._is_active:
            # It's safe to cache parent-chain if we are active, our parent won't change
            # while we are active. See doc-comment on `UContext._is_active` for more detials.
            self._cached_context_chain = chain

        return chain

    def __repr__(self, include_parent=True):
        types_list = list(self._resources.keys())
        if types_list and len(types_list) < 3:
            types_list = [t.__name__ for t in types_list]
            types = ';'.join(types_list)
            types = f'resource_types={types}'
        else:
            types = f'resource_count={len(types_list)}'

        str = f"UContext(name='{self.name}', {types}"
        if include_parent:
            str += f', parent={self.parent}'
        str += ')'
        return str

    def _reset_caches(self):
        """ Used internally to reset parent-chain, so it will be looked
            up next time they are asked for.
        """
        self._cached_context_chain = None

    _cached_context_chain = None
    _is_active = None
    """ This means at some point in the past we were 'activated' via one of these methods:

        `with` or `@` or `UContext.make_current`.

        And we are still 'active' (or even the 'UContext.current');

        When we are active we have a set parent, and can cache specific things since
        our parent won't change while we are 'active'.

        This means the `self` is inside `_current_context_contextvar` somewhere and is part of
        the parent-chain.  See `UContext.parent_chain`.
    """

    _reset_token_stack: List[contextvars.Token] = None
    _resources: Dict[Type[Any], Any] = None

    _is_root_context_for_app = False

    _is_root_context_for_thread: bool = False
    """ If True, this UContext is the root-context for a thread
        (or if only one thread, the only root context).
        This is mostly here for debugging purposes.
    """

    _is_root_like_context: bool = False
    """ If True, this context was originally created to be a root-like/root context.
        The REAL thread-root context will have this AND `UContext._is_root_context_for_thread`
        both set to True.
    """

    _parent: 'Union[UContext, _TreatAsRootParent, None]' = None
    _originally_passed_none_for_parent = True
    """ Used internally to know if None was passed as my parent value originally. """

    _func = None
    """ Used if UContext is used as a function decorator directly, ie:

        >>> @UContext
        >>> def some_method():
        ...     pass
    """


def _setup_blank_app_and_thread_root_contexts_globals():
    """
    Used to create initial global state of app/thread-root contexts containers,
    which keep track of the visible `Contexts` on each thread, and for the app-root `UContext`.

    Is also used by `glazy.pytest_plugin.glazy_test_context` auto-use fixture to blank/clear out
    all root/globally visible contexts by allocating the global-structures again and letting
    the old global structures deallocate.

    This allows for clean slate for each individual unit test run,
    in a way that does not really alter how UContext works.

    It should work exactly the same as the normal, non-uniting app.
    We simply clear and allocate new root/global contexts at the start/end of each
    unit test run via the auto-use fixture.
    """
    global _app_root_context
    global _current_context_contextvar

    _app_root_context = UContext(parent=_TreatAsRootParent, name='AppRoot')
    _app_root_context._make_current_and_get_reset_token(is_app_root_context=True)

    # Keeping this private for now, everything outside of this module should use the UContext class
    # as a ContextManager/ContextDecorator to get/set current context.
    #
    # This is used to keep track of the current context when using a UContext as a ContextManager.

    _current_context_contextvar = contextvars.ContextVar(
        'xyn_sdk-current_context',
        default=None
    )


# Setup initial global UContext objects/state/containers:
_setup_blank_app_and_thread_root_contexts_globals()

# These are globals that should be here at this point:
_app_root_context: UContext
_current_context_contextvar: contextvars.ContextVar[Optional[UContext]]
