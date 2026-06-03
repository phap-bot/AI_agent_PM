# SWE-bench Issue: astropy__astropy-13306

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13306
- Base Commit: b3fa7702635b260b008d391705c521fca7283761
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-06-05T15:18:24Z
- Version: 5.0

## Issue Title
vstack'ing structured array tables fails with casting error

## Problem Statement
vstack'ing structured array tables fails with casting error
<!-- This comments are hidden when you submit the issue,
so you do not need to remove them! -->

<!-- Please be sure to check out our contributing guidelines,
https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md .
Please be sure to check out our code of conduct,
https://github.com/astropy/astropy/blob/main/CODE_OF_CONDUCT.md . -->

<!-- Please have a search on our GitHub repository to see if a similar
issue has already been posted.
If a similar issue is closed, have a quick look to see if you are satisfied
by the resolution.
If not please go ahead and open an issue! -->

<!-- Please check that the development version still produces the same bug.
You can install development version with
pip install git+https://github.com/astropy/astropy
command. -->

### Description
<!-- Provide a general description of the bug. -->
Using `table.vstack` on tables containing columns backed by numpy structured arrays fails.




### Steps to Reproduce
<!-- Ideally a code example could be provided so we can run it ourselves. -->
<!-- If you are pasting code, use triple backticks (```) around
your code snippet. -->
<!-- If necessary, sanitize your screen output to be pasted so you do not
reveal secrets like tokens and passwords. -->



```python
a=Table([dict(field1='test',field2=(1.,0.5,1.5))])
b=Table([dict(field1='foo')])
table.vstack((a,b)) # works
a=Table([dict(field1='test',field2=(1.,0.5,1.5))],dtype=[str,[('val','f4'),('min','f4'),('max','f4')]])
table.vstack((a,b)) # fails
```

```
Traceback (most recent call last):
  Input In [45] in <cell line: 1>
    table.vstack((a,b))
  File ~/code/python/astropy/astropy/table/operations.py:651 in vstack
    out = _vstack(tables, join_type, col_name_map, metadata_conflicts)
  File ~/code/python/astropy/astropy/table/operations.py:1409 in _vstack
    col[idx0:idx1] = array[name]
  File ~/code/python/astropy/astropy/table/column.py:1280 in __setitem__
    self.data[index] = value
TypeError: Cannot cast array data from dtype([('val', '<f4'), ('min', '<f4'), ('max', '<f4')]) to dtype('V12') according to the rule 'unsafe'
```

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
macOS-12.3.1-x86_64-i386-64bit
Python 3.10.4 (main, Apr 26 2022, 19:42:59) [Clang 13.1.6 (clang-1316.0.21.2)]
Numpy 1.22.3
pyerfa 2.0.0.1
astropy 5.2.dev92+gf0e2129aa
Scipy 1.7.3
Matplotlib 3.5.2
```

## Issue Discussion Hints
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

GitHub issues in the Astropy repository are used to track bug reports and feature requests; If your issue poses a question about how to use Astropy, please instead raise your question in the [Astropy Discourse user forum](https://community.openastronomy.org/c/astropy/8) and close this issue.

If you feel that this issue has not been responded to in a timely manner, please leave a comment mentioning our software support engineer @embray, or send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
Hmm, clearly the wrong dtype is inferred for the merged column. I guess our tests did not include a stack of a table that had with one that did not have a structured column.
Actually, one can also not do a `vstack` when both tables have the structured column.

## Failing Tests That Should Pass
- `astropy/table/tests/test_operations.py::TestJoin::test_join_structured_column`
- `astropy/table/tests/test_operations.py::TestVStack::test_vstack_structured_column`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_structured_column`

## Existing Passing Tests To Preserve
- `astropy/table/tests/test_operations.py::TestJoin::test_table_meta_merge[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_table_meta_merge[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_table_meta_merge_conflict[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_table_meta_merge_conflict[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_both_unmasked_inner[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_both_unmasked_inner[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_both_unmasked_left_right_outer[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_both_unmasked_single_key_inner[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_both_unmasked_single_key_inner[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_both_unmasked_single_key_left_right_outer[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_masked_unmasked[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_masked_masked[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_classes`
- `astropy/table/tests/test_operations.py::TestJoin::test_col_rename[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_col_rename[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_rename_conflict[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_rename_conflict[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_missing_keys[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_missing_keys[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_bad_join_type[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_bad_join_type[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_no_common_keys[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_no_common_keys[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_masked_key_column[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_col_meta_merge[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_col_meta_merge[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_join_multidimensional[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_join_multidimensional[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_join_multidimensional_masked[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[arrayswap]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[arraywrap]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[cartesianrep]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[latitude]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[longitude]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[ndarraybig]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[ndarraylil]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[quantity]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[skycoord]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[sphericaldiff]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[sphericalrep]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[sphericalrepdiff]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[time]`
- `astropy/table/tests/test_operations.py::TestJoin::test_mixin_functionality[timedelta]`
- `astropy/table/tests/test_operations.py::TestJoin::test_cartesian_join[Table]`
- `astropy/table/tests/test_operations.py::TestJoin::test_cartesian_join[QTable]`
- `astropy/table/tests/test_operations.py::TestJoin::test_keys_left_right_basic`
- `astropy/table/tests/test_operations.py::TestJoin::test_keys_left_right_exceptions`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_default_same_columns[Table]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_default_same_columns[QTable]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_default_same_tables[Table]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_default_same_tables[QTable]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_extra_col_left_table[Table]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_extra_col_left_table[QTable]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_extra_col_right_table[Table]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_extra_col_right_table[QTable]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_keys[Table]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_keys[QTable]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_missing_key[Table]`
- `astropy/table/tests/test_operations.py::TestSetdiff::test_missing_key[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_validate_join_type`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_rows[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_rows[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_table_column[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_table_column[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_table_meta_merge[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_table_meta_merge[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_table_meta_merge_conflict[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_table_meta_merge_conflict[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_bad_input_type[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_bad_input_type[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_basic_inner[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_basic_inner[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_basic_outer[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_incompatible[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_stack_incompatible[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_vstack_one_masked[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_col_meta_merge_inner[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_col_meta_merge_inner[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_col_meta_merge_outer[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_vstack_one_table[Table]`
- `astropy/table/tests/test_operations.py::TestVStack::test_vstack_one_table[QTable]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[arrayswap]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[arraywrap]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[cartesianrep]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[latitude]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[longitude]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[ndarraybig]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[ndarraylil]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[quantity]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[skycoord]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[sphericaldiff]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[sphericalrep]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[sphericalrepdiff]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[time]`
- `astropy/table/tests/test_operations.py::TestVStack::test_mixin_functionality[timedelta]`
- `astropy/table/tests/test_operations.py::TestVStack::test_vstack_different_representation`
- `astropy/table/tests/test_operations.py::TestDStack::test_validate_join_type`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_table_column[Table]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_table_column[QTable]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_basic_outer[Table]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_basic_inner[Table]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_basic_inner[QTable]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_multi_dimension_column[Table]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_multi_dimension_column[QTable]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_different_length_table[Table]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_different_length_table[QTable]`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_single_table`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_representation`
- `astropy/table/tests/test_operations.py::TestDStack::test_dstack_skycoord`
- `astropy/table/tests/test_operations.py::TestHStack::test_validate_join_type`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_same_table[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_same_table[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_rows[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_rows[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_columns[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_columns[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_table_meta_merge[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_table_meta_merge[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_table_meta_merge_conflict[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_table_meta_merge_conflict[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_bad_input_type[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_bad_input_type[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_basic[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_basic[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_incompatible[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_stack_incompatible[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_hstack_one_masked[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_table_col_rename[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_table_col_rename[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_col_meta_merge[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_col_meta_merge[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_hstack_one_table[Table]`
- `astropy/table/tests/test_operations.py::TestHStack::test_hstack_one_table[QTable]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[arrayswap]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[arraywrap]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[cartesianrep]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[latitude]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[longitude]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[ndarraybig]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[ndarraylil]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[quantity]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[skycoord]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[sphericaldiff]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[sphericalrep]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[sphericalrepdiff]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[time]`
- `astropy/table/tests/test_operations.py::TestHStack::test_mixin_functionality[timedelta]`
- `astropy/table/tests/test_operations.py::test_unique[Table]`
- `astropy/table/tests/test_operations.py::test_unique[QTable]`
- `astropy/table/tests/test_operations.py::test_vstack_bytes[Table]`
- `astropy/table/tests/test_operations.py::test_vstack_bytes[QTable]`
- `astropy/table/tests/test_operations.py::test_vstack_unicode`
- `astropy/table/tests/test_operations.py::test_join_mixins_not_sortable`
- `astropy/table/tests/test_operations.py::test_join_non_1d_key_column`
- `astropy/table/tests/test_operations.py::test_argsort_time_column`
- `astropy/table/tests/test_operations.py::test_sort_indexed_table`
- `astropy/table/tests/test_operations.py::test_get_out_class`
- `astropy/table/tests/test_operations.py::test_masking_required_exception`
- `astropy/table/tests/test_operations.py::test_stack_columns`
- `astropy/table/tests/test_operations.py::test_mixin_join_regression`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
