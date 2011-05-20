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

	htmlfile='math.html'
	resourceType='mathjax'


	def __init__(self, document):
		super(ResourceGenerator, self).__init__(document)

		script = findfile('tex2html.js')

		if script:
			self.compiler = 'phantomjs %s'% (script)
		else:
			print 'Unable to fine tex2html.js'


	def generateResources(self, document, sources, db):
		self.source = StringIO()
		self.writePreamble(document)

		generatableSources=[s for s in sources if self.canGenerate(s)]

		for s in generatableSources:
			self.writeResource(s, '')

		self.source.write('</body></html>')

		output = self.compileSource()



		maths = [math.strip().decode('utf-8') for math in output.split('\n') if math.strip()][:-1]

		if len(maths) != len(generatableSources):
			print 'WARNING.  expected %d maths but got %d' % (len(generatableSources), len(maths))


		tempdir = tempfile.mkdtemp()

		cwd=os.getcwd()

		os.chdir(tempdir)

		i = 1
		for math, source in zip(maths, generatableSources):
			fname='math_%s.xml'%i
			i=i+1
			codecs.open(fname, 'w', 'utf-8').write(math)
			db.setResource(source, [self.resourceType], resources.Resource(os.path.join(tempdir, fname)))

		os.chdir(cwd)

	def writePreamble(self, document):
		self.source.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\
		<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\
		<head>\
		<meta name="generator" content="plasTeX" />\
		<meta content="text/html; charset=utf-8" http-equiv="content-type" />\
		<link rel="stylesheet" href="styles/styles.css" />\
		<script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>\
		<script>\
		MathJax.Hub.Config({\
		  showProcessingMessages: false,\
		  messageStyle: "none",\
		  TeX: {\
			Macros: {\
						rlin: [ \'\\overleftrightarrow{#1}\', 1],\
						vv: [ \'\\overrightarrow{#1}\', 1]\
				}\
		}\
		})\
		</script>\
		</head>\
		<body>')

	def writeResource(self, source, context):
		self.source.write('%s<span class="mathjax math tex2jax_process mathquill-embedded-latex">\(%s\)</span>\n\n' % (context , cgi.escape(source[1:-1])))

	def compileSource(self):
		cwd = os.getcwd()

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()
		os.chdir(tempdir)


		self.source.seek(0)
		codecs.open(self.htmlfile, 'w', 'utf-8').write(self.source.read())

		# Run LaTeX
		os.environ['SHELL'] = '/bin/sh'
		program  = self.compiler

		command = '%s %s' % (self.compiler, self.htmlfile)
		print 'executing %s' %command
		stdout, stderr=subprocess.Popen( command, shell=True, stdout=subprocess.PIPE).communicate()
		print 'out'
		print stdout
		print 'error'
		print stderr

		os.chdir(cwd)

		return stdout

def findfile(path):
    for dirname in sys.path:
        possible = os.path.join(dirname, path)
        if os.path.isfile(possible):
            return possible
    return None
