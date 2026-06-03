# SWE-bench Issue: astropy__astropy-13158

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13158
- Base Commit: b185ca184f8dd574531dcc21e797f00537fefa6a
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-04-22T17:32:23Z
- Version: 5.0

## Issue Title
Model evaluation fails if any model parameter is a `MagUnit` type value

## Problem Statement
Model evaluation fails if any model parameter is a `MagUnit` type value
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
As discovered by @larrybradley in PR #13116, models will fail to evaluate when one of the parameters has a `MagUnit`.

A simplified reproducer is the following code:
```python
from astropy.modeling.models import Const1D
import astropy.units as u

unit = u.ABmag
c = -20.0 * unit
model = Const1D(c)

model(-23.0 * unit)
```

This should evaluate cleanly to `-20.0 * unit`. Instead one gets the following traceback:
```python
---------------------------------------------------------------------------
UnitTypeError                             Traceback (most recent call last)
Input In [1], in <cell line: 8>()
      5 c = -20.0 * unit
      6 model = Const1D(c)
----> 8 model(-23.0 * unit)

File ~/projects/astropy/astropy/modeling/core.py:397, in __call__(self, model_set_axis, with_bounding_box, fill_value, equivalencies, inputs_map, *inputs, **new_inputs)
    390 args = ('self',)
    391 kwargs = dict([('model_set_axis', None),
    392                ('with_bounding_box', False),
    393                ('fill_value', np.nan),
    394                ('equivalencies', None),
    395                ('inputs_map', None)])
--> 397 new_call = make_function_with_signature(
    398     __call__, args, kwargs, varargs='inputs', varkwargs='new_inputs')
    400 # The following makes it look like __call__
    401 # was defined in the class
    402 update_wrapper(new_call, cls)

File ~/projects/astropy/astropy/modeling/core.py:376, in _ModelMeta._handle_special_methods.<locals>.__call__(self, *inputs, **kwargs)
    374 def __call__(self, *inputs, **kwargs):
    375     """Evaluate this model on the supplied inputs."""
--> 376     return super(cls, self).__call__(*inputs, **kwargs)

File ~/projects/astropy/astropy/modeling/core.py:1077, in Model.__call__(self, *args, **kwargs)
   1074 fill_value = kwargs.pop('fill_value', np.nan)
   1076 # prepare for model evaluation (overridden in CompoundModel)
-> 1077 evaluate, inputs, broadcasted_shapes, kwargs = self._pre_evaluate(*args, **kwargs)
   1079 outputs = self._generic_evaluate(evaluate, inputs,
   1080                                  fill_value, with_bbox)
   1082 # post-process evaluation results (overridden in CompoundModel)

File ~/projects/astropy/astropy/modeling/core.py:936, in Model._pre_evaluate(self, *args, **kwargs)
    933 inputs, broadcasted_shapes = self.prepare_inputs(*args, **kwargs)
    935 # Setup actual model evaluation method
--> 936 parameters = self._param_sets(raw=True, units=True)
    938 def evaluate(_inputs):
    939     return self.evaluate(*chain(_inputs, parameters))

File ~/projects/astropy/astropy/modeling/core.py:2704, in Model._param_sets(self, raw, units)
   2702             unit = param.unit
   2703         if unit is not None:
-> 2704             value = Quantity(value, unit)
   2706     values.append(value)
   2708 if len(set(shapes)) != 1 or units:
   2709     # If the parameters are not all the same shape, converting to an
   2710     # array is going to produce an object array
   (...)
   2715     # arrays.  There's not much reason to do this over returning a list
   2716     # except for consistency

File ~/projects/astropy/astropy/units/quantity.py:522, in Quantity.__new__(cls, value, unit, dtype, copy, order, subok, ndmin)
    519         cls = qcls
    521 value = value.view(cls)
--> 522 value._set_unit(value_unit)
    523 if unit is value_unit:
    524     return value

File ~/projects/astropy/astropy/units/quantity.py:764, in Quantity._set_unit(self, unit)
    762         unit = Unit(str(unit), parse_strict='silent')
    763         if not isinstance(unit, (UnitBase, StructuredUnit)):
--> 764             raise UnitTypeError(
    765                 "{} instances require normal units, not {} instances."
    766                 .format(type(self).__name__, type(unit)))
    768 self._unit = unit

UnitTypeError: Quantity instances require normal units, not <class 'astropy.units.function.logarithmic.MagUnit'> instances.
```

