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
import tex2html

class ResourceGenerator(tex2html.ResourceGenerator):

	resourceType='mathjax_display'

	def writeResource(self, source, context):
		self.source.write('%s<span class="mathjax math tex2jax_process mathquill-embedded-latex">%s</span>\n\n' % (context , cgi.escape(source)))
