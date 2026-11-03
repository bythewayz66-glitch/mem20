"""Test package for mem20mktz.

Making ``tests`` a real package is what lets the modules use
``from .conftest import requires_ucg``. Before this file existed, pytest
collected the modules as top-level scripts, so the relative import raised
``ImportError: attempted relative import with no known parent package`` and the
whole suite failed to collect.
"""
