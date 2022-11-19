![PythonSupport](https://img.shields.io/static/v1?label=python&message=%203.8|%203.9|%203.10&color=blue?style=flat-square&logo=python)
![PyPI version](https://badge.fury.io/py/py-u-depend.svg?)

- [Overview](#overview)
- [Install](#install)
- [Quick Start](#quick-start)
- [Licensing](#licensing)

# Overview

Various objects that allow for sentinel-like singleton guards for various purposes, including:

- Ones pre-defined in this library:
  - Default
  - Null
- Also, Easily create your own custom singletons/sentinels types.

**[📄 Detailed Documentation](https://xyngular.github.io/py-u-depend/latest/)** | **[🐍 PyPi](https://pypi.org/project/py-u-depend/)**

# Install

```bash
# via pip
pip install guards

# via poetry
poetry add guards
```

# Quick Start

```python
# This is the "my_resources.py" file/module.

import boto3
from udepend import PerThreadDependency

class S3(PerThreadDependency):
    def __init__(self, **kwargs):
        # Keeping this simple; a more complex version
        # may store the `kwargs` and lazily create the s3 resource
        # only when it's asked for (via a `@property or some such).
        
        self.resource = boto3.resource('s3', **kwargs)
```

To use this resource in codebase, you can do this:

```python
# This is the "my_functions.py" file/module

from .my_resources import S3

def download_file(file_name, dest_path):
    # Get dependency
    s3_resource = S3.grab().resource
    s3_resource.Bucket('my-bucket').download_file(file_name, dest_path)
```

Inject a different version of the resource:

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

# Licensing

This library is licensed under the MIT-0 License. See the LICENSE file.
