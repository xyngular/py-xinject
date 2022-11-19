## Dependency + Dataclasses

You can use the built-in dataclasses with Dependency without a problem.
Just ensure all fields are optional (ie: they all have default values),
so they are not required when creating/init'ing the object.

You can also provide a `__post_init__` method on your `Dependency`
subclass to help you initialize the values into a good default state
(a standard feature of dataclasses).

The purpose to enable lazily creation of the Dependency object
the very first time it's asked for.

Example:

```python
from xinject import Dependency
from dataclasses import dataclass


@dataclass
class DataResource(Dependency):
    # Making all fields optional, so DataResource can be created lazily:
    my_optional_field: str = None
    another_optional_field: str = "hello!"


# Get current DataResource dependency, print it's another_optional_field;
# will print out `hello!`:
print(DataResource.grab().another_optional_field)

DataResource.grab()

DataResource.grab()

DataResource.grab()

```
