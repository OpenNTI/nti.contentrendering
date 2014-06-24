#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

import os
import sys
import time
import glob
import string
import logging
import argparse
import datetime
import functools
import subprocess
from pkg_resources import resource_filename

import plasTeX
from plasTeX.TeX import TeX
from plasTeX.Logging import getLogger

import isodate

log = getLogger(__name__)
logger = log

import zope.exceptions.log
from zope import component
from zope.configuration import xmlconfig

import zope.dublincore.xmlmetadata

from nti.ntiids.ntiids import escape_provider

import nti.contentrendering
from nti.contentrendering import archive
from nti.contentrendering import interfaces
from nti.contentrendering import transforms
from nti.contentrendering import plastexids
from nti.contentrendering import jsonpbuilder
from nti.contentrendering import contentchecks
from nti.contentrendering import tociconsetter
from nti.contentrendering import html5cachefile
from nti.contentrendering import ntiidlinksetter
from nti.contentrendering import contentsizesetter
from nti.contentrendering import relatedlinksetter
from nti.contentrendering import sectionvideoadder
from nti.contentrendering.RenderedBook import RenderedBook
from nti.contentrendering.resources.ResourceDB import ResourceDB
from nti.contentrendering.resources.ResourceRenderer import createResourceRenderer
from nti.contentrendering.resources.resourcetypeoverrides import ResourceTypeOverrides

def _configure_logging(level='INFO'):
	numeric_level = getattr(logging, level.upper(), None)
	numeric_level = logging.INFO if not isinstance(numeric_level, int) else numeric_level
	logging.basicConfig(level=numeric_level)
	logging.root.handlers[0].setFormatter(zope.exceptions.log.Formatter('[%(asctime)-15s] [%(name)s] %(levelname)s: %(message)s'))

def _catching(f):
	@functools.wraps(f)
	def y():
		try:
			f()
		except subprocess.CalledProcessError as spe:
			logger.exception("Failed to run subprocess")
			sys.exit(spe.returncode)
		except:
			logger.exception("Failed to run main")
			sys.exit(1)
	return y

def _set_argparser():
	arg_parser = argparse.ArgumentParser( description="Render NextThought contetn." )

	arg_parser.add_argument( 'contentpath',
							help="Path to top level content file." )
	arg_parser.add_argument( '-c', '--config',
							help='Used by render_content wrapper. Ignore if running nti_render standalone.')
	arg_parser.add_argument( '--nochecking',
							 action='store_true',
							 default=False,
							 help="Perform content checks." )
	arg_parser.add_argument( '--noindexing',
							 action='store_true',
							 default=False,
							 help="Index content files." )
	arg_parser.add_argument('-o', '--outputformat',
							 default='xhtml',
							 help="Output format for rendered files. Default is xhtml" )
	arg_parser.add_argument( '--loglevel',
							 default='INFO',
							 help="Set logging level to INFO, DEBUG, WARNING, ERROR or CRITICAL. Default is INFO." )
	return arg_parser


