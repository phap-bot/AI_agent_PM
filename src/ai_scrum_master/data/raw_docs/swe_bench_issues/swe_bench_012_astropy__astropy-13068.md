# SWE-bench Issue: astropy__astropy-13068

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13068
- Base Commit: 2288ecd4e9c4d3722d72b7f4a6555a34f4f04fc7
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-04-05T19:35:35Z
- Version: 5.0

## Issue Title
Time from astropy.time not precise

## Problem Statement
Time from astropy.time not precise
Hello,

I encounter difficulties with Time. I'm working on a package to perform photometry and occultation. 

For this last case, data need times values accurately estimated. Of course, data coming from different camera will will have different time format in the header.

to manage this without passing long time to build a time parser, i decided to use Time object which do exactly what i need. The problem is, i dont arrive to make accurate conversion between different format using Time.

let's do an exemple:

```
t1 = '2022-03-24T23:13:41.390999'
t1 = Time(t1, format = 'isot', precision = len(t1.split('.')[-1]))
t2 = t1.to_value('jd')
# result is 2459663.4678401737
```
now let's do reverse

```
t2 = Time(t2, format = 'jd', precision = len(str(t2).split('.')[-1]))
t3 = t2.to_value('isot')
# result is 2022-03-24T23:13:41.0551352177
```
as you can see i don't fall back on the same value and the difference is quite high. I would like to fall back on the original one.

thank you in advance

## Issue Discussion Hints
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

