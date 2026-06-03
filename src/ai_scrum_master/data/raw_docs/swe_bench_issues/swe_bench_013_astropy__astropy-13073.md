# SWE-bench Issue: astropy__astropy-13073

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13073
- Base Commit: 43ee5806e9c6f7d58c12c1cb9287b3c61abe489d
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-04-06T16:29:58Z
- Version: 5.0

## Issue Title
Document reading True/False in ASCII table as bool not str

## Problem Statement
Document reading True/False in ASCII table as bool not str
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

#12826 showed a use case for having an ASCII table column consisting of only "True" and "False" be read as `bool` instead of `str` (current behavior). That issue discusses reasons to maintain the current behavior, but there are simple workarounds discussed there that should be brought out to the narrative docs as examples for users.

I'd suggest the following as a recommendation for users:
```
from astropy.io.ascii import convert_numpy
converters = {'*': [convert_numpy(typ) for typ in (int, float, bool, str)]}

# Then for example
dat = Table.read(filename, format='ascii', converters=converters)
```
This new information could go in the existing section on `Converters` in the `io.ascii` read documentation.

### Additional context
<!-- Add any other context or screenshots about the feature request here. -->
<!-- This part is optional. -->

#12826
Control dtype with ascii.read (converters API needs better doc or refactoring)
I cannot find a way to control the dtype of the output table when reading a file into a `Table`. Consider the following MWE, with 3 numerical columns, while one of them would preferably be kept as a string:

```
>>> from astropy.io import ascii

>>> indata = ("# This is a dummy file\n" 
...           "# with some text to ignore, and a header with column names\n" 
...           "# ra dec objid\n" 
...           "1 2 345\n" 
...           "3 4 456\n") 

>>> ascii.read(indata, format='commented_header', header_start=2, guess=False, fast_reader=False)
<Table length=2>
  ra   dec  objid
int64 int64 int64
----- ----- -----
    1     2   345
    3     4   456

>>> ascii.read(indata, format='commented_header', header_start=2, dtye=('i8', 'i8', 'S10'), guess=False, fast_reader=False)
TypeError: __init__() got an unexpected keyword argument 'dtye'
```

Reading in the same with `np.loadtxt` and then converting to a Table works, but it should ideally be supported directly.

```
import numpy as np
from astropy.table import Table

>>> Table(np.loadtxt('/tmp/a', dtype=[('ra', 'i8'), ('dec', 'i8'), ('objid', 'S10')]))
<Table length=2>
  ra   dec   objid 
int64 int64 bytes10
----- ----- -------
    1     2     345
    3     4     456
```

## Issue Discussion Hints
Hi!

I'm wondering if something as simple as this is sufficient or if you think it needs its own example altogether:
```python  
>>> import numpy as np
>>> converters = {'uint_col': [ascii.convert_numpy(np.uint)],
...               'float32_col': [ascii.convert_numpy(np.float32)],
...               'bool_col': [ascii.convert_numpy(bool)]}
>>> ascii.read('file.dat', converters=converters)
```

While we're at it should we update the preceding paragraph

