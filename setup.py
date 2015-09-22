import os
from setuptools import setup

# krpc_utils
# Tools to help with kerbal remote procedure call

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "krpc_utils",
    version = "0.0.1",
    description = "Tools to help with kerbal remote procedure call",
    author = "d4rch0n",
    author_email = "d4rch0n@gmail.com",
    license = "GPLv3+",
    keywords = "",
    url = "https://bitbucket.org/d4rch0n/krpc_utils",
    packages=['krpc_utils'],
    package_dir={'krpc_utils': 'krpc_utils'},
    long_description=read('README.md'),
    classifiers=[
        #'Development Status :: 1 - Planning',
        #'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        #'Development Status :: 4 - Beta',
        #'Development Status :: 5 - Production/Stable',
        #'Development Status :: 6 - Mature',
        #'Development Status :: 7 - Inactive',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Environment :: MacOS X',
        'Environment :: Win32 (MS Windows)',
        'Operating System :: POSIX',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: Microsoft :: Windows',
        'Programming Language :: Python',
    ],
    install_requires=[
    ],
    entry_points = {
        'console_scripts': [
            'krpc_utils = krpc_utils.bin:krpc_utils',
        ],
    },
    #package_data = {
        #'krpc_utils': ['catalog/*.edb'],
    #},
    #include_package_data = True,
)
