# SWE-bench Issue: astropy__astropy-13842

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13842
- Base Commit: 3b448815e21b117d34fe63007b8ef63ee084fefb
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-10-17T20:14:28Z
- Version: 5.0

## Issue Title
Creating a mixin column in a new table from columns of another table renames columns in original table.

## Problem Statement
Creating a mixin column in a new table from columns of another table renames columns in original table.
### Description

Consider the following code, where a subset of columns from another table should be included in a new table with new names, prerably without copying the actual payload data:

```python
from astropy.table import QTable, Table
import astropy.units as u


table1 = QTable({
    'foo': [1, 2, 3] * u.deg,
    'bar': [4, 5, 6] * u.m,
    'baz': [7, 8, 9] * u.TeV,
})

print(table1.colnames)
table2 = QTable({
    "new": table1["foo"],
    "name": table1["bar"]
}, copy=False)
print(table1.colnames)
```

If any of the two classes or both are a `Table`, not a `QTable`, the code works as expected.

### Expected behavior

Data in the columns is not copied, but column names in original table stay the same.

```
['foo', 'bar', 'baz']
['foo', 'bar', 'baz']
```

### Actual behavior

Column names do change in both tables:

```
['foo', 'bar', 'baz']
['new', 'name', 'baz']
```

### Steps to Reproduce

See above.

### System Details
<!-- Even if you do not think this is necessary, it is useful information for the maintainers.
Please run the following snippet and paste the output below:
import platform; print(platform.platform())
import sys; print("Python", sys.version)
import numpy; print("Numpy", numpy.__version__)
import erfa; print("pyerfa", erfa.__version__)
import astropy; print("astropy", astropy.__version__)
import scipy; print("Scipy", scipy.__version__)
import matplotlib; print("Matplotlib", matplotlib.__version__)
-->

```
Linux-5.15.71-1-MANJARO-x86_64-with-glibc2.36
Python 3.10.6 | packaged by conda-forge | (main, Aug 22 2022, 20:35:26) [GCC 10.4.0]
Numpy 1.23.3
pyerfa 2.0.0.1
astropy 5.1
Scipy 1.9.1
Matplotlib 3.6.1
```

(also tested with current `main` branch)

## Issue Discussion Hints
Ouch! Reproduce this. Also
```
table2['new'] is table1['new']
# True
```
so the problem seems to be that the tables hold the same `Quantity` instead of different instances that share the data.
Note that it is not specific to `QTable`, but just to any mixin column (and the behaviour not limited to `dict` either):
```
import numpy as np
from astropy.table import Table
from astropy.time import Time
table1 = Table({'t': Time(np.arange(50000., 50004.), format='mjd')})
table2 = Table({'new': table1['t']}, copy=False)
print(f"{table1.colnames=}, {table2.colnames=}")
# table1.colnames=['new'], table2.colnames=['new']
table3 = Table([table1['new']], names=['old'], copy=False)
print(f"{table1.colnames=}, {table2.colnames=}, {table3.colnames=}")
# table1.colnames=['new'], table2.colnames=['old'], table3.colnames=['old']
```

EDIT: actually the above is puzzling; why is `table1.colnames` still `['new']`? Checking, I see that `table1['new'] is table2['old']` holds and `table1['new'].info.name` gives 'old'...

Not completely sure how easy it is to change this behaviour -- can we could on any mixing column to allow `new_instance = cls(old_instance, copy=False)`. The relevant code is https://github.com/astropy/astropy/blob/96dde46c854cd34cf3fd4b485d1250e32a78648e/astropy/table/table.py#L1265-L1270
It may get a bit worse. After my above example:
```
table1['new'].info.parent_table is table1
# False
table1['new'].info.parent_table is table3
# True
```
Similarly, after the example on top,
```
table1['new'].info.parent_table is table2
# True
```
So, the mixin columns belong to the last table they were made part of.

