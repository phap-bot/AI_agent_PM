# SWE-bench Issue: astropy__astropy-11693

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-11693
- Base Commit: 3832210580d516365ddae1a62071001faf94d416
- Environment Setup Commit: 3832210580d516365ddae1a62071001faf94d416
- Created At: 2021-05-04T10:05:33Z
- Version: 4.2

## Issue Title
'WCS.all_world2pix' failed to converge when plotting WCS with non linear distortions

## Problem Statement
'WCS.all_world2pix' failed to converge when plotting WCS with non linear distortions
<!-- This comments are hidden when you submit the issue,
so you do not need to remove them! -->

<!-- Please be sure to check out our contributing guidelines,
https://github.com/astropy/astropy/blob/master/CONTRIBUTING.md .
Please be sure to check out our code of conduct,
https://github.com/astropy/astropy/blob/master/CODE_OF_CONDUCT.md . -->

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
When trying to plot an image with a WCS as projection that contains non linear Distortions it fails with a `NoConvergence` error.

### Expected behavior
When I add `quiet=True` as parameter to the call 
```pixel = self.all_world2pix(*world_arrays, 0)``` 
at line 326 of `astropy/wcs/wcsapi/fitswcs.py` I get the good enough looking plot below:

![bugreport](https://user-images.githubusercontent.com/64231/112940287-37c2c800-912d-11eb-8ce8-56fd284bb8e7.png)

It would be nice if there was a way of getting that plot without having to hack the library code like that.
### Actual behavior
<!-- What actually happened. -->
<!-- Was the output confusing or poorly described? -->
The call to plotting the grid fails with the following error (last few lines, can provide more if necessary):

```
~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcsapi/fitswcs.py in world_to_pixel_values(self, *world_arrays)
    324 
    325     def world_to_pixel_values(self, *world_arrays):
--> 326         pixel = self.all_world2pix(*world_arrays, 0)
    327         return pixel[0] if self.pixel_n_dim == 1 else tuple(pixel)
    328 

~/work/develop/env/lib/python3.9/site-packages/astropy/utils/decorators.py in wrapper(*args, **kwargs)
    534                     warnings.warn(message, warning_type, stacklevel=2)
    535 
--> 536             return function(*args, **kwargs)
    537 
    538         return wrapper

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in all_world2pix(self, tolerance, maxiter, adaptive, detect_divergence, quiet, *args, **kwargs)
   1886             raise ValueError("No basic WCS settings were created.")
   1887 
-> 1888         return self._array_converter(
   1889             lambda *args, **kwargs:
   1890             self._all_world2pix(

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in _array_converter(self, func, sky, ra_dec_order, *args)
   1335                     "a 1-D array for each axis, followed by an origin.")
   1336 
-> 1337             return _return_list_of_arrays(axes, origin)
   1338 
   1339         raise TypeError(

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in _return_list_of_arrays(axes, origin)
   1289             if ra_dec_order and sky == 'input':
   1290                 xy = self._denormalize_sky(xy)
-> 1291             output = func(xy, origin)
   1292             if ra_dec_order and sky == 'output':
   1293                 output = self._normalize_sky(output)

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in <lambda>(*args, **kwargs)
   1888         return self._array_converter(
   1889             lambda *args, **kwargs:
-> 1890             self._all_world2pix(
   1891                 *args, tolerance=tolerance, maxiter=maxiter,
   1892                 adaptive=adaptive, detect_divergence=detect_divergence,

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in _all_world2pix(self, world, origin, tolerance, maxiter, adaptive, detect_divergence, quiet)
   1869                     slow_conv=ind, divergent=None)
   1870             else:
-> 1871                 raise NoConvergence(
   1872                     "'WCS.all_world2pix' failed to "
   1873                     "converge to the requested accuracy.\n"

NoConvergence: 'WCS.all_world2pix' failed to converge to the requested accuracy.
After 20 iterations, the solution is diverging at least for one input point.
```

### Steps to Reproduce
<!-- Ideally a code example could be provided so we can run it ourselves. -->
<!-- If you are pasting code, use triple backticks (```) around
your code snippet. -->
<!-- If necessary, sanitize your screen output to be pasted so you do not
reveal secrets like tokens and passwords. -->

Here is the code to reproduce the problem:
```
from astropy.wcs import WCS, Sip
import numpy as np
import matplotlib.pyplot as plt

wcs = WCS(naxis=2)
a = [[ 0.00000000e+00,  0.00000000e+00,  6.77532513e-07,
        -1.76632141e-10],
       [ 0.00000000e+00,  9.49130161e-06, -1.50614321e-07,
         0.00000000e+00],
       [ 7.37260409e-06,  2.07020239e-09,  0.00000000e+00,
         0.00000000e+00],
       [-1.20116753e-07,  0.00000000e+00,  0.00000000e+00,
         0.00000000e+00]]
b = [[ 0.00000000e+00,  0.00000000e+00,  1.34606617e-05,
        -1.41919055e-07],
       [ 0.00000000e+00,  5.85158316e-06, -1.10382462e-09,
         0.00000000e+00],
       [ 1.06306407e-05, -1.36469008e-07,  0.00000000e+00,
         0.00000000e+00],
       [ 3.27391123e-09,  0.00000000e+00,  0.00000000e+00,
         0.00000000e+00]]
crpix = [1221.87375165,  994.90917378]
ap = bp = np.zeros((4, 4))

wcs.sip = Sip(a, b, ap, bp, crpix)

plt.subplot(projection=wcs)
plt.imshow(np.zeros((1944, 2592)))
plt.grid(color='white', ls='solid')
```

### System Details
<!-- Even if you do not think this is necessary, it is useful information for the maintainers.
Please run the following snippet and paste the output below:
import platform; print(platform.platform())
import sys; print("Python", sys.version)
import numpy; print("Numpy", numpy.__version__)
import astropy; print("astropy", astropy.__version__)
import scipy; print("Scipy", scipy.__version__)
import matplotlib; print("Matplotlib", matplotlib.__version__)
-->
```
>>> import platform; print(platform.platform())
Linux-5.11.10-arch1-1-x86_64-with-glibc2.33
>>> import sys; print("Python", sys.version)
Python 3.9.2 (default, Feb 20 2021, 18:40:11) 
[GCC 10.2.0]
>>> import numpy; print("Numpy", numpy.__version__)
Numpy 1.20.2
>>> import astropy; print("astropy", astropy.__version__)
astropy 4.3.dev690+g7811614f8
>>> import scipy; print("Scipy", scipy.__version__)
Scipy 1.6.1
>>> import matplotlib; print("Matplotlib", matplotlib.__version__)
Matplotlib 3.3.4
```
'WCS.all_world2pix' failed to converge when plotting WCS with non linear distortions
<!-- This comments are hidden when you submit the issue,
so you do not need to remove them! -->

<!-- Please be sure to check out our contributing guidelines,
https://github.com/astropy/astropy/blob/master/CONTRIBUTING.md .
Please be sure to check out our code of conduct,
https://github.com/astropy/astropy/blob/master/CODE_OF_CONDUCT.md . -->

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
When trying to plot an image with a WCS as projection that contains non linear Distortions it fails with a `NoConvergence` error.

### Expected behavior
When I add `quiet=True` as parameter to the call 
```pixel = self.all_world2pix(*world_arrays, 0)``` 
at line 326 of `astropy/wcs/wcsapi/fitswcs.py` I get the good enough looking plot below:

![bugreport](https://user-images.githubusercontent.com/64231/112940287-37c2c800-912d-11eb-8ce8-56fd284bb8e7.png)

It would be nice if there was a way of getting that plot without having to hack the library code like that.
### Actual behavior
<!-- What actually happened. -->
<!-- Was the output confusing or poorly described? -->
The call to plotting the grid fails with the following error (last few lines, can provide more if necessary):

```
~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcsapi/fitswcs.py in world_to_pixel_values(self, *world_arrays)
    324 
    325     def world_to_pixel_values(self, *world_arrays):
--> 326         pixel = self.all_world2pix(*world_arrays, 0)
    327         return pixel[0] if self.pixel_n_dim == 1 else tuple(pixel)
    328 

~/work/develop/env/lib/python3.9/site-packages/astropy/utils/decorators.py in wrapper(*args, **kwargs)
    534                     warnings.warn(message, warning_type, stacklevel=2)
    535 
--> 536             return function(*args, **kwargs)
    537 
    538         return wrapper

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in all_world2pix(self, tolerance, maxiter, adaptive, detect_divergence, quiet, *args, **kwargs)
   1886             raise ValueError("No basic WCS settings were created.")
   1887 
-> 1888         return self._array_converter(
   1889             lambda *args, **kwargs:
   1890             self._all_world2pix(

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in _array_converter(self, func, sky, ra_dec_order, *args)
   1335                     "a 1-D array for each axis, followed by an origin.")
   1336 
-> 1337             return _return_list_of_arrays(axes, origin)
   1338 
   1339         raise TypeError(

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in _return_list_of_arrays(axes, origin)
   1289             if ra_dec_order and sky == 'input':
   1290                 xy = self._denormalize_sky(xy)
-> 1291             output = func(xy, origin)
   1292             if ra_dec_order and sky == 'output':
   1293                 output = self._normalize_sky(output)

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in <lambda>(*args, **kwargs)
   1888         return self._array_converter(
   1889             lambda *args, **kwargs:
-> 1890             self._all_world2pix(
   1891                 *args, tolerance=tolerance, maxiter=maxiter,
   1892                 adaptive=adaptive, detect_divergence=detect_divergence,

~/work/develop/env/lib/python3.9/site-packages/astropy/wcs/wcs.py in _all_world2pix(self, world, origin, tolerance, maxiter, adaptive, detect_divergence, quiet)
   1869                     slow_conv=ind, divergent=None)
   1870             else:
-> 1871                 raise NoConvergence(
   1872                     "'WCS.all_world2pix' failed to "
   1873                     "converge to the requested accuracy.\n"

NoConvergence: 'WCS.all_world2pix' failed to converge to the requested accuracy.
After 20 iterations, the solution is diverging at least for one input point.
```

### Steps to Reproduce
<!-- Ideally a code example could be provided so we can run it ourselves. -->
<!-- If you are pasting code, use triple backticks (```) around
your code snippet. -->
<!-- If necessary, sanitize your screen output to be pasted so you do not
reveal secrets like tokens and passwords. -->

Here is the code to reproduce the problem:
```
from astropy.wcs import WCS, Sip
import numpy as np
import matplotlib.pyplot as plt

wcs = WCS(naxis=2)
a = [[ 0.00000000e+00,  0.00000000e+00,  6.77532513e-07,
        -1.76632141e-10],
       [ 0.00000000e+00,  9.49130161e-06, -1.50614321e-07,
         0.00000000e+00],
       [ 7.37260409e-06,  2.07020239e-09,  0.00000000e+00,
         0.00000000e+00],
       [-1.20116753e-07,  0.00000000e+00,  0.00000000e+00,
         0.00000000e+00]]
b = [[ 0.00000000e+00,  0.00000000e+00,  1.34606617e-05,
        -1.41919055e-07],
       [ 0.00000000e+00,  5.85158316e-06, -1.10382462e-09,
         0.00000000e+00],
       [ 1.06306407e-05, -1.36469008e-07,  0.00000000e+00,
         0.00000000e+00],
       [ 3.27391123e-09,  0.00000000e+00,  0.00000000e+00,
         0.00000000e+00]]
crpix = [1221.87375165,  994.90917378]
ap = bp = np.zeros((4, 4))

wcs.sip = Sip(a, b, ap, bp, crpix)

plt.subplot(projection=wcs)
plt.imshow(np.zeros((1944, 2592)))
plt.grid(color='white', ls='solid')
```

### System Details
<!-- Even if you do not think this is necessary, it is useful information for the maintainers.
Please run the following snippet and paste the output below:
import platform; print(platform.platform())
import sys; print("Python", sys.version)
import numpy; print("Numpy", numpy.__version__)
import astropy; print("astropy", astropy.__version__)
import scipy; print("Scipy", scipy.__version__)
import matplotlib; print("Matplotlib", matplotlib.__version__)
-->
```
>>> import platform; print(platform.platform())
Linux-5.11.10-arch1-1-x86_64-with-glibc2.33
>>> import sys; print("Python", sys.version)
Python 3.9.2 (default, Feb 20 2021, 18:40:11) 
[GCC 10.2.0]
>>> import numpy; print("Numpy", numpy.__version__)
Numpy 1.20.2
>>> import astropy; print("astropy", astropy.__version__)
astropy 4.3.dev690+g7811614f8
>>> import scipy; print("Scipy", scipy.__version__)
Scipy 1.6.1
>>> import matplotlib; print("Matplotlib", matplotlib.__version__)
Matplotlib 3.3.4
```

## Issue Discussion Hints
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/master/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

If you feel that this issue has not been responded to in a timely manner, please leave a comment mentioning our software support engineer @embray, or send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
You could also directly call

```python
pixel = self.all_world2pix(*world_arrays, 0)
pixel = pixel[0] if self.pixel_n_dim == 1 else tuple(pixel)
```

without patching any code.  But I wonder if the WCSAPI methods shouldn't allow passing additional keyword args to the underlying WCS methods (like `all_world2pix` in this case).  @astrofrog is the one who first introduces this API I think.
I think the cleanest fix here would be that really the FITS WCS APE14 wrapper should call all_* in a way that only emits a warning not raises an exception (since by design we can't pass kwargs through). It's then easy for users to ignore the warning if they really want.

@Cadair any thoughts?

Is this technically a bug?
> the FITS WCS APE14 wrapper should call all_* in a way that only emits a warning

This is probably the best solution. I certainly can't think of a better one.

On keyword arguments to WCSAPI, if we did allow that we would have to mandate that all implementations allowed `**kwargs` to accept and ignore all unknown kwargs so that you didn't make it implementation specific when calling the method, which is a big ugly.
> Is this technically a bug?

I would say so yes.
> > the FITS WCS APE14 wrapper should call all_* in a way that only emits a warning
> 
> This is probably the best solution. I certainly can't think of a better one.
> 

That solution would be also fine for me.


@karlwessel , are you interested in submitting a patch for this? 😸 
In principle yes, but at the moment I really can't say.

Which places would this affect? Only all calls to `all_*` in `wcsapi/fitswcs.py`?
Yes I think that's right
For what it is worth, my comment is about the issues with the example. I think so far the history of `all_pix2world` shows that it is a very stable algorithm that converges for all "real" astronomical images. So, I wanted to learn about this failure. [NOTE: This does not mean that you should not catch exceptions in `pixel_to_world()` if you wish so.]

There are several issues with the example:
1. Because `CTYPE` is not set, essentially the projection algorithm is linear, that is, intermediate physical coordinates are the world coordinates.
2. SIP standard assumes that polynomials share the same CRPIX with the WCS. Here, CRPIX of the `Wcsprm` is `[0, 0]` while the CRPIX of the SIP is set to `[1221.87375165,  994.90917378]`
3. If you run `wcs.all_pix2world(1, 1, 1)` you will get `[421.5126801, 374.13077558]` for world coordinates (and at CRPIX you will get CRVAL which is 0). This is in degrees. You can see that from the center pixel (CRPIX) to the corner of the image you are circling the celestial sphere many times (well, at least once; I did not check the other corners).

In summary, yes `all_world2pix` can fail but it does not imply that there is a bug in it. This example simply contains large distortions (like mapping `(1, 1) -> [421, 374]`) that cannot be handled with the currently implemented algorithm but I am not sure there is another algorithm that could do better.

With regard to throwing or not an exception... that's tough. On one hand, for those who are interested in correctness of the values, it is better to know that the algorithm failed and one cannot trust returned values. For plotting, this may be an issue and one would prefer to just get, maybe, the linear approximation. My personal preference is for exceptions because they can be caught and dealt with by the caller.
The example is a minimal version of our real WCS whichs nonlinear distortion is taken from a checkerboard image and it fits it quit well:
![fitteddistortion](https://user-images.githubusercontent.com/64231/116892995-be892a00-ac30-11eb-826f-99e3635af1fa.png)

The WCS was fitted with `fit_wcs_from_points` using an artificial very small 'RA/DEC-TAN' grid so that it is almost linear.

I guess the Problem is that the camera really has a huge distortion which just isn't fitable with a polynomial. Nevertheless it still is a real camera distortion, but I agree in that it probably is not worth to be considered a bug in the `all_world2pix` method.
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/master/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

If you feel that this issue has not been responded to in a timely manner, please leave a comment mentioning our software support engineer @embray, or send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
You could also directly call

```python
pixel = self.all_world2pix(*world_arrays, 0)
pixel = pixel[0] if self.pixel_n_dim == 1 else tuple(pixel)
```

without patching any code.  But I wonder if the WCSAPI methods shouldn't allow passing additional keyword args to the underlying WCS methods (like `all_world2pix` in this case).  @astrofrog is the one who first introduces this API I think.
I think the cleanest fix here would be that really the FITS WCS APE14 wrapper should call all_* in a way that only emits a warning not raises an exception (since by design we can't pass kwargs through). It's then easy for users to ignore the warning if they really want.

@Cadair any thoughts?

Is this technically a bug?
> the FITS WCS APE14 wrapper should call all_* in a way that only emits a warning

This is probably the best solution. I certainly can't think of a better one.

On keyword arguments to WCSAPI, if we did allow that we would have to mandate that all implementations allowed `**kwargs` to accept and ignore all unknown kwargs so that you didn't make it implementation specific when calling the method, which is a big ugly.
> Is this technically a bug?

I would say so yes.
> > the FITS WCS APE14 wrapper should call all_* in a way that only emits a warning
> 
> This is probably the best solution. I certainly can't think of a better one.
> 

That solution would be also fine for me.


@karlwessel , are you interested in submitting a patch for this? 😸 
In principle yes, but at the moment I really can't say.

Which places would this affect? Only all calls to `all_*` in `wcsapi/fitswcs.py`?
Yes I think that's right
For what it is worth, my comment is about the issues with the example. I think so far the history of `all_pix2world` shows that it is a very stable algorithm that converges for all "real" astronomical images. So, I wanted to learn about this failure. [NOTE: This does not mean that you should not catch exceptions in `pixel_to_world()` if you wish so.]

There are several issues with the example:
1. Because `CTYPE` is not set, essentially the projection algorithm is linear, that is, intermediate physical coordinates are the world coordinates.
2. SIP standard assumes that polynomials share the same CRPIX with the WCS. Here, CRPIX of the `Wcsprm` is `[0, 0]` while the CRPIX of the SIP is set to `[1221.87375165,  994.90917378]`
3. If you run `wcs.all_pix2world(1, 1, 1)` you will get `[421.5126801, 374.13077558]` for world coordinates (and at CRPIX you will get CRVAL which is 0). This is in degrees. You can see that from the center pixel (CRPIX) to the corner of the image you are circling the celestial sphere many times (well, at least once; I did not check the other corners).

In summary, yes `all_world2pix` can fail but it does not imply that there is a bug in it. This example simply contains large distortions (like mapping `(1, 1) -> [421, 374]`) that cannot be handled with the currently implemented algorithm but I am not sure there is another algorithm that could do better.

With regard to throwing or not an exception... that's tough. On one hand, for those who are interested in correctness of the values, it is better to know that the algorithm failed and one cannot trust returned values. For plotting, this may be an issue and one would prefer to just get, maybe, the linear approximation. My personal preference is for exceptions because they can be caught and dealt with by the caller.
The example is a minimal version of our real WCS whichs nonlinear distortion is taken from a checkerboard image and it fits it quit well:
![fitteddistortion](https://user-images.githubusercontent.com/64231/116892995-be892a00-ac30-11eb-826f-99e3635af1fa.png)

The WCS was fitted with `fit_wcs_from_points` using an artificial very small 'RA/DEC-TAN' grid so that it is almost linear.

I guess the Problem is that the camera really has a huge distortion which just isn't fitable with a polynomial. Nevertheless it still is a real camera distortion, but I agree in that it probably is not worth to be considered a bug in the `all_world2pix` method.

## Failing Tests That Should Pass
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_non_convergence_warning`

## Existing Passing Tests To Preserve
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_empty`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_simple_celestial`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values[tai]`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values[tcb]`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values[tcg]`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values[tdb]`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values[tt]`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values[ut1]`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values[utc]`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values[local]`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values_gps`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values_deprecated`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_values_time`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_high_precision`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_location_geodetic`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_location_geocentric`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_location_geocenter`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_location_missing`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_location_incomplete`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_location_unsupported`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_time_1d_unsupported_ctype`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_unrecognized_unit`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_distortion_correlations`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_custom_ctype_to_ucd_mappings`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_caching_components_and_classes`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_sub_wcsapi_attributes`
- `astropy/wcs/wcsapi/tests/test_fitswcs.py::test_phys_type_polarization`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