> The type provided to [convert_numpy()](https://docs.astropy.org/en/stable/api/astropy.io.ascii.convert_numpy.html#astropy.io.ascii.convert_numpy) must be a valid [NumPy type](https://numpy.org/doc/stable/user/basics.types.html) such as numpy.int, numpy.uint, numpy.int8, numpy.int64, numpy.float, numpy.float64, or numpy.str.

 to use the regular python types for `string`, `int` and `bool` instead of the deprecated `np.string`, `np.int` and `np.bool`?
Thanks for looking into this @pjs902. I think the advantage of the original suggested workaround is that it will work for any table regardless of column names. I suspect that in most cases of tables with `True/False` strings, the user wants this applied to every column that looks like a bool.

Definitely :+1: on updating the docs to use regular Python types instead of the deprecated numpy versions.
@taldcroft Sorry if I wasn't clear, I had only changed the column names to make it obvious that we had columns with different types, not suggesting that we require certain column names for certain types, I could switch these back to the original column names which were just `col1`, `col2`, `col3`.
@pjs902 - I had a mistake in the original suggested workaround to document, which I have now fixed:
```
converters = {'*': [convert_numpy(typ) for typ in (int, float, bool, str)]}
```
With this definition of `converters`, there is no need to specify any column names at all since the `*` glob matches every column name.
@taldcroft Both solutions seem to work equally well, do you think it's better to switch the example in the docs to 

> converters = {'*': [convert_numpy(typ) for typ in (int, float, bool, str)]}

or better to leave the existing pattern as is, just including a boolean example? Something like this:

> converters = {'col1': [ascii.convert_numpy(np.uint)],
  ...      'col2': [ascii.convert_numpy(np.float32)],
  ...       'col3': [ascii.convert_numpy(bool)]}


 I think, for the documentation, I prefer the existing pattern where each column is individually specified as is. In the next paragraph, we explicitly go over the usage of `fnmatch` for matching glob patterns but I'm happy to defer to your judgement here. 
@pjs902 - hopefully you haven't started in on this, because this morning I got an idea to simplify the converter input to not require this whole `ascii.convert_numpy()` wrapper. So I'm just going to fold in this bool not str into my doc updates now.
@taldcroft No worries! Sounds like a much nicer solution!
I used [converters](https://docs.astropy.org/en/stable/io/ascii/read.html#converters) when I had to do this a long time ago. And I think it still works? 

```python
>>> converters = {
...     'ra': [ascii.convert_numpy(np.int)],
...     'dec': [ascii.convert_numpy(np.int)],
...     'objid': [ascii.convert_numpy(np.str)]}
>>> t = ascii.read(
...     indata, format='commented_header', header_start=2,
...     converters=converters, guess=False, fast_reader=False)
>>> t
<Table length=2>
  ra   dec  objid
int32 int32  str3
----- ----- -----
    1     2   345
    3     4   456
```

You might have to play around with it until you get the exact data type you want though. Hope this helps!
Oh, yes, indeed, this is exactly what I need. One minor comment though, it would be helpful to have the word `dtype` somewhere in the docs, as I was searching for `dtype` in that and many other docs pages without any useful results. (maybe it's just me, that case this can be closed without a docs change, otherwise this can be a good "first issue").

It's also not clear what the "previous section" is referred to in ``These take advantage of the convert_numpy() function which returns a two-element tuple (converter_func, converter_type) as described in the previous section.`` 
Yes, the `converters` mechanism is not that obvious and a perfect example of overdesign from this 10+ year old package.

It probably would be easy to add a `dtype` argument to mostly replace `converters`. This would pretty much just generate those `converters` at the point when needed.  Thoughts?
I agree that the `converters` API could be improved; I have a very old feature request at #4934  , which will be moot if you use a new API like `dtype=[np.int, np.int, np.str]` or `dtype=np.int` (the latter assumes broadcasting to all columns, which might or might not be controversial).
I've implemented this in a few lines of code. As always the pain is testing, docs etc. But maybe there will be a PR on the way.
```
In [2]: >>> ascii.read(indata, format='commented_header', header_start=2, dtype=('i8', 'i4', 'S10'), guess=False, fast_reader=False)
Out[2]: 
<Table length=2>
  ra   dec   objid 
int64 int32 bytes10
----- ----- -------
    1     2     345
    3     4     456
```
Thank you, this looks very good to me. I suppose converter is a bit like clobber for fits, makes total sense when you already know about it, but a bit difficult to discover. The only question whether dtype should also understand the list of tuples that include the column name to be consistent with numpy. I don't think that API is that great, still is worth some thinking about.
Do we... need an APE? 😸 
I was planning for the `dtype` to be consistent what `Table` accepts, which is basically just a sequence of simple dtypes. It starts getting complicated otherwise because of multiple potentially conflicting ways to provide the names. Allowing names in the dtype would also not fit in well with the current implementation in `io.ascii`.

## Failing Tests That Should Pass
- `astropy/io/ascii/tests/test_read.py::test_read_converters_simplified`

## Existing Passing Tests To Preserve
- `astropy/io/ascii/tests/test_read.py::test_convert_overflow[True]`
- `astropy/io/ascii/tests/test_read.py::test_convert_overflow[fast_reader2]`
- `astropy/io/ascii/tests/test_read.py::test_convert_overflow[fast_reader3]`
- `astropy/io/ascii/tests/test_read.py::test_convert_overflow[force]`
- `astropy/io/ascii/tests/test_read.py::test_read_specify_converters_with_names`
- `astropy/io/ascii/tests/test_read.py::test_read_remove_and_rename_columns`
- `astropy/io/ascii/tests/test_read.py::test_guess_with_names_arg`
- `astropy/io/ascii/tests/test_read.py::test_guess_with_format_arg`
- `astropy/io/ascii/tests/test_read.py::test_guess_with_delimiter_arg`
- `astropy/io/ascii/tests/test_read.py::test_reading_mixed_delimiter_tabs_spaces`
- `astropy/io/ascii/tests/test_read.py::test_read_with_names_arg[True]`
- `astropy/io/ascii/tests/test_read.py::test_read_with_names_arg[False]`
- `astropy/io/ascii/tests/test_read.py::test_read_with_names_arg[force]`
- `astropy/io/ascii/tests/test_read.py::test_read_all_files[True]`
- `astropy/io/ascii/tests/test_read.py::test_read_all_files[False]`
- `astropy/io/ascii/tests/test_read.py::test_read_all_files[force]`
- `astropy/io/ascii/tests/test_read.py::test_read_all_files_via_table[True]`
- `astropy/io/ascii/tests/test_read.py::test_read_all_files_via_table[False]`
- `astropy/io/ascii/tests/test_read.py::test_read_all_files_via_table[force]`
- `astropy/io/ascii/tests/test_read.py::test_guess_all_files`
- `astropy/io/ascii/tests/test_read.py::test_validate_read_kwargs`
- `astropy/io/ascii/tests/test_read.py::test_daophot_indef`
- `astropy/io/ascii/tests/test_read.py::test_daophot_types`
- `astropy/io/ascii/tests/test_read.py::test_daophot_header_keywords`
- `astropy/io/ascii/tests/test_read.py::test_daophot_multiple_aperture`
- `astropy/io/ascii/tests/test_read.py::test_daophot_multiple_aperture2`
- `astropy/io/ascii/tests/test_read.py::test_empty_table_no_header[True]`
- `astropy/io/ascii/tests/test_read.py::test_empty_table_no_header[False]`
- `astropy/io/ascii/tests/test_read.py::test_empty_table_no_header[force]`
- `astropy/io/ascii/tests/test_read.py::test_wrong_quote[True]`
- `astropy/io/ascii/tests/test_read.py::test_wrong_quote[False]`
- `astropy/io/ascii/tests/test_read.py::test_wrong_quote[force]`
- `astropy/io/ascii/tests/test_read.py::test_extra_data_col[True]`
- `astropy/io/ascii/tests/test_read.py::test_extra_data_col[False]`
- `astropy/io/ascii/tests/test_read.py::test_extra_data_col[force]`
- `astropy/io/ascii/tests/test_read.py::test_extra_data_col2[True]`
- `astropy/io/ascii/tests/test_read.py::test_extra_data_col2[False]`
- `astropy/io/ascii/tests/test_read.py::test_extra_data_col2[force]`
- `astropy/io/ascii/tests/test_read.py::test_missing_file`
- `astropy/io/ascii/tests/test_read.py::test_set_names[True]`
- `astropy/io/ascii/tests/test_read.py::test_set_names[False]`
- `astropy/io/ascii/tests/test_read.py::test_set_names[force]`
- `astropy/io/ascii/tests/test_read.py::test_set_include_names[True]`
- `astropy/io/ascii/tests/test_read.py::test_set_include_names[False]`
- `astropy/io/ascii/tests/test_read.py::test_set_include_names[force]`
- `astropy/io/ascii/tests/test_read.py::test_set_exclude_names[True]`
- `astropy/io/ascii/tests/test_read.py::test_set_exclude_names[False]`
- `astropy/io/ascii/tests/test_read.py::test_set_exclude_names[force]`
- `astropy/io/ascii/tests/test_read.py::test_include_names_daophot`
- `astropy/io/ascii/tests/test_read.py::test_exclude_names_daophot`
- `astropy/io/ascii/tests/test_read.py::test_custom_process_lines`
- `astropy/io/ascii/tests/test_read.py::test_custom_process_line`
- `astropy/io/ascii/tests/test_read.py::test_custom_splitters`
- `astropy/io/ascii/tests/test_read.py::test_start_end`
- `astropy/io/ascii/tests/test_read.py::test_set_converters`
- `astropy/io/ascii/tests/test_read.py::test_from_string[True]`
- `astropy/io/ascii/tests/test_read.py::test_from_string[False]`
- `astropy/io/ascii/tests/test_read.py::test_from_string[force]`
- `astropy/io/ascii/tests/test_read.py::test_from_filelike[True]`
- `astropy/io/ascii/tests/test_read.py::test_from_filelike[False]`
- `astropy/io/ascii/tests/test_read.py::test_from_filelike[force]`
- `astropy/io/ascii/tests/test_read.py::test_from_lines[True]`
- `astropy/io/ascii/tests/test_read.py::test_from_lines[False]`
- `astropy/io/ascii/tests/test_read.py::test_from_lines[force]`
- `astropy/io/ascii/tests/test_read.py::test_comment_lines`
- `astropy/io/ascii/tests/test_read.py::test_fill_values[True]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values[False]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values[force]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_col[True]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_col[False]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_col[force]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_include_names[True]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_include_names[False]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_include_names[force]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_exclude_names[True]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_exclude_names[False]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_exclude_names[force]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_list[True]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_list[False]`
- `astropy/io/ascii/tests/test_read.py::test_fill_values_list[force]`
- `astropy/io/ascii/tests/test_read.py::test_masking_Cds_Mrt`
- `astropy/io/ascii/tests/test_read.py::test_null_Ipac`
- `astropy/io/ascii/tests/test_read.py::test_Ipac_meta`
- `astropy/io/ascii/tests/test_read.py::test_set_guess_kwarg`
- `astropy/io/ascii/tests/test_read.py::test_read_rdb_wrong_type[True]`
- `astropy/io/ascii/tests/test_read.py::test_read_rdb_wrong_type[False]`
- `astropy/io/ascii/tests/test_read.py::test_read_rdb_wrong_type[force]`
- `astropy/io/ascii/tests/test_read.py::test_default_missing[True]`
- `astropy/io/ascii/tests/test_read.py::test_default_missing[False]`
- `astropy/io/ascii/tests/test_read.py::test_default_missing[force]`
- `astropy/io/ascii/tests/test_read.py::test_header_start_exception`
- `astropy/io/ascii/tests/test_read.py::test_csv_table_read`
- `astropy/io/ascii/tests/test_read.py::test_overlapping_names[True]`
- `astropy/io/ascii/tests/test_read.py::test_overlapping_names[False]`
- `astropy/io/ascii/tests/test_read.py::test_overlapping_names[force]`
- `astropy/io/ascii/tests/test_read.py::test_sextractor_units`
- `astropy/io/ascii/tests/test_read.py::test_sextractor_last_column_array`
- `astropy/io/ascii/tests/test_read.py::test_list_with_newlines`
- `astropy/io/ascii/tests/test_read.py::test_commented_csv`
- `astropy/io/ascii/tests/test_read.py::test_meta_comments`
- `astropy/io/ascii/tests/test_read.py::test_guess_fail`
- `astropy/io/ascii/tests/test_read.py::test_guessing_file_object`
- `astropy/io/ascii/tests/test_read.py::test_pformat_roundtrip`
- `astropy/io/ascii/tests/test_read.py::test_ipac_abbrev`
- `astropy/io/ascii/tests/test_read.py::test_almost_but_not_quite_daophot`
- `astropy/io/ascii/tests/test_read.py::test_commented_header_comments[False]`
- `astropy/io/ascii/tests/test_read.py::test_commented_header_comments[force]`
- `astropy/io/ascii/tests/test_read.py::test_probably_html`
- `astropy/io/ascii/tests/test_read.py::test_data_header_start[True]`
- `astropy/io/ascii/tests/test_read.py::test_data_header_start[False]`
- `astropy/io/ascii/tests/test_read.py::test_data_header_start[force]`
- `astropy/io/ascii/tests/test_read.py::test_table_with_no_newline`
- `astropy/io/ascii/tests/test_read.py::test_path_object`
- `astropy/io/ascii/tests/test_read.py::test_column_conversion_error`
- `astropy/io/ascii/tests/test_read.py::test_no_units_for_char_columns`
- `astropy/io/ascii/tests/test_read.py::test_initial_column_fill_values`
- `astropy/io/ascii/tests/test_read.py::test_latex_no_trailing_backslash`
- `astropy/io/ascii/tests/test_read.py::test_read_with_encoding[utf8]`
- `astropy/io/ascii/tests/test_read.py::test_read_with_encoding[latin1]`
- `astropy/io/ascii/tests/test_read.py::test_read_with_encoding[cp1252]`
- `astropy/io/ascii/tests/test_read.py::test_unsupported_read_with_encoding`
- `astropy/io/ascii/tests/test_read.py::test_read_chunks_input_types`
- `astropy/io/ascii/tests/test_read.py::test_read_chunks_formats[True]`
- `astropy/io/ascii/tests/test_read.py::test_read_chunks_formats[False]`
- `astropy/io/ascii/tests/test_read.py::test_read_chunks_chunk_size_too_small`
- `astropy/io/ascii/tests/test_read.py::test_read_chunks_table_changes`
- `astropy/io/ascii/tests/test_read.py::test_read_non_ascii`
- `astropy/io/ascii/tests/test_read.py::test_kwargs_dict_guess[True]`
- `astropy/io/ascii/tests/test_read.py::test_kwargs_dict_guess[False]`
- `astropy/io/ascii/tests/test_read.py::test_kwargs_dict_guess[force]`
- `astropy/io/ascii/tests/test_read.py::test_deduplicate_names_basic[False-False]`
- `astropy/io/ascii/tests/test_read.py::test_deduplicate_names_basic[False-True]`
- `astropy/io/ascii/tests/test_read.py::test_deduplicate_names_basic[force-False]`
- `astropy/io/ascii/tests/test_read.py::test_deduplicate_names_basic[force-True]`
- `astropy/io/ascii/tests/test_read.py::test_include_names_rdb_fast`
- `astropy/io/ascii/tests/test_read.py::test_deduplicate_names_with_types[False]`
- `astropy/io/ascii/tests/test_read.py::test_deduplicate_names_with_types[force]`
- `astropy/io/ascii/tests/test_read.py::test_set_invalid_names[False-False]`
- `astropy/io/ascii/tests/test_read.py::test_set_invalid_names[False-True]`
- `astropy/io/ascii/tests/test_read.py::test_set_invalid_names[force-False]`
- `astropy/io/ascii/tests/test_read.py::test_set_invalid_names[force-True]`
- `astropy/io/ascii/tests/test_read.py::test_read_masked_bool`
- `astropy/io/ascii/tests/test_read.py::test_read_converters_wildcard`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
