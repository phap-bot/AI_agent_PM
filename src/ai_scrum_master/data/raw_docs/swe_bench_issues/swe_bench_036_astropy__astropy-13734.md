# SWE-bench Issue: astropy__astropy-13734

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13734
- Base Commit: 9fd247339e51441460b43368d415fced327c97a2
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-09-22T09:27:55Z
- Version: 5.0

## Issue Title
Add option to input/output column units for fixed width tables

## Problem Statement
Add option to input/output column units for fixed width tables
Extend the `io.ascii.FixedWidth` reader to include a keyword arg that will specify that there is a row of unit specifiers after the column name specifiers (or at the top of the header if there are no column names).  This will apply for both reading and writing fixed width tables.

This allows for outputting a table to a file in a format like `Table.pprint` with `show_units=True`, and then reading back that table with no information loss.

## Issue Discussion Hints
Rescheduling for 1.1 since there was interest.

Will finish off #2869 for 1.2.

## Failing Tests That Should Pass
- `astropy/io/ascii/tests/test_fixedwidth.py::test_fixed_width_header_rows`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_fixed_width_two_line_header_rows`

## Existing Passing Tests To Preserve
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_normal`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_normal_names`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_normal_names_include`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_normal_exclude`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_weird`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_double`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_space_delimiter`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_no_header_autocolumn`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_no_header_names`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_no_header_autocolumn_NoHeader`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_no_header_names_NoHeader`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_col_starts`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_detect_col_starts_or_ends`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_normal`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_fill_values`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_no_pad`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_no_bookend`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_no_delimiter`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_noheader_normal`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_noheader_no_pad`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_noheader_no_bookend`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_noheader_no_delimiter`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_formats`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_twoline_normal`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_twoline_ReST`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_twoline_human`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_twoline_fail`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_read_twoline_wrong_marker`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_twoline_normal`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_twoline_no_pad`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_write_twoline_no_bookend`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_fixedwidthnoheader_splitting`
- `astropy/io/ascii/tests/test_fixedwidth.py::test_fixed_width_no_header_header_rows`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