GitHub issues in the Astropy repository are used to track bug reports and feature requests; If your issue poses a question about how to use Astropy, please instead raise your question in the [Astropy Discourse user forum](https://community.openastronomy.org/c/astropy/8) and close this issue.

If you feel that this issue has not been responded to in a timely manner, please leave a comment mentioning our software support engineer @embray, or send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
@mhvk will have the answer I guess, but it seems the issue comes from the use of `precision`, which probably does not do what you expect. And should be <= 9 :

> precision: int between 0 and 9 inclusive
    Decimal precision when outputting seconds as floating point.

The interesting thing is that when precision is > 9 the results are incorrect:

```
In [52]: for p in range(15):
    ...:     print(f'{p:2d}', Time(t2, format = 'jd', precision = p).to_value('isot'))
    ...: 
 0 2022-03-24T23:13:41
 1 2022-03-24T23:13:41.4
 2 2022-03-24T23:13:41.39
 3 2022-03-24T23:13:41.391
 4 2022-03-24T23:13:41.3910
 5 2022-03-24T23:13:41.39101
 6 2022-03-24T23:13:41.391012
 7 2022-03-24T23:13:41.3910118
 8 2022-03-24T23:13:41.39101177
 9 2022-03-24T23:13:41.391011775
10 2022-03-24T23:13:41.0551352177
11 2022-03-24T23:13:41.00475373422
12 2022-03-24T23:13:41.-00284414132
13 2022-03-24T23:13:41.0000514624247
14 2022-03-24T23:13:41.00000108094123
```

To get a better precision you can use `.to_value('jd', 'long')`: (and the weird results with `precision > 9` remain)

```
In [53]: t2 = t1.to_value('jd', 'long'); t2
Out[53]: 2459663.4678401735996

In [54]: for p in range(15):
    ...:     print(f'{p:2d}', Time(t2, format = 'jd', precision = p).to_value('isot'))
    ...: 
 0 2022-03-24T23:13:41
 1 2022-03-24T23:13:41.4
 2 2022-03-24T23:13:41.39
 3 2022-03-24T23:13:41.391
 4 2022-03-24T23:13:41.3910
 5 2022-03-24T23:13:41.39100
 6 2022-03-24T23:13:41.390999
 7 2022-03-24T23:13:41.3909990
 8 2022-03-24T23:13:41.39099901
 9 2022-03-24T23:13:41.390999005
10 2022-03-24T23:13:41.0551334172
11 2022-03-24T23:13:41.00475357898
12 2022-03-24T23:13:41.-00284404844
13 2022-03-24T23:13:41.0000514607441
14 2022-03-24T23:13:41.00000108090593
```
`astropy.time.Time` uses two float 64 to obtain very high precision, from the docs:

> All time manipulations and arithmetic operations are done internally using two 64-bit floats to represent time. Floating point algorithms from [1](https://docs.astropy.org/en/stable/time/index.html#id2) are used so that the [Time](https://docs.astropy.org/en/stable/api/astropy.time.Time.html#astropy.time.Time) object maintains sub-nanosecond precision over times spanning the age of the universe.

https://docs.astropy.org/en/stable/time/index.html

By doing `t1.to_value('jd')` you combine the two floats into a single float, loosing precision. However, the difference should not be 2 seconds, rather in the microsecond range.

When I leave out the precision argument or setting it to 9 for nanosecond precision, I get a difference of 12µs when going through the single jd float, which is expected:

```
from astropy.time import Time
import astropy.units as u


isot = '2022-03-24T23:13:41.390999'

t1 = Time(isot, format = 'isot', precision=9)
jd = t1.to_value('jd')
t2 = Time(jd, format='jd', precision=9)

print(f"Original:       {t1.isot}")
print(f"Converted back: {t2.isot}")
print(f"Difference:     {(t2 - t1).to(u.us):.2f}")

t3 = Time(t1.jd1, t1.jd2, format='jd', precision=9)
print(f"Using jd1+jd2:  {t3.isot}")
print(f"Difference:     {(t3 - t1).to(u.ns):.2f}")
```

prints:

```
Original:       2022-03-24T23:13:41.390999000
Converted back: 2022-03-24T23:13:41.391011775
Difference:     12.77 us
Using jd1+jd2:  2022-03-24T23:13:41.390999000
Difference:     0.00 ns
```
Thank you for your answers.

do they are a way to have access to this two floats? if i use jd tranformation it's because it's more easy for me to manipulate numbers. 
@antoinech13 See my example, it accesses `t1.jd1` and `t1.jd2`.
oh yes thank you.
Probably we should keep this open to address the issue with precsion > 9 that @saimn found?
sorry. yes indeed
Hello, I'm not familiar with this repository, but from my quick skimming it seems that using a precision outside of the range 0-9 (inclusive) is intended to trigger an exception. (see [here](https://github.com/astropy/astropy/blob/main/astropy/time/core.py#L610-L611), note that this line is part of the `TimeBase` class which `Time` inherits from). Though someone more familiar with the repository can correct me if I'm wrong.

Edit:
It seems the exception was only written for the setter and not for the case where `Time()` is initialized with the precision. Thus:
```
>>> from astropy.time import Time
>>> t1 = Time(123, fromat="jd")
>>> t1.precision = 10
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/home/brett/env/lib/python3.8/site-packages/astropy/time/core.py", line 610, in precision
    raise ValueError('precision attribute must be an int between '
ValueError: precision attribute must be an int between 0 and 9
```
produces the exception, but 
```
>>> t2 = Time(123, format="jd", precision=10)
>>> 
```
does not.

@saimn - good catch on the precision issue, this is not expected but seems to be the cause of the original problem.

This precision is just being passed straight through to ERFA, which clearly is not doing any validation on that value. It looks like giving a value > 9 actually causes a bug in the output, yikes.
FYI @antoinech13 - the `precision` argument only impacts the precision of the seconds output in string formats like `isot`. So setting the precision for a `jd` format `Time` object is generally not necessary.
@taldcroft - I looked and indeed there is no specific check in https://github.com/liberfa/erfa/blob/master/src/d2tf.c, though the comment notes:
```
**  2) The largest positive useful value for ndp is determined by the
**     size of days, the format of double on the target platform, and
**     the risk of overflowing ihmsf[3].  On a typical platform, for
**     days up to 1.0, the available floating-point precision might
**     correspond to ndp=12.  However, the practical limit is typically
**     ndp=9, set by the capacity of a 32-bit int, or ndp=4 if int is
**     only 16 bits.
```
This is actually a bit misleading, since the fraction of the second is stored in a 32-bit int, so it cannot possibly store more than 9 digits. Indeed,
```
In [31]: from erfa import d2tf

In [32]: d2tf(9, 1-2**-47)
Out[32]: (b'+', (23, 59, 59, 999999999))

In [33]: d2tf(10, 1-2**-47)
Out[33]: (b'+', (23, 59, 59, 1410065407))

In [34]: np.int32('9'*10)
Out[34]: 1410065407

In [36]: np.int32('9'*9)
Out[36]: 999999999
```
As for how to fix this, right now we do check `precision` as a property, but not on input:
```
In [42]: t = Time('J2000')

In [43]: t = Time('J2000', precision=10)

In [44]: t.precision
Out[44]: 10

In [45]: t.precision = 10
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
<ipython-input-45-59f84a57d617> in <module>
----> 1 t.precision = 10

/usr/lib/python3/dist-packages/astropy/time/core.py in precision(self, val)
    608         del self.cache
    609         if not isinstance(val, int) or val < 0 or val > 9:
--> 610             raise ValueError('precision attribute must be an int between '
    611                              '0 and 9')
    612         self._time.precision = val

ValueError: precision attribute must be an int between 0 and 9
```
Seems reasonable to check on input as well.

## Failing Tests That Should Pass
- `astropy/time/tests/test_basic.py::TestBasic::test_precision_input`

## Existing Passing Tests To Preserve
- `astropy/time/tests/test_basic.py::TestBasic::test_different_dimensions`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[jd]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[mjd]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[decimalyear]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[unix]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[unix_tai]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[cxcsec]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[gps]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[plot_date]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[stardate]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[datetime]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[ymdhms]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[iso]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[isot]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[yday]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[datetime64]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[fits]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[byear]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[jyear]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[byear_str]`
- `astropy/time/tests/test_basic.py::TestBasic::test_empty_value[jyear_str]`
- `astropy/time/tests/test_basic.py::TestBasic::test_copy_time[2455197.5]`
- `astropy/time/tests/test_basic.py::TestBasic::test_copy_time[value1]`
- `astropy/time/tests/test_basic.py::TestBasic::test_getitem`
- `astropy/time/tests/test_basic.py::TestBasic::test_properties`
- `astropy/time/tests/test_basic.py::TestBasic::test_precision`
- `astropy/time/tests/test_basic.py::TestBasic::test_transforms`
- `astropy/time/tests/test_basic.py::TestBasic::test_transforms_no_location`
- `astropy/time/tests/test_basic.py::TestBasic::test_location`
- `astropy/time/tests/test_basic.py::TestBasic::test_location_array`
- `astropy/time/tests/test_basic.py::TestBasic::test_all_scale_transforms`
- `astropy/time/tests/test_basic.py::TestBasic::test_creating_all_formats`
- `astropy/time/tests/test_basic.py::TestBasic::test_local_format_transforms`
- `astropy/time/tests/test_basic.py::TestBasic::test_datetime`
- `astropy/time/tests/test_basic.py::TestBasic::test_datetime64`
- `astropy/time/tests/test_basic.py::TestBasic::test_epoch_transform`
- `astropy/time/tests/test_basic.py::TestBasic::test_input_validation`
- `astropy/time/tests/test_basic.py::TestBasic::test_utc_leap_sec`
- `astropy/time/tests/test_basic.py::TestBasic::test_init_from_time_objects`
- `astropy/time/tests/test_basic.py::TestVal2::test_unused_val2_raises[d0]`
- `astropy/time/tests/test_basic.py::TestVal2::test_unused_val2_raises[d1]`
- `astropy/time/tests/test_basic.py::TestVal2::test_unused_val2_raises[d2]`
- `astropy/time/tests/test_basic.py::TestVal2::test_unused_val2_raises[d3]`
- `astropy/time/tests/test_basic.py::TestVal2::test_val2`
- `astropy/time/tests/test_basic.py::TestVal2::test_val_broadcasts_against_val2`
- `astropy/time/tests/test_basic.py::TestVal2::test_broadcast_not_writable`
- `astropy/time/tests/test_basic.py::TestVal2::test_broadcast_one_not_writable`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_input_subformat`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_input_subformat_fail`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_bad_input_subformat`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_output_subformat`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_fits_format`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_yday_format`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_scale_input`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_fits_scale`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_scale_default`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_epoch_times`
- `astropy/time/tests/test_basic.py::TestSubFormat::test_plot_date`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_example`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_longdouble`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_longdouble_one_val`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_longdouble_for_other_types[mjd]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_longdouble_for_other_types[unix]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_longdouble_for_other_types[cxcsec]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_subformat_input`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_subformat_output[str]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_subformat_output[bytes]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_string_other_formats[jd-2451544.5333981-2451544.5-0.0333981]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_string_other_formats[decimalyear-2000.54321-2000.0-0.54321]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_string_other_formats[cxcsec-100.0123456-100.0123456-None]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_string_other_formats[unix-100.0123456-100.0123456-None]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_string_other_formats[gps-100.0123456-100.0123456-None]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_string_other_formats[byear-1950.1-1950.1-None]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_explicit_string_other_formats[jyear-2000.1-2000.1-None]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_basic_subformat_setting`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_basic_subformat_cache_does_not_crash`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_decimal_context_does_not_affect_string[jd]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_decimal_context_does_not_affect_string[mjd]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_decimal_context_does_not_affect_string[cxcsec]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_decimal_context_does_not_affect_string[unix]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_decimal_context_does_not_affect_string[gps]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_decimal_context_does_not_affect_string[jyear]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_decimal_context_caching`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_timedelta_basic[sec-long-longdouble]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_timedelta_basic[sec-decimal-Decimal]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_timedelta_basic[sec-str-str]`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_need_format_argument`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_wrong_in_subfmt`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_wrong_subfmt`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_not_allowed_subfmt`
- `astropy/time/tests/test_basic.py::TestNumericalSubFormat::test_switch_to_format_with_no_out_subfmt`
- `astropy/time/tests/test_basic.py::TestSofaErrors::test_bad_time`
- `astropy/time/tests/test_basic.py::TestCopyReplicate::test_immutable_input`
- `astropy/time/tests/test_basic.py::TestCopyReplicate::test_replicate`
- `astropy/time/tests/test_basic.py::TestCopyReplicate::test_copy`
- `astropy/time/tests/test_basic.py::TestStardate::test_iso_to_stardate`
- `astropy/time/tests/test_basic.py::TestStardate::test_stardate_to_iso[dates0]`
- `astropy/time/tests/test_basic.py::TestStardate::test_stardate_to_iso[dates1]`
- `astropy/time/tests/test_basic.py::TestStardate::test_stardate_to_iso[dates2]`
- `astropy/time/tests/test_basic.py::test_python_builtin_copy`
- `astropy/time/tests/test_basic.py::test_now`
- `astropy/time/tests/test_basic.py::test_decimalyear`
- `astropy/time/tests/test_basic.py::test_fits_year0`
- `astropy/time/tests/test_basic.py::test_fits_year10000`
- `astropy/time/tests/test_basic.py::test_dir`
- `astropy/time/tests/test_basic.py::test_time_from_epoch_jds`
- `astropy/time/tests/test_basic.py::test_bool`
- `astropy/time/tests/test_basic.py::test_len_size`
- `astropy/time/tests/test_basic.py::test_TimeFormat_scale`
- `astropy/time/tests/test_basic.py::test_byteorder`
- `astropy/time/tests/test_basic.py::test_datetime_tzinfo`
- `astropy/time/tests/test_basic.py::test_subfmts_regex`
- `astropy/time/tests/test_basic.py::test_set_format_basic`
- `astropy/time/tests/test_basic.py::test_unix_tai_format`
- `astropy/time/tests/test_basic.py::test_set_format_shares_subfmt`
- `astropy/time/tests/test_basic.py::test_set_format_does_not_share_subfmt`
- `astropy/time/tests/test_basic.py::test_replicate_value_error`
- `astropy/time/tests/test_basic.py::test_remove_astropy_time`
- `astropy/time/tests/test_basic.py::test_isiterable`
- `astropy/time/tests/test_basic.py::test_to_datetime`
- `astropy/time/tests/test_basic.py::test_cache`
- `astropy/time/tests/test_basic.py::test_epoch_date_jd_is_day_fraction`
- `astropy/time/tests/test_basic.py::test_sum_is_equivalent`
- `astropy/time/tests/test_basic.py::test_string_valued_columns`
- `astropy/time/tests/test_basic.py::test_bytes_input`
- `astropy/time/tests/test_basic.py::test_writeable_flag`
- `astropy/time/tests/test_basic.py::test_setitem_location`
- `astropy/time/tests/test_basic.py::test_setitem_from_python_objects`
- `astropy/time/tests/test_basic.py::test_setitem_from_time_objects`
- `astropy/time/tests/test_basic.py::test_setitem_bad_item`
- `astropy/time/tests/test_basic.py::test_setitem_deltas`
- `astropy/time/tests/test_basic.py::test_subclass`
- `astropy/time/tests/test_basic.py::test_strftime_scalar`
- `astropy/time/tests/test_basic.py::test_strftime_array`
- `astropy/time/tests/test_basic.py::test_strftime_array_2`
- `astropy/time/tests/test_basic.py::test_strftime_leapsecond`
- `astropy/time/tests/test_basic.py::test_strptime_scalar`
- `astropy/time/tests/test_basic.py::test_strptime_array`
- `astropy/time/tests/test_basic.py::test_strptime_badinput`
- `astropy/time/tests/test_basic.py::test_strptime_input_bytes_scalar`
- `astropy/time/tests/test_basic.py::test_strptime_input_bytes_array`
- `astropy/time/tests/test_basic.py::test_strptime_leapsecond`
- `astropy/time/tests/test_basic.py::test_strptime_3_digit_year`
- `astropy/time/tests/test_basic.py::test_strptime_fracsec_scalar`
- `astropy/time/tests/test_basic.py::test_strptime_fracsec_array`
- `astropy/time/tests/test_basic.py::test_strftime_scalar_fracsec`
- `astropy/time/tests/test_basic.py::test_strftime_scalar_fracsec_precision`
- `astropy/time/tests/test_basic.py::test_strftime_array_fracsec`
- `astropy/time/tests/test_basic.py::test_insert_time`
- `astropy/time/tests/test_basic.py::test_insert_exceptions`
- `astropy/time/tests/test_basic.py::test_datetime64_no_format`
- `astropy/time/tests/test_basic.py::test_hash_time`
- `astropy/time/tests/test_basic.py::test_hash_time_delta`
- `astropy/time/tests/test_basic.py::test_get_time_fmt_exception_messages`
- `astropy/time/tests/test_basic.py::test_ymdhms_defaults`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[False-kwargs0-tm_input0]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[False-kwargs0-tm_input1]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[False-kwargs0-recarray]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[False-kwargs1-tm_input0]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[False-kwargs1-tm_input1]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[False-kwargs1-recarray]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[True-kwargs0-tm_input0]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[True-kwargs0-tm_input1]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[True-kwargs0-recarray]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[True-kwargs1-tm_input0]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[True-kwargs1-tm_input1]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_table_like[True-kwargs1-recarray]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_dict_array`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_dict_scalar[kwargs0]`
- `astropy/time/tests/test_basic.py::test_ymdhms_init_from_dict_scalar[kwargs1]`
- `astropy/time/tests/test_basic.py::test_ymdhms_exceptions`
- `astropy/time/tests/test_basic.py::test_ymdhms_masked`
- `astropy/time/tests/test_basic.py::test_ymdhms_output`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[jd]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[mjd]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[decimalyear]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[unix]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[unix_tai]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[cxcsec]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[gps]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[plot_date]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[stardate]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[datetime]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[ymdhms]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[iso]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[isot]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[yday]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[datetime64]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[fits]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[byear]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[jyear]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[byear_str]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[jyear_str]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[jd]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[mjd]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[decimalyear]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[unix]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[unix_tai]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[cxcsec]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[gps]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[plot_date]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[stardate]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[datetime]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[ymdhms]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[iso]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[isot]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[yday]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[datetime64]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[fits]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[byear]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[jyear]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[byear_str]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_fits[jyear_str]`
- `astropy/time/tests/test_basic.py::test_broadcasting_writeable`
- `astropy/time/tests/test_basic.py::test_format_subformat_compatibility`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[jd-TimeJD]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[mjd-TimeMJD]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[decimalyear-TimeDecimalYear]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[unix-TimeUnix]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[unix_tai-TimeUnixTai]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[cxcsec-TimeCxcSec]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[gps-TimeGPS]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[plot_date-TimePlotDate]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[stardate-TimeStardate]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[datetime-TimeDatetime]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[ymdhms-TimeYMDHMS]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[iso-TimeISO]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[isot-TimeISOT]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[yday-TimeYearDayTime]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[datetime64-TimeDatetime64]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[fits-TimeFITS]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[byear-TimeBesselianEpoch]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[jyear-TimeJulianEpoch]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[byear_str-TimeBesselianEpochString]`
- `astropy/time/tests/test_basic.py::test_to_value_with_subfmt_for_every_format[jyear_str-TimeJulianEpochString]`
- `astropy/time/tests/test_basic.py::test_location_init[None]`
- `astropy/time/tests/test_basic.py::test_location_init[location1]`
- `astropy/time/tests/test_basic.py::test_location_init_fail`
- `astropy/time/tests/test_basic.py::test_linspace`
- `astropy/time/tests/test_basic.py::test_linspace_steps`
- `astropy/time/tests/test_basic.py::test_linspace_fmts`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
