# SWE-bench Issue: astropy__astropy-14295

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-14295
- Base Commit: 15cc8f20a4f94ab1910bc865f40ec69d02a7c56c
- Environment Setup Commit: 5f74eacbcc7fff707a44d8eb58adaa514cb7dcb5
- Created At: 2023-01-23T06:51:46Z
- Version: 5.1

## Issue Title
Presence of SIP keywords leads to ignored PV keywords.

## Problem Statement
Presence of SIP keywords leads to ignored PV keywords.
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
I am working on updating the fits header for one of our telescopes. We wanted to represent the distortions in SIP convention and the projection to be 'CAR'.
While working on this, I noticed if SIP coefficients are present in the header and/or '-SIP' is added to CTYPEia keywords,
astropy treats the PV keywords (PV1_0, PV1_1 and PV1_2) as "redundant SCAMP distortions".

Earlier I could not figure out why the projection weren't going as I expected, and I suspected a bug in astropy wcs. After talking to Mark Calabretta about the difficulties I'm facing, that suspicion only grew stronger. The header was working as expected with WCSLIB but was giving unexpected behavior in astropy wcs.

The following would be one example header - 
```
header_dict = {
'SIMPLE'  : True, 
'BITPIX'  : -32, 
'NAXIS'   :  2,
'NAXIS1'  : 1024,
'NAXIS2'  : 1024,
'CRPIX1'  : 512.0,
'CRPIX2'  : 512.0,
'CDELT1'  : 0.01,
'CDELT2'  : 0.01,
'CRVAL1'  : 120.0,
'CRVAL2'  : 29.0,
'CTYPE1'  : 'RA---CAR-SIP',
'CTYPE2'  : 'DEC--CAR-SIP',
'PV1_1'   :120.0,
'PV1_2'   :29.0,
'PV1_0'   :1.0,
'A_ORDER' :2,
'A_2_0'   :5.0e-4,
'B_ORDER' :2,
'B_2_0'   :5.0e-4
}
from astropy.io import fits
header = fits.Header(header_dict)
```

