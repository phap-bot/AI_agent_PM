# SWE-bench Issue: astropy__astropy-13572

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13572
- Base Commit: 986123f73ce94d4511f453dbdd4470c72f47402a
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-08-25T03:49:28Z
- Version: 5.0

## Issue Title
Problem in function nutation_matrix in earth_orientation.py

## Problem Statement
Problem in function nutation_matrix in earth_orientation.py
Recently, when I try to call function nutation_matrix in astropy.coordinates.earth_orientation, error occurs with following info:

astropy.units.core.UnitTypeError: Angle instances require units equivalent to 'rad', so cannot set it to '0'.

Then, I checked the code of def nutation_matrix as follows:
```
def nutation_matrix(epoch):
    """
    Nutation matrix generated from nutation components.

    Matrix converts from mean coordinate to true coordinate as
    r_true = M * r_mean
    """
    # TODO: implement higher precision 2006/2000A model if requested/needed
    epsa, dpsi, deps = nutation_components2000B(epoch.jd)  # all in radians

    return matrix_product(rotation_matrix(-(epsa + deps), 'x', False),
                          rotation_matrix(-dpsi, 'z', False),
                          rotation_matrix(epsa, 'x', False))
```
In its return sentence, the third argument of 'rotation_matrix' should be units.radian, rather than False.

Any response?

## Issue Discussion Hints
`git blame` points out that @eteq or @mhvk might be able to clarify.
Yes, logically, those `False` ones should be replaced by `u.radian` (or, perhaps better, `nutation_components200B` should just return values in angular units, and the `False` can be removed altogether).

What I am surprised about, though, is that this particular routine apparently is neither used nor tested. Isn't all this stuff in `erfa`? Indeed, more generally, could we make these routines wrappers around `erfa`?

@zhutinglei - separately, it might help to understand why you needed the nutation? Are we missing a coordinate transform?
Thanks for the quick response @mhvk . 

First, answer your question on why I need the nutation. I am trying to get the position velocity vector of an observatory (of type `EarthLocation`), in J2000.0 Geocentric Celestial Reference Frame (i.e. mean equinox, mean equator at epoch J2000.0). Although the class `EarthLocation` provide  `get_gcrs_posvel()`, I failed to find the document that describes it. As a result, I decided to write my own code to do this, and then I need the precession and nutation matrix. Another minor cause is that sometimes I do not need polar motion (it is too small compared with precision I need), but it seems that I cannot choose to close polar motion when I call `get_gcrs_posvel()`. Hence I need to code my own transformation with only precession and nutation. Is there any documentation helpful?

In addition, actually, I also need TEME (true equator, mean equinox) coordinate system, which is used by Two-Line Element (TLE). Currently, I simply use the rotation matrix Rz(-\mu-\Delta\mu), where \mu and \Delta\mu are precession and nutation angle in right ascension, to transform vectors from TOD (true of date, i.e. true equator, true equinox) frame to TEME frame. It might help if you add the coordinate transform related with TEME.
@zhutinglei - the little documentation we have is indeed sparse [1], [2]; where exactly would it help you to be clearer about what happens?

On your actual problem, I *think* `get_gcrs_posvel` is all you should need if you just want x, y, z - you can then use the result to define a frame in which an object is observed to pass on `obsgeopos` and `obsgeovel`.  If you want an actual J2000 GCRS coordinate, the standard route would be via `ITRS`:
```
el = EarthLocation(...)
gcrs = el.get_itrs().transform_to(GCRS)
gcrs
# GCRS Coordinate (obstime=J2000.000, obsgeoloc=( 0.,  0.,  0.) m, obsgeovel=( 0.,  0.,  0.) m / s): (ra, dec, distance) in (deg, deg, m)
#     ( 325.46088987,  29.83393221,  6372824.42030426)>
gcrs.cartesian
# <CartesianRepresentation (x, y, z) in m
#     ( 4553829.11686306, -3134338.92680929,  3170402.33382524)>
```
This is the same as the position from `get_gcrs_posvel`:
```
el.get_gcrs_posvel(obstime=Time('J2000'))
# (<CartesianRepresentation (x, y, z) in m
#      ( 4553829.11686306, -3134338.92680929,  3170402.33382524)>,
#  <CartesianRepresentation (x, y, z) in m / s
#      ( 228.55962584,  332.07049505,  0.)>)
```

On the remainder: I'm confused about what you mean by "cannot choose to close polar motion" - what exactly would you hope to do?

