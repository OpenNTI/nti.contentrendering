#!/usr/bin/env python

import codecs, os, shutil, time
import resources
import tempfile
from StringIO import StringIO
import subprocess
import cgi
from plasTeX.Imagers import *
import html2mathml
from concurrent.futures import ProcessPoolExecutor

_debug = False

class SetGenerator():
	
	htmlfile = 'math.html'
	
	illegalCommands=None
		
	def __init__(self, compiler, batch):
		self.batch = batch
		self.compiler = compiler;
		self.writer = StringIO()
		self.generatables = list()
		
	def size(self):
		return len(self.generatables)
	
	def addResource(self, s, context=''):
		self.generatables.append(s)
		self.writeResource(s, context)
		
	def writePreamble(self, document, configName):
		
		self.writer.write('<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"\
		"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">\
		<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">\
		<head>\
		<link rel="stylesheet" href="styles/styles.css" />\
		<script type="text/javascript" src="http://cdn.mathjax.org/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML"></script>')

		if configName:
			self.writer.write('<script type="text/javascript" src="%s"></script>' % configName)
		
		self.writer.write('<script type="text/javascript"\
		src="http://ajax.googleapis.com/ajax/libs/jquery/1.6.1/jquery.min.js"></script>\
		<script type="text/javascript" src="https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.13/jquery-ui.min.js">\
		</script>\
		</head>\
		<body>')
		
	def writeResource(self, source, context):
		self.writer.write('%s<span class="mathjax math tex2jax_process mathquill-embedded-latex">\(%s\)</span>\n\n' % (context , cgi.escape(source[1:-1])))

	def writePostamble(self):
		self.writer.write('</body></html>')
		
	def processSource(self, sourceConfigPath):
		
		start = time.time()
		
		output = self.compileSource(sourceConfigPath)
		
		files = self.convert(output)
		nfiles = len(files)
		
		if nfiles != len(self.generatables):
			print 'WARNING.	Expected %s files but only generated %s for batch %s' %\
				  (len(self.generatables), len(files), self.batch)
		
		elapsed = time.time() - start
		print "%s sources generated in %sms for batch %s" % (nfiles, elapsed, self.batch)
			
		return zip(files, self.generatables)
	
	def compileSource(self, sourceConfigPath):

		source = self.writer;
		source.seek(0)
		htmlSource = source.read()
		
		tempdir = tempfile.mkdtemp()
		
		#We need to copy the html file
		htmlOutFile = os.path.join(tempdir, self.htmlfile)
		codecs.open(htmlOutFile, 'w', 'utf-8').write(htmlSource)
		
		configName = os.path.basename(sourceConfigPath);
		configOutFile = os.path.join(tempdir, configName)
		try:
			configOutFile = os.path.join(tempdir, configName)
			copy(sourceConfigPath, configOutFile)
			
			program	 = self.compiler
			command = '%s "%s"' % (program, htmlOutFile)
			
			print 'executing %s' %command
			stdout, stderr=subprocess.Popen( command, shell=True, stdout=subprocess.PIPE).communicate()
			
			if _debug:
				print 'out'
				print stdout
				print 'error'
				print stderr
			
			return stdout	
		finally:
			os.remove(configOutFile)
			
	def convert(self, output):
		
		tempdir = tempfile.mkdtemp()
		
		maths = [math.strip().decode('utf-8') for math in output.split('\n') if math.strip()]

		i = 1
		files=[]
		for math in maths:
			fname=os.path.join(tempdir, ('math_%s.xml' % i))
			i=i+1
			codecs.open(fname, 'w', 'utf-8').write(math)
			files.append(fname)

		return files
	
#End SetGenerator
		
class ResourceGenerator(html2mathml.ResourceGenerator):

	concurrency = 4
	resourceType = 'mathjax_inline'
	javascript = '%s/tex2html.js'%(os.path.dirname(__file__))
	mathjaxconfigname = 'mathjaxconfig.js'
	mathjaxconfigfile = '%s/../renderers/Themes/AoPS/js/%s'%(os.path.dirname(__file__), mathjaxconfigname)

	def __init__(self, document):
		super(ResourceGenerator, self).__init__(document)

		script = self.javascript

		if script:
			self.compiler = 'phantomjs %s'% (script)
		else:
			print 'Unable to find tex2html.js'


	def generateResources(self, document, sources, db):
		
		generatableSources=[s for s in sources if self.canGenerate(s)]

		size = len(generatableSources)
		if not size > 0:
			print 'No sources to generate'
			return
		else:
			print 'Generating %s sources' % size
			
		configName = self.mathjaxconfigfile if self.mathjaxconfigname else None
		if not configName:
			print 'Mathjax config has not been provided.'
			
		generators = list()
		for i in range(self.concurrency):
			g = SetGenerator(self.compiler, i)	
			generators.append(g);	
			g.writePreamble(document, configName)
				
		i = 0
		for s in generatableSources:
			g = generators[i]
			g.addResource(s, '')
			i = i+1 if (i+1) < self.concurrency else 0

		for g in generators:
			g.writePostamble()

		#Process batches in parallel,
		params = [self.mathjaxconfigfile]*self.concurrency
		with ProcessPoolExecutor() as executor:
			for zipped in executor.map( _processBatchSource, generators, params):
				for fpath, source in zipped:
					if _debug:
						print '%s  -- %s' % (source, os.path.basename(fpath))
					db.setResource(source, [self.resourceType], resources.Resource(fpath))
			
	def writePreamble(self, document):
		pass
	
	def convert(self, output):
		pass
	
	def writeResource(self, source, context):
		pass
	
	def compileSource(self):
		pass
	
#End ResourceGenerator		
	
def _processBatchSource(generator, sourceConfigPath):
	if generator.size() > 0:
		return generator.processSource(sourceConfigPath);
	else:
		return ()
			
def findfile(file, searchPaths):
	for dirname in searchPaths:
		possible = os.path.join(dirname, file)
		if os.path.isfile(possible):
			return possible
	return None

def copy(source, dest):

	if _debug:
		print 'Copying %s to %s' % (source, dest)

	if not os.path.exists(os.path.dirname(dest)):
		os.makedirs(os.path.dirname(dest))
	try:
		shutil.copy2(source, dest)
	except OSError:
		shutil.copy(source, dest)
