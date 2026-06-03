# SWE-bench Issue: astropy__astropy-13803

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13803
- Base Commit: 192be538570db75f1f3bf5abe0c7631750e6addc
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-10-06T12:48:27Z
- Version: 5.0

## Issue Title
float32 representation of pi/2 is rejected by `Latitude`

## Problem Statement
float32 representation of pi/2 is rejected by `Latitude`
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

The closest float32 value to pi/2 is by accident slightly larger than pi/2:

```
In [5]: np.pi/2
Out[5]: 1.5707963267948966

In [6]: np.float32(np.pi/2)
Out[6]: 1.5707964
```

Astropy checks using float64 precision, rejecting "valid" alt values (e.g. float32 values read from files):

```

In [1]: from astropy.coordinates import Latitude

In [2]: import numpy as np

In [3]: lat = np.float32(np.pi/2)

In [4]: Latitude(lat, 'rad')
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
Cell In [4], line 1
----> 1 Latitude(lat, 'rad')

File ~/.local/lib/python3.10/site-packages/astropy/coordinates/angles.py:564, in Latitude.__new__(cls, angle, unit, **kwargs)
    562     raise TypeError("A Latitude angle cannot be created from a Longitude angle")
    563 self = super().__new__(cls, angle, unit=unit, **kwargs)
--> 564 self._validate_angles()
    565 return self

File ~/.local/lib/python3.10/site-packages/astropy/coordinates/angles.py:585, in Latitude._validate_angles(self, angles)
    582     invalid_angles = (np.any(angles.value < lower) or
    583                       np.any(angles.value > upper))
    584 if invalid_angles:
--> 585     raise ValueError('Latitude angle(s) must be within -90 deg <= angle <= 90 deg, '
    586                      'got {}'.format(angles.to(u.degree)))

ValueError: Latitude angle(s) must be within -90 deg <= angle <= 90 deg, got 90.00000250447816 deg
```

### Expected behavior

Be lenient? E.g. only make the comparison up to float 32 precision?

### Actual behavior
See error above

### Steps to Reproduce

See snippet above.

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
Linux-5.15.65-1-MANJARO-x86_64-with-glibc2.36
Python 3.10.7 (main, Sep  6 2022, 21:22:27) [GCC 12.2.0]
Numpy 1.23.3
pyerfa 2.0.0.1
astropy 5.0.1
Scipy 1.9.1
Matplotlib 3.5.2
```

## Issue Discussion Hints
> Be lenient? E.g. only make the comparison up to float 32 precision?

Instead, we could make the comparison based on the precision of the ``dtype``, using something like https://numpy.org/doc/stable/reference/generated/numpy.finfo.html?highlight=finfo#numpy.finfo
That's a funny one! I think @nstarman's suggestion would work: would just need to change the dtype of `limit` to `self.dtype` in `_validate_angles`.
That wouldn't solve the case where the value is read from a float32 into a float64, which can happen pretty fast due to the places where casting can happen. Better than nothing, but...
Do we want to simply let it pass with that value, or rather "round" the input value down to the float64 representation of `pi/2`? Just wondering what may happen with larger values in any calculations down the line; probably nothing really terrible (like ending up with inverse Longitude), but...
This is what I did to fix it on our end:
https://github.com/cta-observatory/ctapipe/pull/2077/files#diff-d2022785b8c35b2f43d3b9d43c3721efaa9339d98dbff39c864172f1ba2f4f6f
```python
_half_pi = 0.5 * np.pi
_half_pi_maxval = (1 + 1e-6) * _half_pi




def _clip_altitude_if_close(altitude):
    """
    Round absolute values slightly larger than pi/2 in float64 to pi/2

    These can come from simtel_array because float32(pi/2) > float64(pi/2)
    and simtel using float32.

    Astropy complains about these values, so we fix them here.
    """
    if altitude > _half_pi and altitude < _half_pi_maxval:
        return _half_pi


    if altitude < -_half_pi and altitude > -_half_pi_maxval:
        return -_half_pi


    return altitude
```

Would that be an acceptable solution also here?
Does this keep the numpy dtype of the input?
No, the point is that this casts to float64.
So ``Latitude(pi/2, unit=u.deg, dtype=float32)``  can become a float64?
> Does this keep the numpy dtype of the input?

If `limit` is cast to `self.dtype` (is that identical to `self.angle.dtype`?) as per your suggestion above, it should.
But that modification should already catch the cases of `angle` still passed as float32, since both are compared at the same resolution. I'd vote to do this and only implement the more lenient comparison (for float32 that had already been upcast to float64)  as a fallback, i.e. if still `invalid_angles`, set something like
`_half_pi_maxval = (0.5 + np.finfo(np.float32).eps)) * np.pi` and do a second comparison to that, if that passes, set to  `limit * np.sign(self.angle)`. Have to remember that `self.angle` is an array in general...
> So `Latitude(pi/2, unit=u.deg, dtype=float32)` can become a float64?

`Latitude(pi/2, unit=u.rad, dtype=float32)` would in that approach, as it currently raises the `ValueError`.
I'll open a PR with unit test cases and then we can decide about the wanted behaviour for each of them

## Failing Tests That Should Pass
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[value2-expected_value2-None-float32--1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[value2-expected_value2-None-float32-1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[value3-expected_value3-float32-float32--1]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_limits[value3-expected_value3-float32-float32-1]`

## Existing Passing Tests To Preserve
- `astropy/coordinates/tests/test_angles.py::test_create_angles`
- `astropy/coordinates/tests/test_angles.py::test_angle_from_view`
- `astropy/coordinates/tests/test_angles.py::test_angle_ops`
- `astropy/coordinates/tests/test_angles.py::test_angle_methods`
- `astropy/coordinates/tests/test_angles.py::test_angle_convert`
- `astropy/coordinates/tests/test_angles.py::test_angle_formatting`
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
- `astropy/coordinates/tests/test_angles.py::test_latitude_out_of_limits[1.5708277427214323-float32]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_out_of_limits[value1-float32]`
- `astropy/coordinates/tests/test_angles.py::test_latitude_out_of_limits[1.5708277427214323-float64]`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