Time to ping @taldcroft...
@taldcroft - I think the solution would be to have something like `Time`'s `replicate()` on all info. The implementation that would work for all astropy classes (I think) is
```
map = mixin.info._represent_as_dict()
map['copy'] = False
new_instance = mixin.info._construct_from_dict(map)
```

Something like this could become part of `col_copy` if it had a `copy` argument.
@mhvk - not good... unfortunately I'm trying to be mostly on vacation at the moment, but if you have ideas please have a go at trying an implementation.

## Failing Tests That Should Pass
- `astropy/table/tests/test_mixin.py::test_add_column[arrayswap-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[arraywrap-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[cartesianrep-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[earthlocation-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[latitude-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[longitude-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[ndarraybig-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[ndarraylil-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[quantity-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[skycoord-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[sphericaldiff-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[sphericalrep-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[sphericalrepdiff-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[time-False]`
- `astropy/table/tests/test_mixin.py::test_add_column[timedelta-False]`
- `astropy/table/tests/test_mixin.py::test_ensure_input_info_is_unchanged[QTable-False]`

## Existing Passing Tests To Preserve
- `astropy/table/tests/test_mixin.py::test_attributes[arrayswap]`
- `astropy/table/tests/test_mixin.py::test_attributes[arraywrap]`
- `astropy/table/tests/test_mixin.py::test_attributes[cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_attributes[earthlocation]`
- `astropy/table/tests/test_mixin.py::test_attributes[latitude]`
- `astropy/table/tests/test_mixin.py::test_attributes[longitude]`
- `astropy/table/tests/test_mixin.py::test_attributes[ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_attributes[ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_attributes[quantity]`
- `astropy/table/tests/test_mixin.py::test_attributes[skycoord]`
- `astropy/table/tests/test_mixin.py::test_attributes[sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_attributes[sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_attributes[sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_attributes[time]`
- `astropy/table/tests/test_mixin.py::test_attributes[timedelta]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-arrayswap]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-arraywrap]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-earthlocation]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-latitude]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-longitude]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-quantity]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-skycoord]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-time]`
- `astropy/table/tests/test_mixin.py::test_make_table[unmasked-timedelta]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-arrayswap]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-arraywrap]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-earthlocation]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-latitude]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-longitude]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-quantity]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-skycoord]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-time]`
- `astropy/table/tests/test_mixin.py::test_make_table[masked-timedelta]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-arrayswap]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-arraywrap]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-earthlocation]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-latitude]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-longitude]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-quantity]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-skycoord]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-time]`
- `astropy/table/tests/test_mixin.py::test_make_table[subclass-timedelta]`
- `astropy/table/tests/test_mixin.py::test_io_ascii_write`
- `astropy/table/tests/test_mixin.py::test_votable_quantity_write`
- `astropy/table/tests/test_mixin.py::test_io_time_write_fits_local[Table]`
- `astropy/table/tests/test_mixin.py::test_io_time_write_fits_local[QTable]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[arrayswap]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[arraywrap]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[skycoord]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[time]`
- `astropy/table/tests/test_mixin.py::test_votable_mixin_write_fail[timedelta]`
- `astropy/table/tests/test_mixin.py::test_join[unmasked]`
- `astropy/table/tests/test_mixin.py::test_join[masked]`
- `astropy/table/tests/test_mixin.py::test_join[subclass]`
- `astropy/table/tests/test_mixin.py::test_hstack[unmasked]`
- `astropy/table/tests/test_mixin.py::test_hstack[masked]`
- `astropy/table/tests/test_mixin.py::test_hstack[subclass]`
- `astropy/table/tests/test_mixin.py::test_get_items[arrayswap]`
- `astropy/table/tests/test_mixin.py::test_get_items[arraywrap]`
- `astropy/table/tests/test_mixin.py::test_get_items[cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_get_items[earthlocation]`
- `astropy/table/tests/test_mixin.py::test_get_items[latitude]`
- `astropy/table/tests/test_mixin.py::test_get_items[longitude]`
- `astropy/table/tests/test_mixin.py::test_get_items[ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_get_items[ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_get_items[quantity]`
- `astropy/table/tests/test_mixin.py::test_get_items[skycoord]`
- `astropy/table/tests/test_mixin.py::test_get_items[sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_get_items[sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_get_items[sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_get_items[time]`
- `astropy/table/tests/test_mixin.py::test_get_items[timedelta]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[arrayswap]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[arraywrap]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[earthlocation]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[latitude]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[longitude]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[quantity]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[skycoord]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[time]`
- `astropy/table/tests/test_mixin.py::test_info_preserved_pickle_copy_init[timedelta]`
- `astropy/table/tests/test_mixin.py::test_add_column[arrayswap-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[arraywrap-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[cartesianrep-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[earthlocation-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[latitude-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[longitude-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[ndarraybig-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[ndarraylil-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[quantity-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[skycoord-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[sphericaldiff-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[sphericalrep-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[sphericalrepdiff-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[time-True]`
- `astropy/table/tests/test_mixin.py::test_add_column[timedelta-True]`
- `astropy/table/tests/test_mixin.py::test_vstack`
- `astropy/table/tests/test_mixin.py::test_insert_row[arrayswap]`
- `astropy/table/tests/test_mixin.py::test_insert_row[arraywrap]`
- `astropy/table/tests/test_mixin.py::test_insert_row[cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_insert_row[earthlocation]`
- `astropy/table/tests/test_mixin.py::test_insert_row[latitude]`
- `astropy/table/tests/test_mixin.py::test_insert_row[longitude]`
- `astropy/table/tests/test_mixin.py::test_insert_row[ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_insert_row[ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_insert_row[quantity]`
- `astropy/table/tests/test_mixin.py::test_insert_row[skycoord]`
- `astropy/table/tests/test_mixin.py::test_insert_row[sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_insert_row[sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_insert_row[sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_insert_row[time]`
- `astropy/table/tests/test_mixin.py::test_insert_row[timedelta]`
- `astropy/table/tests/test_mixin.py::test_insert_row_bad_unit`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[arrayswap]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[arraywrap]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[earthlocation]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[latitude]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[longitude]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[quantity]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[skycoord]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[time]`
- `astropy/table/tests/test_mixin.py::test_convert_np_array[timedelta]`
- `astropy/table/tests/test_mixin.py::test_assignment_and_copy`
- `astropy/table/tests/test_mixin.py::test_conversion_qtable_table`
- `astropy/table/tests/test_mixin.py::test_setitem_as_column_name`
- `astropy/table/tests/test_mixin.py::test_quantity_representation`
- `astropy/table/tests/test_mixin.py::test_representation_representation`
- `astropy/table/tests/test_mixin.py::test_skycoord_representation`
- `astropy/table/tests/test_mixin.py::test_ndarray_mixin[True]`
- `astropy/table/tests/test_mixin.py::test_ndarray_mixin[False]`
- `astropy/table/tests/test_mixin.py::test_possible_string_format_functions`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[arrayswap]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[arraywrap]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[cartesianrep]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[earthlocation]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[latitude]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[longitude]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[ndarraybig]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[ndarraylil]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[quantity]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[skycoord]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[sphericaldiff]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[sphericalrep]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[sphericalrepdiff]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[time]`
- `astropy/table/tests/test_mixin.py::test_rename_mixin_columns[timedelta]`
- `astropy/table/tests/test_mixin.py::test_represent_mixins_as_columns_unit_fix`
- `astropy/table/tests/test_mixin.py::test_primary_data_column_gets_description`
- `astropy/table/tests/test_mixin.py::test_skycoord_with_velocity`
- `astropy/table/tests/test_mixin.py::test_ensure_input_info_is_unchanged[Table-True]`
- `astropy/table/tests/test_mixin.py::test_ensure_input_info_is_unchanged[Table-False]`
- `astropy/table/tests/test_mixin.py::test_ensure_input_info_is_unchanged[QTable-True]`
- `astropy/table/tests/test_mixin.py::test_bad_info_class`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
