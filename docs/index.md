# Install

```bash
# via pip
pip install udepend

# via poetry
poetry add udepend
```

# Introduction

Glazy is short for "Global Lazy", ie: a globally lazy resource.

Galzy allows you to easily inject global resource dependencies into whatever code that needs them,
in an easy to understand and self-documenting way.

???+ note
  Read this document first to get a general overview before reading the API reference
  documentation.
  
  When you're done here and want more details go to [API Reference](api/glazy)
  or directly to [`Dependency API Refrence`](api/glazy/resource.html#glazy.resource.Resource)
  for more detailed reference-type documentation.


# How To Use

## Quick Start Example Code

Although it's not required, most of the time you subclass `Dependency`. A subclass will inherit some nice features.

```python
from udepend import Dependency


# This is an example Dependency class, the intent with this class is to treat 
# it as a semi-singleton shared resource.
class MyGlobalResource(Dependency):

  # It's important to allow resources to be allocated with
  # no required init arguments.
  # That way a default-instance/version of the class can
  # easily be created lazily.
  def __init__(self, name=None):
    if name is not None:
      self.name = name

  name: str = 'my-default-value'


# Gets currently active instance of `MyResource`, or lazily creates if needed.
# If system creates a new instance of MyResource, it will save it and reuse it
# in the future when it's asked for.
#
# Next, we get value of `some_attribute` off of it.
# Prints 'my-default-value'
print(MyGlobalResource.resource().name)

# Change the value of the name attribute on current resource
MyGlobalResource.resource().name = 'changing-the-value'

# Now prints 'changing-the-value'
print(MyGlobalResource.resource().name)

# You can temporarily override a resource via a python context manager:
with MyGlobalResource(name='my-temporary-name'):
  # When someone asks for the current resource of `MyResource`,
  # they will get back the one I created in `with` statement above.

  assert MyGlobalResource.resource().name == 'my-temporary-name'

# Object we created and temporary activated by above `with` statement
# has been deactivated (ie: thrown out).
# Old one that was the active one previously is the one that is now used when
# the current resource for `MyResource` is asked for.

assert MyGlobalResource.resource().name == 'changing-the-value'



```

In the above example, `MyGlobalResource` is a global 

You can also easily get a basic proxy-object that represents the currently used object:

```python
my_global_resource = MyGlobalResource.resource_proxy()

assert my_global_resource.name == 'changing-the-value'

with MyGlobalResource(name='my-temporary-name'):
    # When someone asks for the current resource of `MyResource`,
    # they will get back the one I created in `with` statement above
    # via the proxy object (which proxies to the currently used/activated MyGlobalResource).
    
    assert my_global_resource.name == 'my-temporary-name'
```




### What It's Used For

If you need a lazily created singleton-type object
(but can still temporary override in a decoupled fashion if needed)
then this library could come in use for your situation.

#### Example Use Cases

- Network connection and/or a remote resource/client.
  - You can wrap these objects in a `resource`, the resource provides the object.
  - Objects to wrap are 'client' like things, and allow you to communicate with some external system.
  - Very common for these objects to represent an already-open network connection,
    So there are performance considerations to try and keep connection open and to reuse it.
  - See `xyn_aws` for a special Dependency subclass that wraps boto clients/resources,
    allows you to lazily get a shared aws client/resource.
    - It also uses a more advance feature, ActiveResourceProxy, to represent boto resources/clients
      that are importable into other modules and directly usable.
- Common configuration or setting values
  - See also:
    - xyn_settings
      - A Dependency subclass that has extra features geared towards this use case.
    - xyn_config
      - Way to get settings from SSM, Secrets Manager and other remote locations.
- Anything that needs to be lazily allocated,
  especially if they need to be re-created for each unit-test run.
  - Example: things with moto, requests-mock
    - This use useful when session/clients needs to be created after a mock installed.
      So if code-base uses Dependency  to grab a requests session (for example),
      when a new unit-test runs it will allocate a new requests session, and mock will therefore work.
      While at the same time the code in prod/deployed code it will just use a shared session
      that sticks around  between lambda runs, etc. (which is what you want to happen in deployed code).
- Basic dependency injection scenarios, where two separate pieces of code need to use a shared
  object of some sort that you want to 'inject' into them.
  - Does it in a way that prevents you having to pass around the object manually everywhere.
  - Promotes code-decoupling, since there is less-temptation to couple them if it's easy to share
    what they need between each-other, without having each piece of code having to know about each-other.

### Overview

The main class used most of the time is `glazy.resource.Dependency`,
you can look at the doc-comment for that module and class for more details.

Allows you to create sub-classes that act as sharable singleton-type objects that
we are calling resources here.
These are also typically objects that should generally stick around and should be created lazily.

Also allows code to temporarily create, customize and activate a resource if you don't want
the customization to stick around permanently.
You can do it without your or other code needing to be aware of each other.

This helps promote code decoupling, since it's so easy to make a Dependency activate it
as the 'current' version to use.

The only coupling that takes place is to the Dependency sub-class it's self.

Each separate piece of code can be completely unaware of each other,
and yet each one can take advantage of the shared resource.

This means that Dependency can also help with simple dependency injection use-case scenarios.


## Advanced Use Cases

### Dependency + Dataclasses

You can use the built-in dataclasses with Dependency without a problem.
Just ensure all fields are optional (ie: they all have default values).

Example:

```python
from udepend import Dependency
from dataclasses import dataclass


@dataclass
class DataResource(Dependency):
  # Making all fields optional, so DataResource can be created lazily:
  my_optional_field: str = None
  another_optional_field: str = "hello!"


# Get current DataResource resource, print it's another_optional_field;
# will print out `hello!`:
print(DataResource.resource().another_optional_field)
```

### Thread Safety

There is a concept of an app-root, and thread-root contexts.

By default, each Dependency subclass will be shared between different threads,
ie: it's assumed to be thread-safe.

You can indicate a Dependency subclass should not be shared between threads
by inheriting from `glazy.resource.ThreadUnsafeResource` instead,
or by setting the **class attribute** (on your custom sub-class of Dependency)
`glazy.resource.Dependency.resource_thread_sharable` to `False`.

Things that are probably not thread-safe in general
are resources that contain network/remote type connections/sessions/clients.

Concrete Examples In Code Base:

- Requests library session
  - xyn_model_rest uses a Dependency to wrap requests library session, so it can automatically
    reuse connections on same thread, but use new session if on different thread.
    Also helps with unit testing, when Mocking requests URL calls.
- boto client/resource
  - Library says it's not thread-safe, you need to use a diffrent object per-thread.
  - Moto mocking library for AWS services needs you to allocate a client after it's setup,
    (so lazily allocate client/resource from boto).
  - Use `xyn_aws` for easy to use Dependency's that wrap boto client/resources that
    accomplish being both lazy and will allocate a new one per-thread for you automatically.

### Active Dependency Proxy

You can use the convenience method `glazy.resource.Dependency.resource_proxy` to easily get a
proxy object.

Or you can use `glazy.proxy.ActiveResourceProxy.wrap` to create an object that will act
like the current resource.
All non-dunder attributes/methods will be grabbed/set on the current object instead of the proxy.

This means you can call all non-special methods and access normal attributes,
as if the object was really the currently active resource instance.

Any methods/attributes that start with a `_` will not be used on the proxied object,
but will be used on only the proxy-object it's self.
This means, you should not ask/set any attributes that start with `_` (underscore)
when using the proxy object.

A real-world example is `xyn_config.config.config`, it uses this code for that object:

```python
from udepend import ActiveResourceProxy
from xyn_config import Config

# The `xny_resource.proxy.ActiveResourceProxy.wrap` method to get a correctly type-hinted (for IDE)
# proxy back:
config = ActiveResourceProxy.wrap(Config)

# This is a simpler way to get the same proxy
# (no imports are needed, just call the class method on any resource class):
config = Config.resource_proxy()
```

Now someone can import and use it as-if it's the current config object:

```python
from xyn_config import config

value = config.get('some_config_var')
```

When you ask `config` for it's `get` attribute, it will get it from the current
active resource for `Config`. So it's the equivalent of doing this:

```python
from xyn_config import Config

get_method = Config.resource().get
value = get_method('some_config_var')
```

The code then executes the method that was attached to the `get` attribute.
This makes the call-stack clean, if an error happens it won't be going through
the ActiveResourceProxy.
The `glazy.proxy.ActiveResourceProxy` already return the `get` method  and is finished.
The outer-code is the one that executed/called the method.

Another read-world example is in the `xyn_aws`.

See `glazy.proxy.ActiveResourceProxy` for more ref-doc type details.

## Unit Testing

The `glazys.pytest_plugin.xyn_context` fixture in particular will be automatically used 
for every unit test. This is important, it ensures a blank root-context is used each time
a unit test executes.

This is accomplished via an `autouse=True` fixture.
The fixture is in a pytest plugin module.
This plugin module is automatically found and loaded by pytest.
pytest checks all installed dependencies in the environment it runs in,
so as long as glazy is installed in the environment as a dependency it will find this
and autoload this fixture for each unit test.

This means for each unit test executed via pytest, it will always start with no resources
from a previous unit-test execution.

Each unit-test will therefore always start out in the same state,
and a unit-test won't leak/let-slip any of the changes it makes to its
Resources into another unit-test.

This use useful when session/clients needs to be created after a mock installed.
So if code-base uses Dependency  to grab a requests session (for example),
when a new unit-test runs it will allocate a new requests session, and mock will therefore work.
While at the same time the code in prod/deployed code it will just use a shared session
that sticks around  between lambda runs, etc. (which is what you want to happen in deployed code).

