#!/usr/bin/env python

from distutils.core import setup
import glob
import os
from distutils.command.install import INSTALL_SCHEMES

from bdist_mpkg.cmd_bdist_mpkg import bdist_mpkg as bdist_mpkg

class pma_bdist_mpkg(bdist_mpkg):
    def initialize_options(self):
        bdist_mpkg.initialize_options(self)
        self.readme = "ReadMe.html"

    def finalize_options(self):
        bdist_mpkg.finalize_options(self)
        self.scheme_map['scripts'] = '/usr/local/sbin'

# For non-pkg installs, tarballs, etc.    
INSTALL_SCHEMES['unix_prefix']['scripts'] = '$base/sbin'

setup(
    version      = '1.0',
    name         = 'PyMacAdmin',
    description  = "Python tools for Mac administration",
    author       = "Chris Adams",
    author_email = "chris@improbable.org",
    url          = "http://pymacadmin.googlecode.com/",
    platforms    = [ 'macosx-10.5' ],
    license      = 'Apache Software License',
    classifiers  = [
              'Development Status :: 4 - Beta',
              'Environment :: Console',
              'Environment :: MacOS X',
              'Intended Audience :: Developers',
              'Intended Audience :: System Administrators',
              'License :: OSI Approved :: Apache Software License',
              'License :: OSI Approved :: Python Software Foundation License',
              'Operating System :: MacOS :: MacOS X',
              'Programming Language :: Python',
              'Topic :: Software Development :: Libraries :: Application Frameworks',
              'Topic :: System :: Systems Administration',
              'Topic :: Utilities',
    ],
    package_dir  = { '' : 'lib' },
    packages     = [ 
        ".".join(dirpath.split("/")[1:]) for dirpath, dirnames, filenames in os.walk('lib') if "__init__.py" in filenames
    ],
    scripts      = glob.glob(os.path.join(os.path.dirname(__file__), 'bin', '*.py')),
    cmdclass = {
        'bdist_mpkg': pma_bdist_mpkg
    }
)
