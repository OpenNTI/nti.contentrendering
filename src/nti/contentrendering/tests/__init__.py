#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

import io
import os
import sys
import shutil
import tempfile
import StringIO
import pkg_resources

import zope.component
resource_filename = getattr(pkg_resources, 'resource_filename')

import plasTeX
from plasTeX.TeX import TeX

from nti.testing.base import SharedConfiguringTestBase as _ConfiguringTestBase

class ConfiguringTestBase(_ConfiguringTestBase):
	set_up_packages = ('nti.contentrendering',)

import zope.testing.cleanup

from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin


class SharedConfiguringTestLayer(ZopeComponentLayer,
								 ConfiguringLayerMixin):

	description = "nti.contentrendering is ZCML configured"

	set_up_packages = ('nti.contentrendering',)

	@classmethod
	def setUp(cls):
		cls.setUpPackages()

	@classmethod
	def tearDown(cls):
		cls.tearDownPackages()
		zope.testing.cleanup.cleanUp()

	@classmethod
	def testSetUp(cls):
		cls.__cwd = os.getcwd()

	@classmethod
	def testTearDown(cls):
		os.chdir(cls.__cwd)



class NonDevmodeSharedConfiguringTestLayer(ZopeComponentLayer,
										   ConfiguringLayerMixin):

	description = "nti.contentrendering is ZCML configured without devmode"

	set_up_packages = ('nti.contentrendering',)

	@classmethod
	def setUp(cls):
		cls.setUpPackages()

	@classmethod
	def tearDown(cls):
		cls.tearDownPackages()
		zope.testing.cleanup.cleanUp()

	@classmethod
	def testSetUp(cls):
		cls.__cwd = os.getcwd()

	@classmethod
	def testTearDown(cls):
		os.chdir(cls.__cwd)


import unittest

class ContentrenderingLayerTest(unittest.TestCase):
	layer = SharedConfiguringTestLayer

class NonDevmodeContentrenderingLayerTest(unittest.TestCase):
	layer = NonDevmodeSharedConfiguringTestLayer


def buildDomFromString(docString,
                       mkdtemp=False,
                       output_encoding=None,
                       input_encoding=None,
                       chdir=False,
                       working_dir=None,
					   config_hook=lambda doc: None):
	document = plasTeX.TeXDocument()
	if input_encoding:
		strIO = io.StringIO( docString.decode( input_encoding ) )
		strIO.name = 'temp'
	else:
		strIO = StringIO.StringIO(docString)
		strIO.name = 'temp'

	document.userdata['jobname'] = 'temp'
	work_dir = (working_dir or tempfile.gettempdir()) if not mkdtemp else tempfile.mkdtemp()
	document.userdata['working-dir'] = work_dir
	document.config['files']['directory'] = work_dir
	strIO.name = os.path.join( work_dir, strIO.name )
	if chdir:
		os.chdir( work_dir )
	document.config.add_section( "NTI" )
	document.config.set( "NTI", 'provider', 'testing' )

	# TODO: Much, but not all of this, is directly
	# copied from nti_render
	document.config.set( 'NTI', 'extra-scripts', '' )
	document.config.set( 'NTI', 'extra-styles', '' )

	# setup default config options we want
	document.config['files']['split-level'] = 1
	# Arbitrary number greater than the actual depth possible
	document.config['document']['toc-depth'] = sys.maxint
	document.config['document']['toc-non-files'] = True

	# By outputting in ASCII, we are still valid UTF-8, but we use
	# XML entities for high characters. This is more likely to survive
	# through various processing steps that may not be UTF-8 aware
	document.config['files']['output-encoding'] = output_encoding or 'ascii'
	document.config['general']['theme'] = 'NTIDefault'
	document.config['general']['theme-base'] = 'NTIDefault'

	document.userdata['extra_scripts'] = document.config['NTI']['extra-scripts'].split()
	document.userdata['extra_styles'] = document.config['NTI']['extra-styles'].split()

	tex = TeX(document, strIO)
	config_hook(document)
	tex.parse()
	return document

