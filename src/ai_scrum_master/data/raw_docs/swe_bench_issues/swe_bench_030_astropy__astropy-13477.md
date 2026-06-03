# SWE-bench Issue: astropy__astropy-13477

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13477
- Base Commit: c40b75720a64186b57ad1de94ad7f21fa7728880
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-07-22T07:51:19Z
- Version: 5.0

## Issue Title
Comparing Frame with data and SkyCoord with same data raises exception

## Problem Statement
Comparing Frame with data and SkyCoord with same data raises exception
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

`SkyCoord` instances and `Frame` instances with data are somewhat used interchangebly and I am still not sure after all this time spending with astropy what is preferable when...

So it's  a bit surprising to me, that comparing a frame with data to a `SkyCoord` instance with exactly the same data raises an exception:

```

### Expected behavior
<!-- What did you expect to happen. -->
Compare to true / false depending on data.

### Actual behavior
Exception


### Steps to Reproduce


```python
In [1]: from astropy.coordinates import SkyCoord, ICRS

In [2]: frame = ICRS("0d", "0d")

In [3]: coord = SkyCoord(frame)

In [4]: frame == coord
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Input In [4], in <cell line: 1>()
----> 1 frame == coord

File ~/.local/lib/python3.10/site-packages/astropy/coordinates/baseframe.py:1657, in BaseCoordinateFrame.__eq__(self, value)
   1651 def __eq__(self, value):
   1652     """Equality operator for frame.
   1653 
   1654     This implements strict equality and requires that the frames are
   1655     equivalent and that the representation data are exactly equal.
   1656     """
-> 1657     is_equiv = self.is_equivalent_frame(value)
   1659     if self._data is None and value._data is None:
   1660         # For Frame with no data, == compare is same as is_equivalent_frame()
   1661         return is_equiv

File ~/.local/lib/python3.10/site-packages/astropy/coordinates/baseframe.py:1360, in BaseCoordinateFrame.is_equivalent_frame(self, other)
   1358     return True
   1359 elif not isinstance(other, BaseCoordinateFrame):
-> 1360     raise TypeError("Tried to do is_equivalent_frame on something that "
   1361                     "isn't a frame")
   1362 else:
   1363     return False

TypeError: Tried to do is_equivalent_frame on something that isn't a frame

```

Comparing Frame with data and SkyCoord with same data raises exception
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

`SkyCoord` instances and `Frame` instances with data are somewhat used interchangebly and I am still not sure after all this time spending with astropy what is preferable when...

So it's  a bit surprising to me, that comparing a frame with data to a `SkyCoord` instance with exactly the same data raises an exception:

```

### Expected behavior
<!-- What did you expect to happen. -->
Compare to true / false depending on data.

### Actual behavior
Exception


### Steps to Reproduce


```python
In [1]: from astropy.coordinates import SkyCoord, ICRS

In [2]: frame = ICRS("0d", "0d")

In [3]: coord = SkyCoord(frame)

In [4]: frame == coord
---------------------------------------------------------------------------
TypeError                                 Traceback (most recent call last)
Input In [4], in <cell line: 1>()
----> 1 frame == coord

File ~/.local/lib/python3.10/site-packages/astropy/coordinates/baseframe.py:1657, in BaseCoordinateFrame.__eq__(self, value)
   1651 def __eq__(self, value):
   1652     """Equality operator for frame.
   1653 
   1654     This implements strict equality and requires that the frames are
   1655     equivalent and that the representation data are exactly equal.
   1656     """
-> 1657     is_equiv = self.is_equivalent_frame(value)
   1659     if self._data is None and value._data is None:
   1660         # For Frame with no data, == compare is same as is_equivalent_frame()
   1661         return is_equiv

File ~/.local/lib/python3.10/site-packages/astropy/coordinates/baseframe.py:1360, in BaseCoordinateFrame.is_equivalent_frame(self, other)
   1358     return True
   1359 elif not isinstance(other, BaseCoordinateFrame):
-> 1360     raise TypeError("Tried to do is_equivalent_frame on something that "
   1361                     "isn't a frame")
   1362 else:
   1363     return False

TypeError: Tried to do is_equivalent_frame on something that isn't a frame

```

## Issue Discussion Hints
No issue discussion hints provided.

## Failing Tests That Should Pass
- `astropy/coordinates/tests/test_frames.py::test_frame_coord_comparison`