@_catching
def main():
	""" Main program routine """
	argv = sys.argv[1:]
	arg_parser = _set_argparser()
	args = arg_parser.parse_args(args=argv)

	sourceFile = args.contentpath
	_configure_logging(args.loglevel)
	dochecking = not args.nochecking
	doindexing = not args.noindexing
	outFormat = args.outputformat

	out_format_to_render_name = {'xhtml': 'XHTML',
								 'text': 'Text'}

	logger.info("Start main")
	start_t = time.time()
	source_dir = os.path.dirname(os.path.abspath(os.path.expanduser(sourceFile)))

	# Set up imports for style files. The preferred, if verbose, way is to
	# use a fully qualified Python name. But for legacy and convenience
	# reasons, we support non-qualified imports (if the module does)
	# by adding that directory directly to the path
	packages_path = os.path.join(os.path.dirname(__file__) ,
								 str('plastexpackages'))
	sys.path.append(packages_path)

	# Also allow the source directory to cntain a 'plastexpackages'
	# directory. If it exists, it should be a directory containing
	# packages that are referenced by fully-qualified name
	# or possibly raw modules that are referenced by a short name;
	# note that in the module case, they won't be able to import each other.
	# Also note that the content-local `configure.zcml` file can (SHOULD) be used
	# to register IPythonPackage adapters/utilities
	local_packages_path = os.path.join( source_dir,
										str('plastexpackages'))
	sys.path.append(local_packages_path)

	zope_pre_conf_name = os.path.join(source_dir, str('pre_configure.zcml'))
	xml_conf_context = None
	if os.path.exists(zope_pre_conf_name):
		xml_conf_context = xmlconfig.file(os.path.abspath(zope_pre_conf_name), package=nti.contentrendering)

	xml_conf_context = xmlconfig.file('configure.zcml', package=nti.contentrendering, context=xml_conf_context)


	# Create document instance that output will be put into
	document = plasTeX.TeXDocument()
	# setup id generation
	plastexids.patch_all()
	# Certain things like to assume that the root document is called index.html. Make it so.
	# This is actually plasTeX.Base.LaTeX.Document.document, but games are played
	# with imports. damn it.
	plasTeX.Base.document.filenameoverride = property(lambda s: 'index')  # .html added automatically

	# setup default config options we want
	document.config['files']['split-level'] = 1
	document.config['document']['toc-depth'] = sys.maxint  # Arbitrary number greater than the actual depth possible
	document.config['document']['toc-non-files'] = True

	if outFormat in out_format_to_render_name:
		document.config['general']['renderer'] = out_format_to_render_name[outFormat]

	# By outputting in ASCII, we are still valid UTF-8, but we use
	# XML entities for high characters. This is more likely to survive
	# through various processing steps that may not be UTF-8 aware
	document.config['files']['output-encoding'] = 'ascii'
	document.config['general']['theme'] = 'NTIDefault'
	document.config['general']['theme-base'] = 'NTIDefault'
	# Read a config if present
	document.config.add_section('NTI')
	document.config.set('NTI',
						'provider',
						escape_provider(os.environ.get('NTI_PROVIDER', 'AOPS')))
	document.config.set('NTI', 'extra-scripts', '')
	document.config.set('NTI', 'extra-styles', '')
	document.config.set('NTI', 'timezone-name', 'US/Central')
	conf_name = os.path.join(source_dir, "nti_render_conf.ini")
	document.config.read((conf_name,))

	# Configure components and utilities
	zope_conf_name = os.path.join(source_dir, 'configure.zcml')
	if os.path.exists(zope_conf_name):
		xml_conf_context = xmlconfig.file(os.path.abspath(zope_conf_name), package=nti.contentrendering, context=xml_conf_context)

	# Instantiate the TeX processor
	tex = TeX(document, file=sourceFile)

	# Populate variables for use later
	jobname = document.userdata['jobname'] = tex.jobname
	# Create a component lookup ("site manager") that will
	# look for components named for the job implicitly
	# TODO: Consider installing hooks and using 'with site()' for this?
	components = interfaces.JobComponents(jobname)

	cwd = document.userdata['working-dir'] = os.getcwd()
	document.userdata['generated_time'] = isodate.datetime_isoformat(datetime.datetime.utcnow())
	# This variable contains either a time.tzname tuple or a pytz timezone
	# name
	document.userdata['document_timezone_name'] = document.config['NTI']['timezone-name']


	document.userdata['transform_process'] = True

	document.userdata['extra_scripts'] = document.config['NTI']['extra-scripts'].split()
	document.userdata['extra_styles'] = document.config['NTI']['extra-styles'].split()

	# When changes are made to the rendering process that would impact the ability
	# of deployed code to properly consume documents, this needs to be incremented.
	# Currently it is for an entire renderable package (book) but in the future we
	# might need/want to make it per-page/per-feature (e.g., if a unit doesn't use
	# new quiz functionality, it may be compatible with older viewers)
	document.userdata['renderVersion'] = 2

	# Load aux files for cross-document references
	pauxname = '%s.paux' % jobname
	for dirname in [cwd] + document.config['general']['paux-dirs']:
	 	for fname in glob.glob(os.path.join(dirname, '*.paux')):
	 		if os.path.basename(fname) == pauxname:
	 			continue
	 		document.context.restore(fname, document.config['general']['renderer'])


	# Set up TEXINPUTS to include the current directory for the renderer,
	# plus our packages directory
	texinputs = (os.getcwd(), source_dir, packages_path, os.environ.get('TEXINPUTS', ''))
	os.environ['TEXINPUTS'] = os.path.pathsep.join(texinputs)

	# Likewise for the renderers, with the addition of the legacy 'zpts' directory.
	# Parts of the code (notably tex2html._find_theme_mathjaxconfig) depend on
	# the local Template being first. Note that earlier values will take precedence
	# over later values.
	xhtmltemplates = (os.path.join(os.getcwd(), 'Templates'),
					  packages_path,
					  resource_filename(__name__, 'zpts'),
					  os.environ.get('XHTMLTEMPLATES', ''))
	os.environ['XHTMLTEMPLATES'] = os.path.pathsep.join(xhtmltemplates)
	setupChameleonCache(config=True)

	# Parse the document
	logger.info("Tex Parsing %s", sourceFile)
	tex.parse()

	# Change to specified directory to output to
	outdir = document.config['files']['directory']
	if outdir:
		outdir = string.Template(outdir).substitute({'jobname':jobname})
		if not os.path.isdir(outdir):
			os.makedirs(outdir)
		log.info('Directing output files to directory: %s.' % outdir)
		os.chdir(outdir)

	# Perform prerender transforms
	logger.info("Perform prerender transforms.")
	transforms.performTransforms(document, context=components)

	db = None
	if outFormat in ('images', 'xhtml', 'text'):
		logger.info("Generating images")
		db = generateImages(document)

	if outFormat == 'xhtml':
		logger.info("Begin render")
		render(document, document.config['general']['renderer'], db)
		logger.info("Begin post render")
		postRender(document, jobname=jobname, context=components, dochecking=dochecking, doindexing=doindexing)

	elif outFormat == 'xml':
		logger.info("To Xml.")
		toXml(document, jobname)

	elif outFormat == 'text':
		logger.info("Begin render")
		render(document, document.config['general']['renderer'], db)


	logger.info("Write metadata.")
	write_dc_metadata(document, jobname)

	elapsed = time.time() - start_t
	logger.info("Rendering took %s(s)", elapsed)