I believe the issue might lie in `astropy.modeling.core` with this call:
https://github.com/astropy/astropy/blob/675dc03e138d5c6a1cb6936a6b2c3211f39049d3/astropy/modeling/core.py#L2703-L2704

I think more sophisticated logic for handling turning parameters into quantity like values needs to be included here, or possibly a refactor of the [`._param_sets`](https://github.com/astropy/astropy/blob/675dc03e138d5c6a1cb6936a6b2c3211f39049d3/astropy/modeling/core.py#L2662) method in general. I would like some input from those with more familiarity with the intricacies of the `astropy.units` for assistance with how to improve this logic.

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
macOS-10.15.7-x86_64-i386-64bit
Python 3.9.10 (main, Feb  4 2022, 14:54:08)
[Clang 12.0.0 (clang-1200.0.32.29)]
Numpy 1.22.3
pyerfa 2.0.0.1
astropy 5.1.dev901+g675dc03e1
Scipy 1.8.0
Matplotlib 3.5.1
```

## Issue Discussion Hints
Note that the simple change of https://github.com/astropy/astropy/blob/675dc03e138d5c6a1cb6936a6b2c3211f39049d3/astropy/modeling/core.py#L2704
to `value = value * unit` with the above example still passes all the modeling unit tests. However, it produces a different error
```python
---------------------------------------------------------------------------
UnitTypeError                             Traceback (most recent call last)
Input In [1], in <cell line: 8>()
      5 c = -20.0 * unit
      6 model = Const1D(c)
----> 8 model(-23.0 * unit)

File ~/projects/astropy/astropy/modeling/core.py:397, in __call__(self, model_set_axis, with_bounding_box, fill_value, equivalencies, inputs_map, *inputs, **new_inputs)
    390 args = ('self',)
    391 kwargs = dict([('model_set_axis', None),
    392                ('with_bounding_box', False),
    393                ('fill_value', np.nan),
    394                ('equivalencies', None),
    395                ('inputs_map', None)])
--> 397 new_call = make_function_with_signature(
    398     __call__, args, kwargs, varargs='inputs', varkwargs='new_inputs')
    400 # The following makes it look like __call__
    401 # was defined in the class
    402 update_wrapper(new_call, cls)

File ~/projects/astropy/astropy/modeling/core.py:376, in _ModelMeta._handle_special_methods.<locals>.__call__(self, *inputs, **kwargs)
    374 def __call__(self, *inputs, **kwargs):
    375     """Evaluate this model on the supplied inputs."""
--> 376     return super(cls, self).__call__(*inputs, **kwargs)

File ~/projects/astropy/astropy/modeling/core.py:1079, in Model.__call__(self, *args, **kwargs)
   1076 # prepare for model evaluation (overridden in CompoundModel)
   1077 evaluate, inputs, broadcasted_shapes, kwargs = self._pre_evaluate(*args, **kwargs)
-> 1079 outputs = self._generic_evaluate(evaluate, inputs,
   1080                                  fill_value, with_bbox)
   1082 # post-process evaluation results (overridden in CompoundModel)
   1083 return self._post_evaluate(inputs, outputs, broadcasted_shapes, with_bbox, **kwargs)

File ~/projects/astropy/astropy/modeling/core.py:1043, in Model._generic_evaluate(self, evaluate, _inputs, fill_value, with_bbox)
   1041     outputs = bbox.evaluate(evaluate, _inputs, fill_value)
   1042 else:
-> 1043     outputs = evaluate(_inputs)
   1044 return outputs

File ~/projects/astropy/astropy/modeling/core.py:939, in Model._pre_evaluate.<locals>.evaluate(_inputs)
    938 def evaluate(_inputs):
--> 939     return self.evaluate(*chain(_inputs, parameters))

File ~/projects/astropy/astropy/modeling/functional_models.py:1805, in Const1D.evaluate(x, amplitude)
   1802     x = amplitude * np.ones_like(x, subok=False)
   1804 if isinstance(amplitude, Quantity):
-> 1805     return Quantity(x, unit=amplitude.unit, copy=False)
   1806 return x

File ~/projects/astropy/astropy/units/quantity.py:522, in Quantity.__new__(cls, value, unit, dtype, copy, order, subok, ndmin)
    519         cls = qcls
    521 value = value.view(cls)
--> 522 value._set_unit(value_unit)
    523 if unit is value_unit:
    524     return value

File ~/projects/astropy/astropy/units/quantity.py:764, in Quantity._set_unit(self, unit)
    762         unit = Unit(str(unit), parse_strict='silent')
    763         if not isinstance(unit, (UnitBase, StructuredUnit)):
--> 764             raise UnitTypeError(
    765                 "{} instances require normal units, not {} instances."
    766                 .format(type(self).__name__, type(unit)))
    768 self._unit = unit

UnitTypeError: Quantity instances require normal units, not <class 'astropy.units.function.logarithmic.MagUnit'> instances.
```
Magnitude is such a headache. Maybe we should just stop supporting it altogether... _hides_

More seriously, maybe @mhvk has ideas.
The problem is that `Quantity(...)` by default creates a `Quantity`, which seems quite logical. But `Magnitude` is a subclass.... This is also why multiplying with the unit does work. I *think* adding `subok=True` for the `Quantity` initializations should fix the specific problems, though I fear it may well break elsewhere... 

p.s. It does make me wonder if one shouldn't just return a subclass in the first place if the unit asks for that.
> The problem is that `Quantity(...)` by default creates a `Quantity`, which seems quite logical. But `Magnitude` is a subclass.... This is also why multiplying with the unit does work. I _think_ adding `subok=True` for the `Quantity` initializations should fix the specific problems, though I fear it may well break elsewhere...

For my reproducer adding `subok=True` everywhere in the call stack that uses `Quantity(...)` does prevent mitigate the bug. I guess a possible fix for this bug is to ensure that `Quantity` calls in modeling include this optional argument.

> p.s. It does make me wonder if one shouldn't just return a subclass in the first place if the unit asks for that.

This change could make things a bit easier for modeling. I'm not sure why this is not the default.

## Failing Tests That Should Pass
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model38]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model38]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model38]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model0]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model1]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model4]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model5]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model6]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model7]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model8]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model9]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model10]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model11]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model12]`
- `astropy/modeling/tests/test_models_quantities.py::test_Schechter1D_errors`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test__set_unit`
- `astropy/modeling/tests/test_quantities_parameters.py::test_magunit_parameter`

## Existing Passing Tests To Preserve
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model0]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model2]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model3]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model4]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model5]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model6]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model7]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model8]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model9]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model10]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model11]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model12]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model13]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model14]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model15]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model16]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model17]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model18]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model19]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model20]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model21]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model22]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model23]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model24]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model25]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model26]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model27]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model28]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model30]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model32]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model33]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model34]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model35]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model36]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model37]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model38]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model39]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model40]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model41]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model42]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model43]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model44]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model45]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_without_units[model46]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model0]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model2]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model3]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model4]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model5]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model6]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model7]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model8]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model9]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model10]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model11]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model12]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model13]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model14]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model15]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model16]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model17]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model18]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model19]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model20]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model21]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model22]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model23]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model24]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model25]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model26]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model27]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model28]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model30]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model32]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model33]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model34]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model35]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model36]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model37]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model39]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model40]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model41]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model42]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model43]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model44]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model45]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units[model46]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model0]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model2]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model3]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model4]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model5]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model6]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model7]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model8]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model9]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model10]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model11]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model12]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model13]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model14]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model15]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model16]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model17]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model18]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model19]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model20]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model21]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model22]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model23]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model24]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model25]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model26]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model27]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model28]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model30]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model32]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model33]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model34]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model35]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model36]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model37]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model39]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model40]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model41]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model42]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model43]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model44]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model45]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_x_array[model46]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model0]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model2]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model3]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model4]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model5]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model6]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model7]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model8]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model9]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model10]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model11]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model12]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model13]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model14]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model15]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model16]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model17]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model18]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model19]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model20]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model21]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model22]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model23]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model24]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model25]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model26]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model27]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model28]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model30]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model32]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model33]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model34]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model35]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model36]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model37]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model39]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model40]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model41]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model42]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model43]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model44]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model45]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_with_units_param_array[model46]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model0]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model2]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model3]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model4]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model5]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model6]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model7]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model8]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model9]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model10]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model11]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model12]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model13]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model14]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model15]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model16]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model17]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model18]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model19]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model20]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model21]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model22]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model23]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model24]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model25]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model26]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model27]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model28]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model30]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model32]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model33]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model34]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model35]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model36]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model37]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model38]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model39]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model40]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model41]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model42]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model43]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model44]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model45]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_bounding_box[model46]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model0]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model1]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model2]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model3]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model4]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model5]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model6]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model7]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model8]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model9]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model10]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model11]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model12]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model13]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model14]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model15]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model16]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model17]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model18]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model19]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model20]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model21]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model22]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model23]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model24]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model25]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model26]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model27]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model28]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model29]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model30]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model31]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model32]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model33]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model34]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model35]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model36]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model37]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model38]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model39]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model40]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model41]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model42]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model43]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model44]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model45]`
- `astropy/modeling/tests/test_models_quantities.py::test_compound_model_input_units_equivalencies_defaults[model46]`
- `astropy/modeling/tests/test_models_quantities.py::test_input_unit_mismatch_error[model0]`
- `astropy/modeling/tests/test_models_quantities.py::test_input_unit_mismatch_error[model1]`
- `astropy/modeling/tests/test_models_quantities.py::test_input_unit_mismatch_error[model2]`
- `astropy/modeling/tests/test_models_quantities.py::test_input_unit_mismatch_error[model3]`
- `astropy/modeling/tests/test_models_quantities.py::test_input_unit_mismatch_error[model4]`
- `astropy/modeling/tests/test_models_quantities.py::test_input_unit_mismatch_error[model5]`
- `astropy/modeling/tests/test_models_quantities.py::test_input_unit_mismatch_error[model7]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model2]`
- `astropy/modeling/tests/test_models_quantities.py::test_models_evaluate_magunits[model3]`
- `astropy/modeling/tests/test_parameters.py::test__tofloat`
- `astropy/modeling/tests/test_parameters.py::test_parameter_properties`
- `astropy/modeling/tests/test_parameters.py::test_parameter_operators`
- `astropy/modeling/tests/test_parameters.py::test_parameter_inheritance`
- `astropy/modeling/tests/test_parameters.py::test_param_metric`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_set_parameters_as_list`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_set_parameters_as_array`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_set_as_tuple`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_set_model_attr_seq`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_set_model_attr_num`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_set_item`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_wrong_size1`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_wrong_size2`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_wrong_shape`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_par_against_iraf`
- `astropy/modeling/tests/test_parameters.py::TestParameters::testPolynomial1D`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_poly1d_multiple_sets`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_par_slicing`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_poly2d`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_poly2d_multiple_sets`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_shift_model_parameters1d`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_scale_model_parametersnd`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_bounds`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_modify_value`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_quantity`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_size`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_std`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_fixed`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_tied`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_validator`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_validate`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_copy`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_model`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_raw_value`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test__create_value_wrapper`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_bool`
- `astropy/modeling/tests/test_parameters.py::TestParameters::test_param_repr_oneline`
- `astropy/modeling/tests/test_parameters.py::TestMultipleParameterSets::test_change_par`
- `astropy/modeling/tests/test_parameters.py::TestMultipleParameterSets::test_change_par2`
- `astropy/modeling/tests/test_parameters.py::TestMultipleParameterSets::test_change_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_single_model_scalar_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_single_model_scalar_and_array_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_single_model_1d_array_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_single_model_1d_array_different_length_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_single_model_2d_array_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_single_model_2d_non_square_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_single_model_2d_broadcastable_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_incorrect_scalar_parameters[1-2]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_incorrect_scalar_parameters[1-p21]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_incorrect_scalar_parameters[p12-3]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_incorrect_scalar_parameters[p13-p23]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_incorrect_scalar_parameters[p14-p24]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_scalar_parameters[kwargs0]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_scalar_parameters[kwargs1]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_scalar_parameters[kwargs2]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_scalar_and_array_parameters[kwargs0]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_scalar_and_array_parameters[kwargs1]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_scalar_and_array_parameters[kwargs2]`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_1d_array_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_mixed_dimension_array_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_2d_array_parameters`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_two_model_nonzero_model_set_axis`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_wrong_number_of_params`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_wrong_number_of_params2`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_array_parameter1`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_array_parameter2`
- `astropy/modeling/tests/test_parameters.py::TestParameterInitialization::test_array_parameter4`
- `astropy/modeling/tests/test_parameters.py::test_non_broadcasting_parameters`
- `astropy/modeling/tests/test_parameters.py::test_setter`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_quantity`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_set_quantity`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_lose_units`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_add_units`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_change_unit`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_set_value`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_quantity_property`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_default_units_match`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_defaults[unit0-1.0]`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_defaults[None-default1]`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_quantity_arithmetic`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameter_quantity_comparison`
- `astropy/modeling/tests/test_quantities_parameters.py::test_parameters_compound_models`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