def simpleLatexDocumentText(preludes=(), bodies=()):
	preludes = [unicode(p).encode('utf-8') for p in preludes]
	doc = br"""\documentclass[12pt]{article}  """ + b'\n'.join(preludes) + \
		  br"""\begin{document} """
	mathString = b'\n'.join( [unicode(m).encode('utf-8') for m in bodies] )
	doc = doc + b'\n' + mathString + b'\n\\end{document}'
	return doc

class RenderContext(object):

	def __init__(self, latex_tex, dom=None,
				 output_encoding=None,
				 input_encoding=None,
				 files=(),
				 packages_on_texinputs=False,
				 config_hook=None):
		self.latex_tex = latex_tex
		self.dom = dom
		self._cwd = None
		self._templates = None
		self.output_encoding = output_encoding
		self.input_encoding = input_encoding
		self.files = files
		self._texinputs = None
		self._packages_on_texinputs = packages_on_texinputs
		self._config_hook = config_hook

	@property
	def docdir(self):
		return self.dom.config['files']['directory']

	def render(self, images=False):
		res_db = None
		if images:
			from nti.contentrendering import nti_render
			res_db = nti_render.generateImages( self.dom )

		from nti.contentrendering.resources import ResourceRenderer
		render = ResourceRenderer.createResourceRenderer('XHTML', res_db)
		render.importDirectory( os.path.join( os.path.dirname(__file__), '..' ) )
		render.render( self.dom )

	def read_rendered_file(self, filename):
		with io.open(os.path.join(self.docdir, filename), 'rU',
					 encoding=self.output_encoding or 'utf-8' ) as f:
			return f.read()

	def __enter__(self):
		self._cwd = os.getcwd()
		self._templates = os.environ.get( 'XHTMLTEMPLATES', '' )

		if self._packages_on_texinputs:
			packages_path = resource_filename( 'nti.contentrendering', 'plastexpackages' )
		else:
			packages_path = ''


		# Set up TEXINPUTS to include the current directory for the renderer,
		# plus our packages directory
		self._texinputs = os.environ.get('TEXINPUTS', '')
		texinputs = (os.getcwd(), packages_path, self._texinputs)
		os.environ['TEXINPUTS'] = os.path.pathsep.join(texinputs)

		xhtmltemplates = (os.path.join( os.getcwd(), 'Templates' ),
						  packages_path,
						  # If we fail to install our templates, and then we try to use our
						  # resource renderer, we find that we get failures due to it
						  # not having setup some things required by the plasTeX default
						  # templates, such as renderer/vectorImager
						  resource_filename( 'nti.contentrendering', 'zpts' ),
						  os.environ.get('XHTMLTEMPLATES', ''))
		os.environ['XHTMLTEMPLATES'] = os.path.pathsep.join( xhtmltemplates)

		copied = False
		def _file_copy(to):
			for f in self.files:
				fname = os.path.basename(f)
				shutil.copyfile( f, os.path.join( to, fname ) )

		import nti.contentrendering.plastexids
		nti.contentrendering.plastexids.patch_all()

		from nti.contentrendering.utils import setupChameleonCache
		setupChameleonCache(config=True)

		if self.dom is None:
			work_dir = tempfile.mkdtemp()
			_file_copy(work_dir)
			copied = True
			dom_env = {}
			if self._config_hook:
				dom_env['config_hook'] = self._config_hook
			self.dom = buildDomFromString( self.latex_tex,
										   mkdtemp=False,
										   output_encoding=self.output_encoding,
										   input_encoding=self.input_encoding,
										   chdir=True,
										   working_dir=work_dir,
										   **dom_env)

		if not copied:
			_file_copy( self.docdir )

		os.chdir( self.docdir )

		return self

	def __exit__( self, exc_type, exc_value, traceback ):
		os.environ['XHTMLTEMPLATES'] = self._templates
		os.environ['TEXINPUTS'] = self._texinputs

		os.chdir( self._cwd )
		shutil.rmtree( self.docdir )
