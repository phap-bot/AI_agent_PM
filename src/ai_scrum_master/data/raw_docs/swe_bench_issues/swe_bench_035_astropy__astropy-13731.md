# SWE-bench Issue: astropy__astropy-13731

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13731
- Base Commit: a30301e5535be2f558cb948da6b3475df4e36a98
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-09-21T16:19:30Z
- Version: 5.0

## Issue Title
`Time` parses fractional days in year-month-day format incorrectly

## Problem Statement
`Time` parses fractional days in year-month-day format incorrectly
`Time('2017-08-24.25')` results in `2017-08-24 00:00:00.250`: the fractional days are interpreted as fractional seconds (`2017-08-24 06:00:00` is what I hoped for).

The format `2017-08-24.25` is perhaps not the best format, but it is used, and since Astropy does not raise an exception, but silently returns an incorrect result, this may lead to errors.

The issue can be traced to `astropy.time.formats.TimeString().parse_string()`, which will interpret anything right of the last dot as a fractional second.
Since matching to regexes or `strptime` formats is done afterwards, there is no (easy) way to catch this through a subformat before the fractional second get stripped.

I'd be happy to try and put in a PR for this (if it's indeed a bug), but I'll need to know whether to raise an exception, or implement a proper parser for this format (provided it doesn't clash with other interpretations).
Some suggestions on the best way to attack this issue (or at what point in the code) are welcome as well.

## Issue Discussion Hints
@evertrol - I think the best strategy here is to raise an exception.  The point is that the astropy string subformats like `date` are documented to be symmetric, so that if you put in `2017-08-24.25` then it parses that and the representation would then be something like `2017-08-24.250` (with a default precision of 3 digits).  So this is inventing a whole new class of time formats.  Likewise the current API does not document being able to include fractional days, so it is reasonable to keep the API the same and just raise an exception.

I guess it is fair to ask where "it is used".  Are there officially sanctioned (institutional) uses of this or just informal use?

As for implementation, this would go in the `parse_string` method in `TimeString`.  Unfortunately the current code makes it a difficult to implement a rock-solid way of detecting a problem.  A good start that will detect most problems is basically checking that the inferred date format is in a list of formats that include seconds, e.g. `('date_hms', 'longdate_hms')`.  The problem is with user-defined formats... but perfect is the enemy of good.
I think a match against
```python
re.match(r'\d{4}-\d{1,2}-\d{1,2}\.\d+$', val)
```
may work (followed by a `ValueError`). No other date formats that spring to my mind match that. But I may have missed how much flexibility there is for a user to define a format.

As to where it is used: I very much doubt this is a sanctioned format, and I see it mostly used in telegrams and circulars, depending on the group that submits it. A recent example is [ATel 10652](http://www.astronomerstelegram.org/?read=10652).
So the danger for errors may mostly be when people copy-paste such a date into a `Time` object, and not notice the resulting incorrect time (e.g., when subtracting another `Time` directly from it).

Strange that a somewhat-official telegram would use this non-format.  Well maybe it's worth allowing this on input.  Sigh.

One way that might work and be relatively low-impact is to change this [loop here](https://github.com/astropy/astropy/blob/b6e291779ea76b7e4710df90e1800e5dfefc52e8/astropy/time/formats.py#L713) to include the format name, i.e.:
```
for format_name, strptime_fmt_or_regex, _ in subfmts:
```
Then later in the loop (at the `# add fractional seconds` bit), if the format_name is `date` then apply the fractional part as a day.  If it is a format that supports fractional seconds, then apply as seconds.  Otherwise if `format_name` is one of the defined core astropy format names (but not in the previous two categories) then raise an exception.  This would catch input like `2016-01-01 10:10.25`.  However, if the format name is something custom from a user then just continue the current behavior of the code.

Anyway this is just brainstorming for something simple.  One can imagine higher-impact, more robust solutions, but it isn't totally clear we want to go there for this corner case.
One interesting edge case is where a user actually defines a fractional hour or minute format themselves. For example:
```python
class FracHour(TimeString):
    subfmts = (
        ('fh', 
         (r'(?P<year>\d{4})-(?P<mon>\d{1,2})-(?P<mday>\d{1,2}) '
          r'(?P<hour>\d{1,2}(\.\d*))'), 
         '{year:d}-{mon:02d}-{day:02d}T{hour:05.2f}'),
    )
```
This will raise a `ValueError: Input values did not match the format class fh` even with correct input: `Time('1999-01-01 5.5', format='fh')`.

I guess that's correct though: Astropy can't go out of its way to infer when a fraction belongs to a day, hour, minute or second (it could, but the rewrite would be quite horrendous, and not worth the effort).

<hr>

I've now gone the route of allowing fractional days for both `'date'` and `'yday'` formats, allowing fractional seconds for `...endswith('hms')` and otherwise skip to the next sub-format.
This has caught me out a few times as well. The Minor Planet Center (MPC) uses a specific format for observations of asteroids and comets:
`'2020 08 15.59280'`
Which isn't understood by astropy.time.Time, but if spaces are replaced with dashes, it gives:
```
Time('2020 08 15.59280'.replace(' ', '-'))
<Time object: scale='utc' format='iso' value=2020-08-15 00:00:00.593>
```
whereas it should in fact convert to
`'2020-08-15 14:13:37.920'`
The best solution I have found is to add the decimal after converting to a Time object:
```
>>> Time('2020 08 15'.replace(' ', '-'))+'.59280'
<Time object: scale='utc' format='iso' value=2020-08-15 14:13:37.920>
```
But this is somewhat clunky. It would be nice if "mpc" (or "mpc_obs80") could be added to the allowed formats, so that I'd just need to remember to add the correct format specifier instead of changing spaces to dashes and adding the decimal day after the conversion to a Time object. 

(I work at the MPC, and my research also uses MPC-formatted files extensively, so I often come across this problem and finally decided to go raise an issue about it; I found several already open, so I just added to this one.)
Sorry there hasn't been any progress on this issue. I'll go back to my original point that `"2020-08-15.59280"` is unequivocally not an ISO8601-formatted date, so passing in this string should currently raise an exception. In other words there is no current Time format which should match that string. The fact that the ISO format matches is a bug in the parser.

An enhancement could be to define a new Time format which does match that like `date_fracday` or something. Some of my original discussion that alluded to making a new ISO time subformat for this case was off base.

## Failing Tests That Should Pass
- `astropy/time/tests/test_basic.py::test_format_fractional_string_parsing[False]`

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
- `astropy/time/tests/test_basic.py::TestBasic::test_precision_input`
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
- `astropy/time/tests/test_basic.py::test_insert_time_out_subfmt`
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
- `astropy/time/tests/test_basic.py::test_format_fractional_string_parsing[force]`
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
