# SWE-bench Issue: astropy__astropy-12880

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-12880
- Base Commit: b49ad06b4de9577648a55d499d914e08baeef2c6
- Environment Setup Commit: 298ccb478e6bf092953bca67a3d29dc6c35f6752
- Created At: 2022-02-21T13:57:37Z
- Version: 4.3

## Issue Title
No longer able to read BinnedTimeSeries with datetime column saved as ECSV after upgrading from 4.2.1 -> 5.0+

## Problem Statement
No longer able to read BinnedTimeSeries with datetime column saved as ECSV after upgrading from 4.2.1 -> 5.0+
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
<!-- Provide a general description of the bug. -->
Hi, [This commit](https://github.com/astropy/astropy/commit/e807dbff9a5c72bdc42d18c7d6712aae69a0bddc) merged in PR #11569 breaks my ability to read an ECSV file created using Astropy v 4.2.1, BinnedTimeSeries class's write method, which has a datetime64 column. Downgrading astropy back to 4.2.1 fixes the issue because the strict type checking in line 177 of ecsv.py is not there.

Is there a reason why this strict type checking was added to ECSV? Is there a way to preserve reading and writing of ECSV files created with BinnedTimeSeries across versions? I am happy to make a PR on this if the strict type checking is allowed to be scaled back or we can add datetime64 as an allowed type. 

### Expected behavior
<!-- What did you expect to happen. -->

The file is read into a `BinnedTimeSeries` object from ecsv file without error.

### Actual behavior
<!-- What actually happened. -->
<!-- Was the output confusing or poorly described? -->

ValueError is produced and the file is not read because ECSV.py does not accept the datetime64 column.
`ValueError: datatype 'datetime64' of column 'time_bin_start' is not in allowed values ('bool', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float16', 'float32', 'float64', 'float128', 'string')`

### Steps to Reproduce
<!-- Ideally a code example could be provided so we can run it ourselves. -->
<!-- If you are pasting code, use triple backticks (```) around
your code snippet. -->
<!-- If necessary, sanitize your screen output to be pasted so you do not
reveal secrets like tokens and passwords. -->

The file is read using:    
`BinnedTimeSeries.read('<file_path>', format='ascii.ecsv')`
which gives a long error. 


The file in question is a binned time series created by  `astropy.timeseries.aggregate_downsample`. which itself is a binned version of an `astropy.timeseries.TimeSeries` instance with some TESS data. (loaded via TimeSeries.from_pandas(Tess.set_index('datetime')). I.e., it has a datetime64 index.  The file was written using the classes own .write method in Astropy V4.2.1 from an instance of said class:   
`myBinnedTimeSeries.write('<file_path>',format='ascii.ecsv',overwrite=True)`

I'll attach a concatenated version of the file (as it contains private data). However, the relevant part from the header is on line 4:

```
# %ECSV 0.9
# ---
# datatype:
# - {name: time_bin_start, datatype: datetime64}
```

as you can see, the datatype is datetime64. This works fine with ECSV V0.9 but not V1.0 as some sort of strict type checking was added. 

### 
Full error log:
```
---------------------------------------------------------------------------
ValueError                                Traceback (most recent call last)
Input In [3], in <module>
---> 49 tsrbin = BinnedTimeSeries.read('../Photometry/tsr_bin.dat', format='ascii.ecsv')

File ~/Apps/miniconda3/envs/py310_latest/lib/python3.10/site-packages/astropy/timeseries/binned.py:285, in BinnedTimeSeries.read(self, filename, time_bin_start_column, time_bin_end_column, time_bin_size_column, time_bin_size_unit, time_format, time_scale, format, *args, **kwargs)
    230 """
    231 Read and parse a file and returns a `astropy.timeseries.BinnedTimeSeries`.
    232 
   (...)
    279 
    280 """
    282 try:
    283 
    284     # First we try the readers defined for the BinnedTimeSeries class
--> 285     return super().read(filename, format=format, *args, **kwargs)
    287 except TypeError:
    288 
    289     # Otherwise we fall back to the default Table readers
    291     if time_bin_start_column is None:

File ~/Apps/miniconda3/envs/py310_latest/lib/python3.10/site-packages/astropy/table/connect.py:62, in TableRead.__call__(self, *args, **kwargs)
     59 units = kwargs.pop('units', None)
     60 descriptions = kwargs.pop('descriptions', None)
---> 62 out = self.registry.read(cls, *args, **kwargs)
     64 # For some readers (e.g., ascii.ecsv), the returned `out` class is not
     65 # guaranteed to be the same as the desired output `cls`.  If so,
     66 # try coercing to desired class without copying (io.registry.read
     67 # would normally do a copy).  The normal case here is swapping
     68 # Table <=> QTable.
     69 if cls is not out.__class__:

File ~/Apps/miniconda3/envs/py310_latest/lib/python3.10/site-packages/astropy/io/registry/core.py:199, in UnifiedInputRegistry.read(self, cls, format, cache, *args, **kwargs)
    195     format = self._get_valid_format(
    196         'read', cls, path, fileobj, args, kwargs)
    198 reader = self.get_reader(format, cls)
--> 199 data = reader(*args, **kwargs)
    201 if not isinstance(data, cls):
    202     # User has read with a subclass where only the parent class is
    203     # registered.  This returns the parent class, so try coercing
    204     # to desired subclass.
    205     try:

File ~/Apps/miniconda3/envs/py310_latest/lib/python3.10/site-packages/astropy/io/ascii/connect.py:18, in io_read(format, filename, **kwargs)
     16     format = re.sub(r'^ascii\.', '', format)
     17     kwargs['format'] = format
---> 18 return read(filename, **kwargs)

File ~/Apps/miniconda3/envs/py310_latest/lib/python3.10/site-packages/astropy/io/ascii/ui.py:376, in read(table, guess, **kwargs)
    374     else:
    375         reader = get_reader(**new_kwargs)
--> 376         dat = reader.read(table)
    377         _read_trace.append({'kwargs': copy.deepcopy(new_kwargs),
    378                             'Reader': reader.__class__,
    379                             'status': 'Success with specified Reader class '
    380                                       '(no guessing)'})
    382 # Static analysis (pyright) indicates `dat` might be left undefined, so just
    383 # to be sure define it at the beginning and check here.

File ~/Apps/miniconda3/envs/py310_latest/lib/python3.10/site-packages/astropy/io/ascii/core.py:1343, in BaseReader.read(self, table)
   1340 self.header.update_meta(self.lines, self.meta)
   1342 # Get the table column definitions
-> 1343 self.header.get_cols(self.lines)
   1345 # Make sure columns are valid
   1346 self.header.check_column_names(self.names, self.strict_names, self.guessing)

File ~/Apps/miniconda3/envs/py310_latest/lib/python3.10/site-packages/astropy/io/ascii/ecsv.py:177, in EcsvHeader.get_cols(self, lines)
    175 col.dtype = header_cols[col.name]['datatype']
    176 if col.dtype not in ECSV_DATATYPES:
--> 177     raise ValueError(f'datatype {col.dtype!r} of column {col.name!r} '
    178                      f'is not in allowed values {ECSV_DATATYPES}')
    180 # Subtype is written like "int64[2,null]" and we want to split this
    181 # out to "int64" and [2, None].
    182 subtype = col.subtype

ValueError: datatype 'datetime64' of column 'time_bin_start' is not in allowed values ('bool', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float16', 'float32', 'float64', 'float128', 'string')
```
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
(For the version that does not work)
Python 3.10.2 | packaged by conda-forge | (main, Feb  1 2022, 19:28:35) [GCC 9.4.0]
Numpy 1.22.2
pyerfa 2.0.0.1
astropy 5.0.1
Scipy 1.8.0
Matplotlib 3.5.1

(For the version that does work)
Python 3.7.11 (default, Jul 27 2021, 14:32:16) [GCC 7.5.0]
Numpy 1.20.3
pyerfa 2.0.0.1
astropy 4.2.1
Scipy 1.7.0
Matplotlib 3.4.2

## Issue Discussion Hints
I hope you don't mind me tagging you @taldcroft as it was your commit, maybe you can help me figure out if this is a bug or an evolution in `astropy.TimeSeries` that requires an alternative file format? I was pretty happy using ecsv formatted files to save complex data as they have been pretty stable, easy to visually inspect, and read in/out of scripts with astropy. 


[example_file.dat.txt](https://github.com/astropy/astropy/files/8043511/example_file.dat.txt)
(Also I had to add a .txt to the filename to allow github to put it up.)
@emirkmo - sorry, it was probably a mistake to make the reader be strict like that and raise an exception. Although that file is technically non-compliant with the ECSV spec, the reader should instead issue a warning but still carry on if possible (being liberal on input). I'll put in a PR to fix that.

The separate issue is that the `Time` object has a format of `datetime64` which leads to that unexpected numpy dtype in the output. I'm not immediately sure of what the right behavior for writing ECSV should be there. Maybe actually just `datetime64` as an allowed type, but that opens a small can of worms itself. Any thoughts @mhvk?

One curiosity @emirko is how you ended up with the timeseries object `time_bin_start` column having that `datetime64` format (`ts['time_bin_start'].format`). In my playing around it normally has `isot` format, which would not have led to this problem.
I would be happy to contribute this PR @taldcroft, as I have been working on it on a local copy anyway, and am keen to get it working. I currently monkey patched ecsv in my code to not raise, and it seems to work. If you let me know what the warning should say, I can make a first attempt. `UserWarning` of some sort? 

The `datetime64` comes through a chain:

 - Data is read into `pandas` with a `datetime64` index.
 - `TimeSeries` object is created using `.from_pandas`.
 - `aggregate_downsample` is used to turn this into a `BinnedTimeSeries`
 - `BinnedTimeSeries` object is written to an .ecsv file using its internal method.

Here is the raw code, although some of what you see may be illegible due to variable names. I didn't have easy access to the original raw data anymore, hence why I got stuck in trying to read it from the binned light curve. 
```
perday = 12
Tess['datetime'] = pd.to_datetime(Tess.JD, unit='D', origin='julian')
ts = TimeSeries.from_pandas(Tess.set_index('datetime'))
tsb = aggregate_downsample(ts, time_bin_size=(1.0/perday)*u.day, 
                           time_bin_start=Time(beg.to_datetime64()), n_bins=nbin)
tsb.write('../Photometry/Tess_binned.ecsv', format='ascii.ecsv', overwrite=True)
```
My PR above at least works for reading in the example file and my original file. Also passes my local tests on io module. 
Ouch, that is painful! Apart from changing the error to a warning (good idea!), I guess the writing somehow should change the data type from `datetime64` to `string`. Given that the format is stored as `datetime64`, I think this would still round-trip fine. I guess it would mean overwriting `_represent_as_dict` in `TimeInfo`.
> I guess it would mean overwriting _represent_as_dict in TimeInfo

That's where I got to, we need to be a little more careful about serializing `Time`. In some sense I'd like to just use `jd1_jd2` always for Time in ECSV (think of this as lossless serialization), but that change might not go down well.
Yes, what to pick is tricky: `jd1_jd2` is lossless, but much less readable.
As a user, I would expect the serializer picked to maintain the current time format in some way, or at least have a general mapping from all available  formats to the most nearby easily serializable ones if some of them are hard to work with. (Days as ISOT string, etc.)

ECSV seems designed to be human readable so I would find it strange if the format was majorly changed, although now I see that all other ways of saving the data use jd1_jd2. I assume a separate PR is needed for changing this.

Indeed, the other formats use `jd1_jd2`, but they are less explicitly meant to be human-readable.  I think this particular case of numpy datetime should not be too hard to fix, without actually changing how the file looks.
Agreed to keep the ECSV serialization as the `value` of the Time object.
I will try to nudge the CI workflow on my minor change tonight, but I was wondering if this is going to fix other related issues with ecsvs and Table read/write that I haven't directly mentioned. For example, `str` instead of `string` also fails after Astropy 4.3. 

1.  Now we will raise a warning, but should we really be raising a warning for `str` instead of `string`?
2. Should I add some tests to my PR to catch possible regressions like this, as these regressions didn't trigger any test failures? Especially since I see Table read/write and ecsv is being worked on actively, with several PRs.

An example error I just dug out:
`raise ValueError(f'datatype {col.dtype!r} of column {col.name!r} '
ValueError: datatype 'str' of column 'photfilter' is not in allowed values ('bool', 'int8', 'int16', 'int32', 'int64', 'uint8', 'uint16', 'uint32', 'uint64', 'float16', 'float32', 'float64', 'float128', 'string')`

Works silently on astropy 4.2.1, but not later, and now will raise a warning instead.
(1) Do you know where the `str` example is coming from? This is actually an excellent case for the new warning because `str` is not an allowed ECSV `datatype` per the ECSV standard. So it means that some code is not doing the right thing when writing that ECSV file (and should be fixed).

(2) You can add optionally add a test for `str`, but I don't think it will help code coverage much since it falls in the same category of a valid numpy `dtype` which is NOT a valid ECSV `datatype`.

Note that ECSV has the goal of not being Python and Numpy-specific, hence the divergence in some of these details here.
<details>
<summary>Unnecessary detail, see next comment</summary>
In the simplest case, it is reading from an .ecsv file sent over as json (from a webserver with a get request) with a column that has `type` of `<class 'str'>`. This json is written to file and then read using `Table.read(<file>, format='ascii.ecsv')`. The .ecsv file itself is constructed from a postgre_sql database with an inbetween step of using an astropy Table. Read below if you want details.

So it's json (formatted as .ecsv) -> python write -> Table.read()


In detail:
For the case above, it's a get request to some webserver, that is storing this data in a database (postgre_sql), the request creates a .ecsv file after grabbing the right data from the database and putting it into a table, however this is done using an old version of astropy (as the pipeline environment that does this needs version locks), which is then sent as json formatted text. The pipeline that created the data is fixed to an old verison of astropy (maybe 4.2.1), and that is what is stored in postgre_sql database. Now, whatever code that is requesting it, turns it into json, writes to a file and then reads it into an astropy table using Table.read(format='ascii.ecsv'). The actual raw data for the column is that is intered into the database is a python string representing a photometric filter name. I don't have much insight into the database part, but I can find out if helpful.

It's this last step that fails after the update. I have a workaround of converting the json string, replacing 'str' with 'string', but it doesn't seem optimal. I see though that maybe if the json was read into an astropy table first, then saved, it would work. I just wasn't sure about the status of json decoding in astropy (and this seemed to work before).
</details>
I've had a look, and I think this may be code problems on our behalf when serializing python `str` data, or it could be just a very outdated astropy version as well. Although I wonder if 'str' could be used as an alias for 'string', so that codes that write .ecsv files from tabular data, maybe while skipping over astropy's own implementation? 

We probably never noticed the issues because prior to the checks, most things would just work rather robustly. 

Edit: Here's an example file:
```
# %ECSV 0.9
# ---
# datatype:
# - {name: time, datatype: float64, description: Time of observation in BMJD}
# - {name: mag_raw, datatype: float64, description: Target magnitude in raw science image}
# - {name: mag_raw_error, datatype: float64, description: Target magnitude error in raw science image}
# - {name: mag_sub, datatype: float64, description: Target magnitude in subtracted image}
# - {name: mag_sub_error, datatype: float64, description: Target magnitude error in subtracted image}
# - {name: photfilter, datatype: str, description: Photometric filter}
# - {name: site, datatype: int32, description: Site/instrument identifier}
# - {name: fileid_img, datatype: int32, description: Unique identifier of science image}
# - {name: fileid_diffimg, datatype: int32, description: Unique identifier of template-subtracted image}
# - {name: fileid_template, datatype: int32, description: Unique identifier of template image}
# - {name: fileid_photometry, datatype: int32, description: Unique identifier of photometry}
# - {name: version, datatype: str, description: Pipeline version}
# delimiter: ','
# meta: !!omap
# - keywords:
#   - {target_name: '2020svo'}
#   - {targetid: 130}
#   - {redshift: }
#   - {redshift_error: }
#   - {downloaded: '2022-02-17 01:04:27'}
# - __serialized_columns__:
#     time:
#       __class__: astropy.time.core.Time
#       format: mjd
#       scale: tdb
#       value: !astropy.table.SerializedColumn {name: time}
# schema: astropy-2.0
time,mag_raw,mag_raw_error,mag_sub,mag_sub_error,photfilter,site,fileid_img,fileid_diffimg,fileid_template,fileid_photometry,version
59129.1064732728991657,010101,,,H,9,1683,,,5894,master-v0.6.4
```
Our group has recently encountered errors very closely related to this.  In our case the ECSV 0.9 type is `object`.  I *think* the ECSV 1.0 equivalent is `string subtype: json`, but I haven't been able to to confirm that yet.

In general, what is the policy on backward-compatibility when reading ECSV files?
@weaverba137 if you don’t mind, would you be able to try my PR #12481 to see if it works for dtype object as well? We’re also interested in backwards compatibility.

(You can clone my branch, and pip install -e ., I don’t have a main so have to clone the PR branch)
@weaverba137 @emirkmo - sorry that the updates in ECSV reading are breaking back-compatibility, I am definitely sensitive to that. Perhaps we can do a bug-fix release which checks for ECSV 0.9 (as opposed to 1.0) and silently reads them without warnings. This will work for files written with older astropy.

@weaverba137 - ~~can you provide an example file with an `object` column?~~ [EDIT - I saw the example and read the discussion in the linked issue].  Going forward (astropy >= 5.0), `object` columns are written (and read) as described at https://github.com/astropy/astropy-APEs/blob/main/APE6.rst#object-columns. This is limited to object types that can be serialized to standard JSON (without any custom representations).
I would be highly supportive of a backwards compatibility bugfix for V0.9, and then an API change for V5.1 that changes the spec. I would be willing to work on a PR for it. 
@emirkmo - OK good plan, sorry again for the trouble. You can see this code here that is parsing the ECSV header. Currently nothing is done with the regex results but you can easily use it to check the version number and disable the current ValueError for ECSV < 1.0.
```
        # Validate that this is a ECSV file
        ecsv_header_re = r"""%ECSV [ ]
                             (?P<major> \d+)
                             \. (?P<minor> \d+)
                             \.? (?P<bugfix> \d+)? $"""

```
This new PR will likely introduce a merge conflict with the PR here, so #12840 would probably need to be on hold in lieu of the bug fix patch.
@taldcroft, good, sounds like you got what you need. That's a toy example of course, but I could provide something more realistic if necessary.

## Failing Tests That Should Pass
- `astropy/io/ascii/tests/test_ecsv.py::test_read_complex_v09`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_bad_datatype_v09`

## Existing Passing Tests To Preserve
- `astropy/io/ascii/tests/test_ecsv.py::astropy.io.ascii.tests.test_ecsv.test_round_trip_masked_table_default`
- `astropy/io/ascii/tests/test_ecsv.py::test_write_simple`
- `astropy/io/ascii/tests/test_ecsv.py::test_write_full`
- `astropy/io/ascii/tests/test_ecsv.py::test_write_read_roundtrip`
- `astropy/io/ascii/tests/test_ecsv.py::test_bad_delimiter`
- `astropy/io/ascii/tests/test_ecsv.py::test_bad_header_start`
- `astropy/io/ascii/tests/test_ecsv.py::test_bad_delimiter_input`
- `astropy/io/ascii/tests/test_ecsv.py::test_multidim_input`
- `astropy/io/ascii/tests/test_ecsv.py::test_round_trip_empty_table`
- `astropy/io/ascii/tests/test_ecsv.py::test_csv_ecsv_colnames_mismatch`
- `astropy/io/ascii/tests/test_ecsv.py::test_regression_5604`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col0]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col1]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col2]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col3]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col4]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col5]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col6]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col8]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col9]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col10]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col11]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col12]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col13]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col14]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col15]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col16]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col17]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col18]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col19]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col20]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col21]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col22]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-Table-name_col23]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col0]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col1]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col2]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col3]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col4]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col5]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col6]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col8]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col9]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col10]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col11]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col12]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col13]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col14]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col15]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col16]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col17]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col18]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col19]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col20]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col21]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col22]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[1-QTable-name_col23]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col0]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col1]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col2]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col3]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col4]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col5]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col6]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col8]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col9]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col10]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col11]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col12]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col13]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col14]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col15]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col16]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col17]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col18]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col19]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col20]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col21]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col22]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-Table-name_col23]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col0]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col1]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col2]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col3]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col4]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col5]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col6]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col8]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col9]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col10]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col11]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col12]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col13]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col14]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col15]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col16]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col17]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col18]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col19]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col20]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col21]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col22]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[2-QTable-name_col23]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col0]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col1]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col2]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col3]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col4]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col5]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col6]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col8]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col9]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col10]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col11]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col12]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col13]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col14]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col15]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col16]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col17]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col18]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col19]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col20]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col21]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col22]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-Table-name_col23]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col0]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col1]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col2]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col3]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col4]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col5]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col6]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col8]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col9]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col10]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col11]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col12]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col13]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col14]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col15]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col16]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col17]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col18]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col19]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col20]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col21]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col22]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_mixins_per_column[3-QTable-name_col23]`
- `astropy/io/ascii/tests/test_ecsv.py::test_round_trip_masked_table_default`
- `astropy/io/ascii/tests/test_ecsv.py::test_round_trip_masked_table_serialize_mask`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_round_trip_user_defined_unit[Table]`
- `astropy/io/ascii/tests/test_ecsv.py::test_ecsv_round_trip_user_defined_unit[QTable]`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_masked_bool`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[,-int64-null_value]`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[,-int64-data_mask]`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[,-float64-null_value]`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[,-float64-data_mask]`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[,-bool-null_value]`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[,-bool-data_mask]`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[,-str-null_value]`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[,-str-data_mask]`
- `astropy/io/ascii/tests/test_ecsv.py::test_roundtrip_multidim_masked_array[`
- `astropy/io/ascii/tests/test_ecsv.py::test_multidim_unknown_subtype[some-user-type]`
- `astropy/io/ascii/tests/test_ecsv.py::test_multidim_unknown_subtype[complex]`
- `astropy/io/ascii/tests/test_ecsv.py::test_multidim_bad_shape`
- `astropy/io/ascii/tests/test_ecsv.py::test_write_not_json_serializable`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_not_json_serializable`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_complex`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_bad_datatype_for_object_subtype`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_bad_datatype`
- `astropy/io/ascii/tests/test_ecsv.py::test_full_repr_roundtrip`
- `astropy/io/ascii/tests/test_ecsv.py::test_specialized_columns[scalar-col0-exp0]`
- `astropy/io/ascii/tests/test_ecsv.py::test_specialized_columns[2-d`
- `astropy/io/ascii/tests/test_ecsv.py::test_specialized_columns[1-d`
- `astropy/io/ascii/tests/test_ecsv.py::test_specialized_columns[scalar`
- `astropy/io/ascii/tests/test_ecsv.py::test_full_subtypes`
- `astropy/io/ascii/tests/test_ecsv.py::test_masked_empty_subtypes`
- `astropy/io/ascii/tests/test_ecsv.py::test_masked_vals_in_array_subtypes`
- `astropy/io/ascii/tests/test_ecsv.py::test_guess_ecsv_with_one_column`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
