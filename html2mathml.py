#!/usr/bin/env python

import codecs, os, re, pdb, shutil
import resources
import xml.sax
import tempfile
from xml.sax.xmlreader import InputSource
from xml.dom import minidom
from StringIO import StringIO

from plasTeX.Imagers import *
import resources



class ResourceGenerator(resources.BaseResourceGenerator):
	compiler = 'ttm'
	fileExtension='.xml'
	resourceType='mathml'
	illegalCommands=['\\\\overleftrightarrow', '\\\\vv', '\\\\smash', '\\\\rlin', '\\\\textregistered']

	def convertOutput(self, output):



		dom = self.buildMathMLDOM(output)
		mathmls = dom.getElementsByTagName('math')
		i = 0
		resourceNames=[]
		cwd=os.getcwd()
		for mathml in mathmls:
			resource='%s_%s%s'%(self.resourceType, i, self.fileExtension)
			i=i+1
			codecs.open(resource, 'w',self.document.config['files']['output-encoding']).write(mathml.toxml())
			resourceNames.append(resource)
		return [resources.Resource(os.path.join(cwd, name)) for name in resourceNames]

	def canGenerate(self, source):
		for command in self.illegalCommands:
			if re.search(command, source):
				return False
		return True

	def buildMathMLDOM(self, output):
		#Load up the results into a dom
		parser = xml.sax.make_parser()
		parser.setEntityResolver(MyEntityResolver())

		return minidom.parse(output, parser)


class MyEntityResolver(xml.sax.handler.EntityResolver):
	def resolveEntity(self, p, s):

		name = s.split('/')[-1:][0]

		print 'looking for local source %s'%name
		local=findfile(name)

		if local:
			print 'Using local source'
			return InputSource(local)

		return InputSource(s)

import os, sys

def findfile(path):
    for dirname in sys.path:
        possible = os.path.join(dirname, path)
        if os.path.isfile(possible):
            return possible
    return None
