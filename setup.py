import codecs
from setuptools import setup, find_packages

VERSION = '0.0.0'

entry_points = {
	'console_scripts': [
		"nti_render = nti.contentrendering.nti_render:main",
		"nti_create_book_archive = nti.contentrendering.archive:main",
		"nti_content_indexer = nti.contentrendering.content_indexer:main",
		"nti_jsonpbuilder = nti.contentrendering.jsonpbuilder:main",
		"nti_gslopinionexport = nti.contentrendering.gslopinionexport:main",
		"nti_default_root_sharing_setter = nti.contentrendering.default_root_sharing_setter:main",
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
		'requests',
		'repoze.lru',
		'simplejson',
		'six',
		'z3c.autoinclude',
		'zope.app.file',
		'zope.browserpage',
		'zope.cachedescriptors',
		'zope.component',
		'zope.configuration',
		'zope.container',
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
		'nti.contenttypes.presentation',
		'nti.externalization',
		'nti.futures',
		'nti.mimetype',
		'nti.ntiids',
		'nti.plasTeX',
		'nti.property',
		'nti.schema',
		'nti.wref',
		'nti.zodb'
	],
	extras_require={
		'test': TESTS_REQUIRE,
	},
	dependency_links=[
	],
	entry_points=entry_points
)
