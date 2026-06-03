# SWE-bench Issue: astropy__astropy-13465

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13465
- Base Commit: 0f3e4a6549bc8bb3276184a021ecdd3482eb5d13
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-07-19T08:36:06Z
- Version: 5.0

## Issue Title
rtol for FITSDiff not working as expected.

## Problem Statement
rtol for FITSDiff not working as expected. 
I have question about the rtol parameter for FITSDiff, when I create a report it appears that the numbers cited as being different are within the given relative tolerance.  I couldn't figure out why so I thought this may be a bug, apologies if I'm missing something super obvious here! 


Here's how to recreate the issue using FITSdiff, I included a zip file containing the two fits file and an example logfile.
```python
from astropy.io import fits
fits1 = fits.open('TEST.0.bin0000.source0000.FITS')
fits2 = fits.open('TEST.0.bin0000.source0000.FITS.benchmark')
fd = fits.FITSDiff(fits1,fits2,ignore_keywords=['DATE-MAP','CDATE','HISTORY'],atol=0,rtol=0.01)
fd.report(fileobj='logfile', indent=0, overwrite=True)
```

[bug_FITSdiff.zip](https://github.com/astropy/astropy/files/8892253/bug_FITSdiff.zip)


```
logfile contents=
 fitsdiff: 4.0.2
 a: /home/usno/difx/DIFX-TRUNK/tests/DiFXtest/complex-complex/TEST.0.bin0000.source0000.FITS
 b: /home/usno/difx/DIFX-TRUNK/tests/DiFXtest/complex-complex//benchmark_results/TEST.0.bin0000.source0000.FITS
 Keyword(s) not to be compared:
  CDATE DATE-MAP HISTORY
 Maximum number of different data values to be reported: 10
 Relative tolerance: 0.01, Absolute tolerance: 0.0

Extension HDU 8:

   Data contains differences:


     Column FLUX data differs in row 5:
        at [3]:
          a> -1.3716967e-11
           ?         ^^
          b> -1.3716938e-11
           ?         ^^
        at [4]:
          a> 0.21090482
           ?          -
          b> 0.2109048
        at [6]:
          a> 0.20984006
           ?          ^
          b> 0.20984003
           ?          ^
        ...and at 5766 more indices.
     1 different table data element(s) found (0.26% different).
```

## Issue Discussion Hints
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

GitHub issues in the Astropy repository are used to track bug reports and feature requests; If your issue poses a question about how to use Astropy, please instead raise your question in the [Astropy Discourse user forum](https://community.openastronomy.org/c/astropy/8) and close this issue.

If you feel that this issue has not been responded to in a timely manner, please leave a comment mentioning our software support engineer @embray, or send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
Has anyone gotten a chance to look at this and recreate the issue? I played around with numpy.allclose which is cited as the function fitsdiff uses here:

rtol[float](https://docs.python.org/3/library/functions.html#float), optional
The relative difference to allow when comparing two float values either in header values, image arrays, or table columns (default: 0.0). Values which satisfy the expression

|𝑎−𝑏|>atol+rtol⋅|𝑏|
are considered to be different. The underlying function used for comparison is [numpy.allclose](https://numpy.org/doc/stable/reference/generated/numpy.allclose.html#numpy.allclose).
(from: https://docs.astropy.org/en/stable/io/fits/api/diff.html)

and using numpy.allclose the results are what I would expect them to be for the numbers in my original post:


Python 3.8.5 (default, Sep  4 2020, 07:30:14) 
[GCC 7.3.0] :: Anaconda, Inc. on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import numpy
>>> numpy.allclose(-1.3716944e-11,-1.3716938e-11,rtol=0.01,atol=0.0, equal_nan=False)
True
>>> numpy.allclose(-1.3716944e-11,-1.3716938e-11,rtol=0.001,atol=0.0, equal_nan=False)
True
>>> numpy.allclose(-1.3716944e-11,-1.3716938e-11,rtol=0.0001,atol=0.0, equal_nan=False)
True
>>> numpy.allclose(-1.3716944e-11,-1.3716938e-11,rtol=0.00001,atol=0.0, equal_nan=False)
True
>>> numpy.allclose(-1.3716944e-11,-1.3716938e-11,rtol=0.000001,atol=0.0, equal_nan=False)
True
>>> numpy.allclose(-1.3716944e-11,-1.3716938e-11,rtol=0.0000001,atol=0.0, equal_nan=False)
False
Indeed there is a bug for multidimensional columns (which is the case for FLUX here). The code identifies the rows where the diff is greater than atol/rtol, and then delegates the printing to `report_diff_values` which doesn't use atol/rtol :
https://github.com/astropy/astropy/blob/2f4b3d2e51e22d2b4309b9cd74aa723a49cfff99/astropy/utils/diff.py#L46

## Failing Tests That Should Pass
- `astropy/io/fits/tests/test_diff.py::test_rawdatadiff_diff_with_rtol`

## Existing Passing Tests To Preserve
- `astropy/io/fits/tests/test_diff.py::test_fitsdiff_hdu_name`
- `astropy/io/fits/tests/test_diff.py::test_fitsdiff_no_hdu_name`
- `astropy/io/fits/tests/test_diff.py::test_fitsdiff_with_names`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
