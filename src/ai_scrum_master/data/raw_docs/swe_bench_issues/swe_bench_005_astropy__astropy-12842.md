# SWE-bench Issue: astropy__astropy-12842

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-12842
- Base Commit: 3a0cd2d8cd7b459cdc1e1b97a14f3040ccc1fffc
- Environment Setup Commit: 298ccb478e6bf092953bca67a3d29dc6c35f6752
- Created At: 2022-02-12T12:38:10Z
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

## Failing Tests That Should Pass
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[datetime]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[datetime64]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[byear]`

## Existing Passing Tests To Preserve
- `astropy/io/ascii/tests/test_ecsv.py::astropy.io.ascii.tests.test_ecsv.test_round_trip_masked_table_default`
- `astropy/io/ascii/tests/test_ecsv.py::test_write_simple`
- `astropy/io/ascii/tests/test_ecsv.py::test_write_full`
- `astropy/io/ascii/tests/test_ecsv.py::test_write_read_roundtrip`
- `astropy/io/ascii/tests/test_ecsv.py::test_bad_delimiter`
- `astropy/io/ascii/tests/test_ecsv.py::test_bad_header_start`
- `astropy/io/ascii/tests/test_ecsv.py::test_bad_delimiter_input`
- `astropy/io/ascii/tests/test_ecsv.py::test_multidim_input`
- `astropy/io/ascii/tests/test_ecsv.py::test_structured_input`
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
- `astropy/io/ascii/tests/test_ecsv.py::test_read_bad_datatype`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_complex`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_str`
- `astropy/io/ascii/tests/test_ecsv.py::test_read_bad_datatype_for_object_subtype`
- `astropy/io/ascii/tests/test_ecsv.py::test_full_repr_roundtrip`
- `astropy/io/ascii/tests/test_ecsv.py::test_specialized_columns[scalar-col0-exp0]`
- `astropy/io/ascii/tests/test_ecsv.py::test_specialized_columns[2-d`
- `astropy/io/ascii/tests/test_ecsv.py::test_specialized_columns[1-d`
- `astropy/io/ascii/tests/test_ecsv.py::test_specialized_columns[scalar`
- `astropy/io/ascii/tests/test_ecsv.py::test_full_subtypes`
- `astropy/io/ascii/tests/test_ecsv.py::test_masked_empty_subtypes`
- `astropy/io/ascii/tests/test_ecsv.py::test_masked_vals_in_array_subtypes`
- `astropy/io/ascii/tests/test_ecsv.py::test_guess_ecsv_with_one_column`
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
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[ymdhms]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[iso]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[isot]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[yday]`
- `astropy/time/tests/test_basic.py::test_write_every_format_to_ecsv[fits]`
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

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
