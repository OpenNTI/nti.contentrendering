#!/usr/bin/env python

import codecs, os, re, pdb, shutil, sys
import resources
import xml.sax
import tempfile
from xml.sax.xmlreader import InputSource
from xml.dom import minidom
from StringIO import StringIO
import subprocess
from xml.dom import minidom
import cgi
from plasTeX.Imagers import *
import resources
import html2mathml

class ResourceGenerator(html2mathml.ResourceGenerator):

	htmlfile = 'math.html'
	resourceType = 'mathjax_inline'

	javascript = '%s/tex2html.js'%(os.path.dirname(__file__))

	mathjaxconfigname = 'mathjaxconfig.js'
	mathjaxconfigfile = '%s/../renderers/Themes/AoPS/js/%s'%(os.path.dirname(__file__), mathjaxconfigname)

	illegalCommands=None

	def __init__(self, document):
		super(ResourceGenerator, self).__init__(document)

		script = self.javascript

		if script:
			self.compiler = 'phantomjs %s'% (script)
		else:
			print 'Unable to find tex2html.js'


	def generateResources(self, document, sources, db):
		self.source = StringIO()

		self.writePreamble(document)

		generatableSources=[s for s in sources if self.canGenerate(s)]

		if not len(generatableSources) > 0:
			print 'No sources to generate'
			return

		for s in generatableSources:
			self.writeResource(s, '')

		self.source.write('</body></html>')

		output = self.compileSource()



		tempdir = tempfile.mkdtemp()

		cwd=os.getcwd()

		os.chdir(tempdir)

		files = self.convert(output)

		if len(files) != len(generatableSources):
			print 'WARNING.	 Expected %s files but only generated %s' % (len(generatableSources), len(files))

		os.chdir(cwd)

		for fname, source in zip(files, generatableSources):
			print '%s  -- %s' % (source, fname)
			db.setResource(source, [self.resourceType], resources.Resource(os.path.join(tempdir, fname)))


	def convert(self, output):
		maths = [math.strip().decode('utf-8') for math in output.split('\n') if math.strip()]


		i = 1
		files=[]
		for math in maths:
			fname='math_%s.xml'%i
			i=i+1
			codecs.open(fname, 'w', 'utf-8').write(math)
			files.append(fname)

		return files

	def writePreamble(self, document):
		self.source.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\
		<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\
		<head>\
		<link rel="stylesheet" href="styles/styles.css" />\
		<script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>')

		if self.mathjaxconfigfile:
			self.source.write('<script type="text/javascript" src="%s"></script>' % self.mathjaxconfigname)
		else:
			print 'Mathjax config has not been provided.'

		self.source.write('<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js"></script>\
		<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js"></script>\
		</head>\
		<body>')

	def writeResource(self, source, context):
		self.source.write('%s<span class="mathjax math tex2jax_process mathquill-embedded-latex">\(%s\)</span>\n\n' % (context , cgi.escape(source[1:-1])))

	def compileSource(self):
		cwd = os.getcwd()

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()
		os.chdir(tempdir)


		#We need to copy the mathjaxconfig file and then reference the relative path
		copy(self.mathjaxconfigfile, os.path.join(tempdir, self.mathjaxconfigname))

		self.source.seek(0)
		codecs.open(self.htmlfile, 'w', 'utf-8').write(self.source.read())

		# Run LaTeX
		os.environ['SHELL'] = '/bin/sh'
		program	 = self.compiler

		command = '%s %s' % (self.compiler, self.htmlfile)
		print 'executing %s' %command
		stdout, stderr=subprocess.Popen( command, shell=True, stdout=subprocess.PIPE).communicate()
		print 'out'
		print stdout
		print 'error'
		print stderr

		os.remove(self.mathjaxconfigname)

		os.chdir(cwd)

		return stdout

def findfile(file, searchPaths):
	for dirname in searchPaths:
		possible = os.path.join(dirname, file)
		if os.path.isfile(possible):
			return possible
	return None

def copy(source, dest):

	print 'Copying %s to %s' % (source, dest)

	if not os.path.exists(os.path.dirname(dest)):
		os.makedirs(os.path.dirname(dest))
	try:
		shutil.copy2(source, dest)
	except OSError:
		shutil.copy(source, dest)
