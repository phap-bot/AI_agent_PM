# SWE-bench Issue: astropy__astropy-13390

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13390
- Base Commit: 1e75f298aef2540240c63b4075d06851d55fc19a
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-06-23T20:06:08Z
- Version: 5.0

## Issue Title
BUG: Table test failures with np 1.23.0rc3

## Problem Statement
BUG: Table test failures with np 1.23.0rc3
```
====================================================================== FAILURES =======================================================================
__________________________________________________________ test_col_unicode_sandwich_unicode __________________________________________________________
numpy.core._exceptions._UFuncNoLoopError: ufunc 'not_equal' did not contain a loop with signature matching types (<class 'numpy.dtype[str_]'>, <class 'numpy.dtype[bytes_]'>) -> None

The above exception was the direct cause of the following exception:

    def test_col_unicode_sandwich_unicode():
        """
        Sanity check that Unicode Column behaves normally.
        """
        uba = 'bä'
        uba8 = uba.encode('utf-8')
    
        c = table.Column([uba, 'def'], dtype='U')
        assert c[0] == uba
        assert isinstance(c[:0], table.Column)
        assert isinstance(c[0], str)
        assert np.all(c[:2] == np.array([uba, 'def']))
    
        assert isinstance(c[:], table.Column)
        assert c[:].dtype.char == 'U'
    
        ok = c == [uba, 'def']
        assert type(ok) == np.ndarray
        assert ok.dtype.char == '?'
        assert np.all(ok)
    
>       assert np.all(c != [uba8, b'def'])

astropy/table/tests/test_column.py:777: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <Column dtype='str3' length=2>
 bä
def, other = [b'b\xc3\xa4', b'def']

    def _compare(self, other):
        op = oper  # copy enclosed ref to allow swap below
    
        # Special case to work around #6838.  Other combinations work OK,
        # see tests.test_column.test_unicode_sandwich_compare().  In this
        # case just swap self and other.
        #
        # This is related to an issue in numpy that was addressed in np 1.13.
        # However that fix does not make this problem go away, but maybe
        # future numpy versions will do so.  NUMPY_LT_1_13 to get the
        # attention of future maintainers to check (by deleting or versioning
        # the if block below).  See #6899 discussion.
        # 2019-06-21: still needed with numpy 1.16.
        if (isinstance(self, MaskedColumn) and self.dtype.kind == 'U'
                and isinstance(other, MaskedColumn) and other.dtype.kind == 'S'):
            self, other = other, self
            op = swapped_oper
    
        if self.dtype.char == 'S':
            other = self._encode_str(other)
    
        # Now just let the regular ndarray.__eq__, etc., take over.
>       result = getattr(super(Column, self), op)(other)
E       FutureWarning: elementwise comparison failed; returning scalar instead, but in the future will perform elementwise comparison

astropy/table/column.py:329: FutureWarning
______________________________________________ test_unicode_sandwich_compare[MaskedColumn-MaskedColumn] _______________________________________________

class1 = <class 'astropy.table.column.MaskedColumn'>, class2 = <class 'astropy.table.column.MaskedColumn'>

    @pytest.mark.parametrize('class1', [table.MaskedColumn, table.Column])
    @pytest.mark.parametrize('class2', [table.MaskedColumn, table.Column, str, list])
    def test_unicode_sandwich_compare(class1, class2):
        """Test that comparing a bytestring Column/MaskedColumn with various
        str (unicode) object types gives the expected result.  Tests #6838.
        """
        obj1 = class1([b'a', b'c'])
        if class2 is str:
            obj2 = 'a'
        elif class2 is list:
            obj2 = ['a', 'b']
        else:
            obj2 = class2(['a', 'b'])
    
        assert np.all((obj1 == obj2) == [True, False])
        assert np.all((obj2 == obj1) == [True, False])
    
        assert np.all((obj1 != obj2) == [False, True])
        assert np.all((obj2 != obj1) == [False, True])
    
>       assert np.all((obj1 > obj2) == [False, True])
E       TypeError: '>' not supported between instances of 'MaskedColumn' and 'MaskedColumn'

astropy/table/tests/test_column.py:857: TypeError
_________________________________________________ test_unicode_sandwich_compare[Column-MaskedColumn] __________________________________________________

class1 = <class 'astropy.table.column.MaskedColumn'>, class2 = <class 'astropy.table.column.Column'>

    @pytest.mark.parametrize('class1', [table.MaskedColumn, table.Column])
    @pytest.mark.parametrize('class2', [table.MaskedColumn, table.Column, str, list])
    def test_unicode_sandwich_compare(class1, class2):
        """Test that comparing a bytestring Column/MaskedColumn with various
        str (unicode) object types gives the expected result.  Tests #6838.
        """
        obj1 = class1([b'a', b'c'])
        if class2 is str:
            obj2 = 'a'
        elif class2 is list:
            obj2 = ['a', 'b']
        else:
            obj2 = class2(['a', 'b'])
    
        assert np.all((obj1 == obj2) == [True, False])
        assert np.all((obj2 == obj1) == [True, False])
    
        assert np.all((obj1 != obj2) == [False, True])
        assert np.all((obj2 != obj1) == [False, True])
    
>       assert np.all((obj1 > obj2) == [False, True])
E       TypeError: '>' not supported between instances of 'MaskedColumn' and 'Column'

astropy/table/tests/test_column.py:857: TypeError
____________________________________________________ test_unicode_sandwich_compare[Column-Column] _____________________________________________________
numpy.core._exceptions._UFuncNoLoopError: ufunc 'equal' did not contain a loop with signature matching types (<class 'numpy.dtype[str_]'>, <class 'numpy.dtype[bytes_]'>) -> None

The above exception was the direct cause of the following exception:

class1 = <class 'astropy.table.column.Column'>, class2 = <class 'astropy.table.column.Column'>

    @pytest.mark.parametrize('class1', [table.MaskedColumn, table.Column])
    @pytest.mark.parametrize('class2', [table.MaskedColumn, table.Column, str, list])
    def test_unicode_sandwich_compare(class1, class2):
        """Test that comparing a bytestring Column/MaskedColumn with various
        str (unicode) object types gives the expected result.  Tests #6838.
        """
        obj1 = class1([b'a', b'c'])
        if class2 is str:
            obj2 = 'a'
        elif class2 is list:
            obj2 = ['a', 'b']
        else:
            obj2 = class2(['a', 'b'])
    
        assert np.all((obj1 == obj2) == [True, False])
>       assert np.all((obj2 == obj1) == [True, False])

astropy/table/tests/test_column.py:852: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _

self = <Column dtype='str1' length=2>
a
b, other = <Column dtype='bytes1' length=2>
a
c

    def _compare(self, other):
        op = oper  # copy enclosed ref to allow swap below
    
        # Special case to work around #6838.  Other combinations work OK,
        # see tests.test_column.test_unicode_sandwich_compare().  In this
        # case just swap self and other.
        #
        # This is related to an issue in numpy that was addressed in np 1.13.
        # However that fix does not make this problem go away, but maybe
        # future numpy versions will do so.  NUMPY_LT_1_13 to get the
        # attention of future maintainers to check (by deleting or versioning
        # the if block below).  See #6899 discussion.
        # 2019-06-21: still needed with numpy 1.16.
        if (isinstance(self, MaskedColumn) and self.dtype.kind == 'U'
                and isinstance(other, MaskedColumn) and other.dtype.kind == 'S'):
            self, other = other, self
            op = swapped_oper
    
        if self.dtype.char == 'S':
            other = self._encode_str(other)
    
        # Now just let the regular ndarray.__eq__, etc., take over.
>       result = getattr(super(Column, self), op)(other)
E       FutureWarning: elementwise comparison failed; returning scalar instead, but in the future will perform elementwise comparison

astropy/table/column.py:329: FutureWarning
___________________________________________________ test_unicode_sandwich_compare[str-MaskedColumn] ___________________________________________________

class1 = <class 'astropy.table.column.MaskedColumn'>, class2 = <class 'str'>

    @pytest.mark.parametrize('class1', [table.MaskedColumn, table.Column])
    @pytest.mark.parametrize('class2', [table.MaskedColumn, table.Column, str, list])
    def test_unicode_sandwich_compare(class1, class2):
        """Test that comparing a bytestring Column/MaskedColumn with various
        str (unicode) object types gives the expected result.  Tests #6838.
        """
        obj1 = class1([b'a', b'c'])
        if class2 is str:
            obj2 = 'a'
        elif class2 is list:
            obj2 = ['a', 'b']
        else:
            obj2 = class2(['a', 'b'])
    
        assert np.all((obj1 == obj2) == [True, False])
        assert np.all((obj2 == obj1) == [True, False])
    
        assert np.all((obj1 != obj2) == [False, True])
        assert np.all((obj2 != obj1) == [False, True])
    
>       assert np.all((obj1 > obj2) == [False, True])
E       TypeError: '>' not supported between instances of 'MaskedColumn' and 'str'

astropy/table/tests/test_column.py:857: TypeError
__________________________________________________ test_unicode_sandwich_compare[list-MaskedColumn] ___________________________________________________

class1 = <class 'astropy.table.column.MaskedColumn'>, class2 = <class 'list'>

    @pytest.mark.parametrize('class1', [table.MaskedColumn, table.Column])
    @pytest.mark.parametrize('class2', [table.MaskedColumn, table.Column, str, list])
    def test_unicode_sandwich_compare(class1, class2):
        """Test that comparing a bytestring Column/MaskedColumn with various
        str (unicode) object types gives the expected result.  Tests #6838.
        """
        obj1 = class1([b'a', b'c'])
        if class2 is str:
            obj2 = 'a'
        elif class2 is list:
            obj2 = ['a', 'b']
        else:
            obj2 = class2(['a', 'b'])
    
        assert np.all((obj1 == obj2) == [True, False])
        assert np.all((obj2 == obj1) == [True, False])
    
        assert np.all((obj1 != obj2) == [False, True])
        assert np.all((obj2 != obj1) == [False, True])
    
>       assert np.all((obj1 > obj2) == [False, True])
E       TypeError: '>' not supported between instances of 'MaskedColumn' and 'list'

astropy/table/tests/test_column.py:857: TypeError
=============================================================== short test summary info ===============================================================
FAILED astropy/table/tests/test_column.py::test_col_unicode_sandwich_unicode - FutureWarning: elementwise comparison failed; returning scalar instea...
FAILED astropy/table/tests/test_column.py::test_unicode_sandwich_compare[MaskedColumn-MaskedColumn] - TypeError: '>' not supported between instances...
FAILED astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-MaskedColumn] - TypeError: '>' not supported between instances of 'M...
FAILED astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-Column] - FutureWarning: elementwise comparison failed; returning sc...
FAILED astropy/table/tests/test_column.py::test_unicode_sandwich_compare[str-MaskedColumn] - TypeError: '>' not supported between instances of 'Mask...
FAILED astropy/table/tests/test_column.py::test_unicode_sandwich_compare[list-MaskedColumn] - TypeError: '>' not supported between instances of 'Mas...
=============================================== 6 failed, 3377 passed, 43 skipped, 14 xfailed in 25.62s ===============================================

```

