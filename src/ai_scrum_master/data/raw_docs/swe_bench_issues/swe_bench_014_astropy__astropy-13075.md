# SWE-bench Issue: astropy__astropy-13075

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13075
- Base Commit: c660b079b6472920662ca4a0c731751a0342448c
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-04-06T19:44:23Z
- Version: 5.0

## Issue Title
Register format ``html`` to ``Cosmology.write`` with nice mathjax

## Problem Statement
Register format ``html`` to ``Cosmology.write`` with nice mathjax
Cosmology can now read and write to files.
It would be nice to register with ``Cosmology.write`` a  method for exporting a Cosmology to a HTML table.
There are good examples of IO with Cosmology at https://github.com/astropy/astropy/tree/main/astropy/cosmology/io
and documentation at https://docs.astropy.org/en/latest/cosmology/io.html#cosmology-io

I'm thinking the ``write_html(...)`` method would call ``cosmology.io.table.to_table()``, format the table to nice MathJax or something and then call the `QTable.write(..., format='html')`.

Edit: also, the mathjax representation of each parameter can be stored on the corresponding Parameter object, like how units have the ``format`` argument in [def_unit](https://docs.astropy.org/en/stable/api/astropy.units.def_unit.html#astropy.units.def_unit).

## Issue Discussion Hints
Hi. I am a new contributor and was wondering if this was still open for contribution? I would like to look into this if possible. 
Hello! The issue is still open, so feel free. 😸 
@JefftheCloudDog  that would be great! No one else is currently working on this feature request. If you need any help or have any questions I am happy to help. You can post here, or in the Astropy Slack cosmology channel. We also have documentation to assist in contributing at https://www.astropy.org/contribute.html#contribute-code-or-docs.
From my understanding of the request description, the high-level steps should look as such:

1. get a QTable object from the `cosmology.io.table.to_table()` function, which returns a QTable
2. format to MathJax 
3. call `QTable.write()` to write
4. The registration should look like this: `readwrite_registry.register_writer("ascii.html", Cosmology, write_table)`

From the steps and observing some examples from Cosmology/io, this `write_table()` should look very similar to `write_ecsv()` from Cosmology/io/ecsv.py

Am I correct in understanding so far? 
@JefftheCloudDog, correct! Looks like a great plan for implementation.

In #12983 we are working on the backend which should make the column naming easier, so each Parameter can hold its mathjax representation.
In the meantime it might be easiest to just have a `dict` of parameter name -> mathjax name.

Ah, I see. The format input is just a dict that has mathjax (or some other type) representation as values which should be an optional parameter. 

I'm looking through the example of def_unit, and looks like a new type of unit is defined with the format dict. 
Should `write_table()` function the same way? Are we creating a new Cosmology or QTable object for formatting? 

I suppose we are essentially using [`Table.write()`](https://docs.astropy.org/en/stable/api/astropy.table.Table.html#astropy.table.Table.write) since a QTable object is mostly identical to a Table object. 
When https://github.com/astropy/astropy/pull/12983 is merged then each parameter will hold its mathjax representation.
e.g. for latex.

```python
class FLRW(Cosmology):
    H0 = Parameter(..., format={"latex": r"$H_0$"})
```

So then the columns of the ``FLRW`` -> ``QTable`` can be renamed like (note this is a quick and dirty implementation)

```python
tbl = to_table(cosmo, ...)
for name in cosmo.__parameters__:
    param = getattr(cosmo.__class__, name)
    new_name = param.get_format_name('latex')
    tbl.rename_column(name, new_name)
```

However, https://github.com/astropy/astropy/pull/12983 is not yet merged, so the whole mathjax format can just be one central dictionary:

```python
mathjax_formats = dict(H0=..., Ode0=...)
```

Making it

```python
tbl = to_table(cosmo, ...)
for name in cosmo.__parameters__:
    new_name = mathjax_formats.get(name, name)  # fallback if not in formats
    tbl.rename_column(name, new_name)
```

Anyway, that's just what I was suggesting as a workaround until https://github.com/astropy/astropy/pull/12983 is in.
Ok, I see. Since this deals with i/o, the new code should go to astropy\cosmology\table.py? 

I see that there is already a line for `convert_registry.register_writer("astropy.table", Cosmology, to_table)`, so I was not sure if there should be a different file to register the new method.
> I see that there is already a line for convert_registry.register_writer("astropy.table", Cosmology, to_table), so I was not sure if there should be a different file to register the new method.

Yes, this should probably have a new file ``astropy/cosmology/io/html.py``.
I am writing tests now and it looks like writing fails with the following errors. I am not quite sure why these errors are appearing. I have been trying to understand why the error is occurring, since ascii.html is a built-in HTML table writer, but I am struggling a little. Can someone provide some support?

I based the first test on cosmology\io\tests\test_ecsv.py. Seems like the test is just failing on write.

```
fp = tmp_path / "test_to_html_table_bad_index.html"
write(file=fp)
```


error: 
```
self = <astropy.cosmology.io.tests.test_html.TestReadWriteHTML object at 0x00000175CE162F70>, read = <function ReadWriteDirectTestBase.read.<locals>.use_read at 0x00000175CE2F3280>
write = <function ReadWriteDirectTestBase.write.<locals>.use_write at 0x00000175CE4B9A60>, tmp_path = WindowsPath('C:/Users/jeffr/AppData/Local/Temp/pytest-of-jeffr/pytest-34/test_to_html_table_bad_index_c7')

    def test_to_html_table_bad_index(self, read, write, tmp_path):
        """Test if argument ``index`` is incorrect"""
        fp = tmp_path / "test_to_html_table_bad_index.html"

>       write(file=fp, format="ascii.html")

astropy\cosmology\io\tests\test_html.py:30:
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
astropy\cosmology\io\tests\base.py:196: in use_write
    return self.functions["write"](cosmo, *args, **kwargs)
astropy\cosmology\io\html.py:86: in write_table
    table.write(file, overwrite=overwrite, **kwargs)
astropy\table\connect.py:129: in __call__
    self.registry.write(instance, *args, **kwargs)
astropy\io\registry\core.py:354: in write
    return writer(data, *args, **kwargs)
astropy\io\ascii\connect.py:26: in io_write
    return write(table, filename, **kwargs)
astropy\io\ascii\ui.py:840: in write
    lines = writer.write(table)
astropy\io\ascii\html.py:431: in write
    new_col = Column([el[i] for el in col])
astropy\table\column.py:1076: in __new__
    self = super().__new__(
astropy\table\column.py:434: in __new__
    self_data = np.array(data, dtype=dtype, copy=copy)
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <Quantity 0. eV>

    def __float__(self):
        try:
            return float(self.to_value(dimensionless_unscaled))
        except (UnitsError, TypeError):
>           raise TypeError('only dimensionless scalar quantities can be '
                            'converted to Python scalars')
E           TypeError: only dimensionless scalar quantities can be converted to Python scalars

astropy\units\quantity.py:1250: TypeError
```
@JefftheCloudDog Thanks for dropping in the test output. The best way for me to help will be to see the code. To do that, it would be great if you opened a Pull Request with your code. Don't worry that the PR is not in it's final state, you can open it as Draft. Thanks!

See https://docs.astropy.org/en/latest/development/workflow/development_workflow.html if you are unsure how to make a Pull Request.
Thanks for the response! I created a [draft pull request ](https://github.com/astropy/astropy/pull/13075) for this issue. I did try to adhere to the instructions, but since this is my first contribution, there might be some mistakes. Please let me know if there are any issues.

## Failing Tests That Should Pass
- `astropy/cosmology/io/tests/test_.py::test_expected_readwrite_io`
- `astropy/cosmology/io/tests/test_.py::test_expected_convert_io`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_json_subclass_partial_info[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_bad_index[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_failed_cls[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[Planck13-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[Planck13-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_instance[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_subclass_partial_info[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_mutlirow[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[Planck13-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[Planck13-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[Planck13-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[Planck13-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[Planck13-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[Planck13-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_json_subclass_partial_info[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_bad_index[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_failed_cls[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[Planck15-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[Planck15-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_instance[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_subclass_partial_info[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_mutlirow[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[Planck15-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[Planck15-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[Planck15-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[Planck15-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[Planck15-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[Planck15-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_json_subclass_partial_info[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_bad_index[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_failed_cls[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[Planck18-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[Planck18-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_instance[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_subclass_partial_info[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_mutlirow[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[Planck18-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[Planck18-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[Planck18-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[Planck18-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[Planck18-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[Planck18-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_json_subclass_partial_info[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_bad_index[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_failed_cls[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP1-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP1-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_instance[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_subclass_partial_info[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_mutlirow[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP1-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP1-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP1-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP1-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP1-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP1-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_json_subclass_partial_info[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_bad_index[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_failed_cls[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP3-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP3-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_instance[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_subclass_partial_info[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_mutlirow[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP3-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP3-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP3-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP3-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP3-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP3-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_json_subclass_partial_info[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_bad_index[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_failed_cls[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP5-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP5-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_instance[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_subclass_partial_info[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_mutlirow[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP5-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP5-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP5-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP5-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP5-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP5-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_json_subclass_partial_info[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_bad_index[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_failed_cls[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP7-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP7-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_instance[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_subclass_partial_info[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_mutlirow[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP7-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP7-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP7-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP7-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP7-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP7-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_json_subclass_partial_info[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_bad_index[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_failed_cls[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP9-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_cls[WMAP9-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_to_ecsv_in_meta[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_instance[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_subclass_partial_info[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_ecsv_mutlirow[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP9-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_complete_info[WMAP9-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP9-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_from_subclass_complete_info[WMAP9-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP9-json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_readwrite_reader_class_mismatch[WMAP9-ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_write_methods_have_explicit_kwarg_overwrite[json-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyReadWrite::test_write_methods_have_explicit_kwarg_overwrite[ascii.ecsv-True-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_yaml[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_default[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_autoidentify[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck13-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml_specify_format[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_bad_index[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_failed_cls[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[Planck13-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[Planck13-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_table[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_instance[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_table_subclass_partial_info[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck13-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck13-astropy.table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_row[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_row_instance[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_row_subclass_partial_info[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck13-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck13-astropy.row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_method[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_callable[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_model_instance[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck13-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck13-astropy.model]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_default[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_wrong_cls[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[Planck13-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[Planck13-OrderedDict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cosmology_as_str[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_cosmology_as_str[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_move_from_meta[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_move_tofrom_meta[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_mapping[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_mapping_default[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_partial_info_mapping[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck13-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck13-mapping]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_cosmology_default[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_cosmology[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_cosmology_default[Planck13]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck13-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck13-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck13-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck13-astropy.cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck13-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck13-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck13-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck13-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck13-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck13-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck13-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck13-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck13-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck13-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck13-format_type0]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck13-format_type1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck13-format_type2]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck13-format_type3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck13-format_type4]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_yaml[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_default[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_autoidentify[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck15-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml_specify_format[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_bad_index[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_failed_cls[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[Planck15-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[Planck15-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_table[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_instance[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_table_subclass_partial_info[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck15-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck15-astropy.table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_row[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_row_instance[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_row_subclass_partial_info[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck15-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck15-astropy.row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_method[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_callable[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_model_instance[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck15-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck15-astropy.model]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_default[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_wrong_cls[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[Planck15-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[Planck15-OrderedDict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cosmology_as_str[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_cosmology_as_str[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_move_from_meta[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_move_tofrom_meta[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_mapping[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_mapping_default[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_partial_info_mapping[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck15-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck15-mapping]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_cosmology_default[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_cosmology[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_cosmology_default[Planck15]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck15-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck15-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck15-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck15-astropy.cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck15-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck15-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck15-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck15-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck15-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck15-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck15-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck15-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck15-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck15-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck15-format_type0]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck15-format_type1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck15-format_type2]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck15-format_type3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck15-format_type4]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_yaml[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_default[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_autoidentify[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[Planck18-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml_specify_format[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_bad_index[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_failed_cls[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[Planck18-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[Planck18-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_table[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_instance[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_table_subclass_partial_info[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck18-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[Planck18-astropy.table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_row[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_row_instance[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_row_subclass_partial_info[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck18-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[Planck18-astropy.row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_method[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_callable[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_model_instance[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck18-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[Planck18-astropy.model]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_default[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_wrong_cls[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[Planck18-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[Planck18-OrderedDict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cosmology_as_str[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_cosmology_as_str[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_move_from_meta[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_move_tofrom_meta[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_mapping[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_mapping_default[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_partial_info_mapping[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck18-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[Planck18-mapping]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_cosmology_default[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_cosmology[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_cosmology_default[Planck18]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck18-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck18-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck18-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[Planck18-astropy.cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck18-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck18-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck18-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck18-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[Planck18-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck18-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck18-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck18-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck18-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[Planck18-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck18-format_type0]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck18-format_type1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck18-format_type2]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck18-format_type3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[Planck18-format_type4]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_yaml[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_default[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_autoidentify[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP1-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml_specify_format[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_bad_index[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_failed_cls[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP1-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP1-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_table[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_instance[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_table_subclass_partial_info[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP1-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP1-astropy.table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_row[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_row_instance[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_row_subclass_partial_info[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP1-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP1-astropy.row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_method[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_callable[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_model_instance[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP1-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP1-astropy.model]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_default[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_wrong_cls[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP1-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP1-OrderedDict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cosmology_as_str[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_cosmology_as_str[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_move_from_meta[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_move_tofrom_meta[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_mapping[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_mapping_default[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_partial_info_mapping[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP1-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP1-mapping]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_cosmology_default[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_cosmology[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_cosmology_default[WMAP1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP1-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP1-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP1-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP1-astropy.cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP1-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP1-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP1-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP1-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP1-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP1-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP1-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP1-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP1-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP1-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP1-format_type0]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP1-format_type1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP1-format_type2]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP1-format_type3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP1-format_type4]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_yaml[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_default[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_autoidentify[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP3-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml_specify_format[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_bad_index[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_failed_cls[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP3-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP3-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_table[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_instance[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_table_subclass_partial_info[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP3-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP3-astropy.table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_row[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_row_instance[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_row_subclass_partial_info[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP3-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP3-astropy.row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_method[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_callable[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_model_instance[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP3-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP3-astropy.model]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_default[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_wrong_cls[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP3-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP3-OrderedDict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cosmology_as_str[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_cosmology_as_str[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_move_from_meta[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_move_tofrom_meta[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_mapping[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_mapping_default[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_partial_info_mapping[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP3-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP3-mapping]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_cosmology_default[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_cosmology[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_cosmology_default[WMAP3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP3-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP3-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP3-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP3-astropy.cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP3-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP3-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP3-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP3-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP3-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP3-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP3-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP3-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP3-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP3-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP3-format_type0]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP3-format_type1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP3-format_type2]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP3-format_type3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP3-format_type4]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_yaml[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_default[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_autoidentify[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP5-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml_specify_format[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_bad_index[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_failed_cls[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP5-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP5-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_table[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_instance[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_table_subclass_partial_info[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP5-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP5-astropy.table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_row[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_row_instance[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_row_subclass_partial_info[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP5-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP5-astropy.row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_method[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_callable[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_model_instance[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP5-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP5-astropy.model]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_default[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_wrong_cls[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP5-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP5-OrderedDict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cosmology_as_str[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_cosmology_as_str[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_move_from_meta[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_move_tofrom_meta[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_mapping[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_mapping_default[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_partial_info_mapping[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP5-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP5-mapping]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_cosmology_default[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_cosmology[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_cosmology_default[WMAP5]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP5-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP5-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP5-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP5-astropy.cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP5-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP5-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP5-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP5-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP5-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP5-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP5-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP5-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP5-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP5-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP5-format_type0]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP5-format_type1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP5-format_type2]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP5-format_type3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP5-format_type4]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_yaml[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_default[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_autoidentify[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP7-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml_specify_format[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_bad_index[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_failed_cls[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP7-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP7-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_table[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_instance[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_table_subclass_partial_info[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP7-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP7-astropy.table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_row[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_row_instance[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_row_subclass_partial_info[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP7-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP7-astropy.row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_method[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_callable[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_model_instance[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP7-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP7-astropy.model]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_default[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_wrong_cls[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP7-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP7-OrderedDict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cosmology_as_str[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_cosmology_as_str[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_move_from_meta[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_move_tofrom_meta[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_mapping[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_mapping_default[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_partial_info_mapping[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP7-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP7-mapping]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_cosmology_default[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_cosmology[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_cosmology_default[WMAP7]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP7-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP7-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP7-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP7-astropy.cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP7-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP7-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP7-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP7-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP7-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP7-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP7-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP7-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP7-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP7-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP7-format_type0]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP7-format_type1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP7-format_type2]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP7-format_type3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP7-format_type4]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_yaml[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_default[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_yaml_autoidentify[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml[WMAP9-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_yaml_specify_format[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_bad_index[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_failed_cls[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP9-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_cls[WMAP9-Table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table_in_meta[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_table[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_table[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_instance[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_table_subclass_partial_info[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_table_mutlirow[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP9-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_table[WMAP9-astropy.table]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_row_in_meta[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_row[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_row_instance[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_row_subclass_partial_info[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP9-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_row[WMAP9-astropy.row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_method[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model_not_callable[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_toformat_model[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_model_instance[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP9-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_model[WMAP9-astropy.model]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_default[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_wrong_cls[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP9-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cls[WMAP9-OrderedDict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_cosmology_as_str[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_cosmology_as_str[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_mapping_move_from_meta[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofrom_mapping_move_tofrom_meta[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_mapping[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_mapping_default[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_partial_info_mapping[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP9-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_mapping[WMAP9-mapping]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_to_cosmology_default[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_not_cosmology[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_from_cosmology_default[WMAP9]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP9-True]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP9-False]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP9-None]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_is_equivalent_to_cosmology[WMAP9-astropy.cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP9-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP9-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP9-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP9-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_tofromformat_complete_info[WMAP9-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP9-mapping-dict]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP9-yaml-str]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP9-astropy.cosmology-Cosmology]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP9-astropy.row-Row]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_subclass_complete_info[WMAP9-astropy.table-QTable]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP9-format_type0]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP9-format_type1]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP9-format_type2]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP9-format_type3]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_class_mismatch[WMAP9-format_type4]`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_model_wrong_cls`
- `astropy/cosmology/tests/test_connect.py::TestCosmologyToFromFormat::test_fromformat_model_subclass_partial_info`

## Existing Passing Tests To Preserve
- None provided.

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
