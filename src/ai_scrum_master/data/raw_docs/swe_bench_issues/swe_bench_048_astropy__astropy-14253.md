# SWE-bench Issue: astropy__astropy-14253

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-14253
- Base Commit: dd2304672cdf4ea1b6f124f9f22ec5069a13c9f5
- Environment Setup Commit: 5f74eacbcc7fff707a44d8eb58adaa514cb7dcb5
- Created At: 2023-01-04T19:59:52Z
- Version: 5.1

## Issue Title
When should `info` be linked to a new object?

## Problem Statement
When should `info` be linked to a new object?
Mostly for @taldcroft - I noticed that in `Quantity` the way we have set up `__array_finalize__`, `info` is passed on not just for views (where it should be), but also for copies (implicitly in arithmetic operations, etc.). Which ones are reasonable?  Just thinking about whether, e.g., `info.name` should be propagated, I'd think:
- Surely for
  - views & reshapes: `q[...]`, `q.squeeze`, etc.
  - insertions: `q.insert(...)`
- Probably for
  - selection of scalars: `q[0]` or in `for q1 in q:` (for columns this returns a scalar without `info`)
  - copies: `q.copy()` and equivalents
  - equivalent unit changes: `q.to(...)`, `q.si`, `q.decompose()`, etc.
- Probably not for
  - operations `q3 = q1 + q2`
  - real unit changes `q * unit` (including in-place??; `q /= u.m`)

What do you think?

p.s. Currently, all of the above happen, in part because I use `__array_finalize__` in `Quantity._new_view`, something which I don't think we had really considered when we made the change in `__array_finalize__`. But that also means that in principle it may not too hard to fairly finely define the behaviour.

## Issue Discussion Hints
@mhvk - I basically agree with your assessment as being logical.  I guess the only question is about having an easily stated rule for what happens.  I wonder if we could make a rule (with a corresponding implementation) which is basically: "Any unary operation on a Quantity will preserve the `info` attribute if defined".  So that would put your "real unit changes.." bullet into the "yes" category.

That makes some sense, but I think I'd treat `q * unit` as a binary operation still (even if it isn't quite implemented that way; I do think it would be confusing if there is a difference in behaviour between that and `q * (1*unit)` (note that the implementation already makes a copy of `q`).

Also, "unary" may be too broad: I don't think I'd want `np.sin(q)` to keep the `info` attribute... 

@mhvk - agreed.  My main point is to strive to make the behavior predictable.

## Failing Tests That Should Pass
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_unary_op`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_binary_op`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_unit_change`
- `astropy/units/tests/test_quantity_info.py::TestStructuredQuantity::test_keying`

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
- `astropy/units/tests/test_quantity.py::test_regression_12964`
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
- `astropy/units/tests/test_quantity.py::TestSpecificTypeQuantity::test_creation`
- `astropy/units/tests/test_quantity.py::TestSpecificTypeQuantity::test_view`
- `astropy/units/tests/test_quantity.py::TestSpecificTypeQuantity::test_operation_precedence_and_fallback`
- `astropy/units/tests/test_quantity.py::test_unit_class_override`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_input[QuantityMimic]`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_input[QuantityMimic2]`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_setting[QuantityMimic]`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_setting[QuantityMimic2]`
- `astropy/units/tests/test_quantity.py::TestQuantityMimics::test_mimic_function_unit`
- `astropy/units/tests/test_quantity.py::test_masked_quantity_str_repr`
- `astropy/units/tests/test_quantity.py::TestQuantitySubclassAboveAndBelow::test_setup`
- `astropy/units/tests/test_quantity.py::TestQuantitySubclassAboveAndBelow::test_attr_propagation`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_copy`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_slice`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_item`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_iter`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_change_to_equivalent_unit`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_reshape`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_insert`
- `astropy/units/tests/test_quantity_info.py::TestQuantityInfo::test_inplace_unit_change`
- `astropy/units/tests/test_quantity_info.py::TestStructuredQuantity::test_slicing`
- `astropy/units/tests/test_quantity_info.py::TestStructuredQuantity::test_item`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
