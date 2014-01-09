#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
$Id$
"""
from __future__ import print_function, unicode_literals, absolute_import
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from nti.contentrendering import plastexids
from nti.contentfragments import interfaces as cfg_interfaces
from nti.contentrendering import interfaces as crd_interfaces
from nti.contentrendering.plastexpackages._util import LocalContentMixin
from nti.contentrendering.plastexpackages.ntilatexmacros import ntivideo
from nti.contentrendering.plastexpackages.graphicx import includegraphics

from plasTeX.Base import Float
from plasTeX.Base import Floats
from plasTeX.Base import Command
from plasTeX.Base import Crossref
from plasTeX.Base import Environment
from plasTeX.Renderers import render_children

from zope import interface
from zope.cachedescriptors.property import readproperty

def _timeconvert( timestring ):
	"""Convert a time in the form HH:MM:SS, with hours and minutes optional, to seconds."""
	_t = timestring.split(':')
	t_out = 0
	if len(_t) == 3:
		if int(_t[1]) >= 60 or int(_t[2]) >= 60:
			raise ValueError('Invalid time in %s' % timestring)
		t_out = int(_t[0]) * 3600 + int(_t[1]) * 60 + float(_t[2])
	elif len(_t) == 2:
		if int(_t[1]) >= 60:
			raise ValueError('Invalid time in %s' % timestring)
		t_out = int(_t[0]) * 60 + float(_t[1])
	elif len(_t) == 1:
		t_out = float(_t[0])
	else:
		raise ValueError('Invalid time in %s' % timestring)
	return t_out

class ntislidedeckname(Command):
	pass

class ntislidedeckref(Crossref.ref):
	"""Used to link a ntislide to a ntislidedeck"""

	def digest(self, tex):
		super(ntislidedeckref, self).digest(tex)
		self.parentNode.slidedeck = self

@interface.implementer(crd_interfaces.IEmbeddedContainer)
class ntislidedeck(LocalContentMixin, Float, plastexids.NTIIDMixin):
	"""
	The ntislidedeck environment stores the metadata for a 'PowerPoint' style presentation.  
	Each slide that is a part of a presentation uses a ntislidedeckref command to link it to the approriate presentation.
	"""

	args = '[ options:dict ]'

	# A Float subclass to get \caption handling
	class caption(Floats.Caption):
		counter = 'ntislidedeck'

	# Only classes with counters can be labeled, and \label sets the
	# id property, which in turn is used as part of the NTIID (when no NTIID is set explicitly)
	counter = "ntislidedeck"
	blockType = True
	forcePars = False
	_ntiid_cache_map_name = '_ntislide_ntiid_map'
	_ntiid_allow_missing_title = False
	_ntiid_suffix = 'nsd.'
	_ntiid_title_attr_name = 'ref'
	_ntiid_type = 'NTISlideDeck'

	creator = None
	image = None
	type = 'application/vnd.nextthought.ntislidedeck'
	title = 'No Title'

	mimeType = 'application/vnd.nextthought.ntislidedeck'

	def digest(self, tokens):
		res = super(ntislidedeck,self).digest(tokens)
		if self.macroMode == self.MODE_BEGIN:
			if not getattr(self, 'title', ''):
				raise ValueError("Must specify a title using \\caption")

			options = self.attributes.get( 'options', {} ) or {}
			__traceback_info__ = options, self.attributes
			if 'creator' in options:
				self.creator = options['creator']

			images = self.getElementsByTagName( 'includegraphics' )
			if images:
				# Must leave the image in the dom so it can be found by the resourceDB
				self.image = images[0]

		return res

	@property
	def description(self):
		texts = []
		for child in self.allChildNodes:
			# Try to extract the text children, ignoring the caption and label, etc
			if child.nodeType == self.TEXT_NODE and (child.parentNode == self or child.parentNode.nodeName == 'par'):
				texts.append( unicode( child ) )

		return cfg_interfaces.IPlainTextContentFragment( cfg_interfaces.ILatexContentFragment( ''.join( texts ).strip() ) )


class ntislidevideoname(Command):
	unicode = u''

class ntislidevideo(LocalContentMixin, Float, plastexids.NTIIDMixin):
	"""
	This environment encapsulates ntiincludevideo objects so that we can tag them with a label and reference them elsewhere.
	"""
	args = '[ options:dict ]'

	# A Float subclass to get \caption handling
	class caption(Floats.Caption):
		counter = 'ntislidevideo'

	counter = "ntislidevideo"
	blockType=True
	forcePars=False
	_ntiid_cache_map_name = '_ntislidevideo_ntiid_map'
	_ntiid_allow_missing_title = False
	_ntiid_suffix = 'nsd.'
	_ntiid_title_attr_name = 'ref'
	_ntiid_type = 'NTISlideVideo'

	_creator = ''
	type = 'local'
	_title = ''
	show_video = False
	_thumbnail = None

	mimeType = 'application/vnd.nextthought.ntislidevideo'
	itemprop = 'presentation-card'

	def digest(self, tokens):
		res = super(ntislidevideo, self).digest(tokens)
		if self.macroMode == self.MODE_BEGIN:
			options = self.attributes.get( 'options', {} ) or {}
			__traceback_info__ = options, self.attributes
			if 'presentationonly' in options and options['presentationonly']:
				self.itemprop = 'presentation-none'
				self.style['display'] = 'none'
			if 'show-video' in options and options['show-video']:
				self.itemprop = 'presentation-video'


			video_els = self.getElementsByTagName( 'ntivideo' )
			if video_els:
				self._title = video_els[0].title
				self._creator = video_els[0].creator
				video_els[0].itemprop = 'presentation-none'

			video_els = self.getElementsByTagName( 'ntiincludevideo' )
			if video_els:
				multimedia = ntivideo()
				multimedia.title = self._title
				multimedia.creator = self._creator
				multimedia.itemprop = 'presentation-none'
				
				multimedia_source = ntivideo.ntivideosource()
				multimedia_source.service = video_els[0].attributes['service']
				multimedia_source.src = {}
				multimedia_source.src['other'] = video_els[0].attributes['video_id']
				multimedia_source.thumbnail = video_els[0].attributes['thumbnail']

				multimedia.append(multimedia_source)
				multimedia.num_sources +=1
				self.append(multimedia)

			# Populate our thumbnail attribute. This is probably not the best way...
			video_source_els = self.getElementsByTagName( 'ntivideosource' )
			for video_source_el in video_source_els:
				if video_source_el.thumbnail is not None:
					self._thumbnail = video_source_el.thumbnail

		return res

	@property
	def description(self):
		els = self.getElementsByTagName( 'ntivideo' )
		if(els):
			return els[0].description
		return cfg_interfaces.IPlainTextContentFragment( cfg_interfaces.ILatexContentFragment( '' ) )

	@readproperty
	def title(self):
		title = 'No Title'
		video_els = self.getElementsByTagName( 'ntivideo' )
		videoref_els = self.getElementsByTagName( 'ntivideoref' )
		if self._title:
			title = self._title
		elif video_els:
			title = video_els[0].title
		elif videoref_els:
			title = videoref_els[0].idref['label'].title
		return title

	@readproperty
	def creator(self):
		creator = 'Unknown'
		video_els = self.getElementsByTagName( 'ntivideo' )
		videoref_els = self.getElementsByTagName( 'ntivideoref' )
		if self._creator:
			creator = self._creator
		elif video_els:
			creator = video_els[0].creator
		elif videoref_els:
			creator = videoref_els[0].idref['label'].creator
		return creator

	@readproperty
	def video_ntiid(self):
		video_ntiid = None
		video_els = self.getElementsByTagName( 'ntivideo' )
		videoref_els = self.getElementsByTagName( 'ntivideoref' )
		if video_els:
			video_ntiid = video_els[0].ntiid
			if not hasattr(video_els[0], 'slidedeck'):
				video_els[0].slidedeck = self.slidedeck.idref['label'].ntiid
		elif videoref_els:
			video_ntiid = videoref_els[0].idref['label'].ntiid
			if not hasattr(videoref_els[0].idref['label'], 'slidedeck'):
				videoref_els[0].idref['label'].slidedeck = self.slidedeck.idref['label'].ntiid
		return video_ntiid

	@readproperty
	def thumbnail(self):
		thumbnail = None
		video_els = self.getElementsByTagName( 'ntivideo' )
		videoref_els = self.getElementsByTagName( 'ntivideoref' )
		if self._thumbnail:
			thumbnail = self._thumbnail
		elif video_els:
			video_source_els = video_els[0].getElementsByTagName( 'ntivideosource' )
			for video_source_el in video_source_els:
				if video_source_el.thumbnail is not None:
					thumbnail = video_source_el.thumbnail
		elif videoref_els:
			video_source_els = videoref_els[0].idref['label'].getElementsByTagName( 'ntivideosource' )
			for video_source_el in video_source_els:
				if video_source_el.thumbnail is not None:
					thumbnail = video_source_el.thumbnail
		return thumbnail


	@readproperty
	def media_sources(self):
		sources = self.getElementsByTagName('ntivideo')
		output = render_children(self.renderer, sources)
		return cfg_interfaces.HTMLContentFragment(''.join(output).strip())

class ntislidename(Command):
	unicode = u''

class ntislide(LocalContentMixin, Float, plastexids.NTIIDMixin):
	"""
	The ntislide environment represents a single slide from a "PowerPoint" style presentation. 

	\begin{ntislide}
	    \caption{title} or \ntislidetitle{title} [depreciated]
	    \includegraphics{imagepath} or \ntislideimage{imagepath} [depreciated]
	    \ntislidevideoref[start=time,stop=time]{video label}
	    \begin{ntislidetext}
	        Arbitrary text goes here
	    \end{ntislidetext}
	\end{ntislide}
	"""
	args = '[ options:dict ]'

	# A Float subclass to get \caption handling
	class caption(Floats.Caption):
		counter = 'ntislide'

	counter = "ntislide"
	blockType = True
	forcePars = False
	_ntiid_cache_map_name = '_ntislide_ntiid_map'
	_ntiid_allow_missing_title = True
	_ntiid_suffix = 'nsd.'
	_ntiid_title_attr_name = 'ref'
	_ntiid_type = 'NTISlide'

	def invoke(self, tex):
		res = super(ntislide, self).invoke(tex)
		if 'options' not in self.attributes or not self.attributes['options']:
			self.attributes['options'] = {}
		if 'presentationonly' not in self.attributes['options']:
			self.attributes['options']['presentationonly'] = False
		elif not self.attributes['options']['presentationonly']:
			pass
		else:
			self.style['display'] = 'none'
		return res

	def digest(self, tokens):
		super(ntislide, self).digest(tokens)
		if not hasattr(self, 'slidenumber'):
			self.slidenumber = self.ownerDocument.context.counters[self.counter].value
			
		images = self.getElementsByTagName( 'includegraphics' )
		if images:
			# Must leave the image in the dom so it can be found by the resourceDB
			self.slideimage = images[0]

	class ntislidetitle(Command):
		"""
		This method has been deprecated in favor of \caption and will be removed in
		the future.
		"""

		args = 'title'

		def digest(self, tokens):
			super(ntislide.ntislidetitle, self).digest(tokens)
			self.parentNode.title = self.attributes['title']

	class ntislidenumber(Command):
		args = 'number:int'

		def digest(self, tokens):
			super(ntislide.ntislidenumber, self).digest(tokens)
			self.parentNode.slidenumber = self.attributes['number']

	class ntislideimage(includegraphics):
		"""
		This method has been deprecated in favor of \includegraphics and will
		be removed in the future.
		"""

		def digest(self, tokens):
			super(ntislide.ntislideimage, self).digest(tokens)
			self.parentNode.slideimage = self

	class ntislidevideoref(Crossref.ref):
		args = '[ options:dict ] label:idref'

		def digest(self, tokens):
			super(ntislide.ntislidevideoref, self).digest(tokens)
			self.starttime = _timeconvert( self.attributes['options']['start'] )
			self.endtime = _timeconvert(self.attributes['options']['end'])
			self.parentNode.slidevideo = self

	class ntislidetext(LocalContentMixin, Environment):
		pass

def ProcessOptions( options, document ):
	document.context.newcounter('ntislidedeck')
	document.context.newcounter('ntislide')
	document.context.newcounter('ntislidevideo')
