# SWE-bench Issue: astropy__astropy-12962

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-12962
- Base Commit: d21dc232d8626b3aff24784628a6e85d177784ae
- Environment Setup Commit: 298ccb478e6bf092953bca67a3d29dc6c35f6752
- Created At: 2022-03-17T01:25:15Z
- Version: 4.3

## Issue Title
Convert CCDData to ImageHDU

## Problem Statement
Convert CCDData to ImageHDU
### Description
As far as I can tell, currently there's no way to directly convert a `CCDData` object to an `ImageHDU` object. If we write it to a file using `CCDData.write()` it will always create a file where the first HDU is a `PrimaryHDU` that contains the `CCDData.data`, followed by optionally some `ImageHDU`s that contain mask or uncertainty. If we instead use `CCDData.to_hdu()`, it will return an `HDUList` equivalent to the file it writes with `CCDData.write()`, that is, the `CCDData.data` is stored in the first element of the `HDUList`, which is always a `PrimaryHDU`.

This is somewhat unexpected given that you can already do it the other way around (that is, convert a `ImageHDU` object to a `CCDData` object):

```python
fits.HDUList([
    fits.PrimaryHDU(),
    fits.ImageHDU(data=np.ones((2, 2))),
    fits.ImageHDU(data=np.ones((5, 5)), header=fits.Header({'BUNIT': 'm'})),
]).writeto('test.fits')  # create example file

ccd_image = CCDData.read('test.fits', hdu=2)  # you can successfully read the 5x5 ImageHDU
```
The problem is that if we then want to use this `ccd_image` as an extension to another FITS file, there's no obvious way to get an `ImageHDU` which would allow us to do that.  As far as I can tell, there's also no trivial way to convert a `PrimaryHDU` to a `ImageHDU`. We could manually create a new `ImageHDU` by copying the data from the `PrimaryHDU`, as well as its relevant cards and so on... but this seems unnecessarily complicated.

I propose the following interfaces:

```python
# Option A: add a new parameter to CCDData.to_hdu() for this functionality
hdus = ccd_image.to_hdu(as_image_hdu=True)  # This returns a HDUList where the first element is an ImageHDU instead of a PrimaryHDU

# Option B: create a new convenience function
hdu = fits.ccddata_to_image_hdu(ccd_image) # This returns a single ImageHDU

# Option C: allowing the user to append the image to an existing FITS file
ccd_image.write('test.fits', append=True) # appends original ImageHDU to existing file
```



### Additional context
This seems somewhat similar to the situation with `Table` and `BinTableHDU`. In that case, we can also specify an `hdu` parameter when reading:

```python
fits.BinTableHDU.from_columns([
    fits.Column(name='test', format='J', array=(1, 2))
]).writeto('table.fits')  # creates a new file with a PrimaryHDU followed by this BinTableHDU
t = Table.read('table.fits', hdu=1) # reads the BinTableHDU as a Table
```

From here we can use:

```python
t.write('new_table.fits')  #  creates a new file with a PrimaryHDU followed by the original BinTableHDU
t.write('existing_table.fits', append=True)  # appends original BinTableHDU to existing file
hdu = fits.table_to_hdu(t)  # returns original BinTableHDU
```

## Issue Discussion Hints
According to this line, that interface already exists:

https://github.com/astropy/astropy/blob/40ba5e4c609d2760152898b8d92a146e3e38c744/astropy/nddata/ccddata.py#L709

https://docs.astropy.org/en/latest/api/astropy.nddata.CCDData.html#astropy.nddata.CCDData.to_hdu
Maybe it just needs some tune up to write the HDU format that you want instead of a whole new interface. (Your Option A)
Yes, I know that `ccd_data.to_hdu()` already exists. My problem with it is that it returns the data as an `HDUList` with a `PrimaryHDU`, not as an `ImageHDU`. This is why I proposed adding an optional parameter to it (option A). Option B and C are basically inspired on the existing interfaces for converting `Tables` back to `BinTableHDU`s, which also seem good options to me. Any of these 3 options would be really useful to me, but I don't necessarily think we need all of them at the same time.
Yes, I replied before coffee kicked in, sorry. 😅 

My vote is Option A but we should wait to hear from @mwcraig .
Option A sounds very useful to me too.
I agree that Option A sounds good -- thanks for the detailed report and thoughtful suggestions, @kYwzor. Are you interested in writing a pull request to implement this? I would have some time this week to help you out if you are interested.

If not, I should be able to open a PR myself this week. 
I've never contributed to a big package like this, but I can give it a try.

