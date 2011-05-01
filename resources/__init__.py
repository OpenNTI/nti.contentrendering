#!/usr/bin/env python

import os, time, tempfile, shutil, re, string, pickle, codecs, pdb
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

class ResourceSet(object):
	def __init__(self, path, source):
		self.path=path
		self.resources={}
		self.source=source
	def getTypes(self):
		return resources.keys()
	def __str__(self):
		return '%s' % self.resources

import uuid
class ResourceDB(object):

	types = {'svg': 'pdf2svg', 'png': 'gspdfpng2', 'mathml': 'html2mathml'}

	"""
	Manages external resources (images, mathml, videos, etc..) for a document
	"""
	def __init__(self, document, path=None):
		self.__document=document
		self.__config=self.__document.config
		if not path:
			path = self.__config['resourcedb']['location']

		self.__dbpath=os.path.join(path, self.__document.userdata['jobname'])

		if not os.path.isdir(self.__dbpath):
			os.makedirs(self.__dbpath)

		log.info('Using %s as resource db' % self.__dbpath)

		self.__indexPath = os.path.join(self.__dbpath, 'resources.index')

		self.__loadResourceDB()

		self.__generateResourceSets()

		self.__saveResourceDB()

	def __str__(self):
		return '%s'%self.__db

	def getResourceSet(self, node):
		if node.source in self.__db:
			return self.__db[node.source]
		else:
			return None

	def __generateResourceSets(self):

		#set of all nodes we need to generate resources for
		nodesToGenerate=self.__findNodes(self.__document)

		#print nodesToGenerate

		#Each unique source gets a resourceset
		for node in nodesToGenerate:
			if not node.source in  self.__db:
				self.__db[node.source]=ResourceSet(os.path.join(self.__dbpath,str(uuid.uuid1())), node.source)
		#Generate a mapping of types to source  {png: [src2, src5], mathml: [src1, src5]}
		typesToSource=defaultdict(set)



		for node in nodesToGenerate:
			resourceset=self.__db[node.source]
			for rType in node.resourceTypes:
				if not rType in resourceset.resources:
					typesToSource[rType].add(node.source)

		print typesToSource

		for rType, sources in typesToSource.items():
			self.__generateResources(rType, sources)

	def __generateResources(self, type, sources):
		#Load a resource generate
		generator=self.__loadGenerator(type)

		if not generator:
			return


		resourcesets=[rset for rset in self.__db.values() if rset.source in sources]

		generator.generateResources(self.__document, resourcesets)

	def __loadGenerator(self, type):
		if not type in self.types:
			log.warn('No generator specified for resource type %s' % type)
			return None
		try:
			exec('from %s import ResourceGenerator' % self.types[type])
			return ResourceGenerator(self.__document)
		except ImportError, msg:
			log.warning("Could not load custom imager '%s' because '%s'" % (type, msg))
			return None



	def __findNodes(self, node):
		nodes=[]
		#print 'looking at node %s'%node
		if getattr(node, 'resourceTypes', None):
		#	print '****** Found resource types %s'%node.resourceTypes
			nodes.append(node)

		if getattr(node, 'attributes', None):
			for attrval in node.attributes.values():
				if getattr(attrval, 'childNodes', None):
					for child in attrval.childNodes:
						nodes.extend(self.__findNodes(child))

		for child in node.childNodes:
			nodes.extend(self.__findNodes(child))

		return list(set(nodes))


	def __loadResourceDB(self):
		if os.path.isfile(self.__indexPath):
			try:
				self.__db = pickle.load(open(self.__indexPath, 'r'))
				for key, value in self.__db.items():
					if not os.path.exists(value.path):
						print 'Deleting resources for %s %s'% (key, value.path)
						del self.__db[key]
						continue
			except ImportError:
				print 'Error loading cache.  Starting from scratch'
				os.remove(self.__indexPath)
				self.__db={}
		else:
			self.__db={}

	def __saveResourceDB(self):
		if not os.path.isdir(os.path.dirname(self.__indexPath)):
			os.makedirs(os.path.dirname(self.__indexPath))
		pickle.dump(self.__db, open(self.__indexPath,'w'))



#We need to add caching so we don't regenerate from run to run.  We also
#need to key images by source so we don't
#generate duplicate images
class ResourceGenerator(object):

	compiler = 'latex'

	imageAttrs = ''

	def __init__(self,document,  imager):
		 self.imager=imager
		 self.document=document

	#resource sets = source->resourceset
	def generateResources(self, document,resourcesets):
		"""
		The first pass collects the latex source for each of the
		provided nodes.  A latex file is generated from the collected source and compiled.  The compiled latex
		is passed to the imager and the the list of generated images are returned.  The images are stored on disk
	    in the path provided by the resource set and noted as appropriate
		"""
		self.config=document.config

		# Start the document with a preamble
		self.source = StringIO()
		self.source.write('\\scrollmode\n')
		self.__writePreamble(document)
		self.source.write('\\begin{document}\n')
		self.source.write('\\graphicspath{{%s/}}\n' % (document.userdata['working-dir']))


		#Collect the requested nodes

		for resourceSet in resourcesets:
			self.writeNode(resourceSet.source)


		#Finish the document
		self.source.write('\n\\end{document}\\endinput')

		#Compile the latex source into something usefull to the imagers
		#Each page of the output is an image and is in the order of the ids
		output = self.__compileLatex(self.source)

		#Given the output execute each imager.  Collect the resulting paths by id
		#so they can be added to the dom

		self.convert(output, resourcesets)


	def convert(self, output,  resourcesets):
		"""
		Given a compiled latex document of images execute the provided imager and
		persist the results.
		"""

		imager=self.imager

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
		if len(images) != len(resourcesets):
 			log.warning('The number of images generated (%d) and the number of images requested (%d) is not the same.' % (len(images), len(nodes)))

		# Sort by creation date
		#images.sort(lambda a,b: cmp(os.stat(a)[9], os.stat(b)[9]))

		images.sort(lambda a,b: cmp(int(re.search(r'(\d+)\.\w+$',a).group(1)),
									int(re.search(r'(\d+)\.\w+$',b).group(1))))

		os.chdir(cwd)

		if PILImage is None:
			log.warning('PIL (Python Imaging Library) is not installed.	 ' +
						'Images will not be cropped.')


		# Move images to their final location and create img objects to return
		for tmpPath, resourceset in zip(images, resourcesets):

			#Create a dest for the image
			finalPath = os.path.join(resourceset.path, tmpPath)

			print 'Moving image for %s to %s' % (resourceset.source, finalPath)

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

			resourceset.resources[self.resourceType]=imageObj

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

		filename = 'resources.tex'

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
		for ext in ['.dvi','.pdf','.ps','.xml']:
			if os.path.isfile('resources'+ext):
				output = WorkingFile('resources'+ext, 'rb', tempdir=tempdir)
				break

		# Change back to original working directory
		os.chdir(cwd)

		return output

	def writeNode(self,source, context=''):
		"""
		Write LaTeX source for the image

		Arguments:
		filename -- the name of the file that will be generated
		code -- the LaTeX code of the image
		context -- the LaTeX code of the context of the image

		"""
		self.source.write('%s\n\\begin{plasTeXimage}{%s}\n%s\n\\end{plasTeXimage}\n' % (context, source,source))



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

