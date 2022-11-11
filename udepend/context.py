"""
Manage shared dependency and dependency injection.


# To Do First:

If you have not already, to get a nice high-level overview of library see either:

- project README.md here:
    - https://github.com/xyngular/py-u-depend#how-to-use
- Or go to udepend module documentation at here:
    - [udepend, How To Use](./#how-to-use)


# Quick Start

## Please Read First

If your looking for a simple example/use of singltone-like dependencies,
go to `udepend.dependency.Dependency`.

The whole point of the `udepend.context.UContext` is to have a place to get shared dependencies.

Normally, code will use some other convenience methods, as an example:

Most of the time a dependency will inherit from `udepend.dependency.Dependency` and that
class provides a class method `udepend.dependency.Resource.dependency` to easily get a
dependency of the inherited type from the current context as a convenience.

So normally, code would do this to get the current object instance for a Resource:

>>> class SomeResource(Dependency):
>>>    my_attribute = "default-value"
>>>
>>> # Normally code would do this to interact with current Dependency subclass object:
>>> SomeResource.grab().my_attribute = "change-value"

Another convenient way to get the current dependency is via the
`udepend.dependency.CurrentDependencyProxy`. This class lets you create an object
that always acts like the current/active object for some Resource.
So you can define it at the top-level of some module, and code can import it
and use it directly.

I would start with [Fundamentals](#fundamentals) if you know nothing of how `udepend.context.UContext` works
and want to learn more about how it works.

Most of the time, you interact with Context indrectly via
`udepend.dependency.Dependency`.  So getting familiar with Context is more about
utilize more advance use-cases. I get into some of these advanced use-cases below.

.. important:: The below is for advanced use-cases and understanding.
    Look at `udepend.dependency.Dependency` or docs just above ^^^ for the normal use-case and
    examples / quick starts.

# Context Overview

Context is used to keep track of a set of dependencies. The dependencies are keyed off the class
type. IE: One dependency per-context per-dependency-type.

Main Classes:

- `udepend.context.UContext`: Container of dependencies, mapped by type.
- For Resource Subclasses:
    - `udepend.dependency.Dependency`: Nice interface to easily get the current dependency.
        Used to implment a something that should be shared and not generally duplicated,
        like a soft-singleton.

# Fundamentals

`udepend.context.UContext` is like a container, used to store various objects we are calling
dependencies.

Used to store various dependencies of any type  in general [ie: configs, auths, clients, etc].
All of these dependencies together represent a sort of "context" from which various pieces of code
can easily get them; that way they can 'share' the dependency when appropriate. This is a way
to do dependcy injection in a easier and more reliable way since you don't have to worry
about passing these dependencies around everywhere manually.

The values are mapped by their type.  When a dependency of a specific type is asked for,
the Context will return it if it finds it. If not found it will create it, add it to its self
and return it. Future calls will return this new dependency.

`udepend.context.UContext` can optionally have a parent. By default, a newly created/used Context
will use the current context Normally, dependencies are still normally created even if a
parent has a value, as long as the current context does not have one yet.

This behavior can be customized by the dependency, see one of these for details:

- `udepend.dependency.Dependency`
    - Useful for a shared/soft overridable shared object; where you can easily get the current
        version of it.


## Dependencies
[dependencies]: #dependencies

There are various ways to get dependencies from the current context. Let's say we have
a dependency called `SomeResourceType`:

>>> next_identifier = 0
>>> class SomeResourceType(Dependency):
...     def __init__(self):
...         global next_identifier
...         self.some_value = "hello!"
...         self.ident = next_identifier
...         next_identifier += 1

.. note:: SomeResourceType's `ident` field gets incremented and set on each newly created object.
    So the first SomeResoureType's `ident` will equal `0`,
    the second one created will be `1` and so forth.

If what you want inherits from `udepend.dependency.Dependency`, it has a nice class method that
returns the current dependency.
The easiest way to get the current dependency for the type in this case is
to call `udepend.dependency.Resource.dependency` on it's type like so:

>>> SomeResourceType.grab().some_value
'hello!'
>>> SomeResourceType.grab().ident
0

When a Context does not have the dependency, by default it will create it for you, as you
saw in the previous example.

`Context.current()` will return the current Context if no params are passed in, or if a
type is passed in, it will return the current Context's dependency for the passed in type.

This means another way to grab dependencies is to get the current `Context.current`,
and then ask it for the dependency like below. This works for any type, including
types that don't inherit from `udepend.dependency.Dependency`:

>>> UContext.current().grab(SomeResourceType).some_value
'hello!'

If you pass a type into `Context.current`, it will do the above ^ for you:

>>> UContext.current(SomeResourceType).some_value
'hello!'
>>> UContext.current(SomeResourceType).ident
0

As you can see, it still returns the same object [ie: `ident == 0`]

## Activating New Resource

You can easily create a new dependency, configure it however you like and then 'activate' it,
so it's the current version of that dependency. This allows you to 'override' and activate your
own copy of a dependency.

You can do it via one of the below listed methods/examples below.

For these examples, say I have this dependency defined:

>>> from dataclasses import dataclass
>>> from udepend import Dependency
>>>
>>> @dataclass
>>> class MyResource(Dependency):
>>>     some_value = 'default-value'
>>>
>>> assert MyResource.grab().some_value == 'default-value'

- Use desired `udepend.dependency.Dependency` subclass as a method decorator:

        >>> @MyResource(some_value='new-value')
        >>> def my_method():
        >>>     assert MyResource.grab().some_value == 'new-value'

## Activating New Context

When you create a new context, you can activate it to make it the current context in three ways
(listed below). Keep in mind that when you make a context current and 'activate' it,
it will implicitly **copy** it's self (so it's unattached from the orginal Context) and
the copy is what is made current/activated (see `Context.__copy__` for more details if intrested).

1. Via the `with` statement.
2. As a method dectorator, ie: `@`.
3. Permently activiating it via `Context.make_current`, making it the new Default/Base
   context in general.
4. When running a unit-test where udepend is installed as a dependcy,
    because the `udepend.ptest_plugin.udepend_test_context` fixture is auto-used in this case.
    This fixture creates a new Context with a None parent;
    that will isolate dependencies between each run of a unit test method.

### Examples

Here are examples of the four ways to create/activate a new context:

>>> with UContext():
...     SomeResourceType.grab().ident
1

This is stack-able as well; as in this can keep track of a stack of contexts, in a
thread-safe way.

When the context manager or decorated method is exited, it will pop-off the context,
and it won't
be the default one anymore. Whatever the default one was before you entered the `with` will
be the default once more.

>>> @UContext():
>>> def a_decorated_method():
...     return SomeResourceType.grab().ident
>>> a_decorated_method()
2
>>> a_decorated_method()
3
>>> SomeResourceType.grab().ident
0

As you can see, after the method exits the old context takes over, and it already had the
older version of the dependency and so returns that one.

By default, a context will create a dependency when it's asked for it and it does not have it
already. As you saw above, every time a blank Context was created, it also created a new
SomeResourceType when it was asked for it because the new blank `udepend.context.UContext` did not already
have the dependency.


>>> UContext().make_current()
>>> SomeResourceType.grab().ident
4

With the context test fixture, it creates a brand new parent-less context every time a test runs
(see `Context.parent` for more about parents). You can use it like so:

>>> from udepend.fixtures import context
>>> def test_some_text(context):
...    SomeResourceType.grab()



There are ways to share dependency in a parent Context that a new blank context would beable
to use. But that's more advanced usage. The above should be enough to get you started quickly.
See below for more advanced usage patterns.

# Parents

A Context can have a parent (`Context.parent`) or event a chain of them (`Context.parent_chain`)

Because it's the safest thing to do by default for naive dependencies, Context's normally don't
consult parents for basic dependencies, they will just create them if they don't already have them.

You can customize this behavior. There are some default dependency base classes that will implment
a few common patterns for you. You can see how they work to get ideas, and customize the process
for your own dependency when needed. See [Resource Base Classes][dependency-base-classes] below for
more details on how to do that.

You can make an isolated Context by doing:

>>> UContext(parent=None)

When creating a new context. This will tell the context NOT to use a parent. By default, a
Context will use the current Context as the time the Context was created as it's parent.
See `Context.parent` for more details.

This is also how the Context test fixture works (see `udepend.ptest_plugin.udepend_test_context`). It creates
a new parent-less context and activates it while the fixture is used.

# Resource Base Classes
[dependency-base-classes]: #dependency-base-classes.

### `udepend.dependency.Dependency`

You can implment the singleton-pattern easily by inherting from the
`udepend.dependency.Dependency` class.
This will try it's best to ensure only one dependency is used amoung a chain/tree of parents.
It does this by returning `self` when `udepend.context.UContext` asks it what it wants to do when a child-context
asks for the dependency of a specific type.
Since `udepend.dependency.Dependency` can be shared amoung many diffrent child Context objects,
and makes the same instance always 'look' like it's the current one;
generally only one is every made or used.

However, you can create a new Context, make it current and put a diffrent instance of the
dependency in it to 'override' this behavior.
See [Activating New Resource](#activating-new-dependency) for more details.

#### Example

I create a new class that uses our previous [SomeResourceType][dependencies] but adds in a
`udepend.dependency.Dependency`.

>>> class MySingleton(SomeResourceType, Dependency):
...     pass
>>> MySingleton.grab().ident
5

Now watch as I do this:

>>> with UContext():
...     MySingleton.grab().ident
5

The same dependency is kept when making a child-context. However, if you make a parent-less
context:

>>> with UContext(parent=None):
...     MySingleton.grab().ident
6

The `udepend.dependency.Dependency` will not see pased the parent-less context,
and so won't see the old dependency.
It will create a new one. The `udepend.dependency.Dependency` will still create it in the
furtherest parent it can... which in this case was the `udepend.context.UContext` activated by the with statement.

"""
import contextvars
import itertools
import functools
from typing import TypeVar, Type, Dict, List, Optional, Union, Any, Iterable, Set
from copy import copy
from guards.default import Default, DefaultType, Singleton
from udepend.errors import UDependError

