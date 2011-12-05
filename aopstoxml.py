#!/usr/bin/env python2.7

import os
import sys
import string
import datetime
import logging

import plasTeX
from plasTeX.TeX import TeX
from plasTeX.Logging import getLogger

import transforms

log = getLogger()

def _configure_logging():
	logging.basicConfig( level=logging.INFO )
	logging.root.handlers[0].setFormatter( logging.Formatter( '[%(name)s] %(levelname)s: %(message)s' ) )

def main(argv):
	""" Main program routine """

	_configure_logging()

	sourceFile = argv.pop(0)
	outFormat = 'xml'

	if argv:
		outFormat = argv.pop(0)

	# Create document instance that output will be put into
	document = plasTeX.TeXDocument()

	#setup config options we want
	document.config['files']['split-level'] = 1
	document.config['general']['theme']='AoPS'

	# Instantiate the TeX processor
	tex = TeX(document, file=sourceFile)

	# Populate variables for use later
	jobname = document.userdata['jobname'] = tex.jobname
	document.userdata['working-dir'] = os.getcwd()
	document.userdata['generated_time'] = str(datetime.datetime.now())
	document.userdata['transform_process'] = True;
	setupResources()

	# Load aux files for cross-document references
#	pauxname = '%s.paux' % jobname

	# for dirname in [cwd] + config['general']['paux-dirs']:
	#	for fname in glob.glob(os.path.join(dirname, '*.paux')):
	#		if os.path.basename(fname) == pauxname:
	#			continue
	#		document.context.restore(fname, rname)

	# Parse the document
	print "Parsing %s" % sourceFile
	tex.parse()

	# Set up TEXINPUTS to include the current directory for the renderer
	os.environ['TEXINPUTS'] = '%s%s%s%s' % (os.getcwd(), os.pathsep,
										 os.environ.get('TEXINPUTS',''), os.pathsep)
	# Change to specified directory to output to
	outdir = document.config['files']['directory']
	if outdir:
		outdir = string.Template(outdir).substitute({'jobname':jobname})
		if not os.path.isdir(outdir):
			os.makedirs(outdir)
		log.info('Directing output files to directory: %s.' % outdir)
		os.chdir(outdir)

	#Perform prerender transforms
	transforms.performTransforms( document )

	if outFormat == 'images' or outFormat == 'xhtml':
		print "Generating images"
		db = generateImages(document)

	if outFormat == 'xhtml':
		render( document, 'XHTML', db )
		postRender(document, indexname=jobname)

	if outFormat == 'xml':
		toXml( document, jobname )

def nextID(self):
	ntiid = getattr(self, 'NTIID',-1)

	ntiid = ntiid + 1

	setattr(self, 'NTIID', ntiid)
	provider = os.environ.get( "NTI_PROVIDER", "AOPS" )
	return 'tag:nextthought.com,2011-10:%s-HTML-%s.%s' % (provider,self.userdata['jobname'], ntiid)

plasTeX.TeXDocument.nextNTIID=nextID

import mirror
import indexer
import tociconsetter
import html5cachefile
import contentsizesetter
import relatedlinksetter
import contentthumbnails

from RenderedBook import RenderedBook

import contentchecks

def postRender(document, contentLocation='.', indexname='prealgebra'):
	print 'Performing post render steps'

	#This goes first b/c it sets the root node of the toc up
	print 'Adding icons to toc and pages'
	toc_file = os.path.join(contentLocation, 'eclipse-toc.xml')
	tociconsetter.transform(toc_file, contentLocation)

	print 'Fetching page info'
	book = RenderedBook(document, contentLocation)

	print 'Storing content height in pages'
	contentsizesetter.transform(book)

	print 'Adding related links to toc'
	relatedlinksetter.transform(book)

	print 'Generating thumbnails for pages'
	contentthumbnails.transform(book)

	print 'Running checks on content'
	contentchecks.performChecks(document, book)

	contentPath = os.path.realpath(contentLocation)
	if not os.path.exists( os.path.join( contentPath, 'indexdir' ) ):
		print "indexing content"
		indexer.index_content(tocFile=toc_file, contentPath=contentPath, indexname=indexname)

	print "Creating html cache-manifest"
	html5cachefile.main(contentPath, contentPath)

	print "Creating a mirror file"
	mirror.main(contentPath, contentPath, indexname + ".zip")

from resources.ResourceRenderer import createResourceRenderer

def render(document, rname, db):
	# Apply renderer
	renderer = createResourceRenderer(rname, db)
	renderer.render(document)

def toXml( document, jobname ):
	outfile = '%s.xml' % jobname
	with open(outfile,'w') as f:
		f.write(document.toXML().encode('utf-8'))

from resources import ResourceDB

def setupResources():
	from plasTeX.Base import Arrays
	tabularTypes = ['png', 'svg']

	Arrays.tabular.resourceTypes = tabularTypes
	Arrays.TabularStar.resourceTypes = tabularTypes
	Arrays.tabularx.resourceTypes = tabularTypes

	from plasTeX.Base import Math

	#The math package does not correctly implement the sqrt macro.	It takes two args
	Math.sqrt.args='[root]{arg}'

	inlineMathTypes = ['mathjax_inline']
	displayMathTypes = ['mathjax_display']

	#inlineMathTypes = ['mathjax_inline', 'png', 'svg']
	#displayMathTypes = ['mathjax_display', 'png', 'svg']

	Math.math.resourceTypes = inlineMathTypes
	Math.ensuremath.resourceTypes=inlineMathTypes

	Math.displaymath.resourceTypes = displayMathTypes
	Math.EqnarrayStar.resourceTypes = displayMathTypes

	# FIXME: Star imports!
	from plasTeX.Packages.amsmath import align, AlignStar, alignat, AlignatStar, gather, GatherStar

	from plasTeX.Packages.graphicx import includegraphics
	includegraphics.resourceTypes = ['png']

	align.resourceTypes = displayMathTypes
	AlignStar.resourceTypes = displayMathTypes
	alignat.resourceTypes = displayMathTypes
	AlignatStar.resourceTypes = displayMathTypes
	gather.resourceTypes = displayMathTypes
	GatherStar.resourceTypes = displayMathTypes

	# XXX FIXME If we don't do this, then we can get
	# a module called graphicx reloaded from this package
	# which doesn't inherit our type. Who is doing that?
	sys.modules['graphicx'] = sys.modules['plasTeX.Packages.graphicx']

	#includegraphics.resourceTypes = ['png', 'svg']

def generateImages(document):
	### Generates required images ###

	overrides = os.path.join(os.path.dirname(__file__), 'resourceoverrides')
	db = ResourceDB(document, overridesLocation=overrides)
	db.generateResourceSets()
	return db

if __name__ == '__main__':
	main(sys.argv[1:])
