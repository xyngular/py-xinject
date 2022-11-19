---
title: Thread Safety
---

There is a concept of an app-root, and thread-root [`XContext`](api/xinject/context.html#xinject.context.XContext){target=_blank}.
The app-root stores dependecies that can be shared between threads, whule the thread-root context stores dependence
for a specific thread.

By default, each Dependency subclass can be shared between different threads,
ie: it's assumed to be thread-safe.

You can indicate a Dependency subclass should not be shared between threads
by inheriting from `xinject.dependency.DependencyPerThread` instead,
or by setting the **class attribute** (on your subclass of Dependency)
`thread_sharable` to `False`; ie:

```python
from xinject import Dependency, DependencyPerThread

class MyThreadUnsafeDependencyOpt1(DependencyPerThread):
    ...

class MyThreadUnsafeDependencyOpt2(Dependency, thread_sharable=False):
    ...
```


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