### Expected behavior
When you parse the wcs information from this header, the image should be centered at ra=120 and dec=29 with lines of constant ra and dec looking like the following image generated using wcslib - 
![wcsgrid_with_PV](https://user-images.githubusercontent.com/97835976/210666592-62860f54-f97a-4114-81bb-b50712194337.png)

### Actual behavior
If I parse the wcs information using astropy wcs, it throws the following warning -
`WARNING: FITSFixedWarning: Removed redundant SCAMP distortion parameters because SIP parameters are also present [astropy.wcs.wcs]`
And the resulting grid is different.
Code - 
```
import numpy as np
import matplotlib.pyplot as plt
from astropy.wcs import WCS
w = WCS(header)
ra = np.linspace(116, 126, 25)
dec = np.linspace(25, 34, 25)

for r in ra:
    x, y = w.all_world2pix(np.full_like(dec, r), dec, 0)
    plt.plot(x, y, 'C0')
for d in dec:
    x, y = w.all_world2pix(ra, np.full_like(ra, d), 0)
    plt.plot(x, y, 'C0')

plt.title('Lines of constant equatorial coordinates in pixel space')
plt.xlabel('x')
plt.ylabel('y')
```
Grid - 
![image](https://user-images.githubusercontent.com/97835976/210667514-4d2a033b-3571-4df5-9646-42e4cbb51026.png)

The astropy wcs grid/solution does not change whethere we keep or remove the PV keywords.
Furthermore, the astropy grid can be recreated in wcslib, by removing the PV keywords.
![wcsgrid_without_PV](https://user-images.githubusercontent.com/97835976/210667756-10336d93-1266-4ae6-ace1-27947746531c.png)


### Steps to Reproduce
<!-- Ideally a code example could be provided so we can run it ourselves. -->
<!-- If you are pasting code, use triple backticks (```) around
your code snippet. -->
<!-- If necessary, sanitize your screen output to be pasted so you do not
reveal secrets like tokens and passwords. -->

1. Initialize the header
2. Parse the header using astropy.wcs.WCS
3. Plot the graticule
4. Remove the PV keywords and run again
5. You will find the same graticule indicating that PV keywords are completely ignored.
6.  Additionally, the graticules can be compared with the wcsgrid utility of wcslib.


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
Linux-6.0.11-200.fc36.x86_64-x86_64-with-glibc2.35
Python 3.9.12 (main, Apr  5 2022, 06:56:58) 
[GCC 7.5.0]
Numpy 1.21.5
pyerfa 2.0.0
astropy 5.1
Scipy 1.7.3
Matplotlib 3.5.1
Remove heuristic code to handle PTF files which is causing a bug
<!-- This comments are hidden when you submit the pull request,
so you do not need to remove them! -->

<!-- Please be sure to check out our contributing guidelines,
https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md .
Please be sure to check out our code of conduct,
https://github.com/astropy/astropy/blob/main/CODE_OF_CONDUCT.md . -->

<!-- If you are new or need to be re-acquainted with Astropy
contributing workflow, please see
http://docs.astropy.org/en/latest/development/workflow/development_workflow.html .
There is even a practical example at
https://docs.astropy.org/en/latest/development/workflow/git_edit_workflow_examples.html#astropy-fix-example . -->

<!-- Astropy coding style guidelines can be found here:
https://docs.astropy.org/en/latest/development/codeguide.html#coding-style-conventions
Our testing infrastructure enforces to follow a subset of the PEP8 to be
followed. You can check locally whether your changes have followed these by
running the following command:

tox -e codestyle

-->

<!-- Please just have a quick search on GitHub to see if a similar
pull request has already been posted.
We have old closed pull requests that might provide useful code or ideas
that directly tie in with your pull request. -->

<!-- We have several automatic features that run when a pull request is open.
They can appear daunting but do not worry because maintainers will help
you navigate them, if necessary. -->

### Description
<!-- Provide a general description of what your pull request does.
Complete the following sentence and add relevant details as you see fit. -->

<!-- In addition please ensure that the pull request title is descriptive
and allows maintainers to infer the applicable subpackage(s). -->

<!-- READ THIS FOR MANUAL BACKPORT FROM A MAINTAINER:
Apply "skip-basebranch-check" label **before** you open the PR! -->

Currently the `_fix_scamp` function remove any PV keywords when SIP distortions are present and no radial terms are present which should not  be the case. This function was put in place for solving https://github.com/astropy/astropy/issues/299 but it causes the bug #14255.

We can either keep adding heuristic code to fix the edge cases as they come up with or remove `_fix_scamp` and let the user deal with non-standard files. I'm opening a pull request for the latter following the discusison in #14255.

<!-- If the pull request closes any open issues you can add this.
If you replace <Issue Number> with a number, GitHub will automatically link it.
If this pull request is unrelated to any issues, please remove
the following line. -->

Fixes #14255

### Checklist for package maintainer(s)
<!-- This section is to be filled by package maintainer(s) who will
review this pull request. -->

This checklist is meant to remind the package maintainer(s) who will review this pull request of some common things to look for. This list is not exhaustive.

- [ ] Do the proposed changes actually accomplish desired goals?
- [ ] Do the proposed changes follow the [Astropy coding guidelines](https://docs.astropy.org/en/latest/development/codeguide.html)?
- [ ] Are tests added/updated as required? If so, do they follow the [Astropy testing guidelines](https://docs.astropy.org/en/latest/development/testguide.html)?
- [ ] Are docs added/updated as required? If so, do they follow the [Astropy documentation guidelines](https://docs.astropy.org/en/latest/development/docguide.html#astropy-documentation-rules-and-guidelines)?
- [ ] Is rebase and/or squash necessary? If so, please provide the author with appropriate instructions. Also see ["When to rebase and squash commits"](https://docs.astropy.org/en/latest/development/when_to_rebase.html).
- [ ] Did the CI pass? If no, are the failures related? If you need to run daily and weekly cron jobs as part of the PR, please apply the `Extra CI` label. Codestyle issues can be fixed by the [bot](https://docs.astropy.org/en/latest/development/workflow/development_workflow.html#pre-commit).
- [ ] Is a change log needed? If yes, did the change log check pass? If no, add the `no-changelog-entry-needed` label. If this is a manual backport, use the `skip-changelog-checks` label unless special changelog handling is necessary.
- [ ] Is this a big PR that makes a "What's new?" entry worthwhile and if so, is (1) a "what's new" entry included in this PR and (2) the "whatsnew-needed" label applied?
- [ ] Is a milestone set? Milestone must be set but `astropy-bot` check might be missing; do not let the green checkmark fool you.
- [ ] At the time of adding the milestone, if the milestone set requires a backport to release branch(es), apply the appropriate `backport-X.Y.x` label(s) *before* merge.

## Issue Discussion Hints
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

GitHub issues in the Astropy repository are used to track bug reports and feature requests; If your issue poses a question about how to use Astropy, please instead raise your question in the [Astropy Discourse user forum](https://community.openastronomy.org/c/astropy/8) and close this issue.

If you feel that this issue has not been responded to in a timely manner, please send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
I have seen this issue discussed in https://github.com/astropy/astropy/issues/299 and https://github.com/astropy/astropy/issues/3559 with an fix in https://github.com/astropy/astropy/pull/1278 which was not perfect and causes the issue for me.

https://github.com/astropy/astropy/blob/966be9fedbf55c23ba685d9d8a5d49f06fa1223c/astropy/wcs/wcs.py#L708-L752

I'm using a CAR projection which needs the PV keywords.
By looking at the previous discussions and the implementation above some I propose some approaches to fix this.

1. Check if the project type is TAN or TPV. I'm not at all familiar with SCAMP distortions but I vaguely remember that they are used on TAN projection. Do correct me if I'm wrong.
2. As @stargaser suggested
> SCAMP always makes a fourth-order polynomial with no radial terms. I think that would be the best fingerprint.

Currently, https://github.com/astropy/astropy/pull/1278 only checks if any radial terms are present but we can also check if 3rd and 4th order terms are definitely present.
3. If wcslib supports SCAMP distortions now, then the filtering could be dropped altogether. I'm not sure whether it will cause any conflict between SIP and SCAMP distortions between wcslib when both distortions keyword are actually  present (not as projection parameters). 

@nden @mcara Mark Calabretta suggested you guys might be able to help with this.

I am not familiar with SCAMP but proposed suggestions seem reasonable, at least at the first glance. I will have to read more about SCAMP distortions re-read this issue, etc. I did not participate in the discussions from a decade ago and so I'll have to look at those too.

> I'm using a CAR projection which needs the PV keywords.

This is strange to me though. I modified your header and removed `SIP` (instead of `PV`). I then printed `Wcsprm`:

```python
header_dict = {
    'SIMPLE'  : True,
    'BITPIX'  : -32,
    'NAXIS'   :  2,
    'NAXIS1'  : 1024,
    'NAXIS2'  : 1024,
    'CRPIX1'  : 512.0,
    'CRPIX2'  : 512.0,
    'CDELT1'  : 0.01,
    'CDELT2'  : 0.01,
    'CRVAL1'  : 120.0,
    'CRVAL2'  : 29.0,
    'CTYPE1'  : 'RA---CAR',
    'CTYPE2'  : 'DEC--CAR',
    'PV1_1'   :120.0,
    'PV1_2'   :29.0,
    'PV1_0'   :1.0,
}
from astropy.wcs import WCS
w = WCS(header_dict)
print(w.wcs)
```

Here is an excerpt of what was reported:
```
   prj.*
       flag: 203
       code: "CAR"
         r0: 57.295780
         pv: (not used)
       phi0: 120.000000
     theta0: 29.000000
     bounds: 7

       name: "plate caree"
   category: 2 (cylindrical)
    pvrange: 0
```

So, to me it seems that `CAR` projection does not use `PV` and this contradicts (at first glance) the statement _"a CAR projection which needs the PV keywords"_.
`PV` keywords are not optional keywords in CAR projection to relate the native spherical coordinates with celestial coordinates (RA, Dec). By default they have values equal to zero, but in my case I need to define these parameters.
Also, from https://doi.org/10.1051/0004-6361:20021327 Table 13 one can see that `CAR` projection is not associated with any PV parameters.
> Table 13 one can see that CAR projection is not associated with any PV parameters.

Yes, that is true. 
But the description of Table 13 says that it only lists required parameters.

Also, PV1_1, and PV1_2 defines $\theta_0$ and $\phi_0$ which are accepted by almost all the projections to change the default value.
Yes, I should have read the footnote to Table 13 (and then Section 2.5).
Just commenting out https://github.com/astropy/astropy/blob/966be9fedbf55c23ba685d9d8a5d49f06fa1223c/astropy/wcs/wcs.py#L793
solves the issue for me.
But, I don't know if that would be desirable as we might be back to square one with the old PTF images.

Once the appropriate approach for fixing this is decided, I can try to make a small PR.
Looking at the sample listing for TPV - https://fits.gsfc.nasa.gov/registry/tpvwcs.html - I see that projection code is 'TPV' (in `CTYPE`). So I am not sure why we ignore `PV` if code is `SIP`. Maybe it was something that was dealing with pre-2012 FITS convention, with files created by SCAMP (pre-2012). How relevant is this nowadays? Maybe those who have legacy files should update `CTYPE`?

In any case, it looks like we should not be ignoring/deleting `PV` when `CTYPE` has `-SIP`.

It is not a good solution but it will allow you to use `astropy.wcs` with your file (until we figure out a permanent solution) if, after creating the WCS object (let's call it `w` as in my example above), you can run:

```python
w.wcs.set_pv([(1, 1, 120.0), (1, 0, 1.0), (1, 2, 29.0)])
w.wcs.set()
```
Your solution proposed above is OK too as a temporary workaround.
NOTE: A useful discussion can be found here: https://jira.lsstcorp.org/browse/DM-2883
> I see that projection code is 'TPV' (in CTYPE). So I am not sure why we ignore PV if code is SIP. Maybe it was something that was dealing with pre-2012 FITS convention, with files created by SCAMP (pre-2012).

Yes. Apparently pre-2012 SCAMP just kept the CTYPE as `TAN` .

> Maybe those who have legacy files should update CTYPE?

That would be my first thought as well instead of getting a pull request through. But, it's been in astropy for so long at this point.

> Your` solution proposed above is OK too as a temporary workaround.

By just commenting out, I don't have to make any change to my header update code or more accurately the header reading code and the subsequent pipelines for our telescope. By commenting the line, we could work on the files now and later an astropy update will clean up things in the background (I'm hoping).

From the discussion https://jira.lsstcorp.org/browse/DM-2883

> David Berry reports:
> 
> The FitsChan class in AST handles this as follows:
> 
> 1) If the CTYPE in a FITS header uses TPV, then the the PVi_j headers are interpreted according to the conventions of the distorted TAN paper above.
> 
> 2) For CTYPEs that use TAN, the interpretation of PVi_j values is controlled by the "PolyTan" attribute of the FitsChan. This can be set to an explicit value before reading the header to indicate the convention to use. If it is not set before reading the header, a heuristic is used to guess the most appropriate convention as follows:
> 
> If the FitsChan contains any PVi_m keywords for the latitude axis, or if it contains PVi_m keywords for the longitude axis with "m" greater than 4, then the distorted TAN convention is used. Otherwise, the standard convention is used.
> 

This seems like something that could be reasonable and it is a combination of my points 1 and 2 earlier.

If we think about removing `fix_scamp` altogether, then we would have to consider the following - 
1. How does the old PTF fits files (which contains both SIP and TPV keywords with TAN projection) behave with current wcslib.
2. How does other SCAMP fits files work with the current wcslib. I think if the projection is written as `TPV` then wcslib will handle it fine, I have no idea about CTYPE 'TAN'
The WCSLIB package ships with some test headers. One of the test header is about SIP and TPV.

>  FITS header keyrecords used for testing the handling of the "SIP" (Simple
>  Imaging Polynomial) and TPV distortions by WCSLIB.
> 
>  This header was adapted from a pair of FITS files from the Palomar Transient
>  Factory (IPAC) provided by David Shupe.  The same distortion was encoded in
>  two ways, the primary representation uses the SIP convention, and the 'P'
>  alternate the TPV projection.  Translations of both of these into other
>  distortion functions were then added as alternates.

In the examples given, the headers have a CTYPE for `RA--TAN-SIP` for SIP distortions and `RA---TPV` for SCAMP distortions. So, as long as the files from SCAMP are of `TPV` CTYPE they should just work.

The file - [SIPTPV.txt](https://github.com/astropy/astropy/files/10367722/SIPTPV.txt)
Also can be found at wcslib/C/test/SIPTPV.keyrec

Since I know nothing about SCAMP and do not know how these changes might affect those who do use SCAMP, I would like to hear opinions from those who might be affected by changes to SIP/SCAMP/TPV issue or from those who worked on the original issue: @lpsinger @stargaser @astrofrog 
Man, this takes me back. This was probably my first Astropy contribution.

Is anyone on this PR going to be at AAS in Seattle this week?
I'm attending the AAS in Seattle this week.

> 2. As @stargaser suggested
> 
> > SCAMP always makes a fourth-order polynomial with no radial terms. I think that would be the best fingerprint.
> 
> Currently, #1278 only checks if any radial terms are present but we can also check if 3rd and 4th order terms are definitely present. 3. If wcslib supports SCAMP distortions now, then the filtering could be dropped altogether. I'm not sure whether it will cause any conflict between SIP and SCAMP distortions between wcslib when both distortions keyword are actually present (not as projection parameters).

I think this would be the easiest solution that would satisfy the aims of #1278 to work with PTF files. I'm afraid it will not be possible to modify the headers of PTF files as the project has been over for several years now.

>  I'm afraid it will not be possible to modify the headers of PTF files as the project has been over for several years now.

I meant on a user level. Someone who is reading the PTF files can just remove the header keywords. 
Or maybe wcslib just handles it without issue now giving the intended wcs output? That has to be checked though.
Does anyone have any thoughts on this about how to proceed?

Also, @stargaser if you have access to the PTF files, could you just try to read them with the `fix_scamp` function removed? This might help us choose what route to take.
> > I'm afraid it will not be possible to modify the headers of PTF files as the project has been over for several years now.
> 
> I meant on a user level. Someone who is reading the PTF files can just remove the header keywords. Or maybe wcslib just handles it without issue now giving the intended wcs output? That has to be checked though.

I am of the same opinion. Those who use SCAMP that does not use correct CTYPE should fix the CTYPE manually. It is not that hard. It is impossible to design software that can deal with every possible interpretation of the same keyword.

True, in this case maybe we could have some sort of heuristic approach and "we can also check if 3rd and 4th order terms are definitely present" but really why do it at all? To me, the idea of FITS "standard" is not to have to guess anything, have heuristics, or software switches that "tell" the code (or "us") how to interpret things in a FITS file. IMO, the point of a standard and "archival format" is that things are unambiguous.

I think if there are no other comments or proposals you should go ahead and make a PR to remove `_fix_scamp()`.
Since this was an actual issue that users encountered, which after very considerable discussion we decided to fix, I think we cannot just remove it, but have to put a mechanism in place for telling the user how they can get back the previous behaviour -- e.g., by adding appropriate text to any error message that now arises. Or we could make the removal depend on a configuration item or so.
p.s. Of course, if at the present time, archives for PTF and other observatories do not have the issue any more, perhaps we can just remove it, but probably best to check that!

## Failing Tests That Should Pass
- `astropy/wcs/tests/test_wcs.py::test_tpv_ctype_tpv`
- `astropy/wcs/tests/test_wcs.py::test_tpv_ctype_tan`
- `astropy/wcs/tests/test_wcs.py::test_car_sip_with_pv`

## Existing Passing Tests To Preserve
- `astropy/wcs/tests/test_wcs.py::TestMaps::test_consistency`
- `astropy/wcs/tests/test_wcs.py::TestMaps::test_maps`
- `astropy/wcs/tests/test_wcs.py::TestSpectra::test_consistency`
- `astropy/wcs/tests/test_wcs.py::TestSpectra::test_spectra`
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
- `astropy/wcs/tests/test_wcs.py::test_validate_wcs_tab`
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
- `astropy/wcs/tests/test_wcs.py::test_tpv_ctype_sip`
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
- `astropy/wcs/tests/test_wcs.py::TestWcsWithTime::test_keywods2wcsprm`
- `astropy/wcs/tests/test_wcs.py::TestWcsWithTime::test_transforms`
- `astropy/wcs/tests/test_wcs.py::test_invalid_coordinate_masking`
- `astropy/wcs/tests/test_wcs.py::test_no_pixel_area`
- `astropy/wcs/tests/test_wcs.py::test_distortion_header`
- `astropy/wcs/tests/test_wcs.py::test_pixlist_wcs_colsel`
- `astropy/wcs/tests/test_wcs.py::test_time_axis_selection`
- `astropy/wcs/tests/test_wcs.py::test_temporal`
- `astropy/wcs/tests/test_wcs.py::test_swapaxes_same_val_roundtrip`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