T = TypeVar('T')
C = TypeVar('C')
ResourceTypeVar = TypeVar('ResourceTypeVar')
"""
Some sort of Dependency, I am usually emphasizing with this that you need to pass in the
`Type` or `Class` of the Dependency you want.
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
    See [Quick Start](#quick-start) in the `udepend.context` module if your new to the UContext
    class.
    """
    copy_as_template = False

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

        return context.dependency(for_type=for_type)

    @classmethod
    def _current_without_creating_thread_root(cls):
        return _current_context_contextvar.get()

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
        my_parent = self._parent
        if my_parent and not my_parent._is_root_context_for_app:
            my_parent._children.add(self)

        return _current_context_contextvar.set(self)

    @property
    def parent(self) -> Optional["UContext"]:
        parent = self._parent
        if self._is_active:
            if parent is None:
                return None

            if parent:
                return parent

            raise UDependError(
                f"Somehow we have a UContext has been activated "
                f"(ie: has activated via decorator `@` or via `with` "
                f"at some point and has not exited yet) "
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
        # Honestly, looking up dependencies with a non-active context should be pretty rare,
        # I am allowing it for more of completeness at this point then anything else.
        # However, it might be more useful at some point.
        if parent is Default:
            return UContext.current()

        if parent in (_TreatAsRootParent, None):
            return None

        raise UDependError(
            f"Somehow we have a UContext that is not active "
            f"(ie: ever activated via decorator `@` or via `with`) but has a specific parent "
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
            dependencies: Union[Dict[Type, Any], List[Any], Any] = None,
            parent: Union[DefaultType, _TreatAsRootParentType, None] = Default,
            name: str = None,
            copy_as_template: bool = False
    ):
        """
        You can give an initial list of dependencies
        (if desired, most of the time you just start with a blank context).

        for `parent`, it can be set to `guards.default.Default` (default value); or to `None.

        If you don't pass anything to parent, then the default value of `Default` will cause us
        to lookup the current context and use that for the parent automatically when the
        UContext is activated.
        For more information on activating a context see
        [Activating A UContext](#activating-a-context).

        If you pass in None for parent, no parent will be used/consulted. Normally you'll only
        want to do this for a root context. Also, useful for unit testing to isolate testing
        method dependencies from other unit tests. Right now, the unit-test Dependency isolation
        happens automatically via an auto-use fixture (`udepend.ptest_plugin.udepend_test_context`).

        A non-activated context will return `guards.default.Default` as it's `UContext.parent`
        if it was created with the default value;
        otherwise we return `None` (if it was created that way).

        Args:
            dependencies (Union[Dict[Type, Any], List[Any], Any]): If you wish to have the
                `UContext` your creating have an initial list of dependencies you can pass them
                in here.

                It can be a single Dependency, or a list of dependencies, or a mapping of dependencies.

                Mainly useful for unit-testing, but could be useful elsewhere too.

                They will be added to use via `UContext.add` for you.

                If you use a dict/mapping, we will use the following for `UContext.add`:

                - Dict-key as the `for_type' method parameter.
                - Dict-value as the `Dependency` method parameter.

                This allows you to map some standard Dependency type into a completely different
                type (useful for unit-testing).

                By default, no dependencies are initially added to a new UContext.

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
            raise UDependError(
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

        self.copy_as_template = copy_as_template
        self._reset_token_stack = []
        self._dependencies = {}
        self._parent = None
        self._cached_parent_dependencies = {}
        self._children = set()

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
            raise UDependError(
                "You must only pass in `Default` or `None` or `_TreatAsRootParentType` for parent "
                f"when creating a new UContext, got ({parent}) instead."
            )

        # Add any requested initial dependencies.
        if isinstance(dependencies, dict):
            # We have a mapping, use that....
            for for_type, resource in dependencies.items():
                self.add(resource, for_type=for_type)
        elif isinstance(dependencies, list):
            # We have one or more Dependency values, add each one.
            for resource in dependencies:
                self.add(resource)
        elif dependencies is not None:
            # Otherwise, we have a single Dependency value.
            self.add(dependencies)

    # todo: Make it so if there is a parent context, and the current config has no property
    # todo: it can ask the UContext for the parent config to see if it has what is needed.
    def add(
            self, dependency: Any, *, for_type: Type = None
    ) -> "UContext":
        """
        Lets you add a dependency to this context, you can only have one-dependency per-type.

        Returns self so that you can keep calling more methods on it easily.... this allws you
        to also add a dependency and then use it directly as decorator (only works on python 3.9),
        ie:

        >>> # Only works on python 3.9+, it relaxes grammar restrictions
        >>> #    (https://www.python.org/dev/peps/pep-0614/)
        >>>
        >>> @UContext().add(2)
        >>> def some_method()
        ...     print(f"my int dependency: {UContext.dependency(int)}")
        Output: "my int dependency: 2"

        As as side-note, you can easily add resources to a new `udepend.context.UContext` via:

        >>> @UContext(dependencies=[2])
        >>> def some_method()
        ...     print(f"my int dependency: {UContext.dependency(int)}")
        Output: "my int dependency: 2"

        With the `Context.add_resource` method, you can subsitute dependency for other
        dependency types, ie:

        >>> def some_method()
        ...     context = UContext()
        ...     context.add(3, for_type=str)
        ...     print(f"my str dependency: {UContext.dependency(str)}")
        Output: "my str dependency: 3"

        If you need to override a dependency, you can create a new context and set me as it's
        parent. At that point you can add whatever resources you want before anyone else
        uses the new `udepend.context.UContext`.

        .. warning:: If you attempt to add a second dependency of the same type...
            ...a `udepend.UDependError` will be
            raised. This is because other objects have already gotten this dependency and are
            relying on it now.  You need to configure any special resources you want to add
            to this context early enough before anything else will need it.

        .. todo:: Consider relaxing this ^ and not producing an error [or at least an option
            to 'replace' an existing dependency in an existing Context. I was cautious on this
            at first because it was the safest thing to do and I could always relax it later
            if I found that desirable. Careful consideration would have to be made.

        Args:
            dependency (Any): Object to add as a dependency, it's type will be mapped to it.

            skip_if_present (bool): If False [default], we raise an exception if dependency
                of that type is already in context/self.

                If True, we don't do anything if dependency of that type is already in
                context/self.

            for_type: You can force a particular mapping by using this option.
                By default, the `for_type` is set to the type of the passed in dependency
                [via `type(dependency)`].

                You can override this behavior by passing a type in the `for_type` param.
                We will then map the dependency for `for_type` to the `dependency` object when
                a dependency is requested for `for_type` in the future. Will still raise the
                error if a dependency for `for_type` already exists in Context.
        Returns:
            Return `self`, so that you can keep calling more methods easily if needed
            (ie: .add(), etc)
        """
        if for_type is None:
            for_type = type(dependency)

        self._dependencies[for_type] = dependency
        self._remove_cached_dependency_and_in_children(for_type)
        return self

    def dependency(
            self, for_type: Type[ResourceTypeVar], *, create: bool = True
    ) -> ResourceTypeVar:
        """

        ## Summary

        The whole point of the `udepend.context.UContext` is to have a place to get shared dependencies. This method
        is the primary way to get a shared resource from a Contet directly

        Normally, code will use some other convenience methods, as an example:

        Normally a resource will inherit from `udepend.resource.Dependency` and that
        class provides a class method `udepend.resource.Resource.resource` to easily get a
        resource of the inherited type from the current context as a convenience.

        So normally, code would do this to get a Resource:

        >>> class SomeResource(Dependency):
        >>>    pass
        >>> # Normally code would do this to get current Dependency object:
        >>> SomeResource.grab()

        Another convenient way to get the current resource is via the
        `udepend.resource.CurrentDependencyProxy`. This class lets you create an object
        that always acts like the current/active object for some Resource.
        So you can define it at the top-level of some module, and code can import it
        and use it directly.

        I would start with [Quick Start](#quick-start) if you know nothing of how `udepend.context.UContext` works
        and want to learn more about how it works.

        Most of the time, you interact with Context indrectly via
        `udepend.context.Dependency`.  So getting familure with Context is more about
        utilize more advance use-cases. I get into some of these advanced use-cases below.

        ## Advanced Usage for Unit Tests

        You can allocate a new Context to inject or customize dependencies. When the context is
        thrown away or otherwise is not the current context anymore, the idea is whatever
        resource you made temporarily active is forgotten.

        You can inject/replace dependencies as needed for unit-testing purposes as well by simply
        adding the resource to a new/blank `udepend.context.UContext` as a diffrent type, see example below.

        In this example, we add a value of int(20) for the `str` resource type.
        I used built-int types to simplify this, but you can image using your own
        custom-resource-class and placing it in the Context for the normal-resource-type
        the normal code asks for.

        >>> UContext().add(20, for_type=str)
        >>> UContext().dependency(str)
        Output: 20

        ## Specific Details

        Given a type of `udepend.resource.Dependency`, or any other type;
        we will return an instance of it.

        If we currently don't have one, we will create a new one of type passe in and return that.
        We will continue to return the one created in the future for the type passed in.

        You can customize this process a bit by having your custom resource inherit from
        `udepend.resource.Dependency`.

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
        """

        # If we find it in self, use that; no need to check anything else...
        obj = self._dependencies.get(for_type, None)
        if obj is not None:
            return obj

        # We next check our cached parent deps...
        obj = self._cached_parent_dependencies.get(for_type, None)
        if obj is not None:
            return obj

        # We must now query the parent-chain to find the dependency.

        # If we are the root context for the entire app (ie: app-root between all threads)
        # then we check to see if dependency is thread-sharable.
        #
        # If it is then we continue as normal.
        # If NOT, then we always return None.
        #
        # This will indicate to the thread-specific UContext that is calling us to allocate
        # the object in its self.
        #
        # If something else is asking us, we still return None because this Dependency does not
        # belong in us, and so we should not accidentally auto-create it in us.
        # ie: Whoever is calling it should handle the None case.
        #
        # In Reality, the only thing that should be calling the app-root context
        # is a thread-root context.  Thread root-contexts should never return None when asked
        # for a dependency.
        #
        # So, code using a Dependency in general should never have to worry about this None case.

        if self._is_root_context_for_app:
            from udepend import Dependency
            if issubclass(for_type, Dependency) and not for_type.resource_thread_safe:
                return None

        parent_value = None
        parent = self.parent

        # Sanity check: If we are active we should have a None or an explicit, non-default parent.
        if self._is_active and parent is Default:
            raise UDependError(
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
            if self is parent:
                raise UDependError(
                    f"Somehow have self ({self}) and parent as same instance (UContext), "
                    f"when self is not currently active and is attempting to find the current "
                    f"active UContext to use as it's temporary parent."
                )
            assert self is not parent, "Somehow have self and parent as same instance."

            # Since our `parent is Default`, we should not be the app-root, or thread-root
            # context; we also don't want to cache anything our parent retrieves so simply
            # return whatever our Default parent returns.
            return parent.dependency(for_type, create=create)

        if parent:
            parent_value = parent.dependency(for_type, create=create)

        # If we can't create the dependency, we can ask the resoruce to potetially create more of
        # its self.
        # We should also not put any value we find in self either.
        # Simply return the parent_value, whatever it is (None or otherwise)
        if not create:
            return parent_value

        # We next create dependency if we don't have an existing one.
        # Allocate a blank object if we have no parent-value to use.
        if parent_value is None:
            obj = for_type()
            self._dependencies[for_type] = obj
            return obj

        # Store in self for future reuse.
        self._cached_parent_dependencies[for_type] = parent_value
        return parent_value

    def resource_chain(
            self, for_type: Type[ResourceTypeVar], create: bool = False
    ) -> Iterable[ResourceTypeVar]:
        """
        Returns a python generator yielding dependencies in self and in each parent;
        returns them in order.

        This won't create a dependency if none exist unless you pass True into `create`, so it's
        possible for no results to be yielded if it's never been created and `create` == False.

        .. warning:: This is mostly used by `udepend.dependency.Dependency` subclasses
            (internally).

            Not normally used elsewhere. It can help the udepend.dependency.Dependency`
            subclass to find it's
            list of parent dependencies to consult on it's own.

            Real Example: `xyn_config.config.Config` uses this to construct it's parent-chain.

        Args:
            for_type (Type[ResourceTypeVar]): The dependency type to look for.
            create (bool): If we should create dependency at each context if it does not already
                exist.
        Yields:
            Generator[ResourceTypeVar, None, None]: Resources that were found in the self/parent
                hierarchy.
        """
        for context in self.parent_chain():
            resource = context.dependency(for_type=for_type, create=create)
            if resource:
                yield resource

    def __copy__(self):
        """ Makes a copy of self.

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
        from udepend import Dependency
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

        # Copy current dependencies from self into new UContext;
        # This uses `self` as a template for the new UContext.
        new_resources = {}
        for k, v in self._dependencies.items():
            v = copy(v)
            new_resources[k] = v

        new_context._dependencies = new_resources
        # Reset context chain cache, if anything was cached in it.
        new_context._reset_caches()
        return new_context

    def __deepcopy__(self, memo):
        """
        Used to make a deepcopy of self via `copy.deepcopy(some_context)`,
        This will in-turn deep-copy all dependencies currently in self.

        At the moment, this is not really used. I considered using this for
        unit tests but decided to use an autouse context to setup the needed dependencies
        instead.

        for now I am just making this method private, as it still works just fine in
        case it's handy to make public and start using again someday.
        Args:
            memo: Memo from `copy.deepcopy`, used to hook up already deep-copied objects
                that have multiple ways/paths to get to in a graph.

        Returns:
            Deep copied object.
        """
        raise UDependError(
            "Deepcopy is currently disabled for udepend.context.UContext. "
            "If there is a desire to use it again in the future, remove this exception "
            "as it should still work."
        )
        # return self.__copy__(deepcopy_resources=True, deepcopy_memo=memo)

    def copy(self):
        """ Convenience method to easily shallow-copy a UContext, calls `return copy.copy(self)`.
            Used when you activate a UContext via a decorator or `with` statement.

            When a UContext is activated, it is copied and then the copy is set to active.
        """
        return copy(self)

    def __enter__(self):
        """
        Used to make a Context usable as a ContextManager via `with` statement.

        If self.copy_as_template is True, will make a copy of self, activate that and return
        that context.

        Otherwise, will activate self, and return self.
        You MUST ensure that a context that is directly activated and with no
        copy made is not currently active right now.

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
                prevent_copying_self: If False (default): If self.copy_as_template is True, will
                    make a copy of self, activate that and return that context.

                    If True: Even if `copy_as_template` is Will activate self, and return self,
                        You MUST ensure that a context that is directly activated and with no
                        copy made is not currently active right now.

                    Generally, `udepend.dependency.Dependency.__enter__` will set to this
                    False because it always creates a blank context just for its self.
                    No need to create two contexts (just an optimization).
        """
        new_ctx = self
        if self.copy_as_template:
            new_ctx = self.copy()
        # Check to make sure new_ctx is not currently active, if it is we either need to:
        #   make a copy of self and activate that instead
        #   raise an error.

        token = new_ctx._make_current_and_get_reset_token()
        self._reset_token_stack.append(token)
        return new_ctx

    def __exit__(self, *args, **kwargs):
        # Makes it possible to use a UContext object in a `with UContext():` statement.
        token = self._reset_token_stack.pop()

        current_context = UContext.current()

        assert current_context is self, (
            f"A UContext ({self}) was exited, and was not current context ({current_context})"
        )

        assert not self._reset_token_stack, (
            f"A UContext ({self}) was exited, and there was still a reset-token on stack."
        )

        # Doing this to be extra-cautious, UContext should dynamically look up current
        # context if it's not active anymore
        # (ie: outside-of / not in python ContextVar: `_current_context_contextvar`).
        #
        # Reset context that is not active anymore back to Default if it had a parent.
        # if the parent is None, it should remain as None.
        # A `Default` parent means it looks up parent dynamically each time (to the current one).
        if self._parent:
            # Remove self from children, reset parent/caches.
            self._parent._children.remove(self)
            self._parent = Default
            self._reset_caches()

        _current_context_contextvar.reset(token)

    def __call__(self, *args, **kwargs):
        """
        This allows us to support using `udepend.context.UContext` as a function decorator in a few ways:

        >>> @UContext
        >>> def some_method():
        ...     pass

        OR

        >>> my_context = UContext()
        >>> my_context.add(Dependency())
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

        What this means is that when `some_method` is called, and we create this new `udepend.context.UContext`
        to use. The next `udepend.context.UContext` will get the same dependencies that are/were assigned to it;
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
        # objects while `some_func` was running. We don't want to bring any dependencies
        # created while function was running into future runs of the function.
        # We want to start fresh each time.

        fail_reason = ""
        if len(args) != 1:
            fail_reason = "zero arguments"
        elif not callable(args[0]):
            fail_reason = "one non-callable argument"

        if fail_reason:
            raise UDependError(
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
        types_list = list(self._dependencies.keys())
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
        self._cached_parent_dependencies.clear()

    def _remove_cached_dependency_and_in_children(self, dependency_type: Type):
        self._cached_parent_dependencies.pop(dependency_type)
        for child in self._children:
            child._remove_cached_dependency_and_in_children(dependency_type)

    _cached_context_chain = None
    _cached_parent_dependencies: dict = None

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
    _dependencies: Dict[Type[Any], Any] = None

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

    _children: Set['UContext'] = None

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

    Is also used by `udepend.pytest_plugin.udepend_test_context` auto-use fixture to blank/clear out
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
