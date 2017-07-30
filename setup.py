import codecs
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
        "nti_render = nti.contentrendering.nti_render:main",
        "nti_jsonpbuilder = nti.contentrendering.jsonpbuilder:main",
        "nti_create_book_archive = nti.contentrendering.archive:main",
        "nti_gslopinionexport = nti.contentrendering.gslopinionexport:main",
        "nti_default_root_sharing_setter = nti.contentrendering.default_root_sharing_setter:main",
    ],
    "z3c.autoinclude.plugin": [
        'target = nti.contentrendering',
    ],
}

TESTS_REQUIRE = [
    'pyhamcrest',
    'nti.testing',
    'zope.testrunner',
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
    url="https://github.com/NextThought/nti.contentrendering",
    license='Apache',
    keywords='content latex rendering',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: CPython'
    ],
    zip_safe=True,
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    namespace_packages=['nti'],
    tests_require=TESTS_REQUIRE,
    install_requires=[
        'setuptools',
        'anyjson',
        'BTrees',
        'html5lib',
        'isodate',
        'lxml',
        'nti.contentfragments',
        'nti.contentprocessing',
        'nti.externalization',
        'nti.futures',
        'nti.mimetype',
        'nti.ntiids',
        'nti.plasTeX',
        'nti.property',
        'nti.schema',
        'nti.wref',
        'Paste',
        'PasteDeploy',
        'plone.namedfile',
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
        'zope.interface',
        'zope.location',
        'zope.mimetype',
        'zope.security',
        'zope.traversing',
    ],
    extras_require={
        'test': TESTS_REQUIRE,
    },
    dependency_links=[],
    entry_points=entry_points
)
