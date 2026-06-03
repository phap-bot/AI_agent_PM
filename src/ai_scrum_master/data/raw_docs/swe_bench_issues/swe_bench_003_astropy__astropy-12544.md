# SWE-bench Issue: astropy__astropy-12544

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-12544
- Base Commit: 3a0cd2d8cd7b459cdc1e1b97a14f3040ccc1fffc
- Environment Setup Commit: 298ccb478e6bf092953bca67a3d29dc6c35f6752
- Created At: 2021-11-30T16:14:01Z
- Version: 4.3

## Issue Title
Can Table masking be turned off?

## Problem Statement
Can Table masking be turned off?
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

### Description
<!-- Provide a general description of the feature you would like. -->
<!-- If you want to, you can suggest a draft design or API. -->
<!-- This way we have a deeper discussion on the feature. -->

As of Astropy 5, when `astropy.table.Table.read()` encounters values such as `NaN`, it automatically creates a `MaskedColumn` and the whole table becomes a `MaskedTable`.  While this might be useful for individual end-users, it is very inconvenient for intermediate data in pipelines.

Here's the scenario: data are being passed via files and `Table.read()`.  A downstream function needs to replace `NaN` with valid values.  Previously those values could be easily identified (*e.g.* `np.isnan()` and replaced.  However, now additional work is need to look "underneath" the mask, extracting the actual values, replacing them, and then possibly creating a new, unmasked column, or even an entirely new table.

Ideally, a keyword like `Table.read(filename, ..., mask=False)` would disable this behavior, for people who don't need this masking.

## Issue Discussion Hints
No issue discussion hints provided.

## Failing Tests That Should Pass
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_mask_nans_on_read`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_mask_str_on_read`

## Existing Passing Tests To Preserve
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_meta_conflicting`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_custom_units_qtable`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_read_with_unit_aliases[Table]`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_read_with_unit_aliases[QTable]`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_masked`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_masked_nan[True]`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_masked_nan[False]`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_masked_serialize_data_mask`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_read_from_fileobj`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_read_with_nonstandard_units`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_write_drop_nonstandard_units[Table]`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_write_drop_nonstandard_units[QTable]`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_memmap`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_oned_single_element`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_write_append`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_write_overwrite`
- `astropy/io/fits/tests/test_connect.py::TestSingleTable::test_mask_null_on_read`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_0`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_1[1]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_1[first]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_2[2]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_2[second]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_3[3]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_3[third]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_4`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_missing[2]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_missing[3]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_missing[1]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_missing[second]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_missing[]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_warning[0]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_warning[2]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_with_hdu_warning[third]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_in_last_hdu[0]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_in_last_hdu[1]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_in_last_hdu[third]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_0`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_single_table[1]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_single_table[first]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_single_table[None]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_1[1]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_1[first]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_2[2]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_2[second]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_3[3]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_3[third]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_warning[0]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_warning[2]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_warning[third]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_missing[2]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_missing[3]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_missing[1]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_missing[second]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_with_hdu_missing[]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_in_last_hdu[0]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_in_last_hdu[1]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_hdulist_in_last_hdu[third]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_single_hdu[None]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_single_hdu[1]`
- `astropy/io/fits/tests/test_connect.py::TestMultipleHDU::test_read_from_single_hdu[first]`
- `astropy/io/fits/tests/test_connect.py::test_masking_regression_1795`
- `astropy/io/fits/tests/test_connect.py::test_scale_error`
- `astropy/io/fits/tests/test_connect.py::test_parse_tdisp_format[EN10.5-format_return0]`
- `astropy/io/fits/tests/test_connect.py::test_parse_tdisp_format[F6.2-format_return1]`
- `astropy/io/fits/tests/test_connect.py::test_parse_tdisp_format[B5.10-format_return2]`
- `astropy/io/fits/tests/test_connect.py::test_parse_tdisp_format[E10.5E3-format_return3]`
- `astropy/io/fits/tests/test_connect.py::test_parse_tdisp_format[A21-format_return4]`
- `astropy/io/fits/tests/test_connect.py::test_fortran_to_python_format[G15.4E2-{:15.4g}]`
- `astropy/io/fits/tests/test_connect.py::test_fortran_to_python_format[Z5.10-{:5x}]`
- `astropy/io/fits/tests/test_connect.py::test_fortran_to_python_format[I6.5-{:6d}]`
- `astropy/io/fits/tests/test_connect.py::test_fortran_to_python_format[L8-{:>8}]`
- `astropy/io/fits/tests/test_connect.py::test_fortran_to_python_format[E20.7-{:20.7e}]`
- `astropy/io/fits/tests/test_connect.py::test_python_to_tdisp[{:3d}-I3]`
- `astropy/io/fits/tests/test_connect.py::test_python_to_tdisp[3d-I3]`
- `astropy/io/fits/tests/test_connect.py::test_python_to_tdisp[7.3f-F7.3]`
- `astropy/io/fits/tests/test_connect.py::test_python_to_tdisp[{:>4}-A4]`
- `astropy/io/fits/tests/test_connect.py::test_python_to_tdisp[{:7.4f}-F7.4]`
- `astropy/io/fits/tests/test_connect.py::test_python_to_tdisp[%5.3g-G5.3]`
- `astropy/io/fits/tests/test_connect.py::test_python_to_tdisp[%10s-A10]`
- `astropy/io/fits/tests/test_connect.py::test_python_to_tdisp[%.4f-F13.4]`
- `astropy/io/fits/tests/test_connect.py::test_logical_python_to_tdisp`
- `astropy/io/fits/tests/test_connect.py::test_bool_column`
- `astropy/io/fits/tests/test_connect.py::test_unicode_column`
- `astropy/io/fits/tests/test_connect.py::test_unit_warnings_read_write`
- `astropy/io/fits/tests/test_connect.py::test_convert_comment_convention`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col0]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col1]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col2]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col3]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col4]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col5]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col7]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col8]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col13]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col14]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col15]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col16]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col17]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[Table-name_col18]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col0]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col1]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col2]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col3]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col4]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col5]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col7]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col8]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col9]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col10]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col11]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col12]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col13]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col14]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col15]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col16]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col17]`
- `astropy/io/fits/tests/test_connect.py::test_fits_mixins_per_column[QTable-name_col18]`
- `astropy/io/fits/tests/test_connect.py::test_info_attributes_with_no_mixins`
- `astropy/io/fits/tests/test_connect.py::test_round_trip_masked_table_serialize_mask[set_cols]`
- `astropy/io/fits/tests/test_connect.py::test_round_trip_masked_table_serialize_mask[names]`
- `astropy/io/fits/tests/test_connect.py::test_round_trip_masked_table_serialize_mask[class]`
- `astropy/io/fits/tests/test_connect.py::test_meta_not_modified`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
