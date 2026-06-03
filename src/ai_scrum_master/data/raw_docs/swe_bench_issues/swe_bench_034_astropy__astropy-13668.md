# SWE-bench Issue: astropy__astropy-13668

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13668
- Base Commit: 7ea140de86b788b44f64ea5eeacfbd78ffd85b69
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-09-14T19:12:10Z
- Version: 5.0

## Issue Title
wcslint crashes on valid WCS

## Problem Statement
wcslint crashes on valid WCS
`wcslint` calls an underlying function here:

https://github.com/astropy/astropy/blob/8c0581fc68ca1f970d7f4e6c9ca9f2b9567d7b4c/astropy/wcs/wcs.py#L3430

Looks like all it does is tries to create a `WCS` object with the header and report warnings, so the bug is either inside `WCS` or it is a matter of updating on how validator calls `WCS` in more complicated cases:

https://github.com/astropy/astropy/blob/8c0581fc68ca1f970d7f4e6c9ca9f2b9567d7b4c/astropy/wcs/wcs.py#L3530-L3534

# Examples

File: https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:HST/product/jbqf03gjq_flc.fits

```
$ fitsinfo jbqf03gjq_flc.fits
Filename: jbqf03gjq_flc.fits
No.    Name      Ver    Type      Cards   Dimensions   Format
  0  PRIMARY       1 PrimaryHDU     285   ()
  1  SCI           1 ImageHDU       241   (4096, 2048)   float32
  2  ERR           1 ImageHDU        53   (4096, 2048)   float32
  3  DQ            1 ImageHDU        45   (4096, 2048)   int16
  4  SCI           2 ImageHDU       256   (4096, 2048)   float32
  5  ERR           2 ImageHDU        53   (4096, 2048)   float32
  6  DQ            2 ImageHDU        45   (4096, 2048)   int16
  7  D2IMARR       1 ImageHDU        16   (64, 32)   float32
  8  D2IMARR       2 ImageHDU        16   (64, 32)   float32
  9  D2IMARR       3 ImageHDU        16   (64, 32)   float32
 10  D2IMARR       4 ImageHDU        16   (64, 32)   float32
 11  WCSDVARR      1 ImageHDU        16   (64, 32)   float32
 12  WCSDVARR      2 ImageHDU        16   (64, 32)   float32
 13  WCSDVARR      3 ImageHDU        16   (64, 32)   float32
 14  WCSDVARR      4 ImageHDU        16   (64, 32)   float32
 15  HDRLET        1 NonstandardExtHDU     18   (8640,)
 16  HDRLET        2 NonstandardExtHDU     26   (112320,)
 17  WCSCORR       1 BinTableHDU     59   14R x 24C   [40A, I, A, 24A, 24A, 24A, 24A, D, ...]
 18  HDRLET       18 NonstandardExtHDU     26   (112320,)
 19  HDRLET        4 NonstandardExtHDU     26   (112320,)

$ wcslint jbqf03gjq_flc.fits
python: malloc.c:2385: sysmalloc: Assertion `(old_top == initial_top (av) && old_size == 0) ||
((unsigned long) (old_size) >= MINSIZE && prev_inuse (old_top) &&
((unsigned long) old_end & (pagesize - 1)) == 0)' failed.
Aborted
```

File: https://github.com/astropy/astropy/blob/main/astropy/wcs/tests/data/tab-time-last-axis.fits

```
$ fitsinfo  tab-time-last-axis.fits
Filename: tab-time-last-axis.fits
No.    Name      Ver    Type      Cards   Dimensions   Format
  0  PRIMARY       1 PrimaryHDU      39   (1, 1, 1)   float64
  1  WCS-TABLE     1 BinTableHDU     13   1R x 1C   [128D]