from nti.utils import setupChameleonCache

def postRender(document, contentLocation='.', jobname='prealgebra', context=None, dochecking=True, doindexing=True):
	# FIXME: This was not particularly well thought out. We're using components,
	# but named utilities, not generalized adapters or subscribers.
	# That makes this not as extensible as it should be.

	# We very likely will get a book that has no pages
	# because NTIIDs are not added yet.
	start_t = time.time()
	logger.info('Creating rendered book')
	book = RenderedBook(document, contentLocation)
	elapsed = time.time() - start_t
	logger.info("Rendered book created in %s(s)", elapsed)

	# This step adds NTIIDs to the TOC in addition to modifying
	# on-disk content.
	logger.info('Adding icons to toc and pages')
	tociconsetter.transform(book, context=context)

	logger.info('Storing content height in pages')
	contentsizesetter.transform(book, context=context)

	logger.info('Adding related links to toc')
	relatedlinksetter.performTransforms(book, context=context)

	# SAJ: Disabled until we determine what thumbnails we need and how to create them in a useful manner.
	#logger.info('Generating thumbnails for pages')
	#contentthumbnails.transform(book, context=context)

	# PhantomJS doesn't cope well with the iframes
	# for embedded videos: you get a black box, and we put them at the top
	# of the pages, so many thumbnails end up looking the same, and looking
	# bad. So do this after taking thumbnails.
	logger.info('Adding videos')
	sectionvideoadder.performTransforms(book, context=context)

	if dochecking:
		logger.info('Running checks on content')
		contentchecks.performChecks(book, context=context)

	contentPath = os.path.realpath(contentLocation)
	if doindexing and  not os.path.exists(os.path.join(contentPath, 'indexdir')):
		# We'd like to be able to run this with pypy (it's /much/ faster)
		# but some of the Zope libs we import during contentsearch (notably Persistent)
		# are not quite compatible. A previous version of this code made the correct
		# changes PYTHONPATH changes for this to work (before contentsearch grew those deps);
		# now it just generates exceptions, so we don't try right now
		start_t = time.time()
		logger.info("Indexing content in-process.")
		for name, impl in component.getUtilitiesFor(interfaces.IRenderedBookIndexer):
			logger.info("Indexing %s content", name)
			impl.transform(book, jobname)
		elapsed = time.time() - start_t
		logger.info("Content indexing took %s(s)", elapsed)

	# TODO: Aren't the things in the archive mirror file the same things
	# we want to list in the manifest? If so, we should be able to combine
	# these steps (if nothing else, just list the contents of the archive to get the
	# manifest)
	logger.info("Creating html cache-manifest")
	html5cachefile.main(contentPath, contentPath)

	logger.info('Changing intra-content links')
	ntiidlinksetter.transform(book)

	# In case order matters, we sort by the name of the
	# utility. To register, use patterns like 001, 002, etc.
	# Ideally order shouldn't matter, and if it does it should be
	# handled by a specialized dispatching utility.
	for name, extractor in sorted(component.getUtilitiesFor(interfaces.IRenderedBookTransformer)):
		if interfaces.IRenderedBookIndexer.providedBy(extractor):
			continue
		logger.info("Extracting %s/%s", name, extractor)
		extractor.transform(book)

	logger.info("Creating JSONP content")
	jsonpbuilder.transform(book)

	logger.info("Creating an archive file")
	archive.create_archive(book, name=jobname)

