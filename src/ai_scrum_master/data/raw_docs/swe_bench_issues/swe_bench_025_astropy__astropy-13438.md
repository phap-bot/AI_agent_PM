# SWE-bench Issue: astropy__astropy-13438

- Dataset: princeton-nlp/SWE-bench
- Repository: astropy/astropy
- Instance ID: astropy__astropy-13438
- Base Commit: 4bd88be61fdf4185b9c198f7e689a40041e392ee
- Environment Setup Commit: cdf311e0714e611d48b0a31eb1f0e2cbffab7f23
- Created At: 2022-07-07T07:29:35Z
- Version: 5.0

## Issue Title
[Security] Jquery 3.1.1 is vulnerable to untrusted code execution

## Problem Statement
[Security] Jquery 3.1.1 is vulnerable to untrusted code execution
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
Passing HTML from untrusted sources - even after sanitizing it - to one of jQuery's DOM manipulation methods (i.e. .html(), .append(), and others) may execute untrusted code (see [CVE-2020-11022](https://nvd.nist.gov/vuln/detail/cve-2020-11022) and [CVE-2020-11023](https://nvd.nist.gov/vuln/detail/cve-2020-11023))

### Expected behavior
<!-- What did you expect to happen. -->
Update jquery to the version 3.5 or newer in https://github.com/astropy/astropy/tree/main/astropy/extern/jquery/data/js

### Actual behavior
<!-- What actually happened. -->
<!-- Was the output confusing or poorly described? -->
 jquery version 3.1.1 is distributed with the latest astropy release

<!-- ### Steps to Reproduce 
<!-- Ideally a code example could be provided so we can run it ourselves. -->
<!-- If you are pasting code, use triple backticks (```) around
your code snippet. -->
<!-- If necessary, sanitize your screen output to be pasted so you do not
reveal secrets like tokens and passwords. -->
<!--
1. [First Step]
2. [Second Step]
3. [and so on...]

```python
# Put your Python code snippet here.
```
-->
<!--### System Details
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

## Issue Discussion Hints
Welcome to Astropy 👋 and thank you for your first issue!

A project member will respond to you as soon as possible; in the meantime, please double-check the [guidelines for submitting issues](https://github.com/astropy/astropy/blob/main/CONTRIBUTING.md#reporting-issues) and make sure you've provided the requested details.

GitHub issues in the Astropy repository are used to track bug reports and feature requests; If your issue poses a question about how to use Astropy, please instead raise your question in the [Astropy Discourse user forum](https://community.openastronomy.org/c/astropy/8) and close this issue.

If you feel that this issue has not been responded to in a timely manner, please leave a comment mentioning our software support engineer @embray, or send a message directly to the [development mailing list](http://groups.google.com/group/astropy-dev).  If the issue is urgent or sensitive in nature (e.g., a security vulnerability) please send an e-mail directly to the private e-mail feedback@astropy.org.
Besides the jquery files  in [astropy/extern/jquery/data/js/](https://github.com/astropy/astropy/tree/main/astropy/extern/jquery/data/js), the jquery version number appears in [astropy/table/jsviewer.py](https://github.com/astropy/astropy/blob/main/astropy/table/jsviewer.py) twice, and in [table/tests/test_jsviewer.py](https://github.com/astropy/astropy/blob/main/astropy/table/tests/test_jsviewer.py) four times. This might be a good time to introduce a constant for the jquery version, and use that ~across the codebase. Or at least~ across the tests.

@skukhtichev Maybe we could speed up the fix by creating a PR?
As Python does not have built-in support for defining constants, I think it's better to keep the hard-coded strings in [astropy/table/jsviewer.py](https://github.com/astropy/astropy/blob/main/astropy/table/jsviewer.py). Don't want to introduce another security problem by allowing attackers to downgrade the jquery version at runtime. Still, a variable for the tests would simplify future updates.
> Maybe we could speed up the fix by creating a PR?

That would definitely help! 😸 

We discussed this in Astropy Slack (https://www.astropy.org/help.html) and had a few ideas, the latest being download the updated files from https://cdn.datatables.net/ but no one has the time to actually do anything yet.

We usually do not modify the bundled code (unless there is no choice) but rather just copy them over. This is because your changes will get lost in the next upgrade unless we have a patch file on hand with instructions (though that can easily break too if upstream has changed too much).
I'll see what I can do about a PR tomorrow :-)
I'd get the jquery update from https://releases.jquery.com/jquery/, latest version is 3.6.0.

## Failing Tests That Should Pass
- `astropy/table/tests/test_jsviewer.py::test_write_jsviewer_default`
- `astropy/table/tests/test_jsviewer.py::test_write_jsviewer_mixin[mixin0]`
- `astropy/table/tests/test_jsviewer.py::test_write_jsviewer_mixin[mixin1]`
- `astropy/table/tests/test_jsviewer.py::test_write_jsviewer_mixin[mixin2]`
- `astropy/table/tests/test_jsviewer.py::test_write_jsviewer_local`

## Existing Passing Tests To Preserve
- `astropy/table/tests/test_jsviewer.py::test_write_jsviewer_overwrite`

## Planning Guidance
Treat this as a real GitHub issue requirement. Create planning output from the issue text, repository context, failing tests, and hints only. Do not infer implementation details from the hidden gold patch.
