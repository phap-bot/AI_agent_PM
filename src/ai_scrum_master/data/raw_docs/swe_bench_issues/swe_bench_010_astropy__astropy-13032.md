# SWE-bench Issue: astropy__astropy-13032

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13032
- Base Commit: d707b792d3ca45518a53b4a395c81ee86bd7b451
- Environment Setup Commit: 298ccb478e6bf092953bca67a3d29dc6c35f6752
- Created At: 2022-03-31T16:32:46Z
- Version: 4.3

## Issue Title
Incorrect ignored usage in `ModelBoundingBox`

## Problem Statement
Incorrect ignored usage in `ModelBoundingBox`
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

Providing `ignored` inputs to `ModelBoundingBox` does not always work as expected.

Running the following code:
```python
from astropy.modeling.bounding_box import ModelBoundingBox
from astropy.modeling import models as astropy_models

bbox = ModelBoundingBox((9, 10), astropy_models.Polynomial2D(1), ignored=["x"])
print(bbox)
print(bbox.ignored_inputs)
```
Produces:
```
ModelBoundingBox(
    intervals={
        x: Interval(lower=9, upper=10)
    }
    model=Polynomial2D(inputs=('x', 'y'))
    order='C'
)
[]
```
This is incorrect. It instead should produce:
```
ModelBoundingBox(
    intervals={
        y: Interval(lower=9, upper=10)
    }
    model=Polynomial2D(inputs=('x', 'y'))
    order='C'
)
['x']
```

Somehow the `ignored` status of the `x` input is being accounted for during the validation which occurs during the construction of the bounding box; however, it is getting "lost" somehow resulting in the weird behavior we see above.

Oddly enough ignoring `y` does not have an issue. E.G. this code:
```python
from astropy.modeling.bounding_box import ModelBoundingBox
from astropy.modeling import models as astropy_models

bbox = ModelBoundingBox((11, 12), astropy_models.Polynomial2D(1), ignored=["y"])
print(bbox)
print(bbox.ignored_inputs)
```
Produces:
```
ModelBoundingBox(
    intervals={
        x: Interval(lower=11, upper=12)
    }
    ignored=['y']
    model=Polynomial2D(inputs=('x', 'y'))
    order='C'
)
['y']
```
as expected.

### System Details
This is present in both astropy 5.03 and astropy develop

## Issue Discussion Hints
You just can't differentiate between a robot and the very best of humans.

*(A special day message.)*

## Failing Tests That Should Pass
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_bounding_box_ignore`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test___repr__`

## Existing Passing Tests To Preserve
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test_create`
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test_copy`
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test__validate_shape`
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test__validate_bounds`
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test_validate`
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test_outside`
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test_domain`
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test__ignored_interval`
- `astropy/modeling/tests/test_bounding_box.py::Test_Interval::test_validate_with_SpectralCoord`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_create`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_copy`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_intervals`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_named_intervals`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test___repr__`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test___len__`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test___contains__`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test___getitem__`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_bounding_box`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test___eq__`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test__setitem__`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test___delitem__`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test__validate_dict`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test__validate_sequence`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test__n_inputs`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test__validate_iterable`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test__validate`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_validate`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_fix_inputs`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_dimension`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_domain`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test__outside`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test__valid_index`
- `astropy/modeling/tests/test_bounding_box.py::TestModelBoundingBox::test_prepare_inputs`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArgument::test_create`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArgument::test_validate`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArgument::test_get_selector`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArgument::test_name`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArgument::test_pretty_repr`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArgument::test_get_fixed_value`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArgument::test_is_argument`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArgument::test_named_tuple`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_create`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_pretty_repr`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_ignore`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_validate`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_get_selector`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_is_selector`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_get_fixed_values`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_is_argument`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_selector_index`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_add_ignore`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_reduce`
- `astropy/modeling/tests/test_bounding_box.py::Test_SelectorArguments::test_named_tuple`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_create`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_copy`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_bounding_boxes`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_selector_args`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_create_selector`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test__get_selector_key`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test___setitem__`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test__validate`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test___eq__`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_validate`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test___contains__`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test__create_bounding_box`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test___getitem__`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test__select_bounding_box`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_prepare_inputs`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test__matching_bounding_boxes`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test__fix_input_selector_arg`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test__fix_input_bbox_arg`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_fix_inputs`
- `astropy/modeling/tests/test_bounding_box.py::TestCompoundBoundingBox::test_complex_compound_bounding_box`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
