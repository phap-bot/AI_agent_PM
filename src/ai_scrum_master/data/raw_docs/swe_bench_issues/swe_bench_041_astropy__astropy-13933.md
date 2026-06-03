# SWE-bench Issue: astropy__astropy-13933

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13933
- Base Commit: 5aa2d0beca53988e054d496c6dcfa2199a405fb8
- Environment Setup Commit: 5f74eacbcc7fff707a44d8eb58adaa514cb7dcb5
- Created At: 2022-10-28T21:49:47Z
- Version: 5.1

## Issue Title
Unpickled Angle.to_string fails

## Problem Statement
Unpickled Angle.to_string fails
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
Pickling and unpickling an Angle object causes the to_string function to fail claiming hourangle and degree units cannot be represented in sexagesimal notation.

### Steps to Reproduce
<!-- Ideally a code example could be provided so we can run it ourselves. -->
<!-- If you are pasting code, use triple backticks (```) around
your code snippet. -->
<!-- If necessary, sanitize your screen output to be pasted so you do not
reveal secrets like tokens and passwords. -->

```python
import astropy.coordinates
import pickle
ang = astropy.coordinates.Angle(0.25 * astropy.units.hourangle)
pang = pickle.loads(pickle.dumps(ang))
ang.to_string()
# Works: 0h15m00s
pang.to_string()
# Fails: ValueError: 'hourangle' can not be represented in sexagesimal notation
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
macOS-10.15.7-x86_64-i386-64bit
Python 3.10.6 | packaged by conda-forge | (main, Aug 22 2022, 20:43:44) [Clang 13.0.1 ]
Numpy 1.23.4
pyerfa 2.0.0.1
astropy 5.1
Scipy 1.9.3
Matplotlib 3.6.1

## Issue Discussion Hints
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

GitHub issues in the Astropy repository are used to track bug reports and feature requests; If your issue poses a question about how to use Astropy, please instead raise your question in the [Astropy Discourse user forum](https://community.openastronomy.org/c/astropy/8) and close this issue.

If you feel that this issue has not been responded to in a timely manner, please send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
I can reproduce this also with 5.2.dev . @adrn , I vaguely remember you did some work on pickling such things?
Bit of troubleshooting: if one does `%debug` at that point, then `unit is u.hourangle` will return `False`, and thus one misses the branch that should typeset this: https://github.com/astropy/astropy/blob/0c37a7141c6c21c52ce054f2d895f6f6eacbf24b/astropy/coordinates/angles.py#L315-L329

The easy fix would be to replace `is` with `==`, but in princple I think pickling and unpickling the unit should have ensured the unit remains a singleton.
It seems like currently with pickle we guarantee only `IrreducibleUnits`?
```
In [5]: pickle.loads(pickle.dumps(u.hourangle)) is u.hourangle
Out[5]: False

In [6]: pickle.loads(pickle.dumps(u.rad)) is u.rad
Out[6]: True

In [7]: pickle.loads(pickle.dumps(u.deg)) is u.deg
Out[7]: False
```

EDIT: indeed only `IrreducibleUnits` have an `__reduce__` method that guarantees the units are the same:
https://github.com/astropy/astropy/blob/0c37a7141c6c21c52ce054f2d895f6f6eacbf24b/astropy/units/core.py#L1854-L1864
OK, I think `==` is correct. Will have a fix shortly.

## Failing Tests That Should Pass
- `astropy/coordinates/tests/test_angles.py::test_create_angles`
- `astropy/coordinates/tests/test_angles.py::test_angle_formatting`
- `astropy/coordinates/tests/test_angles.py::test_angle_pickle_to_string`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_decimal`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_decimal_formats`

## Existing Passing Tests To Preserve
- `astropy/coordinates/tests/test_angles.py::test_angle_from_view`
- `astropy/coordinates/tests/test_angles.py::test_angle_ops`
- `astropy/coordinates/tests/test_angles.py::test_angle_methods`
- `astropy/coordinates/tests/test_angles.py::test_angle_convert`
- `astropy/coordinates/tests/test_angles.py::test_to_string_vector`
- `astropy/coordinates/tests/test_angles.py::test_angle_format_roundtripping`
- `astropy/coordinates/tests/test_angles.py::test_radec`
- `astropy/coordinates/tests/test_angles.py::test_negative_zero_dms`
- `astropy/coordinates/tests/test_angles.py::test_negative_zero_dm`
- `astropy/coordinates/tests/test_angles.py::test_negative_zero_hms`
- `astropy/coordinates/tests/test_angles.py::test_negative_zero_hm`
- `astropy/coordinates/tests/test_angles.py::test_negative_sixty_hm`
- `astropy/coordinates/tests/test_angles.py::test_plus_sixty_hm`
- `astropy/coordinates/tests/test_angles.py::test_negative_fifty_nine_sixty_dms`
- `astropy/coordinates/tests/test_angles.py::test_plus_fifty_nine_sixty_dms`
- `astropy/coordinates/tests/test_angles.py::test_negative_sixty_dms`
- `astropy/coordinates/tests/test_angles.py::test_plus_sixty_dms`
- `astropy/coordinates/tests/test_angles.py::test_angle_to_is_angle`
- `astropy/coordinates/tests/test_angles.py::test_angle_to_quantity`
- `astropy/coordinates/tests/test_angles.py::test_quantity_to_angle`
- `astropy/coordinates/tests/test_angles.py::test_angle_string`
- `astropy/coordinates/tests/test_angles.py::test_angle_repr`
- `astropy/coordinates/tests/test_angles.py::test_large_angle_representation`
- `astropy/coordinates/tests/test_angles.py::test_wrap_at_inplace`
- `astropy/coordinates/tests/test_angles.py::test_latitude`
- `astropy/coordinates/tests/test_angles.py::test_longitude`
- `astropy/coordinates/tests/test_angles.py::test_wrap_at`
- `astropy/coordinates/tests/test_angles.py::test_is_within_bounds`
- `astropy/coordinates/tests/test_angles.py::test_angle_mismatched_unit`
- `astropy/coordinates/tests/test_angles.py::test_regression_formatting_negative`
- `astropy/coordinates/tests/test_angles.py::test_regression_formatting_default_precision`
- `astropy/coordinates/tests/test_angles.py::test_empty_sep`
- `astropy/coordinates/tests/test_angles.py::test_create_tuple`
- `astropy/coordinates/tests/test_angles.py::test_list_of_quantities`
- `astropy/coordinates/tests/test_angles.py::test_multiply_divide`
- `astropy/coordinates/tests/test_angles.py::test_mixed_string_and_quantity`
- `astropy/coordinates/tests/test_angles.py::test_array_angle_tostring`
- `astropy/coordinates/tests/test_angles.py::test_wrap_at_without_new`
- `astropy/coordinates/tests/test_angles.py::test__str__`
- `astropy/coordinates/tests/test_angles.py::test_repr_latex`
- `astropy/coordinates/tests/test_angles.py::test_angle_with_cds_units_enabled`
- `astropy/coordinates/tests/test_angles.py::test_longitude_nan`
- `astropy/coordinates/tests/test_angles.py::test_latitude_nan`
- `astropy/coordinates/tests/test_angles.py::test_angle_wrap_at_nan`
- `astropy/coordinates/tests/test_angles.py::test_angle_multithreading`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input0-nan-nan`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input1-[nan`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input2-[6d00m00s`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input3-[nan`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input4-nan-nan`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input5-[nan`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input6-[6h00m00s`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input7-[nan`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input8-nan-nan`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input9-[nan`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input10-[1.5rad`
- `astropy/coordinates/tests/test_angles.py::test_str_repr_angles_nan[input11-[nan`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[1.5707963267948966-1.5707963267948966-None-float64--1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[1.5707963267948966-1.5707963267948966-None-float64-1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[1.5707963267948966-1.5707963267948966-float64-float64--1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[1.5707963267948966-1.5707963267948966-float64-float64-1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[value2-expected_value2-None-float32--1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[value2-expected_value2-None-float32-1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[value3-expected_value3-float32-float32--1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[value3-expected_value3-float32-float32-1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_out_of_limits[1.5708277427214323-float32]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_out_of_limits[value1-float32]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_out_of_limits[1.5708277427214323-float64]`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_precision`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_formats`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_fields`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_padding`
- `astropy/coordinates/tests/test_formatting.py::test_sexagesimal_rounding_up`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_scalar`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_radian_with_precision`
- `astropy/coordinates/tests/test_formatting.py::test_sexagesimal_round_down`
- `astropy/coordinates/tests/test_formatting.py::test_to_string_fields_colon`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