## Issue Discussion Hints
Related details: https://github.com/astropy/astroquery/issues/2440#issuecomment-1155588504
xref https://github.com/numpy/numpy/pull/21041
It was merged 4 days ago, so does this mean it went into the RC before it hits the "nightly wheel" that we tests against here?
ahh, good point, I forgot that the "nightly" is not in fact a daily build, that at least takes the confusion away of how a partial backport could happen that makes the RC fail but the dev still pass.
Perhaps Numpy could have a policy to refresh the "nightly wheel" along with RC to make sure last-minute backport like this won't go unnoticed for those who test against "nightly"? 🤔 
There you go: https://github.com/numpy/numpy/issues/21758
It seems there are two related problems.
1. When a column is unicode, a comparison with bytes now raises a `FutureWarning`, which leads to a failure in the tests. Here, we can either filter out the warning in our tests, or move to the future and raise a `TypeError`.
2. When one of the two is a `MaskedColumn`, the unicode sandwich somehow gets skipped. This is weird...
See https://github.com/numpy/numpy/issues/21770
Looks like Numpy is thinking to [undo the backport](https://github.com/numpy/numpy/issues/21770#issuecomment-1157077479). If that happens, then we have more time to think about this.
Are these errors related to the same numpy backport? Maybe we finally seeing it in "nightly wheel" and it does not look pretty (45 failures over several subpackages) -- https://github.com/astropy/astropy/runs/6918680788?check_suite_focus=true
@pllim - those other errors are actually due to a bug in `Quantity`, where the unit of an `initial` argument is not taken into account (and where units are no longer stripped in numpy). Working on a fix...
Well, *some* of the new failures are resolved by my fix - but at least it also fixes behaviour for all previous versions of numpy! See #13340.
The remainder all seem to be due to a new check on overflow on casting - we're trying to write `1e45` in a `float32` - see #13341
After merging a few PRs to fix other dev failures, these are the remaining ones in `main` now. Please advise on what we should do next to get rid of these 21 failures. Thanks!

Example log: https://github.com/astropy/astropy/runs/6936666794?check_suite_focus=true

```
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_pathlib
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_meta
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_noextension
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_units[Table]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_units[QTable]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_format[Table]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_format[QTable]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_character_as_bytes[False]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_character_as_bytes[True]
FAILED .../astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model11]
FAILED .../astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model22]
FAILED .../astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model11]
FAILED .../astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model22]
FAILED .../astropy/table/tests/test_column.py::test_col_unicode_sandwich_unicode
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[MaskedColumn-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-Column]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[str-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[list-MaskedColumn]
FAILED .../astropy/table/tests/test_init_table.py::TestInitFromTable::test_partial_names_dtype[True]
```
FWIW, I have #13349 that picked up the RC in question here and you can see there are only 17 failures (4 less from using numpy's "nightly wheel").

Example log: https://github.com/astropy/astropy/runs/6937240337?check_suite_focus=true

```
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_pathlib
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_meta
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_noextension
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_units[Table]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_units[QTable]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_format[Table]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_format[QTable]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_character_as_bytes[False]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_character_as_bytes[True]
FAILED .../astropy/io/misc/tests/test_hdf5.py::test_read_write_unicode_to_hdf5
FAILED .../astropy/table/tests/test_column.py::test_col_unicode_sandwich_unicode
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[MaskedColumn-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-Column]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[str-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[list-MaskedColumn]
```

So...

# In both "nightly wheel" and RC

```
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_pathlib
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_meta
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_simple_noextension
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_units[Table]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_units[QTable]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_format[Table]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_with_format[QTable]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_character_as_bytes[False]
FAILED .../astropy/io/fits/tests/test_connect.py::TestSingleTable::test_character_as_bytes[True]
FAILED .../astropy/table/tests/test_column.py::test_col_unicode_sandwich_unicode
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[MaskedColumn-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-Column]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[str-MaskedColumn]
FAILED .../astropy/table/tests/test_column.py::test_unicode_sandwich_compare[list-MaskedColumn]
```

# RC only

I don't understand why this one only pops up in the RC but not in dev. 🤷 

```
FAILED .../astropy/io/misc/tests/test_hdf5.py::test_read_write_unicode_to_hdf5
```

# "nightly wheel" only

```
FAILED .../astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model11]
FAILED .../astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model22]
FAILED .../astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model11]
FAILED .../astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model22]
FAILED .../astropy/table/tests/test_init_table.py::TestInitFromTable::test_partial_names_dtype[True]
```
@pllim - with the corrections to the rc3, i.e., numpy 1.23.x (1.23.0rc3+10.gcc0e08d20), the failures in `io.fits`, `io.misc`, and `table` are all gone -- all tests pass! So, we can now move to address the problems in `numpy-dev`.
Will there be a rc4?
Looks like numpy released 1.23 🤞 
I am anxiously waiting for the "nightly wheel" to catch up. The other CI jobs passing even after the new release, so at least that is a good sign. 🤞 
I actually don't know that `-dev` was changed too - I think they just reverted the bad commit from 1.23, with the idea that for 1.24 there would be a fix (IIRC, https://github.com/numpy/numpy/pull/21812 would solve at least some of the problems)

## Failing Tests That Should Pass
- `astropy/table/tests/test_column.py::TestColumn::test_quantity_comparison[MaskedColumn]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-Column]`

## Existing Passing Tests To Preserve
- `astropy/table/tests/test_column.py::TestColumn::test_subclass[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_subclass[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_numpy_ops[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_numpy_ops[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_numpy_boolean_ufuncs[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_numpy_boolean_ufuncs[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_view[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_view[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_format[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_format[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_convert_numpy_array[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_convert_numpy_array[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_convert_unit[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_convert_unit[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_array_wrap`
- `astropy/table/tests/test_column.py::TestColumn::test_name_none[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_name_none[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_quantity_init[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_quantity_init[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_quantity_comparison[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_attrs_survive_getitem_after_change[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_attrs_survive_getitem_after_change[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_to_quantity[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_to_quantity[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_to_funcunit_quantity[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_to_funcunit_quantity[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_item_access_type[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_item_access_type[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_basic[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_basic[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_axis[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_axis[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_string_expand[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_string_expand[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_string_masked_values`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_string_type_error[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_string_type_error[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_multidim[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_multidim[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_object[Column]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_object[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_masked`
- `astropy/table/tests/test_column.py::TestColumn::test_masked_multidim_as_list`
- `astropy/table/tests/test_column.py::TestColumn::test_insert_masked_multidim`
- `astropy/table/tests/test_column.py::TestColumn::test_mask_on_non_masked_table`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_5[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_5[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_6[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_6[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_7[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_7[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_8[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_8[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_9[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_9[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_10[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_10[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_11[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_11[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_12[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_12[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_13[Column]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_13[MaskedColumn]`
- `astropy/table/tests/test_column.py::TestAttrEqual::test_col_and_masked_col`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_none`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_mapping_init[meta0]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_mapping_init[meta1]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_mapping_init[meta2]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_non_mapping_init[ceci`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_non_mapping_init[1.2]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_non_mapping_init[meta2]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_mapping_set[meta0]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_mapping_set[meta1]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_mapping_set[meta2]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_non_mapping_set[ceci`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_non_mapping_set[1.2]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_non_mapping_set[meta2]`
- `astropy/table/tests/test_column.py::TestMetaColumn::test_meta_fits_header`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_none`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_mapping_init[meta0]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_mapping_init[meta1]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_mapping_init[meta2]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_non_mapping_init[ceci`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_non_mapping_init[1.2]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_non_mapping_init[meta2]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_mapping_set[meta0]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_mapping_set[meta1]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_mapping_set[meta2]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_non_mapping_set[ceci`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_non_mapping_set[1.2]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_non_mapping_set[meta2]`
- `astropy/table/tests/test_column.py::TestMetaMaskedColumn::test_meta_fits_header`
- `astropy/table/tests/test_column.py::test_getitem_metadata_regression`
- `astropy/table/tests/test_column.py::test_unicode_guidelines`
- `astropy/table/tests/test_column.py::test_scalar_column`
- `astropy/table/tests/test_column.py::test_qtable_column_conversion`
- `astropy/table/tests/test_column.py::test_string_truncation_warning[True]`
- `astropy/table/tests/test_column.py::test_string_truncation_warning[False]`
- `astropy/table/tests/test_column.py::test_string_truncation_warning_masked`
- `astropy/table/tests/test_column.py::test_col_unicode_sandwich_create_from_str[Column]`
- `astropy/table/tests/test_column.py::test_col_unicode_sandwich_create_from_str[MaskedColumn]`
- `astropy/table/tests/test_column.py::test_col_unicode_sandwich_bytes_obj[Column]`
- `astropy/table/tests/test_column.py::test_col_unicode_sandwich_bytes_obj[MaskedColumn]`
- `astropy/table/tests/test_column.py::test_col_unicode_sandwich_bytes[Column]`
- `astropy/table/tests/test_column.py::test_col_unicode_sandwich_bytes[MaskedColumn]`
- `astropy/table/tests/test_column.py::test_col_unicode_sandwich_unicode`
- `astropy/table/tests/test_column.py::test_masked_col_unicode_sandwich`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_set[Column]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_set[MaskedColumn]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_compare[MaskedColumn-MaskedColumn]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_compare[MaskedColumn-Column]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_compare[Column-MaskedColumn]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_compare[str-MaskedColumn]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_compare[str-Column]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_compare[list-MaskedColumn]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_compare[list-Column]`
- `astropy/table/tests/test_column.py::test_unicode_sandwich_masked_compare`
- `astropy/table/tests/test_column.py::test_structured_masked_column_roundtrip`
- `astropy/table/tests/test_column.py::test_structured_empty_column_init[i4,f4]`
- `astropy/table/tests/test_column.py::test_structured_empty_column_init[f4,(2,)f8]`
- `astropy/table/tests/test_column.py::test_column_value_access`
- `astropy/table/tests/test_column.py::test_masked_column_serialize_method_propagation`
- `astropy/table/tests/test_column.py::test_searchsorted[Column-S]`
- `astropy/table/tests/test_column.py::test_searchsorted[Column-U]`
- `astropy/table/tests/test_column.py::test_searchsorted[Column-i]`
- `astropy/table/tests/test_column.py::test_searchsorted[MaskedColumn-S]`
- `astropy/table/tests/test_column.py::test_searchsorted[MaskedColumn-U]`
- `astropy/table/tests/test_column.py::test_searchsorted[MaskedColumn-i]`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