## Existing Passing Tests To Preserve
- `astropy/coordinates/tests/test_frames.py::test_frame_attribute_descriptor`
- `astropy/coordinates/tests/test_frames.py::test_frame_subclass_attribute_descriptor`
- `astropy/coordinates/tests/test_frames.py::test_frame_multiple_inheritance_attribute_descriptor`
- `astropy/coordinates/tests/test_frames.py::test_differentialattribute`
- `astropy/coordinates/tests/test_frames.py::test_create_data_frames`
- `astropy/coordinates/tests/test_frames.py::test_create_orderered_data`
- `astropy/coordinates/tests/test_frames.py::test_create_nodata_frames`
- `astropy/coordinates/tests/test_frames.py::test_frame_repr`
- `astropy/coordinates/tests/test_frames.py::test_frame_repr_vels`
- `astropy/coordinates/tests/test_frames.py::test_converting_units`
- `astropy/coordinates/tests/test_frames.py::test_representation_info`
- `astropy/coordinates/tests/test_frames.py::test_realizing`
- `astropy/coordinates/tests/test_frames.py::test_replicating`
- `astropy/coordinates/tests/test_frames.py::test_getitem`
- `astropy/coordinates/tests/test_frames.py::test_transform`
- `astropy/coordinates/tests/test_frames.py::test_transform_to_nonscalar_nodata_frame`
- `astropy/coordinates/tests/test_frames.py::test_setitem_no_velocity`
- `astropy/coordinates/tests/test_frames.py::test_setitem_velocities`
- `astropy/coordinates/tests/test_frames.py::test_setitem_exceptions`
- `astropy/coordinates/tests/test_frames.py::test_sep`
- `astropy/coordinates/tests/test_frames.py::test_time_inputs`
- `astropy/coordinates/tests/test_frames.py::test_is_frame_attr_default`
- `astropy/coordinates/tests/test_frames.py::test_altaz_attributes`
- `astropy/coordinates/tests/test_frames.py::test_hadec_attributes`
- `astropy/coordinates/tests/test_frames.py::test_representation`
- `astropy/coordinates/tests/test_frames.py::test_represent_as`
- `astropy/coordinates/tests/test_frames.py::test_shorthand_representations`
- `astropy/coordinates/tests/test_frames.py::test_equal`
- `astropy/coordinates/tests/test_frames.py::test_equal_exceptions`
- `astropy/coordinates/tests/test_frames.py::test_dynamic_attrs`
- `astropy/coordinates/tests/test_frames.py::test_nodata_error`
- `astropy/coordinates/tests/test_frames.py::test_len0_data`
- `astropy/coordinates/tests/test_frames.py::test_quantity_attributes`
- `astropy/coordinates/tests/test_frames.py::test_quantity_attribute_default`
- `astropy/coordinates/tests/test_frames.py::test_eloc_attributes`
- `astropy/coordinates/tests/test_frames.py::test_equivalent_frames`
- `astropy/coordinates/tests/test_frames.py::test_equivalent_frame_coordinateattribute`
- `astropy/coordinates/tests/test_frames.py::test_equivalent_frame_locationattribute`
- `astropy/coordinates/tests/test_frames.py::test_representation_subclass`
- `astropy/coordinates/tests/test_frames.py::test_getitem_representation`
- `astropy/coordinates/tests/test_frames.py::test_component_error_useful`
- `astropy/coordinates/tests/test_frames.py::test_cache_clear`
- `astropy/coordinates/tests/test_frames.py::test_inplace_array`
- `astropy/coordinates/tests/test_frames.py::test_inplace_change`
- `astropy/coordinates/tests/test_frames.py::test_representation_with_multiple_differentials`
- `astropy/coordinates/tests/test_frames.py::test_missing_component_error_names`
- `astropy/coordinates/tests/test_frames.py::test_non_spherical_representation_unit_creation`
- `astropy/coordinates/tests/test_frames.py::test_attribute_repr`
- `astropy/coordinates/tests/test_frames.py::test_component_names_repr`
- `astropy/coordinates/tests/test_frames.py::test_galactocentric_defaults`
- `astropy/coordinates/tests/test_frames.py::test_galactocentric_references`
- `astropy/coordinates/tests/test_frames.py::test_coordinateattribute_transformation`
- `astropy/coordinates/tests/test_frames.py::test_realize_frame_accepts_kwargs`
- `astropy/coordinates/tests/test_frames.py::test_nameless_frame_subclass`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
