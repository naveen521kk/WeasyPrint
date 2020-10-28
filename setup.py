#!/usr/bin/env python

"""
    WeasyPrint
    ==========

    WeasyPrint converts web documents to PDF.

"""

import sys
import os
import subprocess
from setuptools import setup,Command
class DownloadPandocCommand(Command):

    """Download pandoc"""

    description = "downloads c dependecy release and adds it to the package"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if sys.platform == "win32":         
            subprocess.check_call(["python","download_binaries.py"])
        else:
            print("Not available")

cmd_classes = {'download_pango': DownloadPandocCommand}

# Make sure wheels end up platform specific, if they include a pandoc binary
has_pandoc =os.path.isfile(os.path.join("weasyprint", "libcairo-2.dll"))
is_build_wheel = ("bdist_wheel" in sys.argv)

if is_build_wheel:
    if has_pandoc:
        # we need to make sure that bdist_wheel is after is_download_pandoc,
        # otherwise we don't include pandoc in the wheel... :-(
        pos_bdist_wheel = sys.argv.index("bdist_wheel")

        # we also need to make sure that this version of bdist_wheel supports
        # the --plat-name argument
        try:
            import wheel
            from distutils.version import StrictVersion
            if not StrictVersion(wheel.__version__) >= StrictVersion("0.27"):
                msg = "Including pandoc in wheel needs wheel >=0.27 but found %s.\nPlease update wheel!"
                raise RuntimeError(msg % wheel.__version__)
        except ImportError:
            # the real error will happen further down...
            print("No wheel installed, please install 'wheel'...")
        from distutils.util import get_platform
        sys.argv.insert(pos_bdist_wheel + 1, '--plat-name')
        sys.argv.insert(pos_bdist_wheel + 2, get_platform())
    else:
        print("no pandoc found, building platform unspecific wheel...")
        print("use 'python setup.py download_pandoc' to download pandoc.")

if sys.version_info.major < 3:
    raise RuntimeError(
        'WeasyPrint does not support Python 2.x anymore. '
        'Please use Python 3 or install an older version of WeasyPrint.')

setup(cmdclass=cmd_classes)