def render(document, rname, db):
	# Apply renderer
	renderer = createResourceRenderer(rname, db, unmix=False)
	renderer.render(document)
	return renderer

def toXml(document, jobname):
	outfile = '%s.xml' % jobname
	with open(outfile, 'w') as f:
		f.write(document.toXML().encode('utf-8'))

def write_dc_metadata(document, jobname):
	"""
	Write an XML file containing the DublinCore metadata we can extract for this document.
	"""
	mapping = {}
	metadata = document.userdata

	logger.info("Writing DublinCore Metadata.")

	if 'author' in metadata:
		# latex author and DC Creator are both arrays
		mapping['Creator'] = [x.textContent for x in metadata['author']]
	if 'title' in metadata:
		# DC Title is an array, latex title is scalar
		# Sometimes title may be a string or it may be a TeXElement, depending
		# on what packages have dorked things up
		mapping['Title'] = (getattr(metadata['title'], 'textContent', metadata['title']),)
	# The 'date' command in latex is free form, which is not
	# what we want for DC...what do we want?


	# For other options, see zope.dublincore.dcterms.name_to_element
	# Publisher, in particular, would be a good one

	if not mapping:
		return

	xml_string = unicode(zope.dublincore.xmlmetadata.dumpString(mapping))
	with open('dc_metadata.xml', 'w') as f:
		f.write(xml_string.encode('utf-8'))

def generateImages(document):
	### Generates required images ###
	# Replace this with configuration/use of ZCA?
	local_overrides = os.path.join(os.getcwd(), '../nti.resourceoverrides')
	if os.path.exists(os.path.join(local_overrides, ResourceTypeOverrides.OVERRIDE_INDEX_NAME)):
		overrides = local_overrides
	else:
		overrides = resource_filename(__name__, 'resourceoverrides')
	db = ResourceDB(document, overridesLocation=overrides)
	db.generateResourceSets()
	return db
