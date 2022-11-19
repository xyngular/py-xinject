---
title: REST API
description: Core utility
---

## Thread Safety

There is a concept of an app-root, and thread-root contexts.

By default, each Dependency subclass will be shared between different threads,
ie: it's assumed to be thread-safe.

You can indicate a Dependency subclass should not be shared between threads
by inheriting from `xinject.dependency.ThreadUnsafeResource` instead,
or by setting the **class attribute** (on your custom subclass of Dependency)
`xinject.dependency.Dependency.resource_thread_sharable` to `False`.

Things that are probably not thread-safe in general
are resources that contain network/remote type connections/sessions/clients.

Example for which you would want a separate dependency instance/object per-thread:

- `requests` library session
  - Requests libraries session object is not thread-safe, there is issue that's been around for 7 years
    to make it thread safe that's still open. For now, you need a seperate requests Session per-thread.
  - `requests-mock` also needs the session created after it's setup, so after unit test runs.
- boto client/dependency
  - Library says it's not thread-safe, you need to use a different object per-thread.
  - Moto mocking library for AWS services needs you to allocate a client after it's setup,
    (so lazily allocate client/dependency from boto).

## Active Dependency Proxy

You can use the convenience method `xinject.dependency.Dependency.proxy` to easily get a
proxy object.

All non-dunder attributes/methods will be grabbed/set on the current object instead of the proxy.

This means you can call all non-special methods and access normal attributes,
as if the object was really the currently active dependency instance.

Any methods/attributes that start with a `_` will not be used on the proxied object,
but will be used on only the proxy-object it's self.
This means, you should not ask/set any attributes that start with `_` (underscore)
when using the proxy object.

Here is an example boto3 s3 resource dependency:

```python
# This is the "my_resources.py" file/module.

from xinject import Dependency

import boto3
from xinject import PerThreadDependency

class S3(PerThreadDependency):
    def __init__(self, **kwargs):
        self.resource = boto3.resource('s3', **kwargs)


# The `xny_resource.proxy.CurrentDependencyProxy.wrap` method to get
# a correctly type-hinted (for IDE) proxy back:
s3 = S3.proxy()
```

You can import the proxy and use it as if it's the current S3 object:

```python
# This is the download_file.py file.

# Import proxy object from my module (lower-case version)
from .my_resources import s3
import sys

if __name__ == '__main__':
    file_name = sys.argv[0]
    dest_path = sys.argv[1]
    
    # Call normal attributes/properties/methods on it like normal,
    # the `s3` proxy will forward them to the current/injected object.
    s3.resource.Bucket("my-bucket").download_file(file_name, dest_path)
```

You can use the proxy objecy like a normal object.

The only things not forwarded are any method/attribute that starts
with a `_`, which conveays the attribute as private/internal.

This includes any dunder-methods, they are not forarded either.

Only use the proxy object for normal attribute/properties/methods.

If you need do use an attribute/method that starts with an underscore `_`,
grab the current object directly via `S3.grab()`.

The [`grab`](api/xinject/dependency.html#xinject.dependency.Dependency.grab)
method returns the current real object each time it's called (and not a proxy).
