# lbdist - LINBIT distribution detection library for Python

This is a opinionated Linux distribution detection library. This was initially written for
`linbit-manage-node.py` when we made it Python 3 clean. Python 3 dropped `platform.linux_distribution()`, which
is very much understandable considering the enormous mess Linux distribution detection is. `/etc/os-release`
helps, there are still differences even where one would not expect them (RHEL vs. Centos vs. RHEL CoreOS,...).

Why not use an existing one? We at LINBIT have a pretty specific naming scheme (e.g., how many digits of the
version, where and how we mangle service pack levels,...), so existing ones are not a perfect fit. We also care
about distributions that others might not, and we don't care about others not relevant to us. All in all,
providing a mapping from `$library` to "LINBIT notation" did not look like a good idea.

The `Distribution` class might be handy for more general cases, but is already slightly opinionated,
`LinbitDistribution` extends this class and provides highly LINBIT specific methods.

This library should still work on very old Python (2.6 as of RHEL6).

`distribution.py` is written in a way that it can be used as a library and a standalone program. We will try
to keep the output of the standalone version compatible. New fields will be printed after the existing ones.
