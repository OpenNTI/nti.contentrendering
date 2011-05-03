#!/usr/bin/env python
import os,tempfile, shutil,re, codecs
from plasTeX.Logging import getLogger
import plasTeX.Imagers, glob, sys, os
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import resources
from collections import defaultdict

log = getLogger()
depthlog = getLogger('render.images.depth')
status = getLogger('status')
imagelog = getLogger('imager')

try:
	import Image as PILImage
	import ImageChops as PILImageChops
except ImportError:
	PILImage = PILImageChops = None


import plasTeX.Imagers
from plasTeX.Imagers import Image, WorkingFile


status = getLogger('status')

gs = 'gs'
if sys.platform.startswith('win'):
	gs = 'gswin32c'

import plasTeX.Imagers.gspdfpng

def _scale(input, output, scale):
	# Use IM to scale. Must be top-level to pickle
	return os.system( 'convert %s -scale %d%% %s' % (input, scale*25 , output) )

class GSPDFPNG2(plasTeX.Imagers.gspdfpng.GSPDFPNG):
	""" Imager that uses gs to convert pdf to png, using PDFCROP to handle the scaling """
	command = ('%s -dSAFER -dBATCH -dNOPAUSE -sDEVICE=pngalpha -r500 ' % gs) + \
			  '-dGraphicsAlphaBits=4 -sOutputFile=img%d.png'
	compiler = 'pdflatex'
	fileExtension = '.png'
	scaleFactor=1

	def executeConverter(self, output):
		open('images.out', 'wb').write(output.read())
		# Now crop it
		print 'croping'
		os.system( "pdfcrop --hires --margin 3 images.out images.out" )
		options = ''
		if self._configOptions:
			for opt, value in self._configOptions:
				opt, value = str(opt), str(value)
				if ' ' in value:
					value = '"%s"' % value
				options += '%s %s ' % (opt, value)

		res = os.system('%s %s%s' % (self.command, options, 'images.out')), None
		self.scaleImages()
		return res

	def scaleImages(self):
		" Uses ImageMagick to scale the images in parallel "
		with ProcessPoolExecutor() as executor:
			pngs=glob.glob('img*.png')
			for i in executor.map( _scale, pngs, pngs, [self.scaleFactor for x in pngs]):
				pass



Imager = GSPDFPNG2

class ResourceGenerator(resources.ResourceGenerator):
	extension='png'
	resourceType='png'
	def __init__(self, document):
		super(ResourceGenerator, self).__init__(document, Imager(document, ''))


	def convert(self, output, resourcesets):
		imager=self.imager

		if not imager:
			log.warning('No imager command is configured.  ' +
						'No images will be created.')
			return []

		cwd = os.getcwd()

		# Make a temporary directory to work in
		baseTemp = tempfile.mkdtemp()
		os.chdir(baseTemp)

		# Execute converter

		scaledImages={1:None, 2:None, 4:None}

		tmpLocations={}

		for scale in scaledImages.keys():

			subTempDir=tempfile.mkdtemp(dir=baseTemp)
			tmpLocations[scale]=subTempDir
			os.chdir(subTempDir)
			output.seek(0)
			scaledImages[scale]=self.__generateWithScaleFactor(output, resourcesets, scale)
			os.chdir(baseTemp)


		if PILImage is None:
			log.warning('PIL (Python Imaging Library) is not installed.	 ' +
						'Images will not be cropped.')

		os.chdir(cwd)



		# Move images to their final location and create img objects to return
		for scale in scaledImages.keys():
			tempdir=tmpLocations[scale]
			for tmpPath, resourceset in zip(scaledImages[scale], resourcesets):

				imageObj = self.__createImageObject(resourceset, tmpPath, '%sx'%scale)

				if not self.resourceType in  resourceset.resources:
					resourceset.resources[self.resourceType]={}

				resourceset.resources[self.resourceType][scale]=imageObj

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
					log.warning('failed to crop %s (%s)', imageObj.path, msg)

		# Remove temporary directory
		shutil.rmtree(baseTemp, True)

	def __generateWithScaleFactor(self,output, resourcesets, factor):
		imager=self.imager
		imager.scaleFactor=factor

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

		return images



	def __createImageObject(self, resourceset, orig, fname):
		#Create a dest for the image
		finalPath = os.path.join(resourceset.path, orig)


		if os.path.exists(finalPath):
			name, ext=os.path.splitext(orig)
			finalPath=os.path.join(os.path.dirname(finalPath),('%s_%s%s'%(name, fname, ext)))

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

		return imageObj
