#!/usr/bin/env python

import codecs, os, re, pdb, shutil
import resources
import xml.sax
import tempfile
from xml.sax.xmlreader import InputSource
from xml.dom import minidom
from StringIO import StringIO

class MathMLGenerator(resources.ResourceGenerator):
	compiler = 'ttm'
	resourceType='mathml'
	extension='xml'
	illegalCommands=['\\\\overleftrightarrow', '\\\\vv', '\\\\smash', '\\\\rlin', '\\\\textregistered']

	def __init__(self, document):
		super(ResourceGenerator, self).__init__(document, None)
		self.document=document

	def writeNode(self, source, context=''):
		"""
		Write LaTeX source for the image

		Arguments:
		filename -- the name of the file that will be generated
		code -- the LaTeX code of the image
		context -- the LaTeX code of the context of the image

		"""
		self.source.write('%s\n%s\n' % (context, source))


	def canGenerate(self, source):
		for command in self.illegalCommands:
			if re.search(command, source):
				return False
		return True

	def convert(self, output, resourcesets):
		cwd = os.getcwd()

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()
		os.chdir(tempdir)

		#pdb.set_trace()
		dom = self.buildMathMLDOM(output)
		mathmls = dom.getElementsByTagName('math')

		i = 0
		resources=[]
		for mathml in mathmls:
			resource='mathml_%s.xml'%i
			i=i+1
			codecs.open(resource, 'w',self.document.config['files']['output-encoding']).write(mathml.toxml())
			resources.append(resource)




		if len(resources) != len(resourcesets):
 			log.warning('The number of resources generated (%d) and the number of images requested (%d) is not the same.' % (len(resources), len(nodes)))



		os.chdir(cwd)

		# Move images to their final location and create img objects to return
		for tmpPath, resourceset in zip(resources, resourcesets):

			#Create a dest for the image
			finalPath = os.path.join(resourceset.path, tmpPath)

			print 'Moving resource for %s to %s' % (resourceset.source, finalPath)



			resourceset.resources[self.resourceType]=finalPath

			# Move the image
			directory = os.path.dirname(finalPath)
			if directory and not os.path.isdir(directory):
				os.makedirs(directory)
			try:
				shutil.copy2(os.path.join(tempdir,tmpPath), finalPath)
			except OSError:
				shutil.copy(os.path.join(tempdir, tmpPath), finalPath)


		# Remove temporary directory
		shutil.rmtree(tempdir, True)

	def buildMathMLDOM(self, output):
		#Load up the results into a dom
		parser = xml.sax.make_parser()
		parser.setEntityResolver(MyEntityResolver())

		return minidom.parse(output, parser)

ResourceGenerator=MathMLGenerator

class MyEntityResolver(xml.sax.handler.EntityResolver):
	def resolveEntity(self, p, s):
		return InputSource(s)
