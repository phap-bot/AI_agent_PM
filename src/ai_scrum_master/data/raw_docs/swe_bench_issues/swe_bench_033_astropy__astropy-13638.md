# SWE-bench Issue: astropy__astropy-13638

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13638
- Base Commit: c00626462ee48a483791d92197582e7d1366c9e0
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-09-11T23:32:16Z
- Version: 5.0

## Issue Title
`Quantity.__ilshift__` throws exception with `dtype=int`

## Problem Statement
`Quantity.__ilshift__` throws exception with `dtype=int`
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

The `astropy.units.quantity_input` decorator throws a `UFuncTypeError` when used on a function that returns a `Quantity` with `dtype=int` and a return type annotation. 

### Expected behavior
<!-- What did you expect to happen. -->

For the function to return a `Quantity` with `dtype=int` with the appropriate units or to throw an exception if the output units are of the wrong type.

### Actual behavior
<!-- What actually happened. -->
<!-- Was the output confusing or poorly described? -->

Using the decorator results in a `UFuncTypeError`

### Steps to Reproduce

```python
import astropy.units as u
@u.quantity_input
def foo()->u.pix: return u.Quantity(1, 'pix', dtype=int)
foo()
```

gives

```python-traceback
---------------------------------------------------------------------------
UFuncTypeError                            Traceback (most recent call last)
Input In [26], in <cell line: 1>()
----> 1 foofoo()

File ~/anaconda/envs/aiapy-dev/lib/python3.9/site-packages/astropy/units/decorators.py:320, in QuantityInput.__call__.<locals>.wrapper(*func_args, **func_kwargs)
    316     _validate_arg_value("return", wrapped_function.__name__,
    317                         return_, valid_targets, self.equivalencies,
    318                         self.strict_dimensionless)
    319     if len(valid_targets) > 0:
--> 320         return_ <<= valid_targets[0]
    321 return return_

File ~/anaconda/envs/aiapy-dev/lib/python3.9/site-packages/astropy/units/quantity.py:1087, in Quantity.__ilshift__(self, other)
   1084     self.view(np.ndarray)[...] = value
   1086 else:
-> 1087     self.view(np.ndarray)[...] *= factor
   1089 self._set_unit(other)
   1090 return self

UFuncTypeError: Cannot cast ufunc 'multiply' output from dtype('float64') to dtype('int64') with casting rule 'same_kind'
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

```
macOS-10.16-x86_64-i386-64bit
Python 3.9.7 (default, Sep 16 2021, 08:50:36)
[Clang 10.0.0 ]
Numpy 1.22.3
pyerfa 2.0.0.1
astropy 5.0.2
Scipy 1.8.0
Matplotlib 3.5.1
```

## Issue Discussion Hints
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

GitHub issues in the Astropy repository are used to track bug reports and feature requests; If your issue poses a question about how to use Astropy, please instead raise your question in the [Astropy Discourse user forum](https://community.openastronomy.org/c/astropy/8) and close this issue.

If you feel that this issue has not been responded to in a timely manner, please leave a comment mentioning our software support engineer @embray, or send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
Don't you want fractional pixels?
In general, yes. My specific use case is perhaps a bit silly. There are times where I want to use the output of the function as the input for the shape for a new array (which has to be of type `int`). Without specifying `dtype=int`, I have to do `.value.astype(int)`.

I just struck me as odd that I can create a `Quantity` with `dtype=int`, but that this does not play nicely with the `quantity_input` decorator.
@Cadair , didn't you originally implemented that decorator?
I don't think the problem is with the decorator, but in `Quantity`.

```python
x = u.Quantity(10, u.km, dtype=int)
x <<= u.pc
```

will raise the same error.
I changed the issue name to reflect the source of the error.
@mhvk I think all we need to do is upcast the dtype of the view?

```python
self.view(float, np.ndarray)[...] *= factor
```

The question is what dtype to upcast to. Maybe
```python
dtype = np.result_type(x.dtype, type(factor))
x.view(dtype, np.ndarray)[...] *= factor
```
As noted in #13638, I'm wondering about whether we should actually fix this.  The previous behaviour is that
```
q = <some quantity>
q2 = q
q <<= new_unit
q2 is q
# always True
```
Similarly with views of `q` (i.e., shared memory).

Above, the request is either to raise an exception if the units are of the wrong type. Currently, we do raise an error but I guess it is very unclear what the actual problem is. So, my preferred route would be to place the inplace multiplication in an `try/except` and `raise UnitsError(...) from exc`. (I guess for consistency we might then have to do the same inside the check for unit transformations via equivalencies...)
The problem appears to be that numpy can't change int<->float dtype without copying. If that were possible this wouldn't be an issue.

```python
>>> x = np.arange(10, dtype=int)
>>> y = x.astype(float, copy=False)  # it copies despite this, because int->float = 😭 

