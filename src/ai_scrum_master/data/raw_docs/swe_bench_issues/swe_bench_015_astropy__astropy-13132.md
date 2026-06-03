# SWE-bench Issue: astropy__astropy-13132

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13132
- Base Commit: 3a0cd2d8cd7b459cdc1e1b97a14f3040ccc1fffc
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-04-21T01:37:30Z
- Version: 5.0

## Issue Title
Add __array_func__ for astropy.time.Time

## Problem Statement
Add __array_func__ for astropy.time.Time
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

xref https://github.com/astropy/astropy/issues/8610. This provides some numpy array functions for `Time` objects. Most notably, one can now do the following without an errror(!):
```python
from astropy.time import Time, TimeDelta
import numpy as np

t0 = Time('2021-01-01')
t1 = Time('2022-01-01')

times = np.linspace(t0, t1, num=50)
```

This still needs:
- [ ] Tests
- [ ] What's new
- [ ] API docs???

but opening now for feedback and a full CI run.

<!-- If the pull request closes any open issues you can add this.
If you replace <Issue Number> with a number, GitHub will automatically link it.
If this pull request is unrelated to any issues, please remove
the following line. -->

### Checklist for package maintainer(s)
<!-- This section is to be filled by package maintainer(s) who will
review this pull request. -->

This checklist is meant to remind the package maintainer(s) who will review this pull request of some common things to look for. This list is not exhaustive.

- [x] Do the proposed changes actually accomplish desired goals?
- [ ] Do the proposed changes follow the [Astropy coding guidelines](https://docs.astropy.org/en/latest/development/codeguide.html)?
- [ ] Are tests added/updated as required? If so, do they follow the [Astropy testing guidelines](https://docs.astropy.org/en/latest/development/testguide.html)?
- [ ] Are docs added/updated as required? If so, do they follow the [Astropy documentation guidelines](https://docs.astropy.org/en/latest/development/docguide.html#astropy-documentation-rules-and-guidelines)?
- [ ] Is rebase and/or squash necessary? If so, please provide the author with appropriate instructions. Also see ["When to rebase and squash commits"](https://docs.astropy.org/en/latest/development/when_to_rebase.html).
- [ ] Did the CI pass? If no, are the failures related? If you need to run daily and weekly cron jobs as part of the PR, please apply the `Extra CI` label.
- [ ] Is a change log needed? If yes, did the change log check pass? If no, add the `no-changelog-entry-needed` label. If this is a manual backport, use the `skip-changelog-checks` label unless special changelog handling is necessary.
- [ ] Is a milestone set? Milestone must be set but `astropy-bot` check might be missing; do not let the green checkmark fool you.
- [ ] At the time of adding the milestone, if the milestone set requires a backport to release branch(es), apply the appropriate `backport-X.Y.x` label(s) *before* merge.

## Issue Discussion Hints
👋 Thank you for your draft pull request! Do you know that you can use `[ci skip]` or `[skip ci]` in your commit messages to skip running continuous integration tests until you are ready?
I think this is good for review now. Somewhat limited in scope to just `linspace`, but once the structure of implementing the numpy functions is settled on I'm happy to expand this in subsequent PR(s).

## Failing Tests That Should Pass
- `astropy/time/tests/test_basic.py::test_linspace`
- `astropy/time/tests/test_basic.py::test_linspace_steps`
- `astropy/time/tests/test_basic.py::test_linspace_fmts`

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

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
