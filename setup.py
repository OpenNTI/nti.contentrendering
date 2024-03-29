import codecs
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
        "nti_render = nti.contentrendering.nti_render:main",
        "nti_jsonpbuilder = nti.contentrendering.jsonpbuilder:main",
        "nti_create_book_archive = nti.contentrendering.archive:main",
        "nti_real_page_extractor = nti.contentrendering.realpageextractor:main",
        "nti_default_root_sharing_setter = nti.contentrendering.default_root_sharing_setter:main",
    ],
    "z3c.autoinclude.plugin": [
        'target = nti.contentrendering',
    ],
}


TESTS_REQUIRE = [
    'fudge',
    'nti.testing',
    'zope.testrunner',
    'nose >= 1.3.0'
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='nti.contentrendering',
    version=_read('version.txt').strip(),
    author='Jason Madden',
    author_email='jason@nextthought.com',
    description="NTI Content Rendering",
    long_description=(_read('README.rst') + '\n\n' + _read("CHANGES.rst")),
    license='Apache',
    keywords='content latex rendering',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    url="https://github.com/OpenNTI/nti.contentrendering",
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'BTrees',
        'html5lib',
        'isodate',
        'lxml',
        'nti.contentfragments',
        'nti.contentprocessing',
        'nti.externalization',
        'nti.futures',
        'nti.mimetype',
        'nti.namedfile',
        'nti.ntiids',
        'nti.plasTeX',
        'nti.property',
        'nti.schema',
        'nti.wref',
        'Paste',
        'PasteDeploy',
        'phantomjs-binary==2.1.3',
        'PyPDF2',
        'pyquery',
        'pytz',
        'ordered-set',
        'requests',
        'repoze.lru',
        'simplejson',
        'six',
        'z3c.autoinclude',
        'zope.browserpage',
        'zope.cachedescriptors',
        'zope.component',
        'zope.configuration',
        'zope.deferredimport',
        'zope.deprecation',
        'zope.dottedname',
        'zope.dublincore',
        'zope.event',
        'zope.exceptions',
        'zope.file',
        'zope.interface',
        'zope.location',
        'zope.mimetype',
        'zope.security',
        'zope.traversing',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ]
    },
    dependency_links=[],
    entry_points=entry_points
)