Finally, on `TEME`, I'll admit I'm not sure what this is. I'm cc'ing @eteq and @StuartLittlefair, who might be more familiar (they may also be able to correct me if I'm wrong above). If it is a system that is regularly used, then ideally we'd support it. (@eteq - see also my more general [question](https://github.com/astropy/astropy/issues/6583#issuecomment-331180713) about why we have a nutation routine that is neither used nor tested!)

[1] http://docs.astropy.org/en/latest/api/astropy.coordinates.EarthLocation.html#astropy.coordinates.EarthLocation.get_gcrs_posvel
[2] http://docs.astropy.org/en/latest/api/astropy.coordinates.GCRS.html#astropy.coordinates.GCRS
@zhutinglei 

Thanks for raising this issue. Depending on the precision you need @mhvk's code may be fine. ```get_gcrs_posvel``` returns Earth-centred coordinates aligned with the ```GCRF```/```ICRF``` reference frames. 

What you seem to want is an Earth-centred equivalent to FK5 (i.e a mean equatorial frame with J2000) epoch. That does not exist in astropy, but the GCRS coordinate returned by ```get_gcrs_posvel``` is consistent with it to [around 80 mas](https://www.iers.org/IERS/EN/Science/ICRS/ICRS.html).

With respect to TEME; I am only vaguely familiar with it. I understand it's an Earth-centred coordinate with the z-axis aligned to the true direction of the pole, but the x-axis aligned with the mean equinox? It does not yet exist in astropy, but @eteq has a nice tutorial for adding new frames [here](http://docs.astropy.org/en/stable/generated/examples/coordinates/plot_sgr-coordinate-frame.html), which you could follow if you need it.

On the other hand, if you simply want an easy way to work with TLE files, I note that @brandon-rhodes [Skyfield](http://rhodesmill.org/skyfield/earth-satellites.html) package is already setup to read and perform calculations with TLE files...
Oops, we never got around to actually fixing this - and probably deprecate in favour of some erfa routine - and now we've got a duplicate - #10680 

p.s. For anyone who happens to hit this issue and needs `TEME` - it is now available, see https://docs.astropy.org/en/latest/api/astropy.coordinates.builtin_frames.TEME.html#astropy.coordinates.builtin_frames.TEME

## Failing Tests That Should Pass
- `astropy/coordinates/tests/test_earth_orientation.py::test_nutation_matrix`

## Existing Passing Tests To Preserve
- `astropy/coordinates/tests/test_earth_orientation.py::test_obliquity[2006-23.43633313804873]`
- `astropy/coordinates/tests/test_earth_orientation.py::test_obliquity[2000-23.43634457995851]`
- `astropy/coordinates/tests/test_earth_orientation.py::test_obliquity[1980-23.436346167704045]`
- `astropy/coordinates/tests/test_earth_orientation.py::test_precession_matrix_Capitaine`
- `astropy/coordinates/tests/test_earth_orientation.py::test_nutation_components2000B`
- `astropy/coordinates/tests/test_sky_coord.py::test_is_transformable_to_str_input`
- `astropy/coordinates/tests/test_sky_coord.py::test_transform_to`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-ICRS-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK4-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-FK5-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[ICRS-Galactic-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-ICRS-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK4-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-FK5-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK4-Galactic-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-ICRS-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK4-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-FK5-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[FK5-Galactic-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-ICRS-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK4-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-FK5-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-None-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-None-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-None-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-None-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-None-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-None-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-None-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-None-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-J1975.0-None-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-J1975.0-None-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-J1975.0-J1975.0-None-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-J1975.0-J1975.0-None-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-J1975.0-None-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-J1975.0-None-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-J1975.0-J1975.0-J1980.0-None]`
- `astropy/coordinates/tests/test_sky_coord.py::test_round_tripping[Galactic-Galactic-J1975.0-J1975.0-J1980.0-J1980.0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_coord_init_string`
- `astropy/coordinates/tests/test_sky_coord.py::test_coord_init_unit`
- `astropy/coordinates/tests/test_sky_coord.py::test_coord_init_list`
- `astropy/coordinates/tests/test_sky_coord.py::test_coord_init_array`
- `astropy/coordinates/tests/test_sky_coord.py::test_coord_init_representation`
- `astropy/coordinates/tests/test_sky_coord.py::test_frame_init`
- `astropy/coordinates/tests/test_sky_coord.py::test_equal`
- `astropy/coordinates/tests/test_sky_coord.py::test_equal_different_type`
- `astropy/coordinates/tests/test_sky_coord.py::test_equal_exceptions`
- `astropy/coordinates/tests/test_sky_coord.py::test_attr_inheritance`
- `astropy/coordinates/tests/test_sky_coord.py::test_setitem_no_velocity[fk4]`
- `astropy/coordinates/tests/test_sky_coord.py::test_setitem_no_velocity[fk5]`
- `astropy/coordinates/tests/test_sky_coord.py::test_setitem_no_velocity[icrs]`
- `astropy/coordinates/tests/test_sky_coord.py::test_setitem_initially_broadcast`
- `astropy/coordinates/tests/test_sky_coord.py::test_setitem_velocities`
- `astropy/coordinates/tests/test_sky_coord.py::test_setitem_exceptions`
- `astropy/coordinates/tests/test_sky_coord.py::test_insert`
- `astropy/coordinates/tests/test_sky_coord.py::test_insert_exceptions`
- `astropy/coordinates/tests/test_sky_coord.py::test_attr_conflicts`
- `astropy/coordinates/tests/test_sky_coord.py::test_frame_attr_getattr`
- `astropy/coordinates/tests/test_sky_coord.py::test_to_string`
- `astropy/coordinates/tests/test_sky_coord.py::test_seps[SkyCoord]`
- `astropy/coordinates/tests/test_sky_coord.py::test_seps[ICRS]`
- `astropy/coordinates/tests/test_sky_coord.py::test_repr`
- `astropy/coordinates/tests/test_sky_coord.py::test_ops`
- `astropy/coordinates/tests/test_sky_coord.py::test_none_transform`
- `astropy/coordinates/tests/test_sky_coord.py::test_position_angle`
- `astropy/coordinates/tests/test_sky_coord.py::test_position_angle_directly`
- `astropy/coordinates/tests/test_sky_coord.py::test_sep_pa_equivalence`
- `astropy/coordinates/tests/test_sky_coord.py::test_directional_offset_by`
- `astropy/coordinates/tests/test_sky_coord.py::test_table_to_coord`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[spherical-unit10-unit20-unit30-Latitude-l-b-distance-spherical-c10-c20-c30]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[spherical-unit11-unit21-unit31-Latitude-l-b-distance-spherical-c11-c21-c31]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[spherical-unit12-unit22-unit32-Latitude-l-b-distance-spherical-c12-c22-c32]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[spherical-unit13-unit23-unit33-Latitude-l-b-distance-spherical-c13-c23-c33]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[spherical-unit14-unit24-unit34-Latitude-l-b-distance-SphericalRepresentation-c14-c24-c34]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[spherical-unit15-unit25-unit35-Latitude-l-b-distance-SphericalRepresentation-c15-c25-c35]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[spherical-unit16-unit26-unit36-Latitude-l-b-distance-SphericalRepresentation-c16-c26-c36]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[spherical-unit17-unit27-unit37-Latitude-l-b-distance-SphericalRepresentation-c17-c27-c37]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[physicsspherical-unit18-unit28-unit38-Angle-phi-theta-r-physicsspherical-c18-c28-c38]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[physicsspherical-unit19-unit29-unit39-Angle-phi-theta-r-physicsspherical-c19-c29-c39]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[physicsspherical-unit110-unit210-unit310-Angle-phi-theta-r-physicsspherical-c110-c210-c310]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[physicsspherical-unit111-unit211-unit311-Angle-phi-theta-r-physicsspherical-c111-c211-c311]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[physicsspherical-unit112-unit212-unit312-Angle-phi-theta-r-PhysicsSphericalRepresentation-c112-c212-c312]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[physicsspherical-unit113-unit213-unit313-Angle-phi-theta-r-PhysicsSphericalRepresentation-c113-c213-c313]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[physicsspherical-unit114-unit214-unit314-Angle-phi-theta-r-PhysicsSphericalRepresentation-c114-c214-c314]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[physicsspherical-unit115-unit215-unit315-Angle-phi-theta-r-PhysicsSphericalRepresentation-c115-c215-c315]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cartesian-unit116-unit216-unit316-Quantity-u-v-w-cartesian-c116-c216-c316]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cartesian-unit117-unit217-unit317-Quantity-u-v-w-cartesian-c117-c217-c317]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cartesian-unit118-unit218-unit318-Quantity-u-v-w-cartesian-c118-c218-c318]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cartesian-unit119-unit219-unit319-Quantity-u-v-w-cartesian-c119-c219-c319]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cartesian-unit120-unit220-unit320-Quantity-u-v-w-CartesianRepresentation-c120-c220-c320]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cartesian-unit121-unit221-unit321-Quantity-u-v-w-CartesianRepresentation-c121-c221-c321]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cartesian-unit122-unit222-unit322-Quantity-u-v-w-CartesianRepresentation-c122-c222-c322]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cartesian-unit123-unit223-unit323-Quantity-u-v-w-CartesianRepresentation-c123-c223-c323]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cylindrical-unit124-unit224-unit324-Angle-rho-phi-z-cylindrical-c124-c224-c324]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cylindrical-unit125-unit225-unit325-Angle-rho-phi-z-cylindrical-c125-c225-c325]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cylindrical-unit126-unit226-unit326-Angle-rho-phi-z-cylindrical-c126-c226-c326]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cylindrical-unit127-unit227-unit327-Angle-rho-phi-z-cylindrical-c127-c227-c327]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cylindrical-unit128-unit228-unit328-Angle-rho-phi-z-CylindricalRepresentation-c128-c228-c328]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cylindrical-unit129-unit229-unit329-Angle-rho-phi-z-CylindricalRepresentation-c129-c229-c329]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cylindrical-unit130-unit230-unit330-Angle-rho-phi-z-CylindricalRepresentation-c130-c230-c330]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_three_components[cylindrical-unit131-unit231-unit331-Angle-rho-phi-z-CylindricalRepresentation-c131-c231-c331]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[spherical-unit10-unit20-unit30-Latitude-l-b-distance-spherical-c10-c20-c30]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[spherical-unit11-unit21-unit31-Latitude-l-b-distance-spherical-c11-c21-c31]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[spherical-unit12-unit22-unit32-Latitude-l-b-distance-spherical-c12-c22-c32]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[spherical-unit13-unit23-unit33-Latitude-l-b-distance-spherical-c13-c23-c33]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[spherical-unit14-unit24-unit34-Latitude-l-b-distance-SphericalRepresentation-c14-c24-c34]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[spherical-unit15-unit25-unit35-Latitude-l-b-distance-SphericalRepresentation-c15-c25-c35]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[spherical-unit16-unit26-unit36-Latitude-l-b-distance-SphericalRepresentation-c16-c26-c36]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[spherical-unit17-unit27-unit37-Latitude-l-b-distance-SphericalRepresentation-c17-c27-c37]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[unitspherical-unit18-unit28-None-Latitude-l-b-None-unitspherical-c18-c28-c38]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[unitspherical-unit19-unit29-None-Latitude-l-b-None-unitspherical-c19-c29-c39]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[unitspherical-unit110-unit210-None-Latitude-l-b-None-unitspherical-c110-c210-c310]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[unitspherical-unit111-unit211-None-Latitude-l-b-None-unitspherical-c111-c211-c311]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[unitspherical-unit112-unit212-None-Latitude-l-b-None-UnitSphericalRepresentation-c112-c212-c312]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[unitspherical-unit113-unit213-None-Latitude-l-b-None-UnitSphericalRepresentation-c113-c213-c313]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[unitspherical-unit114-unit214-None-Latitude-l-b-None-UnitSphericalRepresentation-c114-c214-c314]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_spherical_two_components[unitspherical-unit115-unit215-None-Latitude-l-b-None-UnitSphericalRepresentation-c115-c215-c315]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[spherical-unit10-unit20-unit30-Latitude-l-b-distance-spherical-c10-c20-c30]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[spherical-unit11-unit21-unit31-Latitude-l-b-distance-spherical-c11-c21-c31]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[spherical-unit12-unit22-unit32-Latitude-l-b-distance-spherical-c12-c22-c32]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[spherical-unit13-unit23-unit33-Latitude-l-b-distance-spherical-c13-c23-c33]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[spherical-unit14-unit24-unit34-Latitude-l-b-distance-SphericalRepresentation-c14-c24-c34]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[spherical-unit15-unit25-unit35-Latitude-l-b-distance-SphericalRepresentation-c15-c25-c35]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[spherical-unit16-unit26-unit36-Latitude-l-b-distance-SphericalRepresentation-c16-c26-c36]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[spherical-unit17-unit27-unit37-Latitude-l-b-distance-SphericalRepresentation-c17-c27-c37]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[physicsspherical-unit18-unit28-unit38-Angle-phi-theta-r-physicsspherical-c18-c28-c38]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[physicsspherical-unit19-unit29-unit39-Angle-phi-theta-r-physicsspherical-c19-c29-c39]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[physicsspherical-unit110-unit210-unit310-Angle-phi-theta-r-physicsspherical-c110-c210-c310]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[physicsspherical-unit111-unit211-unit311-Angle-phi-theta-r-physicsspherical-c111-c211-c311]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[physicsspherical-unit112-unit212-unit312-Angle-phi-theta-r-PhysicsSphericalRepresentation-c112-c212-c312]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[physicsspherical-unit113-unit213-unit313-Angle-phi-theta-r-PhysicsSphericalRepresentation-c113-c213-c313]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[physicsspherical-unit114-unit214-unit314-Angle-phi-theta-r-PhysicsSphericalRepresentation-c114-c214-c314]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[physicsspherical-unit115-unit215-unit315-Angle-phi-theta-r-PhysicsSphericalRepresentation-c115-c215-c315]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cartesian-unit116-unit216-unit316-Quantity-u-v-w-cartesian-c116-c216-c316]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cartesian-unit117-unit217-unit317-Quantity-u-v-w-cartesian-c117-c217-c317]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cartesian-unit118-unit218-unit318-Quantity-u-v-w-cartesian-c118-c218-c318]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cartesian-unit119-unit219-unit319-Quantity-u-v-w-cartesian-c119-c219-c319]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cartesian-unit120-unit220-unit320-Quantity-u-v-w-CartesianRepresentation-c120-c220-c320]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cartesian-unit121-unit221-unit321-Quantity-u-v-w-CartesianRepresentation-c121-c221-c321]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cartesian-unit122-unit222-unit322-Quantity-u-v-w-CartesianRepresentation-c122-c222-c322]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cartesian-unit123-unit223-unit323-Quantity-u-v-w-CartesianRepresentation-c123-c223-c323]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cylindrical-unit124-unit224-unit324-Angle-rho-phi-z-cylindrical-c124-c224-c324]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cylindrical-unit125-unit225-unit325-Angle-rho-phi-z-cylindrical-c125-c225-c325]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cylindrical-unit126-unit226-unit326-Angle-rho-phi-z-cylindrical-c126-c226-c326]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cylindrical-unit127-unit227-unit327-Angle-rho-phi-z-cylindrical-c127-c227-c327]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cylindrical-unit128-unit228-unit328-Angle-rho-phi-z-CylindricalRepresentation-c128-c228-c328]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cylindrical-unit129-unit229-unit329-Angle-rho-phi-z-CylindricalRepresentation-c129-c229-c329]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cylindrical-unit130-unit230-unit330-Angle-rho-phi-z-CylindricalRepresentation-c130-c230-c330]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_three_components[cylindrical-unit131-unit231-unit331-Angle-rho-phi-z-CylindricalRepresentation-c131-c231-c331]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[spherical-unit10-unit20-unit30-Latitude-l-b-distance-spherical-c10-c20-c30]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[spherical-unit11-unit21-unit31-Latitude-l-b-distance-spherical-c11-c21-c31]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[spherical-unit12-unit22-unit32-Latitude-l-b-distance-spherical-c12-c22-c32]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[spherical-unit13-unit23-unit33-Latitude-l-b-distance-spherical-c13-c23-c33]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[spherical-unit14-unit24-unit34-Latitude-l-b-distance-SphericalRepresentation-c14-c24-c34]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[spherical-unit15-unit25-unit35-Latitude-l-b-distance-SphericalRepresentation-c15-c25-c35]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[spherical-unit16-unit26-unit36-Latitude-l-b-distance-SphericalRepresentation-c16-c26-c36]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[spherical-unit17-unit27-unit37-Latitude-l-b-distance-SphericalRepresentation-c17-c27-c37]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[unitspherical-unit18-unit28-None-Latitude-l-b-None-unitspherical-c18-c28-c38]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[unitspherical-unit19-unit29-None-Latitude-l-b-None-unitspherical-c19-c29-c39]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[unitspherical-unit110-unit210-None-Latitude-l-b-None-unitspherical-c110-c210-c310]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[unitspherical-unit111-unit211-None-Latitude-l-b-None-unitspherical-c111-c211-c311]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[unitspherical-unit112-unit212-None-Latitude-l-b-None-UnitSphericalRepresentation-c112-c212-c312]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[unitspherical-unit113-unit213-None-Latitude-l-b-None-UnitSphericalRepresentation-c113-c213-c313]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[unitspherical-unit114-unit214-None-Latitude-l-b-None-UnitSphericalRepresentation-c114-c214-c314]`
- `astropy/coordinates/tests/test_sky_coord.py::test_galactic_spherical_two_components[unitspherical-unit115-unit215-None-Latitude-l-b-None-UnitSphericalRepresentation-c115-c215-c315]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_coordinate_input[spherical-unit10-unit20-unit30-Latitude-l-b-distance]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_coordinate_input[physicsspherical-unit11-unit21-unit31-Angle-phi-theta-r]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_coordinate_input[cartesian-unit12-unit22-unit32-Quantity-u-v-w]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_coordinate_input[cylindrical-unit13-unit23-unit33-Angle-rho-phi-z]`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_string_coordinate_input`
- `astropy/coordinates/tests/test_sky_coord.py::test_units`
- `astropy/coordinates/tests/test_sky_coord.py::test_nodata_failure`
- `astropy/coordinates/tests/test_sky_coord.py::test_wcs_methods[wcs-0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_wcs_methods[all-0]`
- `astropy/coordinates/tests/test_sky_coord.py::test_wcs_methods[all-1]`
- `astropy/coordinates/tests/test_sky_coord.py::test_frame_attr_transform_inherit`
- `astropy/coordinates/tests/test_sky_coord.py::test_deepcopy`
- `astropy/coordinates/tests/test_sky_coord.py::test_no_copy`
- `astropy/coordinates/tests/test_sky_coord.py::test_immutable`
- `astropy/coordinates/tests/test_sky_coord.py::test_init_with_frame_instance_keyword`
- `astropy/coordinates/tests/test_sky_coord.py::test_guess_from_table`
- `astropy/coordinates/tests/test_sky_coord.py::test_skycoord_list_creation`
- `astropy/coordinates/tests/test_sky_coord.py::test_nd_skycoord_to_string`
- `astropy/coordinates/tests/test_sky_coord.py::test_equiv_skycoord`
- `astropy/coordinates/tests/test_sky_coord.py::test_equiv_skycoord_with_extra_attrs`
- `astropy/coordinates/tests/test_sky_coord.py::test_constellations`
- `astropy/coordinates/tests/test_sky_coord.py::test_getitem_representation`
- `astropy/coordinates/tests/test_sky_coord.py::test_spherical_offsets_to_api`
- `astropy/coordinates/tests/test_sky_coord.py::test_spherical_offsets_roundtrip[comparison_data0-icrs]`
- `astropy/coordinates/tests/test_sky_coord.py::test_spherical_offsets_roundtrip[comparison_data0-galactic]`
- `astropy/coordinates/tests/test_sky_coord.py::test_spherical_offsets_roundtrip[comparison_data1-icrs]`
- `astropy/coordinates/tests/test_sky_coord.py::test_spherical_offsets_roundtrip[comparison_data1-galactic]`
- `astropy/coordinates/tests/test_sky_coord.py::test_spherical_offsets_roundtrip[comparison_data2-icrs]`
- `astropy/coordinates/tests/test_sky_coord.py::test_spherical_offsets_roundtrip[comparison_data2-galactic]`
- `astropy/coordinates/tests/test_sky_coord.py::test_frame_attr_changes`
- `astropy/coordinates/tests/test_sky_coord.py::test_cache_clear_sc`
- `astropy/coordinates/tests/test_sky_coord.py::test_set_attribute_exceptions`
- `astropy/coordinates/tests/test_sky_coord.py::test_extra_attributes`
- `astropy/coordinates/tests/test_sky_coord.py::test_apply_space_motion`
- `astropy/coordinates/tests/test_sky_coord.py::test_custom_frame_skycoord`
- `astropy/coordinates/tests/test_sky_coord.py::test_user_friendly_pm_error`
- `astropy/coordinates/tests/test_sky_coord.py::test_contained_by`
- `astropy/coordinates/tests/test_sky_coord.py::test_none_differential_type`
- `astropy/coordinates/tests/test_sky_coord.py::test_multiple_aliases`
- `astropy/coordinates/tests/test_sky_coord.py::test_passing_inconsistent_coordinates_and_units_raises_helpful_error[kwargs0-Unit`
- `astropy/coordinates/tests/test_sky_coord.py::test_passing_inconsistent_coordinates_and_units_raises_helpful_error[kwargs1-Unit`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
