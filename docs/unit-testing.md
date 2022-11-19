

## Overview - pytest

Library has a pytest plugin, with the objective of clearing out dependencies at the start of each unit test run.

This use useful when session/clients needs to be created after a mock installed.
If the code-base uses a Dependency to grab a requests-session (for example),
when a new unit-test runs it will allocate a new requests session, and mock will therefore work and start out blank,
ready to be configured by the unit-test function that is currently running.

While at the same time the code in prod/deployed code it will just use a shared session via the dependency,
as that will stick around between lambda events, and so on and allow code to reuse already established connections
(which is what you want to happen in deployed code).

All you need to do is write a normal unit-test to take advantage of this feature:

```python
# This is the "my_library/my_resources.py" file/module.

import boto3
from udepend import PerThreadDependency

class S3(PerThreadDependency):
    def __init__(self, **kwargs):
        # Keeping this simple; a more complex version
        # may store the `kwargs` and lazily create the s3 resource
        # only when it's asked for (via a `@property or some such).
        
        self.resource = boto3.resource('s3', **kwargs)
```

```python
# This is the "my_library/my_functions.py" file/module

from .my_resources import S3
def download_file(file_name, dest_path):
    S3.grab().resource.Bucket('my-bucket').download_file(
        file_name, dest_path
    )
```

```python
# This is a unit-testing file/module

from my_library.my_resources import S3
from my_library.my_functions import download_file
from moto import mock_s3
import tempfile
import pytest

@mock_s3
@pytest.mark.parametrize(
    "test_file",
    ["a-file-1.txt", "a-file-2.txt"],
)
def test_download_file(test_file):
    """
    `test_download_file` will be executed twice, once for each
    parameterized value.
    
    At the start of each run of the `test_download_file` function
    (once for each parameterized value), the dependencies are cleared.
    
    This means `S3.grab()` will create a S3 resource for me lazily
    each time this unit-test function runs.
    
    And so I can have separate, independent tests that won't leak
    dependencies into the next function test-run.
    """
    
    S3.grab().resource.Bucket('my-bucket').put_object(
        Key=test_file,
        Body=b'some-bytes'
    )
    
    with tempfile.NamedTemporaryFile() as tmp:
        download_file(test_file, tmp.name)
        with open(tmp.name, 'r') as file:
            assert file.read() == b'some-bytes'
```

### Implementation Details

This is just extra info in case your intrested.

Before the start of each pytest unit-test function run, the current dependencies are deactivated and a new blank UContext
(which contains the dependencies) is created.

This means that by default, at the start of each running unit test function there will be no dependencies 'visible'.


??? note "PyTest Plugin Details"

    This project contains a pytest plugin to automatically install a brand-new app-root and thread-root UContext's 
    at the start of each unit test run.     

    This is important, it ensures a blank root-context is used each time
    a unit test executes.
    
    This is accomplished via an `autouse=True` fixture.
    
    The fixture is in a pytest plugin module.
    This plugin module is automatically found and loaded by pytest.
    pytest checks all installed dependencies in the environment it runs in,
    so as long as udepend is installed in the environment as a dependency it will find this
    and autoload this fixture for each unit test.

    If curious The [`udepend_test_context`](api/udepend/pytest_plugin.html#udepend.pytest_plugin.udepend_test_context)
    fixture is how it's implemented.


The result is for each unit test executed via pytest, it will always start with no resources
from a previous unit-test execution. So no dependencies changes/state will 'leak' between each unit test function run.

Each unit-test will therefore always start out in the same state.
This allows each unit test to run in any order, as it should not affect the dependencies of the next unit-test function
that runs.


