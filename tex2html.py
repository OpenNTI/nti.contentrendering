#!/usr/bin/env python

import codecs, os
import resources
import tempfile
import subprocess
import cgi
from plasTeX.Imagers import *
import html2mathml

_debug = False

class ResourceSetGenerator(resources.BaseResourceSetGenerator):

	htmlfile 			= 'math.html'
	mathjaxconfigname	= 'mathjaxconfig.js'
	mathjaxconfigfile	= '%s/../renderers/Themes/AoPS/js/%s'%(os.path.dirname(__file__), mathjaxconfigname)

	def __init__(self, compiler, encoding, batch):
		super(ResourceSetGenerator, self).__init__(compiler, encoding, batch)

		#TODO: Why the check???
		self.configName = self.mathjaxconfigfile if self.mathjaxconfigname else None
		if not self.configName:
			print 'Mathjax config has not been provided.'


	def writePreamble(self, preamble):

		self.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\
		"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\
		<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\
		<head>\
		<link rel="stylesheet" href="styles/styles.css" />\
		<script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>')

		if self.configName:
			self.write('<script type="text/javascript" src="%s"></script>' % self.configName)

		self.write('<script type="text/javascript"\
		src="http://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js"></script>\
		<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js">\
		</script>\
		</head>\
		<body>')

	def writeResource(self, source, context):
		self.write('%s<span class="mathjax math tex2jax_process mathquill-embedded-latex">\(%s\)</span>\n\n' %\
					(context , cgi.escape(source[1:-1])))

	def writePostamble(self):
		self.write('</body></html>')

	def compileSource(self):

		source = self.writer;
		source.seek(0)
		htmlSource = source.read()

		tempdir = tempfile.mkdtemp()

		#We need to copy the html file
		htmlOutFile = os.path.join(tempdir, self.htmlfile)
		codecs.open(htmlOutFile, 'w', 'utf-8').write(htmlSource)

		configName = os.path.basename(self.mathjaxconfigfile);
		configOutFile = os.path.join(tempdir, configName)
		try:
			configOutFile = os.path.join(tempdir, configName)
			resources.copy(self.mathjaxconfigfile, configOutFile, _debug)

			program	 = self.compiler
			command = '%s "%s"' % (program, htmlOutFile)

			print 'executing %s' %command
			stdout, stderr=subprocess.Popen( command, shell=True, stdout=subprocess.PIPE).communicate()

			if _debug:
				print 'out'
				print stdout
				print 'error'
				print stderr

			return (stdout, tempdir)
		finally:
			os.remove(configOutFile)

	def convert(self, output, workdir):

		tempdir = tempfile.mkdtemp()

		maths = [math.strip().decode('utf-8') for math in output.split('\n') if math.strip()]

		i = 1
		files = list()
		for math in maths:
			fname = os.path.join(tempdir, ('math_%s.xml' % i))
			codecs.open(fname, 'w', 'utf-8').write(math)
			files.append(fname)
			i = i+1

		return [resources.Resource(name) for name in files]

#End ResourceSetGenerator

class ResourceGenerator(html2mathml.ResourceGenerator):

	concurrency			= 4
	illegalCommands		= None
	resourceType		= 'mathjax_inline'
	javascript 			= '%s/tex2html.js'%(os.path.dirname(__file__))

	def __init__(self, document):
		super(ResourceGenerator, self).__init__(document)
		self.compiler = 'phantomjs %s'% (self.javascript)

	def createResourceSetGenerator(self, compiler='', encoding = 'utf-8', batch = 0):
		return ResourceSetGenerator(compiler, encoding, batch)

#End ResourceGenerator

def _processBatchSource(generator, params):
	if generator.size() > 0:
		return generator.processSource()
	else:
		return ()


