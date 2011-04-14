#!/usr/bin/env python

import os, re
import plasTeX.Imagers

from concurrent.futures import ThreadPoolExecutor

class PDF2SVG(plasTeX.Imagers.VectorImager):
	""" Imager that uses pdf2svg """
	fileExtension = '.svg'
	verification = 'pdf2svg --help'
	compiler = 'pdflatex'

	def executeConverter(self, output):
		rc = 0
		open('images.pdf', 'w').write(output.read())
		#Crop all the pages of the PDF to the exact size
		os.system( "pdfcrop --hires --margin 0 images.pdf images.pdf" )
		#Find out how many pages to expect
		import subprocess
		maxpages = int(subprocess.Popen( "pdfinfo images.pdf | grep Pages | awk '{print $2}'", shell=True, stdout=subprocess.PIPE).communicate()[0])

		class Convert(object):

			def __call__( self, page ):
				# convert to svg
				filename = 'img%d.svg' % page
				rc = os.system('pdf2svg images.pdf %s %d' % (filename, page) )

				if not open(filename).read().strip():
					os.remove(filename)
					print 'Failed to convert %s' %filename
					return None

				#Then remove the width and height boxes since this interacts badly with
				#HTML embedding
				os.system( "sed -i '' 's/width=.*pt\"//' %s" % filename )
				return filename


		filenames = []
		with ThreadPoolExecutor( max_workers=16 ) as executor:
			for i in executor.map( Convert(), xrange( 1, maxpages + 1 ) ):
				if i:
					filenames.append( i )

		return 0, filenames

	def verify(self):
		return True

Imager = PDF2SVG