There seems to be consensus for `ccd_data.to_hdu(as_image_hdu=True)`, but I'm not sure that we're all in agreement regarding what exactly this should return. I see essentially three options:

1. Return an `HDUList` where the first element is an empty `PrimaryHDU`, followed by an `ImageHDU` which contains data/headers coming from the `CCDData` object, possibly followed by `ImageHDU`s containing mask and/or uncertainty (if they are present in the `CCDData` object).
2. Same as option 1, but without the `PrimaryHDU` (the first element is an `ImageHDU`).
3. Return just an `ImageHDU` (not an `HDUList`), even if mask or uncertainty exist.

Option 1 is probably more consistent with the usual behavior when returning `HDUList`s (I think when Astropy builds an `HDUList` for the user, it's usually returned in a state that can be directly written to a file). The argument for option 2 is that if you're using `as_image_hdu` you probably don't intend on directly writing the returning `HDUList` to a file (otherwise you'd likely just use the default parameters), so adding a PrimaryHDU may be unnecessary bloat. Although I'm not a fan of option 3, it might be what someone expects from a parameter named "as_image_hdu"... but it would be pretty weird to completely drop mask/uncertainty and to return a different type of object, so maybe we could have a better name for this parameter.

I think option 1 is probably the best option because if you don't want the PrimaryHDU (option 2) you can easily do that with `hdus.pop(0)` and if you only want the ImageHDU (option 3) you can get it via `hdus[1]`, so it seems like it should fit everyone's needs.
> 1. Return an HDUList where the first element is an empty PrimaryHDU, followed by an ImageHDU which contains data/headers coming from the CCDData object, possibly followed by ImageHDUs containing mask and/or uncertainty (if they are present in the CCDData object).
> 2. Same as option 1, but without the PrimaryHDU (the first element is an ImageHDU).
> 3. Return just an ImageHDU (not an HDUList), even if mask or uncertainty exist.

I lean towards 2 since the keyword indicates you want the HDU as an `ImageHDU` -- it might be even clearer if the keyword were named `as_image_hdu_only` or something like that. Let's wait to see what @pllim and @saimn have to say too. 

