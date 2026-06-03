# SWE-bench Issue: astropy__astropy-12825

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-12825
- Base Commit: 43ee5806e9c6f7d58c12c1cb9287b3c61abe489d
- Environment Setup Commit: 298ccb478e6bf092953bca67a3d29dc6c35f6752
- Created At: 2022-02-05T12:13:44Z
- Version: 4.3

## Issue Title
SkyCoord in Table breaks aggregate on group_by

## Problem Statement
SkyCoord in Table breaks aggregate on group_by
### Description, actual behaviour, reproduction
When putting a column of `SkyCoord`s in a `Table`, `aggregate` does not work on `group_by().groups`:

```python
from astropy.table import Table
import astropy.units as u
from astropy.coordinates import SkyCoord
import numpy as np

ras = [10, 20] * u.deg
decs = [32, -2] * u.deg

str_col = ['foo', 'bar']
coords = SkyCoord(ra=ras, dec=decs)

table = Table([str_col, coords], names=['col1', 'col2'])
table.group_by('col1').groups.aggregate(np.mean)
```

 fails with 

```
Traceback (most recent call last):
  File "repro.py", line 13, in <module>
    table.group_by('col1').groups.aggregate(np.mean)
  File "astropy/table/groups.py", line 357, in aggregate
    new_col = col.groups.aggregate(func)
  File "astropy/coordinates/sky_coordinate.py", line 835, in __getattr__
    raise AttributeError("'{}' object has no attribute '{}'"
AttributeError: 'SkyCoord' object has no attribute 'groups'
```
This happens irregardless of the aggregation function.

### Expected behavior
Aggregation works, only fails to aggregate columns where operation does not make sense.


### System Details
```
Linux-5.14.11-arch1-1-x86_64-with-glibc2.33
Python 3.9.7 (default, Aug 31 2021, 13:28:12) 
[GCC 11.1.0]
Numpy 1.21.2
astropy 5.0.dev945+g7dfa1edb2
(no scipy or matplotlib)
```
and
```
Linux-5.14.11-arch1-1-x86_64-with-glibc2.33
Python 3.9.7 (default, Aug 31 2021, 13:28:12) 
[GCC 11.1.0]
Numpy 1.21.2
astropy 4.3.1
Scipy 1.7.1
Matplotlib 3.4.3
```

## Issue Discussion Hints
Hmm. Maybe the logic here needs fixing:

https://github.com/astropy/astropy/blob/bcde23429a076859af856d941282f3df917b8dd4/astropy/table/groups.py#L351-L360
Mostly finished with a fix for this which makes it possible to aggregate tables that have mixin columns. In cases where the aggregation makes sense (e.g. with Quantity) it will just work. In other cases a warning only.

## Failing Tests That Should Pass
- `astropy/table/tests/test_groups.py::test_table_aggregate[False]`
- `astropy/table/tests/test_groups.py::test_table_aggregate[True]`
- `astropy/table/tests/test_groups.py::test_group_mixins_unsupported[col0]`
- `astropy/table/tests/test_groups.py::test_group_mixins_unsupported[col1]`
- `astropy/table/tests/test_groups.py::test_group_mixins_unsupported[col2]`

## Existing Passing Tests To Preserve
- `astropy/table/tests/test_groups.py::test_column_group_by[False]`
- `astropy/table/tests/test_groups.py::test_column_group_by[True]`
- `astropy/table/tests/test_groups.py::test_table_group_by[False]`
- `astropy/table/tests/test_groups.py::test_groups_keys[False]`
- `astropy/table/tests/test_groups.py::test_groups_keys[True]`
- `astropy/table/tests/test_groups.py::test_groups_iterator[False]`
- `astropy/table/tests/test_groups.py::test_groups_iterator[True]`
- `astropy/table/tests/test_groups.py::test_grouped_copy[False]`
- `astropy/table/tests/test_groups.py::test_grouped_copy[True]`
- `astropy/table/tests/test_groups.py::test_grouped_slicing[False]`
- `astropy/table/tests/test_groups.py::test_grouped_slicing[True]`
- `astropy/table/tests/test_groups.py::test_group_column_from_table[False]`
- `astropy/table/tests/test_groups.py::test_group_column_from_table[True]`
- `astropy/table/tests/test_groups.py::test_table_groups_mask_index[False]`
- `astropy/table/tests/test_groups.py::test_table_groups_mask_index[True]`
- `astropy/table/tests/test_groups.py::test_table_groups_array_index[False]`
- `astropy/table/tests/test_groups.py::test_table_groups_array_index[True]`
- `astropy/table/tests/test_groups.py::test_table_groups_slicing[False]`
- `astropy/table/tests/test_groups.py::test_table_groups_slicing[True]`
- `astropy/table/tests/test_groups.py::test_grouped_item_access[False]`
- `astropy/table/tests/test_groups.py::test_grouped_item_access[True]`
- `astropy/table/tests/test_groups.py::test_mutable_operations[False]`
- `astropy/table/tests/test_groups.py::test_mutable_operations[True]`
- `astropy/table/tests/test_groups.py::test_group_by_masked[False]`
- `astropy/table/tests/test_groups.py::test_group_by_errors[False]`
- `astropy/table/tests/test_groups.py::test_group_by_errors[True]`
- `astropy/table/tests/test_groups.py::test_groups_keys_meta[False]`
- `astropy/table/tests/test_groups.py::test_groups_keys_meta[True]`
- `astropy/table/tests/test_groups.py::test_table_aggregate_reduceat[False]`
- `astropy/table/tests/test_groups.py::test_table_aggregate_reduceat[True]`
- `astropy/table/tests/test_groups.py::test_column_aggregate[False]`
- `astropy/table/tests/test_groups.py::test_column_aggregate[True]`
- `astropy/table/tests/test_groups.py::test_column_aggregate_f8`
- `astropy/table/tests/test_groups.py::test_table_filter`
- `astropy/table/tests/test_groups.py::test_column_filter`
- `astropy/table/tests/test_groups.py::test_group_mixins`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
