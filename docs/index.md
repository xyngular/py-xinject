---
title: Getting Started
---

## Install

```bash
# via pip
pip install xinject

# via poetry
poetry add xinject
```

## Introduction

Main focus is an easy way to create lazy universally injectable dependencies;
in less magical way. It also leans more on the side of making it easier to get
the dependency you need anywhere in the codebase.

py-xinject allows you to easily inject lazily created universal dependencies into whatever code that needs them,
in an easy to understand and self-documenting way.

??? note "xinject is short for "Universal Dependency""
    ie: a lazy universally injectable dependency



???+ note
    Read this document first to get a general overview before reading the API reference
    documentation.
    
    When you're done here and want more details go to [API Reference](api/xinject)
    or directly to [`Dependency API Refrence`](api/xinject/dependency.html#xinject.dependency.Dependency){target=_blank}
    for more detailed reference-type documentation.

## Quick Start

Although it's not required, most of the time you'll want to subclass [`Dependency`](api/xinject/dependency.html#xinject.dependency.Dependency){target=_blank}.
The subclass will inherit some nice features that make it easier to use.

The following is a specific usecase followed by a more generalized example

### Lazy S3 Resource Dependency Example

Here is a very basic injectable/sharable lazily created S3 resource.

We have a choice to inherit from ether Dependency, or DependencyPerThread.

The normal `Dependency` class lets the dependency be shared between threads, so more of a true singleton type
of object where under normal/default circomstances there would ever only be one instance of a partculare `Dependency`.

Using [`DependencyPerThread`](api/xinject/dependency.html#xinject.dependency.DependencyPerThread){target=_blank} will automatically get a
separate dependency object per-thread (ie: separate instance per-thread).
It simply inherits from Dependency and configures it to not be thread sharable.

In the example below, we do that with the Boto resource, as the boto documentation for resources states they
are not thread-safe. That means our program will need a separate s3 resource per-thread.

```python
# This is the "my_resources.py" file/module.

import boto3
from xinject import DependencyPerThread


class S3(DependencyPerThread):
    def __init__(self, **kwargs):
        # Keeping this simple; a more complex version
        # may store the `kwargs` and lazily create the s3 resource
        # only when it's asked for (via a `@property or some such).

        self.resource = boto3.resource('s3', **kwargs)
```

To use this resource in any codebase, you can do this:

```python
# This is the "my_functions.py" file/module

from .my_resources import S3

def download_file(file_name, dest_path):
    s3_resource = S3.grab().resource
    s3_resource.Bucket('my-bucket').download_file(
        file_name, dest_path
    )
```

When `grab_file` is called it will grab the current `S3` dependency
and get the resource off of it.
If `S3` dependency has not been created yet, it will do so on the fly
and store and return the lazily created dependency in the future when
asked for it.

This means, the resource is only created when it needs to be.

### Inject Temporarily

Now, let's say you wanted to change/inject a different version of the
S3 dependency, you could do this:

```python
from .my_resources import S3
from .my_functions import download_file

us_west_s3_resource = S3(region_name='us-west-2')

def get_s3_file_from_us_west(file, dest_path):
    # Can use Dependencies as a context-manager,
    # inject `use_west_s3_resource` inside `with`:
    with us_west_s3_resource:
        download_file(file, dest_path)

# Can also use Dependencies as a function decorator,
# inject `use_west_s3_resource` whenever this method is called.
@us_west_s3_resource
def get_s3_file_from_us_west(file, dest_path):
    download_file(file, dest_path)
```

All classes that inherit from `Dependency` are context managers,
and so the `with` statement will 'activate' that dependency as the
current version to use.

That will inject an S3 resource configured with `region_name='us-west-2`
into the function you are calling.

It does not matter how many other methods needs to be called to get
to the method that needs the `S3` resource, it would still be injected
and used.

After the `with` statement is exited, the previous `S3` instance
(if any) that was active before the `with` statement is now what is used
from that point forward.

This allows you to decouple the code. Code that needs a resource can
grab it from the S3 class, and code that needs to configure
the resource can do so without having to know exactly what other methods
needs that dependency. It can configure the dependencies as/if needed,
start the app/process and be done.

The resource also sticks around inside the dependency, and can be reused/shared.
This allows the boto3 s3 resource (in the example above) to reuse already opened
TCP connections to s3 as the s3 resource is used from various parts of the
code base.

### Inject Permanently

If instead (see previous example) you don't want to temporarily inject
a dependency, but instead permanently do it you can do so in a few ways:

- Change the current dependency by setting attributes or calling methods on it.
- Replace the current dependency with a different object.

The first way is easy, you just access the current version of the resource.
I'll be using the `S3` dependency from the previous example:

```python
from .my_resources import S3
S3.grab().resource = boto.resource('s3', region_name='us-west-2')
```

In this case, I am replacing the `resource` attribute on the S3 current
dependency instance/object with my own version of the resource.
From this point forward, it will be what is used
(unless some other code after this point temporarily injects their own
resource via a `with`; see previous example).

Fro the second way, you can access the repository of dependencies 
and swap/inject a different resource there.

This will add the dependency to the current context, and when that 
dependency is next asked for it will return the one that was added
here:

```python
from xinject import XContext
from .my_resources import S3

us_west_s3_resource = S3(region_name='us-west-2')
XContext.grab().add(us_west_s3_resource)
```

And finally, you can replace dependencies with a completely different
class of object. This is sometimes useful when doing unit-testing.

What we do here is add out special MyS3MockingClass object
and tell context to use this in place for the `S3` type dependency.

In the future, this mocking object will be returned when the code
asks for the `S3` dependency-type.

```python
from xinject import XContext
from .my_resources import S3
from .my_mocks import MyS3MockingClass

s3_mocking_obj = MyS3MockingClass()
XContext.grab().add(s3_mocking_obj, for_type=S3)
```



### Generalized/Generic Example

Although it's not required, most of the time you'll want to subclass [`Dependency`](api/xinject/dependency.html#xinject.dependency.Dependency){target=_blank}.
The subclass will inherit some nice features that make it easier to use.

```python
from xinject import Dependency

# This is an example Dependency class, the intent with this class
# is to treat it as a semi-singleton shared dependency.
class MyUniversalDependency(Dependency):

  # It's important to allow dependencies to be allocated with
  # no required init arguments.
  # That way a default-instance/version of the class can
  # easily be created lazily.
  def __init__(self, name=None):
    if name is not None:
      self.name = name

  name: str = 'original-value'


# Gets currently active instance of `MyUniversalDependency`,
# or lazily creates if needed. If system creates a new
# instance of MyUniversalDependency, it will save it and
# reuse it in the future when it's asked for.
#
# Next, we get value of it's `name` attribute:

assert MyUniversalDependency.grab().name == 'original-value'

# Change the value of the name attribute on current dependency
MyUniversalDependency.grab().name = 'changed-value'

# We still have access to the same object, so it has the new value:
assert MyUniversalDependency.grab().name == 'changed-value'

# Inherit from Dependency allows you to use them as a context manager.
# This allows you to easily/temporarily inject dependencies:

with MyUniversalDependency(name='injected-value'):
  # When someone asks for the current dependency of `MyResource`,
  # they will get the one I created in `with` statement above.

  assert MyUniversalDependency.grab().name == 'injected-value'

# Object we created and temporary activated/injected
# by above `with` statement has been deactivated/uninjected.
# So, the previous object is what is now used:

assert MyUniversalDependency.grab().name == 'changed-value'
```

There is also a way to get a proxy-object that represents the
currently used object.

This allows you to have an object that is directly importable/usable
and still have it be injectable.

```python
from xinject import Dependency


class MyUniversalDependency(Dependency):
    def __init__(self, name='default-value'):
        self.name = name


my_universal_dependency = MyUniversalDependency.proxy()

assert my_universal_dependency.name == 'changing-the-value'

with MyUniversalDependency(name='injected-value'):
    # The proxy object proxies to the currently activated/injected
    # version of the dependency:
    assert my_universal_dependency.name == 'injected-value'
```

## Overview

The main class used most of the time is [`Dependency`](api/xinject/dependency.html#xinject.dependency.Dependency){target=_blank}.

Allows you to create sub-classes that act as sharable singleton-type objects that
we are calling resources here.
These are also typically objects that should generally stick around and should be created lazily.

Also allows code to temporarily create, customize and activate a dependency if you don't want
the customization to stick around permanently.
You can do it without your or other code needing to be aware of each other.

This helps promote code decoupling, since it's so easy to make a Dependency activate it
as the 'current' version to use.

The only coupling that takes place is to the Dependency sub-class it's self.

Each separate piece of code can be completely unaware of each other,
and yet each one can take advantage of the shared dependency.

This means that Dependency can also help with simple dependency injection use-case scenarios.

### What It's Used For

- Lazily created singleton-type objects that you can still override/inject as needed in a decoupled fashion.
- Supports foster decoupled code by making it easy to use dependency injection code patterns.
    - Lazily created resources, like api clients.
    - Helps with unit testing mock frameworks.
        - Example: moto needs boto clients to be created after unit test starts, so it can intercept and mock it.
        - Using a dependency to get boto client allows them to be lazily created/mocked during each unit-test run.
- Lazily create sharable objects on demand when/where needed.
    - Things that need to be shared in many locations, without having to pass them everywhere, or couple the code together.
    - Example: session from requests library, so code can re-use already open TCP connections to an API.


### Example Use Cases

- Network connection and/or a remote dependency/client.
    - You can wrap these objects in a `dependency`, the dependency provides the object.
    - Objects to wrap are 'client' like things, and allow you to communicate with some external system.
    - Very common for these objects to represent an already-open network connection,
      So there are performance considerations to try and keep connection open and to reuse it.
- Common configuration or setting objects.
- Anything that needs to be lazily allocated,
  especially if they need to be re-created for each unit-test run.
    - Since all dependencies are thrown-away before running each unit-test function,
      all dependencies will be lazily re-created each time by default.
    - Examples:
        - moto
            - You need to create boto clients after moto is setup in order for moto to intercept/mock
              the service the boto client uses.
            - But you also don't want the main code base to create a brand new boto client each time it needs it,
              so that it can reuse/share already established TCP connections.
            - Using a Dependency to lazily manage your boto clients solves both of these issues.
        - requests-mock
            - Requests-mock needs to be in place before the code base creates a requests-session
                - You want to use a session in main code base to reuse/share already established TCP connections
                  to your http apis.
            - Using a Dependency to manage a shared requests session lets you both lazily create the session to help
              with unit testing, but also allows you to easily reuse the session in your codebase in a decoupled manner.
- Basic dependency injection scenarios, where two separate pieces of code need to use a shared
  object of some sort that you want to 'inject' into them.
    - Does it in a way that prevents you having to pass around the object manually everywhere.
    - Promotes code-decoupling, since there is less-temptation to couple them if it's easy to share
      what they need between each-other, without having each piece of code having to know about each-other.
