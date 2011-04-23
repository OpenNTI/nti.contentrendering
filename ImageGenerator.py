#!/usr/bin/env python

import os, time, tempfile, shutil, re, string, pickle, codecs
try: from hashlib import md5
except ImportError: from md5 import new as md5
from plasTeX.Logging import getLogger
from StringIO import StringIO
from plasTeX.Filenames import Filenames
from plasTeX.dictutils import ordereddict
import subprocess
import shlex
import plasTeX.Imagers
from plasTeX.Imagers import WorkingFile, Image


log = getLogger()
depthlog = getLogger('render.images.depth')
status = getLogger('status')
imagelog = getLogger('imager')

try:
	import Image as PILImage
	import ImageChops as PILImageChops
except ImportError:
	PILImage = PILImageChops = None

from collections import defaultdict

#We need to add caching so we don't regenerate from run to run.  We also
#need to key images by source so we don't
#generate duplicate images
class ImageGenerator(object):

	compiler = 'latex'

	imageAttrs = ''

	def __init__(self, document, names = None):
		self.config=document.config

		imagerNames = [ x for x in names if x ]

		self.imagers=[]

		for name in imagerNames:
			if name == 'none':
				break
			try:
				exec('from plasTeX.Imagers.%s import Imager' % name)
			except ImportError, msg:
				log.warning("Could not load default imager '%s' because '%s'" % (name, msg))
			try:
				exec('from %s import Imager' % name)
			except ImportError, msg:
				log.warning("Could not load custom imager '%s' because '%s'" % (name, msg))
				continue

			imager = Imager(document, None)



			# Make sure that this imager works on this machine
			if imager.verify():
				self.imagers.append(imager)
				log.info('Using the imager "%s".' % name)

		if len(self.imagers) == 0:
			log.warn('No imagers found.  Images will not be generated')



	def renderImages(self, document, nodes):
		"""
		The first pass collects the latex source for each of the
		provided nodes.  A latex file is generated from the collected source and compiled.  The compiled latex
		is passed to each imager and the the list of generated images are returned.  The images are stored on disk
		and another pass is made over the dom to add image details to the specified nodes.
		"""


		self.config = document.config

		# Start the document with a preamble
		self.source = StringIO()
		self.source.write('\\scrollmode\n')
		self.__writePreamble(document)
		self.source.write('\\begin{document}\n')
		self.source.write('\\graphicspath{{%s/}}\n' % (document.userdata['working-dir']))


		#Collect the requested nodes

		for node in nodes:
			self.__writeImage(node)


		#Finish the document
		self.source.write('\n\\end{document}\\endinput')

		#Compile the latex source into something usefull to the imagers
		#Each page of the output is an image and is in the order of the ids
		output = self.__compileLatex(self.source)

		#Given the output execute each imager.  Collect the resulting paths by id
		#so they can be added to the dom


		convertedImages = defaultdict(list)
		for imager in self.imagers:
			log.info('Converting images using %s' % imager)
			#Make sure we are at the beginning of the output for each imager
			output.seek(0)
			images = self.__convert(output, nodes, imager)
			#print images
			for node, generatedPath in zip(nodes, images):
				convertedImages[node].append(generatedPath)

		#pass back over the nodes and add info for the images
		for node in nodes:
			node.images=convertedImages[node]


	def __convert(self, output, nodes, imager):
		"""
		Given a compiled latex document of images execute the provided imager and
		persist the results. The list of persisted image objects are returned
		"""
		if not imager:
			log.warning('No imager command is configured.  ' +
						'No images will be created.')
			return []

		cwd = os.getcwd()

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()
		os.chdir(tempdir)

		# Execute converter


		rc, images = imager.executeConverter(output)
		if rc:
			log.warning('Image converter did not exit properly.	 ' +
						'Images may be corrupted or missing.')
		#print "Converted images are"
		#print images

		# Get a list of all of the image files
		if images is None:
			images = [f for f in os.listdir('.')
							if re.match(r'^img\d+\.\w+$', f)]
		if len(images) != len(nodes):
 			log.warning('The number of images generated (%d) and the number of images requested (%d) is not the same.' % (len(images), len(nodes)))

		# Sort by creation date
		#images.sort(lambda a,b: cmp(os.stat(a)[9], os.stat(b)[9]))

		images.sort(lambda a,b: cmp(int(re.search(r'(\d+)\.\w+$',a).group(1)),
									int(re.search(r'(\d+)\.\w+$',b).group(1))))

		os.chdir(cwd)

		if PILImage is None:
			log.warning('PIL (Python Imaging Library) is not installed.	 ' +
						'Images will not be cropped.')

		imageObjs=[]

		# Move images to their final location and create img objects to return
		for tmpPath, node in zip(images, nodes):

			#Create a dest for the image
			finalPath = 'images/%s/%s%s' % (node.id, node.id, imager.fileExtension)

			imageObj = Image(finalPath, self.config['images'])

			# Populate image attrs that will be bound later
			if self.imageAttrs:
				tmpl = string.Template(self.imageAttrs)
				vars = {'filename':filename}
				for name in ['height','width','depth']:
					if getattr(img, name) is None:
						vars['attr'] = name
						value = DimensionPlaceholder(tmpl.substitute(vars))
						value.imageUnits = self.imageUnits
						setattr(img, name, value)

			imageObjs.append(imageObj)

			# Move the image
			directory = os.path.dirname(imageObj.path)
			if directory and not os.path.isdir(directory):
				os.makedirs(directory)
			try:
				shutil.copy2(os.path.join(tempdir,tmpPath), imageObj.path)
			except OSError:
				shutil.copy(os.path.join(tempdir, tmpPath), imageObj.path)

			try:
				imageObj.crop()
			 	status.dot()
			except Exception, msg:
			 	import traceback
			 	traceback.print_exc()
			 	log.warning('failed to crop %s (%s)', dest.path, msg)

		# Remove temporary directory
		shutil.rmtree(tempdir, True)

		return imageObjs


	def __compileLatex(self, source):
		"""
		Compile the LaTeX source

		Arguments:
		source -- the LaTeX source to compile

		Returns:
		file object corresponding to the output from LaTeX

		"""
		cwd = os.getcwd()

		# Make a temporary directory to work in
		tempdir = tempfile.mkdtemp()
		os.chdir(tempdir)

		filename = 'images.tex'

		# Write LaTeX source file
		if self.config['images']['save-file']:
			self.source.seek(0)
			codecs.open(os.path.join(cwd,filename), 'w', self.config['files']['input-encoding']).write(self.source.read())
		self.source.seek(0)
		codecs.open(filename, 'w', self.config['files']['input-encoding']).write(self.source.read())

		# Run LaTeX
		os.environ['SHELL'] = '/bin/sh'
		program = self.config['images']['compiler']
		if not program:
			program = self.compiler


		os.system(r"%s %s" % (program, filename))
		#JAM: This does not work. Fails to read input
		# cmd = str('%s %s' % (program, filename))
		# print shlex.split(cmd)
		# p = subprocess.Popen(shlex.split(cmd),
		# 			 stdout=subprocess.PIPE,
		# 			 stderr=subprocess.STDOUT,
		# 			 )
		# while True:
		# 	line = p.stdout.readline()
		# 	done = p.poll()
		# 	if line:
		# 		imagelog.info(str(line.strip()))
		# 	elif done is not None:
		# 		break

		output = None
		for ext in ['.dvi','.pdf','.ps']:
			if os.path.isfile('images'+ext):
				output = WorkingFile('images'+ext, 'rb', tempdir=tempdir)
				break

		# Change back to original working directory
		os.chdir(cwd)

		return output

	def __writeImage(self,node, context=''):
		"""
		Write LaTeX source for the image

		Arguments:
		filename -- the name of the file that will be generated
		code -- the LaTeX code of the image
		context -- the LaTeX code of the context of the image

		"""
		self.source.write('%s\n\\begin{plasTeXimage}{%s}\n%s\n\\end{plasTeXimage}\n' % (context, node.id, node.source))



	def __writePreamble(self, document):
		""" Write any necessary code to the preamble of the document """
		self.source.write(document.preamble.source)
		self.source.write('\\makeatletter\\oddsidemargin -0.25in\\evensidemargin -0.25in\n')

#		self.source.write('\\tracingoutput=1\n')
#		self.source.write('\\tracingonline=1\n')
#		self.source.write('\\showboxbreadth=\maxdimen\n')
#		self.source.write('\\showboxdepth=\maxdimen\n')
#		self.source.write('\\newenvironment{plasTeXimage}[1]{\\def\\@current@file{#1}\\thispagestyle{empty}\\def\\@eqnnum{}\\setbox0=\\vbox\\bgroup}{\\egroup\\typeout{imagebox:\\@current@file(\\the\\ht0+\\the\\dp0)}\\box0\\newpage}')

		self.source.write('\\@ifundefined{plasTeXimage}{'
						  '\\newenvironment{plasTeXimage}[1]{' +
						  '\\vfil\\break\\plasTeXregister' +
						  '\\thispagestyle{empty}\\def\\@eqnnum{}\\def\\tagform@{\\@gobble}' +
						  '\\ignorespaces}{}}{}\n')
		self.source.write('\\@ifundefined{plasTeXregister}{' +
						  '\\def\\plasTeXregister{\\parindent=-0.5in\\ifhmode\\hrule' +
						  '\\else\\vrule\\fi height 2pt depth 0pt ' +
						  'width 2pt\\hskip2pt}}{}\n')