Contributing follows a fairly standard set of steps, [detailed at length here](https://docs.astropy.org/en/latest/development/workflow/development_workflow.html). Boiled down to essentials, it is: fork the repo in github, clone your fork to your computer, *make a new branch* and then make your changes. Include a test of the new feature -- in this case it could be a straightforward one that makes sure an `ImageHDU` is returned if the keyword is used. Commit your changes, push to your fork, then open a pull request.

If you run into questions along the way feel free to ask here or in the #nddata channel in the [astropy slack](https://astropy.slack.com/) workspace.

From an "outsider" perspective (in terms of `CCDData` usage), I would prefer a solution that is the closest to what `.write()` would have done, but returns the object instead of writing it to a file. You can name the keyword whatever that makes sense to you in that regard. I think that behavior is the least surprising one.

Of course, I don't use it a lot, so I can be overruled.
I also lean towards 2 since I think the use case would to construct manually the HDUList with possibly more than 1 CCDData object. Having the PrimaryHDU could also be useful, but maybe that should be a different option in `CCDData.write`.

## Failing Tests That Should Pass
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_writer_as_imagehdu`
- `astropy/nddata/tests/test_ccddata.py::test_to_hdu_as_imagehdu`

## Existing Passing Tests To Preserve
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_empty`
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_must_have_unit`
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_unit_cannot_be_set_to_none`
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_meta_header_conflict`
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_simple`
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_init_with_string_electron_unit`
- `astropy/nddata/tests/test_ccddata.py::test_initialize_from_FITS`
- `astropy/nddata/tests/test_ccddata.py::test_initialize_from_fits_with_unit_in_header`
- `astropy/nddata/tests/test_ccddata.py::test_initialize_from_fits_with_ADU_in_header`
- `astropy/nddata/tests/test_ccddata.py::test_initialize_from_fits_with_invalid_unit_in_header`
- `astropy/nddata/tests/test_ccddata.py::test_initialize_from_fits_with_technically_invalid_but_not_really`
- `astropy/nddata/tests/test_ccddata.py::test_initialize_from_fits_with_data_in_different_extension`
- `astropy/nddata/tests/test_ccddata.py::test_initialize_from_fits_with_extension`
- `astropy/nddata/tests/test_ccddata.py::test_write_unit_to_hdu`
- `astropy/nddata/tests/test_ccddata.py::test_initialize_from_FITS_bad_keyword_raises_error`
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_writer`
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_meta_is_case_sensitive`
- `astropy/nddata/tests/test_ccddata.py::test_ccddata_meta_is_not_fits_header`
- `astropy/nddata/tests/test_ccddata.py::test_fromMEF`
- `astropy/nddata/tests/test_ccddata.py::test_metafromheader`
- `astropy/nddata/tests/test_ccddata.py::test_metafromdict`
- `astropy/nddata/tests/test_ccddata.py::test_header2meta`
- `astropy/nddata/tests/test_ccddata.py::test_metafromstring_fail`
- `astropy/nddata/tests/test_ccddata.py::test_setting_bad_uncertainty_raises_error`
- `astropy/nddata/tests/test_ccddata.py::test_setting_uncertainty_with_array`
- `astropy/nddata/tests/test_ccddata.py::test_setting_uncertainty_wrong_shape_raises_error`
- `astropy/nddata/tests/test_ccddata.py::test_to_hdu`
- `astropy/nddata/tests/test_ccddata.py::test_copy`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[True-2.0-multiply-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[True-2.0-divide-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[True-operand1-multiply-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[True-operand1-divide-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[True-operand2-multiply-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[True-operand2-divide-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[False-2.0-multiply-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[False-2.0-divide-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[False-operand1-multiply-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[False-operand1-divide-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[False-operand2-multiply-True]`
- `astropy/nddata/tests/test_ccddata.py::test_mult_div_overload[False-operand2-divide-True]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[True-2.0-UnitsError-add-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[True-2.0-UnitsError-subtract-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[True-operand1-UnitsError-add-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[True-operand1-UnitsError-subtract-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[True-operand2-False-add-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[True-operand2-False-subtract-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[False-2.0-UnitsError-add-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[False-2.0-UnitsError-subtract-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[False-operand1-UnitsError-add-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[False-operand1-UnitsError-subtract-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[False-operand2-False-add-False]`
- `astropy/nddata/tests/test_ccddata.py::test_add_sub_overload[False-operand2-False-subtract-False]`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_overload_fails`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_no_wcs_compare`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_with_wcs_compare`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_with_wcs_compare_fail`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_overload_ccddata_operand`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_overload_differing_units`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_add_with_array`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_subtract_with_array`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_multiply_with_array`
- `astropy/nddata/tests/test_ccddata.py::test_arithmetic_divide_with_array`
- `astropy/nddata/tests/test_ccddata.py::test_history_preserved_if_metadata_is_fits_header`
- `astropy/nddata/tests/test_ccddata.py::test_infol_logged_if_unit_in_fits_header`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_attribute`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_keywords_removed_from_header`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_SIP_coefficient_keywords_removed`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_keyword_removal_for_wcs_test_files`
- `astropy/nddata/tests/test_ccddata.py::test_read_wcs_not_creatable`
- `astropy/nddata/tests/test_ccddata.py::test_header`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_arithmetic`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_arithmetic_ccd[multiply]`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_arithmetic_ccd[divide]`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_arithmetic_ccd[add]`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_arithmetic_ccd[subtract]`
- `astropy/nddata/tests/test_ccddata.py::test_wcs_sip_handling`
- `astropy/nddata/tests/test_ccddata.py::test_mask_arithmetic_ccd[multiply]`
- `astropy/nddata/tests/test_ccddata.py::test_mask_arithmetic_ccd[divide]`
- `astropy/nddata/tests/test_ccddata.py::test_mask_arithmetic_ccd[add]`
- `astropy/nddata/tests/test_ccddata.py::test_mask_arithmetic_ccd[subtract]`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_mask_default`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_uncertainty_default[StdDevUncertainty]`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_uncertainty_default[VarianceUncertainty]`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_uncertainty_default[InverseVariance]`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_uncertainty_different_uncertainty_key[StdDevUncertainty]`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_uncertainty_different_uncertainty_key[VarianceUncertainty]`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_uncertainty_different_uncertainty_key[InverseVariance]`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_not`
- `astropy/nddata/tests/test_ccddata.py::test_write_read_multiextensionfits_custom_ext_names`
- `astropy/nddata/tests/test_ccddata.py::test_read_old_style_multiextensionfits`
- `astropy/nddata/tests/test_ccddata.py::test_wcs`
- `astropy/nddata/tests/test_ccddata.py::test_recognized_fits_formats_for_read_write`
- `astropy/nddata/tests/test_ccddata.py::test_stddevuncertainty_compat_descriptor_no_parent`
- `astropy/nddata/tests/test_ccddata.py::test_stddevuncertainty_compat_descriptor_no_weakref`
- `astropy/nddata/tests/test_ccddata.py::test_read_returns_image`
- `astropy/nddata/tests/test_ccddata.py::test_sliced_ccdata_to_hdu`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
