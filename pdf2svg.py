#!/usr/bin/env python

import os, re
import plasTeX.Imagers

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
		page = 1
		while page <= maxpages:
			#convert to svg
			filename = 'img%d.svg' % page
			rc = os.system('pdf2svg images.pdf %s %d' % (filename, page) )
			if rc:
				break
			if not open(filename).read().strip():
				os.remove(filename)
				break
			#Then remove the width and height boxes since this interacts badly with
			#HTML embedding
			os.system( "sed -i '' 's/width=.*pt\"//' %s" % filename )
			page += 1
		return rc, None

	def verify(self):
		return True

Imager = PDF2SVG
