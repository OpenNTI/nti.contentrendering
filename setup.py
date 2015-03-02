import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	'console_scripts': [
	],
	"z3c.autoinclude.plugin": [
		'target = nti.contentrendering',
	],
}

TESTS_REQUIRE = [
	'nose',
	'nose-timer',
	'nose-pudb',
	'nose-progressive',
	'nose2[coverage_plugin]',
	'pyhamcrest',
	'zope.testing',
	'nti.nose_traceback_info',
	'nti.testing'
]

setup(
	name='nti.contentrendering',
	version=VERSION,
	author='Jason Madden',
	author_email='jason@nextthought.com',
	description="NTI Content Rendering",
	long_description=codecs.open('README.rst', encoding='utf-8').read(),
	license='Proprietary',
	keywords='Content LaTeX Rendering',
	classifiers=[
		'Intended Audience :: Developers',
		'Natural Language :: English',
		'Operating System :: OS Independent',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 2.7',
		'Programming Language :: Python :: Implementation :: CPython'
	],
	packages=find_packages('src'),
	package_dir={'': 'src'},
	namespace_packages=['nti'],
	tests_require=TESTS_REQUIRE,
	install_requires=[
		'setuptools',
		'anyjson',
		'BTrees',
		'html5lib',
		'isodate',
		'lxml',
		'Paste',
		'PasteDeploy',
		'plone.namedfile',
		'PyPDF2',
		'pyquery',
		'pytz',
		'rdflib',
		'requests',
		'repoze.lru',
		'simplejson',
		'six',
		'z3c.autoinclude',
		'zope.app.file',
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
		'nti.common',
		'nti.contentfragments',
		'nti.contentindexing',
		'nti.contentprocessing',
		'nti.externalization',
		'nti.futures',
		'nti.mimetype',
		'nti.ntiids',
		'nti.plasTeX',
		'nti.schema'
	],
	extras_require={
		'test': TESTS_REQUIRE,
	},
	dependency_links=[
		'git+https://github.com/NextThought/nti.schema.git#egg=nti.schema',
		'git+https://github.com/NextThought/nti.plasTeX.git#egg=nti.plasTeX',
		'git+https://github.com/NextThought/nti.nose_traceback_info.git#egg=nti.nose_traceback_info'
	],
	entry_points=entry_points
)
