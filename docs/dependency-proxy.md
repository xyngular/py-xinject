---
title: Dependency Proxy
---

You can use the method
[`Dependency.proxy()`](api/xinject/dependency.html#xinject.dependency.Dependency.proxy){target=_blank}
to easily get a proxy object.

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
from xinject import DependencyPerThread


class S3(DependencyPerThread):
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

You can use the proxy object like a normal object.

The only things not forwarded are any method/attribute that starts
with a `_`, which conveays the attribute as private/internal.

This includes any dunder-methods, they are not forarded either.

Only use the proxy object for normal attribute/properties/methods.

If you need do use an attribute/method that starts with an underscore `_`,
grab the current object directly via `S3.grab()`.

The [`grab()`](api/xinject/dependency.html#xinject.dependency.Dependency.grab){target=_blank}
method returns the current real object each time it's called (and not a proxy).
