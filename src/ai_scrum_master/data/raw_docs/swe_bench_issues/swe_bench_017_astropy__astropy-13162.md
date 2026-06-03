# SWE-bench Issue: astropy__astropy-13162

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13162
- Base Commit: 78c4ac119a182eee14cb3761e0dc9ea0e59b291f
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-04-22T18:22:32Z
- Version: 5.0

## Issue Title
Angle bug for (d, m, s) tuple input (deprecate dms_to_degrees)

## Problem Statement
Angle bug for (d, m, s) tuple input (deprecate dms_to_degrees)
`Angle` does not handle the sign correctly for a `(d, m, s)` tuple input if `d=0`:

```python
>>> from astropy.coordinates import Angle
>>> ang = Angle((-0, -42, -17), unit='deg')
>>> print(ang)
0d42m17s
>>> print(ang.dms)
dms_tuple(d=0.0, m=42.0, s=16.999999999999886)
>>> print(ang.signed_dms)
signed_dms_tuple(sign=1.0, d=0.0, m=42.0, s=16.999999999999886)
```

<!-- Provide a general description of the bug. -->

### Expected behavior

```python
>>> ang = Angle((-0, -42, -17), unit='deg')
>>> print(ang)
-0d42m17s
>>> print(ang.dms)
dms_tuple(d=-0.0, m=-42.0, s=-16.999999999999886)
>>> print(ang.signed_dms)
signed_dms_tuple(sign=-1.0, d=0.0, m=42.0, s=16.999999999999886)
```

fix for the issue #12239 (Angle bug for (d, m, s) tuple input (deprecate dms_to_degrees))
fix for the issue #12239 

Two solutions are proposed.
code for solution 1 is presented in this pull request.

## Issue Discussion Hints
Hi @larrybradley  and others,
I am recently working on this issue.
In the process..
I cannot find the definition of namedtuple()
I don't know yet whether it is a class or function.
Please help me here.
I came to know that the namedtuple is from python collections module.

## Failing Tests That Should Pass
- `astropy/coordinates/tests/test_angles.py::test_create_angles`
- `astropy/coordinates/tests/test_angles.py::test_radec`
- `astropy/coordinates/tests/test_angles.py::test_create_tuple`
- `astropy/coordinates/tests/test_arrays.py::test_hms`

## Existing Passing Tests To Preserve
- `astropy/coordinates/tests/test_angles.py::test_angle_from_view`
- `astropy/coordinates/tests/test_angles.py::test_angle_ops`
- `astropy/coordinates/tests/test_angles.py::test_angle_methods`
- `astropy/coordinates/tests/test_angles.py::test_angle_convert`
- `astropy/coordinates/tests/test_angles.py::test_angle_formatting`
- `astropy/coordinates/tests/test_angles.py::test_to_string_vector`
- `astropy/coordinates/tests/test_angles.py::test_angle_format_roundtripping`
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
- `astropy/coordinates/tests/test_arrays.py::test_dms`
- `astropy/coordinates/tests/test_arrays.py::test_array_coordinates_creation`
- `astropy/coordinates/tests/test_arrays.py::test_array_coordinates_distances`
- `astropy/coordinates/tests/test_arrays.py::test_array_precession`
- `astropy/coordinates/tests/test_arrays.py::test_array_indexing`
- `astropy/coordinates/tests/test_arrays.py::test_array_len`
- `astropy/coordinates/tests/test_arrays.py::test_array_eq`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
