#!/usr/bin/env python

import cgi
import tex2html
from plasTeX.Imagers import *

class ResourceSetGenerator(tex2html.ResourceSetGenerator):

	def writeResource(self, source, context):
		self.writer.write('%s<span class="mathjax math tex2jax_process mathquill-embedded-latex">%s</span>\n\n' %\
						 (context , cgi.escape(source)))

#End ResourceSetGenerator

class ResourceGenerator(tex2html.ResourceGenerator):

	resourceType='mathjax_display'

	def createResourceSetGenerator(self, compiler='', encoding = 'utf-8', batch = 0):
		return ResourceSetGenerator(compiler, encoding, batch)

#End ResourceGenerator

def _processBatchSource(generator, sourceConfigPath):
	if generator.size() > 0:
		return generator.processSource()
	else:
		return ()



