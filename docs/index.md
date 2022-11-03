## Install

```bash
# via pip
pip install udepend

# via poetry
poetry add udepend
```

# Introduction

Library's main focus is an easy way to create lazy universally injectable dependencies;
in less magical way. It also leans more on the side of making it easier to get
the dependency you need anywhere in the codebase.

u-depend allows you to easily inject universal resource dependencies into whatever code that needs them,
in an easy to understand and self-documenting way.

??? note "udepend is short for "Universal Dependency""
    ie: a lazy universally injectable dependency



???+ note
    Read this document first to get a general overview before reading the API reference
    documentation.
    
    When you're done here and want more details go to [API Reference](api/udepend)
    or directly to [`Dependency API Refrence`](api/udepend/dependency.html#udepend.dependency.Dependency)
    for more detailed reference-type documentation.

# How To Use

## Quick Start Example Code

Although it's not required, most of the time you'll want to subclass [`Dependency`](api/udepend/dependency.html#udepend.dependency.Dependency).
Tge subclass will inherit some nice features that make it easier to use.

```python
from udepend import Dependency

# This is an example Dependency class, the intent with this class
# is to treat it as a semi-singleton shared dependency.
class MyUniversalDependency(Dependency):

  # It's important to allow resources to be allocated with
  # no required init arguments.
  # That way a default-instance/version of the class can
  # easily be created lazily.
  def __init__(self, name=None):
    if name is not None:
      self.name = name

  name: str = 'original-value'


# Gets currently active instance of `MyResource`, or lazily creates if
# needed. If system creates a new instance of MyResource, it will save
# it and reuse it in the future when it's asked for.
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
from udepend import Dependency


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

# Overview

The main class used most of the time is `udepend.resource.Dependency`,
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

## What It's Used For

- Lazily created singleton-type objects that you can still override/inject as needed in a decoupled fashion.
- Supports foster decoupled code by making it easy to use dependency injection code patterns.
    - Lazily created resources, like api clients.
    - Helps with unit testing mock frameworks.
        - Example: moto needs boto clients to be created after unit test starts, so it can intercept and mock it.
        - Using a dependency to get boto client allows them to be lazily created/mocked during each unit-test run.
- Lazily create sharable objects on demand when/where needed.
    - Things that need to be shared in many locations, without having to pass them everywhere, or couple the code together.
    - Example: session from requests library, so code can re-use already open TCP connections to an API.


## Example Use Cases

- Network connection and/or a remote resource/client.
  - You can wrap these objects in a `resource`, the resource provides the object.
  - Objects to wrap are 'client' like things, and allow you to communicate with some external system.
  - Very common for these objects to represent an already-open network connection,
    So there are performance considerations to try and keep connection open and to reuse it.
  - See `xyn_aws` for a special Dependency subclass that wraps boto clients/resources,
    allows you to lazily get a shared aws client/resource.
    - It also uses a more advance feature, CurrentDependencyProxy, to represent boto resources/clients
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






## Unit Testing

The `udepends.pytest_plugin.xyn_context` fixture in particular will be automatically used 
for every unit test. This is important, it ensures a blank root-context is used each time
a unit test executes.

This is accomplished via an `autouse=True` fixture.
The fixture is in a pytest plugin module.
This plugin module is automatically found and loaded by pytest.
pytest checks all installed dependencies in the environment it runs in,
so as long as udepend is installed in the environment as a dependency it will find this
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