>>> np.may_share_memory(x, y)
False
```
So either we give up the assurance of shared memory, or this should error for most cases.
We can make this work for the case that the dtype of ``factor`` in https://github.com/astropy/astropy/issues/12964#issuecomment-1073295287 is can cast to the same type (e.g. ``(10 * u.km) <<= u.m``  )
Yes, numpy cannot change in-place since also the number of bytes is not quaranteed to be the same (`int32` can only be represented safely as `float64`).

On second thought about the whole issue, though, I think it may make more sense to give up the guarantee of shared memory. In the end, what the user wants is quite clear. And in a lot of python, if `a <<= b` does not work, it returns `NotImplemented`, and then one gets `b.__rlshift(a)` instead. Indeed, this is how `array <<= unit` is able to return a quantity.

## Failing Tests That Should Pass
- `astropy/units/tests/test_quantity.py::test_regression_12964`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_inplace_conversion`

## Existing Passing Tests To Preserve
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_1`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_2`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_3`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_nan_inf`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_unit_property`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_preserve_dtype`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_numpy_style_dtype_inspect`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_float_dtype_promotion`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_copy`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_subok`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_order`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_ndmin`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_non_quantity_with_unit`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_creation_via_view`
- `astropy/units/tests/test_quantity.py::TestQuantityCreation::test_rshift_warns`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_addition`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_subtraction`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_multiplication`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_division`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_commutativity`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_power`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_matrix_multiplication`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_unary`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_abs`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_incompatible_units`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_non_number_type`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_dimensionless_operations`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_complicated_operation`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_comparison`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_numeric_converters`
- `astropy/units/tests/test_quantity.py::TestQuantityOperations::test_array_converters`
- `astropy/units/tests/test_quantity.py::test_quantity_conversion`
- `astropy/units/tests/test_quantity.py::test_quantity_ilshift`
- `astropy/units/tests/test_quantity.py::test_quantity_value_views`
- `astropy/units/tests/test_quantity.py::test_quantity_conversion_with_equiv`
- `astropy/units/tests/test_quantity.py::test_quantity_conversion_equivalency_passed_on`
- `astropy/units/tests/test_quantity.py::test_self_equivalency`
- `astropy/units/tests/test_quantity.py::test_si`
- `astropy/units/tests/test_quantity.py::test_cgs`
- `astropy/units/tests/test_quantity.py::TestQuantityComparison::test_quantity_equality`
- `astropy/units/tests/test_quantity.py::TestQuantityComparison::test_quantity_equality_array`
- `astropy/units/tests/test_quantity.py::TestQuantityComparison::test_quantity_comparison`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_dimensionless_quantity_repr`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_dimensionless_quantity_str`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_dimensionless_quantity_format`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_scalar_quantity_str`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_scalar_quantity_repr`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_array_quantity_str`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_array_quantity_repr`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_scalar_quantity_format`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_uninitialized_unit_format`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_to_string`
- `astropy/units/tests/test_quantity.py::TestQuantityDisplay::test_repr_latex`
- `astropy/units/tests/test_quantity.py::test_decompose`
- `astropy/units/tests/test_quantity.py::test_decompose_regression`
- `astropy/units/tests/test_quantity.py::test_arrays`
- `astropy/units/tests/test_quantity.py::test_array_indexing_slicing`
- `astropy/units/tests/test_quantity.py::test_array_setslice`
- `astropy/units/tests/test_quantity.py::test_inverse_quantity`
- `astropy/units/tests/test_quantity.py::test_quantity_mutability`
- `astropy/units/tests/test_quantity.py::test_quantity_initialized_with_quantity`
- `astropy/units/tests/test_quantity.py::test_quantity_string_unit`
- `astropy/units/tests/test_quantity.py::test_quantity_invalid_unit_string`
- `astropy/units/tests/test_quantity.py::test_implicit_conversion`
- `astropy/units/tests/test_quantity.py::test_implicit_conversion_autocomplete`
- `astropy/units/tests/test_quantity.py::test_quantity_iterability`
- `astropy/units/tests/test_quantity.py::test_copy`
- `astropy/units/tests/test_quantity.py::test_deepcopy`
- `astropy/units/tests/test_quantity.py::test_equality_numpy_scalar`
- `astropy/units/tests/test_quantity.py::test_quantity_pickelability`
- `astropy/units/tests/test_quantity.py::test_quantity_initialisation_from_string`
- `astropy/units/tests/test_quantity.py::test_unsupported`
- `astropy/units/tests/test_quantity.py::test_unit_identity`
- `astropy/units/tests/test_quantity.py::test_quantity_to_view`
- `astropy/units/tests/test_quantity.py::test_quantity_tuple_power`
- `astropy/units/tests/test_quantity.py::test_quantity_fraction_power`
- `astropy/units/tests/test_quantity.py::test_quantity_from_table`
- `astropy/units/tests/test_quantity.py::test_assign_slice_with_quantity_like`
- `astropy/units/tests/test_quantity.py::test_insert`
- `astropy/units/tests/test_quantity.py::test_repr_array_of_quantity`
- `astropy/units/tests/test_quantity.py::test_unit_class_override`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_input[QuantityMimic]`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_input[QuantityMimic2]`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_setting[QuantityMimic]`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_setting[QuantityMimic2]`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_function_unit`
- `astropy/units/tests/test_quantity.py::test_masked_quantity_str_repr`
- `astropy/units/tests/test_quantity.py::TestQuantitySubclassAboveAndBelow::test_setup`
- `astropy/units/tests/test_quantity.py::TestQuantitySubclassAboveAndBelow::test_attr_propagation`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialization_and_keying`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_recursive_initialization`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_extreme_recursive_initialization`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialization_names_invalid_list_errors[names0-['p',`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialization_names_invalid_list_errors[names1-['pv',`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialization_names_invalid_list_errors[names2-['pv',`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialization_names_invalid_list_errors[names3-()]`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialization_names_invalid_list_errors[names4-None]`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialization_names_invalid_list_errors[names5-'']`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_looks_like_unit`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialize_with_float_dtype`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialize_with_structured_unit_for_names`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_initialize_single_field`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_equality`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_parsing`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_to_string`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_str`
- `astropy/units/tests/test_structured.py::TestStructuredUnitBasics::test_repr`
- `astropy/units/tests/test_structured.py::TestStructuredUnitsCopyPickle::test_copy`
- `astropy/units/tests/test_structured.py::TestStructuredUnitsCopyPickle::test_deepcopy`
- `astropy/units/tests/test_structured.py::TestStructuredUnitsCopyPickle::test_pickle[0]`
- `astropy/units/tests/test_structured.py::TestStructuredUnitsCopyPickle::test_pickle[1]`
- `astropy/units/tests/test_structured.py::TestStructuredUnitsCopyPickle::test_pickle[-1]`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_len`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_keys`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_values`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_field_names`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_as_iterable[list]`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_as_iterable[set]`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_as_dict`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_contains`
- `astropy/units/tests/test_structured.py::TestStructuredUnitAsMapping::test_setitem_fails`
- `astropy/units/tests/test_structured.py::TestStructuredUnitMethods::test_physical_type_id`
- `astropy/units/tests/test_structured.py::TestStructuredUnitMethods::test_physical_type`
- `astropy/units/tests/test_structured.py::TestStructuredUnitMethods::test_si`
- `astropy/units/tests/test_structured.py::TestStructuredUnitMethods::test_cgs`
- `astropy/units/tests/test_structured.py::TestStructuredUnitMethods::test_decompose`
- `astropy/units/tests/test_structured.py::TestStructuredUnitMethods::test_is_equivalent`
- `astropy/units/tests/test_structured.py::TestStructuredUnitMethods::test_conversion`
- `astropy/units/tests/test_structured.py::TestStructuredUnitArithmatic::test_multiplication`
- `astropy/units/tests/test_structured.py::TestStructuredUnitArithmatic::test_division`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_initialization_and_keying`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_initialization_with_unit_tuples`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_initialization_with_string`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_initialization_by_multiplication_with_unit`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_initialization_by_shifting_to_unit`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_initialization_without_unit`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_getitem`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_value`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_conversion`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_conversion_via_lshift`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_si`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_cgs`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_equality`
- `astropy/units/tests/test_structured.py::TestStructuredQuantity::test_setitem`
- `astropy/units/tests/test_structured.py::TestStructuredQuantityFunctions::test_empty_like`
- `astropy/units/tests/test_structured.py::TestStructuredQuantityFunctions::test_zeros_ones_like[zeros_like]`
- `astropy/units/tests/test_structured.py::TestStructuredQuantityFunctions::test_zeros_ones_like[ones_like]`
- `astropy/units/tests/test_structured.py::TestStructuredQuantityFunctions::test_structured_to_unstructured`
- `astropy/units/tests/test_structured.py::TestStructuredQuantityFunctions::test_unstructured_to_structured`
- `astropy/units/tests/test_structured.py::TestStructuredSpecificTypeQuantity::test_init`
- `astropy/units/tests/test_structured.py::TestStructuredSpecificTypeQuantity::test_error_on_non_equivalent_unit`
- `astropy/units/tests/test_structured.py::TestStructuredLogUnit::test_unit_initialization`
- `astropy/units/tests/test_structured.py::TestStructuredLogUnit::test_quantity_initialization`
- `astropy/units/tests/test_structured.py::TestStructuredLogUnit::test_quantity_si`
- `astropy/units/tests/test_structured.py::TestStructuredMaskedQuantity::test_init`
- `astropy/units/tests/test_structured.py::TestStructuredMaskedQuantity::test_slicing`
- `astropy/units/tests/test_structured.py::TestStructuredMaskedQuantity::test_conversion`
- `astropy/units/tests/test_structured.py::TestStructuredMaskedQuantity::test_si`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
