

## Thread Safety

There is a concept of an app-root, and thread-root contexts.

By default, each Dependency subclass will be shared between different threads,
ie: it's assumed to be thread-safe.

You can indicate a Dependency subclass should not be shared between threads
by inheriting from `udepend.dependency.ThreadUnsafeResource` instead,
or by setting the **class attribute** (on your custom sub-class of Dependency)
`udepend.dependency.Dependency.resource_thread_sharable` to `False`.

Things that are probably not thread-safe in general
are resources that contain network/remote type connections/sessions/clients.

Concrete Examples In Code Base:

- Requests library session
  - xyn_model_rest uses a Dependency to wrap requests library session, so it can automatically
    reuse connections on same thread, but use new session if on different thread.
    Also helps with unit testing, when Mocking requests URL calls.
- boto client/dependency
  - Library says it's not thread-safe, you need to use a different object per-thread.
  - Moto mocking library for AWS services needs you to allocate a client after it's setup,
    (so lazily allocate client/dependency from boto).
  - Use `xyn_aws` for easy to use Dependency's that wrap boto client/resources that
    accomplish being both lazy and will allocate a new one per-thread for you automatically.

## Active Dependency Proxy

You can use the convenience method `udepend.dependency.Dependency.proxy` to easily get a
proxy object.

Or you can use `udepend.proxy.CurrentDependencyProxy.wrap` to create an object that will act
like the current dependency.
All non-dunder attributes/methods will be grabbed/set on the current object instead of the proxy.

This means you can call all non-special methods and access normal attributes,
as if the object was really the currently active dependency instance.

Any methods/attributes that start with a `_` will not be used on the proxied object,
but will be used on only the proxy-object it's self.
This means, you should not ask/set any attributes that start with `_` (underscore)
when using the proxy object.

A real-world example is `xyn_config.config.config`, it uses this code for that object:

```python
from udepend import CurrentDependencyProxy
from xyn_config import Config

# The `xny_resource.proxy.CurrentDependencyProxy.wrap` method to get a correctly type-hinted (for IDE)
# proxy back:
config = CurrentDependencyProxy.wrap(Config)

# This is a simpler way to get the same proxy
# (no imports are needed, just call the class method on any Dependency class):
config = Config.proxy()
```

Now someone can import and use it as-if it's the current config object:

```python
from xyn_config import config

value = config.get('some_config_var')
```

When you ask `config` for it's `get` attribute, it will get it from the current
active dependency for `Config`. So it's the equivalent of doing this:

```python
from xyn_config import Config

get_method = Config.grab().get
value = get_method('some_config_var')
```

The code then executes the method that was attached to the `get` attribute.
This makes the call-stack clean, if an error happens it won't be going through
the CurrentDependencyProxy.
The `udepend.proxy.CurrentDependencyProxy` already return the `get` method  and is finished.
The outer-code is the one that executed/called the method.

Another read-world example is in the `xyn_aws`.

See `udepend.proxy.CurrentDependencyProxy` for more ref-doc type details.