$ wcslint  tab-time-last-axis.fits
  File ".../astropy/wcs/wcslint.py", line 18, in main
    print(wcs.validate(args.filename[0]))
  File ".../astropy/wcs/wcs.py", line 3531, in validate
    WCS(hdu.header,
  File ".../astropy/wcs/wcs.py", line 466, in __init__
    tmp_wcsprm = _wcs.Wcsprm(header=tmp_header_bytes, key=key,
ValueError: HDUList is required to retrieve -TAB coordinates and/or indices.
```

File:  https://mast.stsci.edu/api/v0.1/Download/file?uri=mast:HST/product/iabj01a2q_flc.fits 
(Reported by @mcara)

```
$ wcslint iabj01a2q_flc.fits
INFO:
                Inconsistent SIP distortion information is present in the FITS header and the WCS object:
                SIP coefficients were detected, but CTYPE is missing a "-SIP" suffix.
                astropy.wcs is using the SIP distortion coefficients,
                therefore the coordinates calculated here might be incorrect.

                If you do not want to apply the SIP distortion coefficients,
                please remove the SIP coefficients from the FITS header or the
                WCS object.  As an example, if the image is already distortion-corrected
                (e.g., drizzled) then distortion components should not apply and the SIP
                coefficients should be removed.

                While the SIP distortion coefficients are being applied here, if that was indeed the intent,
                for consistency please append "-SIP" to the CTYPE in the FITS header or the WCS object.

                 [astropy.wcs.wcs]
python3(27402,0x118052dc0) malloc: Incorrect checksum for freed object 0x7ff48b84a800:
probably modified after being freed.
Corrupt value: 0x0
python3(27402,0x118052dc0) malloc: *** set a breakpoint in malloc_error_break to debug
Abort trap: 6
```

## Issue Discussion Hints
> `wcslint` calls an underlying function here:
> 
> https://github.com/astropy/astropy/blob/8c0581fc68ca1f970d7f4e6c9ca9f2b9567d7b4c/astropy/wcs/wcs.py#L3430
> 
> Looks like all it does is tries to create a `WCS` object with the header and report warnings, so the bug is either inside `WCS` or it is a matter of updating on how validator calls `WCS` in more complicated cases:
> 
> https://github.com/astropy/astropy/blob/8c0581fc68ca1f970d7f4e6c9ca9f2b9567d7b4c/astropy/wcs/wcs.py#L3530-L3534

Nope. _That_ is the bug here:
```python
     WCS(hdu.header,  # should become:
     WCS(hdu.header, hdulist,
```

This should fix ACS and WCS-TAB errors but not the memory errors in WFC3 images. Even that one is a bug in `wcslint` or validation function and not in `WCS` itself.
FWIW, my error for WFC3/UVIS with astropy 5.1 is slightly different:

```
$ wcslint iabj01a2q_flc.fits
corrupted size vs. prev_size
Aborted
```
Maybe things have changed: I used an old file lying around my file system while yours is likely a fresh baked one with some HAP stuff.
Try running `updatewcs.updatewcs(filename, use_db=False)` from `stwcs`.
The segfault is quite something else and it is not really from validation itself, so I am going to open a new issue for it. See https://github.com/astropy/astropy/issues/13667

## Failing Tests That Should Pass
- `astropy/wcs/tests/test_wcs.py::test_validate_wcs_tab`

## Existing Passing Tests To Preserve
- `astropy/wcs/tests/test_wcs.py::test_fixes`
- `astropy/wcs/tests/test_wcs.py::test_outside_sky`
- `astropy/wcs/tests/test_wcs.py::test_pix2world`
- `astropy/wcs/tests/test_wcs.py::test_load_fits_path`
- `astropy/wcs/tests/test_wcs.py::test_dict_init`
- `astropy/wcs/tests/test_wcs.py::test_extra_kwarg`
- `astropy/wcs/tests/test_wcs.py::test_3d_shapes`
- `astropy/wcs/tests/test_wcs.py::test_preserve_shape`
- `astropy/wcs/tests/test_wcs.py::test_broadcasting`
- `astropy/wcs/tests/test_wcs.py::test_shape_mismatch`
- `astropy/wcs/tests/test_wcs.py::test_invalid_shape`
- `astropy/wcs/tests/test_wcs.py::test_warning_about_defunct_keywords`
- `astropy/wcs/tests/test_wcs.py::test_warning_about_defunct_keywords_exception`
- `astropy/wcs/tests/test_wcs.py::test_to_header_string`
- `astropy/wcs/tests/test_wcs.py::test_to_fits`
- `astropy/wcs/tests/test_wcs.py::test_to_header_warning`
- `astropy/wcs/tests/test_wcs.py::test_no_comments_in_header`
- `astropy/wcs/tests/test_wcs.py::test_find_all_wcs_crash`
- `astropy/wcs/tests/test_wcs.py::test_validate`
- `astropy/wcs/tests/test_wcs.py::test_validate_with_2_wcses`
- `astropy/wcs/tests/test_wcs.py::test_crpix_maps_to_crval`
- `astropy/wcs/tests/test_wcs.py::test_all_world2pix`
- `astropy/wcs/tests/test_wcs.py::test_scamp_sip_distortion_parameters`
- `astropy/wcs/tests/test_wcs.py::test_fixes2`
- `astropy/wcs/tests/test_wcs.py::test_unit_normalization`
- `astropy/wcs/tests/test_wcs.py::test_footprint_to_file`
- `astropy/wcs/tests/test_wcs.py::test_validate_faulty_wcs`
- `astropy/wcs/tests/test_wcs.py::test_error_message`
- `astropy/wcs/tests/test_wcs.py::test_out_of_bounds`
- `astropy/wcs/tests/test_wcs.py::test_calc_footprint_1`
- `astropy/wcs/tests/test_wcs.py::test_calc_footprint_2`
- `astropy/wcs/tests/test_wcs.py::test_calc_footprint_3`
- `astropy/wcs/tests/test_wcs.py::test_sip`
- `astropy/wcs/tests/test_wcs.py::test_sub_3d_with_sip`
- `astropy/wcs/tests/test_wcs.py::test_printwcs`
- `astropy/wcs/tests/test_wcs.py::test_invalid_spherical`
- `astropy/wcs/tests/test_wcs.py::test_no_iteration`
- `astropy/wcs/tests/test_wcs.py::test_sip_tpv_agreement`
- `astropy/wcs/tests/test_wcs.py::test_tpv_copy`
- `astropy/wcs/tests/test_wcs.py::test_hst_wcs`
- `astropy/wcs/tests/test_wcs.py::test_cpdis_comments`
- `astropy/wcs/tests/test_wcs.py::test_d2im_comments`
- `astropy/wcs/tests/test_wcs.py::test_sip_broken`
- `astropy/wcs/tests/test_wcs.py::test_no_truncate_crval`
- `astropy/wcs/tests/test_wcs.py::test_no_truncate_crval_try2`
- `astropy/wcs/tests/test_wcs.py::test_no_truncate_crval_p17`
- `astropy/wcs/tests/test_wcs.py::test_no_truncate_using_compare`
- `astropy/wcs/tests/test_wcs.py::test_passing_ImageHDU`
- `astropy/wcs/tests/test_wcs.py::test_inconsistent_sip`
- `astropy/wcs/tests/test_wcs.py::test_bounds_check`
- `astropy/wcs/tests/test_wcs.py::test_naxis`
- `astropy/wcs/tests/test_wcs.py::test_sip_with_altkey`
- `astropy/wcs/tests/test_wcs.py::test_to_fits_1`
- `astropy/wcs/tests/test_wcs.py::test_keyedsip`
- `astropy/wcs/tests/test_wcs.py::test_zero_size_input`
- `astropy/wcs/tests/test_wcs.py::test_scalar_inputs`
- `astropy/wcs/tests/test_wcs.py::test_footprint_contains`
- `astropy/wcs/tests/test_wcs.py::test_cunit`
- `astropy/wcs/tests/test_wcs.py::test_invalid_coordinate_masking`
- `astropy/wcs/tests/test_wcs.py::test_no_pixel_area`
- `astropy/wcs/tests/test_wcs.py::test_distortion_header`
- `astropy/wcs/tests/test_wcs.py::test_pixlist_wcs_colsel`
- `astropy/wcs/tests/test_wcs.py::test_time_axis_selection`
- `astropy/wcs/tests/test_wcs.py::test_temporal`
- `astropy/wcs/tests/test_wcs.py::test_swapaxes_same_val_roundtrip`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
