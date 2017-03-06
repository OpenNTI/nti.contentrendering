#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define NTI Latex Macros

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import codecs
import hashlib

import simplejson as json

from zope import interface

from zope.cachedescriptors.property import readproperty

from plasTeX import Base
from plasTeX import Command 
from plasTeX import Environment 
from plasTeX import TeXFragment

from plasTeX.Base import Crossref
from plasTeX.Base import TextCommand

from plasTeX.Packages.hyperref import href as base_href
		
from nti.contentrendering import plastexids
from nti.contentrendering import interfaces as crd_interfaces

from nti.contentrendering.plastexpackages._util import _OneText
from nti.contentrendering.plastexpackages._util import LocalContentMixin
from nti.contentrendering.plastexpackages._util import incoming_sources_as_plain_text

from nti.contentrendering.plastexpackages.graphicx import includegraphics

from nti.contentrendering.resources import interfaces as resource_interfaces

from nti.ntiids import ntiids

# Monkey patching time
# SAJ: The following are set to render properly nested HTML.
Base.hrule.blockType = True
Base.parbox.blockType = True
Base.figure.forcePars = False
Base.minipage.blockType = True
Base.centerline.blockType = True

_incoming_sources_as_plain_text = incoming_sources_as_plain_text

# util classes

from nti.contentrendering.plastexpackages._util import Ignored
_Ignored = Ignored

# eurosym

from nti.contentrendering.plastexpackages.eurosym import eur
from nti.contentrendering.plastexpackages.eurosym import euro

eur = eur
euro = euro

# SAJ: Sectioning commands for custom rendering treatment
class chaptertitlesuppressed( Base.chapter ):
	pass

class sectiontitlesuppressed( Base.section ):
	pass

# TODO: do pagerefs even make sense in our dom?
# Try to find an intelligent page name for the reference
# so we don't have to render the link text as '3'
class pageref(Crossref.pageref):
	# we would hope to generate the pagename attribute in
	# the invoke method but since it is dependent on the page
	# splits used at render time we define a function to be called
	# from the page template
	def getPageNameForRef(self):
		# Look up the dom tree until we find something
		# that would create a file
		fileNode = self.idref['label']
		while not getattr(fileNode, 'title', None) and getattr(fileNode, 'parentNode', None):
			fileNode = fileNode.parentNode

		if hasattr(fileNode, 'title'):
			return getattr(fileNode.title, 'textContent', fileNode.title)

		return None

# lists

from nti.contentrendering.plastexpackages.ntilists import ntilist
from nti.contentrendering.plastexpackages.ntilists import ntiitemize
from nti.contentrendering.plastexpackages.ntilists import ntinavlist
from nti.contentrendering.plastexpackages.ntilists import ntitrivlist
from nti.contentrendering.plastexpackages.ntilists import ntienumerate

ntilist = ntilist
ntiitemize = ntiitemize
ntinavlist = ntinavlist
ntitrivlist = ntitrivlist
ntienumerate = ntienumerate

# external graphics

from nti.contentrendering.plastexpackages.ntiexternalgraphics import ntiexternalgraphics

ntiexternalgraphics = ntiexternalgraphics

###############################################################################
# The following block of commands concern general resource handling
###############################################################################

@interface.implementer(resource_interfaces.IRepresentableContentUnit,	
					   resource_interfaces.IRepresentationPreferences)
class DeclareMediaResource( Base.Command ):
	"""
	This command is extremely experimental and should be avoided for now.
	"""

	args = 'src:str label:id'
	resourceTypes = ( 'jsonp', )

	def invoke( self, tex ):
		result = super(DeclareMediaResource, self).invoke( tex )
		self.attributes['src'] = os.path.join(
			self.ownerDocument.userdata.getPath('working-dir'), self.attributes['src'])
		return result

###############################################################################
# The following block of commands concern media resource handling
###############################################################################


class ntiincludevideo(_OneText):
	args = '[options:dict] video_url:url'

	def invoke( self, tex ):
		result = super(ntiincludevideo, self).invoke( tex )
		options = self.attributes.get('options', None) or {}

		# Set the id of the element
		source = self.source
		_id = hashlib.md5(source.strip().encode('utf-8')).hexdigest()
		setattr( self, "@id", _id )
		setattr( self, "@hasgenid", True )

		# change youtube view links to embed
		if hasattr(self.attributes['video_url'], 'source'):
			self.attributes['video_url'] = self.attributes['video_url'].source.replace(' ', '') \
										.replace('\\&', '&') \
										.replace('\\_', '_') \
										.replace('\\%', '%') \
										.replace(u'\u2013', u'--') \
										.replace(u'\u2014', u'---')

		self.attributes['video_url'] = self.attributes['video_url'].replace( "/watch?v=", '/embed/' )
		self.width = options.get('width') or u'640px'
		self.height = options.get('height') or unicode((int(self.width.replace('px',''))/640) * 360)+'px'
		_t = self.attributes['video_url'].split('/')
		if 'youtube' in _t[2]:
			# TODO: See https://github.com/coleifer/micawber
			# for handling this; our poster and thumbnail are just
			# guesses.
			self.attributes['service'] = 'youtube'
			self.attributes['video_id'] = _t[len(_t)-1].split('?')[0]
			self.attributes['poster'] = '//img.youtube.com/vi/' + self.attributes['video_id'] + '/0.jpg'
			self.attributes['thumbnail'] = '//img.youtube.com/vi/' + self.attributes['video_id'] + '/1.jpg'
		return result

# This command is a HACK to work around issues in the web app and pad with in-line
# Kaltura videos in the content.
class ntiincludekalturavideo(Command):
	args = '[ options:dict ] video_id:str'

	def digest(self, tokens):
		res = super(ntiincludekalturavideo, self).digest(tokens)

		options = self.attributes.get( 'options', {} ) or {}
		__traceback_info__ = options, self.attributes

		video = self.attributes.get( 'video_id' ).split(':')

		partner_id = video[0]
		subpartner_id = video[0] + u'00'
		uiconf_id = u'16401392'
		player_id = u'kaltura_player_' + video[1]
		entry_id = video[1]
		self.video_source = "https://cdnapisec.kaltura.com/p/%s/sp/%s/embedIframeJs/uiconf_id/%s/partner_id/%s?iframeembed=true&playerId=%s&entry_id=%s&flashvars[streamerType]=auto" % \
							(partner_id, subpartner_id, uiconf_id, partner_id, player_id, entry_id)
		self.width = u'640'
		self.height = u'390'
		return res

# media

from nti.contentrendering.plastexpackages.ntimedia import ntimedia
from nti.contentrendering.plastexpackages.ntimedia import ntimediaref
from nti.contentrendering.plastexpackages.ntimedia import mediatranscript

ntimedia = ntimedia
ntimediaref = ntimediaref
mediatranscript = mediatranscript

# audio

from nti.contentrendering.plastexpackages.ntimedia import ntiaudio
from nti.contentrendering.plastexpackages.ntimedia import ntiaudioref
from nti.contentrendering.plastexpackages.ntimedia import ntiaudioname

ntiaudio = ntiaudio
ntiaudioref = ntiaudioref
ntiaudioname = ntiaudioname

# video

from nti.contentrendering.plastexpackages.ntimedia import ntivideo
from nti.contentrendering.plastexpackages.ntimedia import ntivideoref
from nti.contentrendering.plastexpackages.ntimedia import ntivideoname

ntivideo = ntivideo
ntivideoref = ntivideoref
ntivideoname = ntivideoname

class ntilocalvideoname(Command):
	unicode = ''

class ntilocalvideo( Base.Environment ):
	args = '[ options:dict ]'
	counter = "ntilocalvideo"
	blockType=True

	def invoke(self, tex):
		_t = super(ntilocalvideo, self).invoke(tex)
		if 'options' not in self.attributes or not self.attributes['options']:
			self.attributes['options'] = {}
		return _t

	def digest(self, tex):
		super(ntilocalvideo, self).digest(tex)
		video = self.getElementsByTagName( 'ntiincludelocalvideo' )[0]
		self.src = {}
		self.src['mp4'] = video.attributes['src'] + u'.mp4'
		self.src['webm'] = video.attributes['src'] + u'.webm'
		self.title = video.attributes['title']
		self.poster = video.attributes['poster']
		if 'width' in video.attributes['options']:
			self.width = video.attributes['options']['width']
		if 'height' in video.attributes['options']:
			self.height = video.attributes['options']['height']
		self.id = video.id

	class ntiincludelocalvideo( Base.Command ):
		args = '[ options:dict ] src title poster'

class ntiincludeannotationgraphics(includegraphics):

	@readproperty
	def caption(self):
		if self.title:
			title = TeXFragment()
			title.parentNode = self
			title.ownerDocument = self.ownerDocument
			title.appendChild(self.title)
			return title

class ntiincludenoannotationgraphics(includegraphics):

	@readproperty
	def caption(self):
		if self.title:
			title = TeXFragment()
			title.parentNode = self
			title.ownerDocument = self.ownerDocument
			title.appendChild(self.title)
			return title

class ntipagenum(_OneText):
	pass

class ntiglossaryterm(Base.Command):
	args = 'term self'

class ntihref(base_href):
	args = '[options:dict] url:url self'

	def invoke(self, tex):
		_t = super(ntihref, self).invoke(tex)
		if 'options' not in self.attributes or not self.attributes['options']:
			self.attributes['options'] = {}
		options = self.attributes.get('options')
		self.attributes['nti-requirements'] = u''
		requirements = options.get('nti-requirements', u'').split()
		for requirement in requirements:
			if requirement == u'flash':
				requirement = u'mime-type:application/x-shockwave-flash'
			self.attributes['nti-requirements'] = ' '.join([self.attributes['nti-requirements'], requirement])
		self.attributes['nti-requirements'] = self.attributes['nti-requirements'].strip()
		if self.attributes['nti-requirements'] == u'':
			self.attributes['nti-requirements'] = None

		return _t

class ntiimagehref(Base.Command):
	args = 'img url'

class ntifancyhref(Base.Command):
	args = 'url:str:source self class'

class textsuperscript(Base.Command):
	args = 'self'

class textsubscript(Base.Command):
	args = 'self'

# Custom text treatments
class modified(TextCommand):
	pass

# The following are LaTeX 2e escape commands

class backslash(Base.Command):
	unicode = u'\u005C'

# The following 'text' symbols are 'Predefined' LaTeX 2e commands

class textcopyright(Base.Command):
	unicode = u'\u00A9'

class textgreater(Base.Command):
	unicode = u'\u003E'

class textless(Base.Command):
	unicode = u'\u003C'

class textregistered(Base.Command):
	unicode = u'\u00AE'

class texttrademark(Base.Command):
	unicode = u'\u2122'

# The following 'text' symbols are from the textcomp package.

class textapprox(Base.Command):
	unicode = u'\u2248'

class textdegree(Base.Command):
	unicode = u'\u00B0'

class textdiv(Base.Command):
	unicode = u'\u00F7'

class textminus(Base.Command):
	unicode = u'\u2212'

class textpm(Base.Command):
	unicode = u'\u00B1'

class textrightarrow(Base.Command):
	unicode = u'\u2192'

class textsmiley(Base.Command):
	unicode = u'\u263A'

class texttimes(Base.Command):
	unicode = u'\u00D7'

# The following 'text' commands are custom and specific to NTI
class textangle(Base.Command):
	unicode = u'\u2220'

class textcong(Base.Command):
	unicode = u'\u2245'

class textge(Base.Command):
	unicode = u'\u2265'

class textle(Base.Command):
	unicode = u'\u2264'

class textneq(Base.Command):
	unicode = u'\u2260'

class textparallel(Base.Command):
	unicode = u'\u2016'

class textsurd(Base.Command):
	unicode = u'\u221A'

class textperp(Base.Command):
	unicode = u'\u22A5'

class textinfty(Base.Command):
	unicode = u'\u221E'

class textprime(Base.Command):
	unicode = u'\u2032'

class textsim(Base.Command):
	unicode = u'\u007E'

class textsquare(Base.Command):
	unicode = u'\u25A1'

class texttriangle(Base.Command):
	unicode = u'\u25B3'

class textdoublehyphen(Command):
	unicode = u'\u002D' + u'\u002D'

class textcelsius(Base.Command):
	unicode = u'\u2103'

class textfahrenheit(Base.Command):
	unicode = u'\u2109'

# Currency symbols
class yen(Base.Command):
	unicode = u'\xA5'

class textcent(Base.Command):
	unicode = u'\xA2'

# Handle pdfLatex primatives
class pdfminorversion(Command):
	args = 'version:int'

# Handle latex commands that make no sense in a web layout
class flushbottom(Command):
	args = ''

class nobreak(Base.Command):
	args = 'self'

class vfrac(Base.Command):
	args = 'nom denom'


# common

from nti.contentrendering.plastexpackages.nticommon import ntidescription
ntidescription = ntidescription

# Media collection

from nti.contentrendering.plastexpackages.ntimedia import ntivideoroll
from nti.contentrendering.plastexpackages.ntimedia import ntivideorollname
from nti.contentrendering.plastexpackages.ntimedia import ntimediacollection

ntivideoroll = ntivideoroll
ntivideorollname = ntivideorollname

# Image collections
class ntiimagecollectionname(Base.Command):
	pass

class ntiimagecollection(ntimediacollection):
	counter = "ntiimagecollection"
	_ntiid_cache_map_name = '_ntiimagecollection_ntiid_map'
	_ntiid_allow_missing_title = True
	_ntiid_suffix = 'ntiimagecollection.'
	_ntiid_title_attr_name = 'ref'
	_ntiid_type = 'NTIIC'

class ntipreviouspage(Base.Command):
	pass

# Cards

from nti.contentrendering.plastexpackages.nticard import nticard
from nti.contentrendering.plastexpackages.nticard import nticardname

nticard = nticard
nticardname = nticardname


###############################################################################
# The following block of commands concern representing related readings
###############################################################################

class relatedworkname(Base.Command):
	pass

@interface.implementer(crd_interfaces.IEmbeddedContainer)
class relatedwork(LocalContentMixin, Base.Environment, plastexids.NTIIDMixin):
	args = '[ options:dict ]'

	# Only classes with counters can be labeled, and \label sets the
	# id property, which in turn is used as part of the NTIID (when no NTIID is set explicitly)
	counter = 'relatedwork'
	blockType = True
	_ntiid_cache_map_name = '_relatedwork_ntiid_map'
	_ntiid_allow_missing_title = False
	_ntiid_suffix = 'relatedwork.'
	_ntiid_title_attr_name = 'ref' # Use our counter to generate IDs if no ID is given
	_ntiid_type = 'RelatedWork'

	#: From IEmbeddedContainer
	mimeType = "application/vnd.nextthought.relatedwork"
	targetMimeType = "application/vnd.nextthought.content"
	icon = None
	iconResource = None
	target_ntiid = None
	_description = None
	_uri = u''

	class worktitle(Base.Command):
		args = 'title'

		def digest(self, tokens):
			tok = super(relatedwork.worktitle,self).digest(tokens)
			self.parentNode.title = self.attributes['title']
			return tok

	class workcreator(Base.Command):
		args = 'creator'

		def digest(self, tokens):
			tok = super(relatedwork.workcreator,self).digest(tokens)
			self.parentNode.creator = self.attributes['creator']
			return tok

	class worksource(Base.Command):
		args = 'uri:url'

		tokens = ( 	( ' ', '' ), ( '\\&', '&' ), ( '\\_', '_' ), ( '\\%', '%' ), 
					(u'\u2013', u'--'), (u'\u2014', u'---') )
		
		def replacer(self, source):
			for a, b in self.tokens:
				source = source.replace(a, b)
			return source

		def digest(self, tokens):
			tok = super(relatedwork.worksource,self).digest(tokens)
			self.attributes['uri'] = self.replacer(self.attributes['uri'].source)
			return tok

	class worksourceref(Base.Crossref.ref):
		args = 'target:idref'

	def digest(self, tokens):
		tok = super(relatedwork,self).digest(tokens)

		options = self.attributes.get( 'options', {} ) or {}
		self.visibility = 'everyone'
		if 'visibility' in options.keys():
			self.visibility = options['visibility']

		self.target_ntiid = None
		self.targetMimeType = None

		icons = self.getElementsByTagName('includegraphics')
		if icons:
			self.iconResource = icons[0]

		return tok

	@readproperty
	def description(self):
		if self._description is None:
			self._description = TeXFragment()
			self._description.parentNode = self
			self._description.ownerDocument = self.ownerDocument
			node_types = ['label', 'worktitle', 'workcreator', 'worksource', 'worksourceref', 'includegraphics']
			for child in self.childNodes:
				if child.nodeName not in node_types:
					self._description.appendChild(child)
		return self._description

	@readproperty
	def uri(self):
		if not self._uri:
			worksources = self.getElementsByTagName('worksource')
			if worksources:
				self._uri = worksources[0].attributes.get('uri')
			else:
				worksources = self.getElementsByTagName('worksourceref')
				if worksources:
					if hasattr(worksources[0].idref['target'], 'ntiid'):
						self._uri = worksources[0].idref['target'].ntiid
		return self._uri

	def gen_target_ntiid(self):
		from nti.ntiids.ntiids import is_valid_ntiid_string

		uri = self.uri
		if is_valid_ntiid_string( uri ):
			self.target_ntiid = uri
			self.targetMimeType = 'application/vnd.nextthought.content'
			ntiid_specific = ntiids.get_specific( uri )
			self.icon = '/'.join([u'..', ntiid_specific.split('.')[0], 'icons', 'chapters', 'generic_book.png'])

		else:
			from nti.ntiids.ntiids import make_ntiid, TYPE_UUID
			from hashlib import md5
			# TODO: Hmm, what to use as the provider? Look for a hostname in the
			# URL?
			self.target_ntiid = make_ntiid( provider='NTI',
											nttype=TYPE_UUID,
											specific=md5(uri).hexdigest() )
			self.targetMimeType = 'application/vnd.nextthought.externallink'

class relatedworkrefname(Base.Command):
	pass

@interface.implementer(crd_interfaces.IEmbeddedContainer)
class relatedworkref(Base.Crossref.ref, plastexids.NTIIDMixin):
	args = '[ options:dict ] label:idref uri:url desc < NTIID:str >'

	counter = 'relatedworkref'
	blockType = True
	_ntiid_cache_map_name = '_relatedworkref_ntiid_map'
	_ntiid_allow_missing_title = False
	_ntiid_suffix = 'relatedworkref.'
	_ntiid_title_attr_name = 'label'
	_ntiid_type = 'RelatedWorkRef'

	#: From IEmbeddedContainer
	mimeType = "application/vnd.nextthought.relatedworkref"
	_targetMimeType = None
	_target_ntiid = None

	def digest(self, tokens):
		tok = super(relatedworkref, self).digest(tokens)

		self._options = self.attributes.get( 'options', {} ) or {}
		self.attributes['nti-requirements'] = u''
		requirements = self._options.get('nti-requirements', u'').split()
		for requirement in requirements:
			if requirement == u'flash':
				requirement = u'mime-type:application/x-shockwave-flash'
			self.attributes['nti-requirements'] = ' '.join([self.attributes['nti-requirements'], requirement])
		self.attributes['nti-requirements'] = self.attributes['nti-requirements'].strip()
		if self.attributes['nti-requirements'] == u'':
			self.attributes['nti-requirements'] = None
		self.label = self.attributes.get('label')

		self._uri = self.attributes['uri']
		if hasattr(self._uri, 'source'):
			self._uri = self._uri.source.replace(' ', '') \
										.replace('\\&', '&') \
										.replace('\\_', '_') \
										.replace('\\%', '%') \
										.replace(u'\u2013', u'--') \
										.replace(u'\u2014', u'---')
		self.relatedwork = self.idref['label']
		self._creator = None
		self._description = None
		self._title = None

		# Remove the empty NTIID key so auto NTIID generation works

		# SAJ: It is a hack to have this code here. The code in
		# contentrendering.platexids should account for the possibility that the
		# value of the 'NTIID' key could be 'None', however I have not evaluated what
		# undesired side affects might come from changing the code in
		# contentrendering.plastexids.
		if 'NTIID' in self.attributes and self.attributes['NTIID'] is None:
			del self.attributes['NTIID']

		self._target_ntiid = None

		return tok

	@readproperty
	def category(self):
		return self._options.get('category') or u'required'

	@readproperty
	def creator(self):
		if self._creator is None:
			return self.relatedwork.creator
		return self._creator

	@readproperty
	def description(self):
		description = self.attributes.get('desc')
		if len(description.childNodes) == 0:
			return self.relatedwork.description
		return description

	@readproperty
	def icon(self):
		if self.relatedwork.iconResource is not None:
			return self.relatedwork.iconResource.image.url
		elif self.relatedwork.icon is not None:
			return self.relatedwork.icon
		else:
			return ''

	@readproperty
	def target_ntiid(self):
		if self._target_ntiid is None:
			self.gen_target_ntiid()
		return self._target_ntiid

	@readproperty
	def targetMimeType(self):
		if self._targetMimeType is None:
			self.gen_target_ntiid()
		return self._targetMimeType

	@readproperty
	def title(self):
		if self._title is None:
			return self.relatedwork.title
		return self._title

	@readproperty
	def uri(self):
		if self._uri == '' or self._uri is None:
			return self.relatedwork.uri
		return self._uri

	@readproperty
	def visibility(self):
		visibility = self._options.get('visibility')
		if visibility == '' or visibility is None:
			return self.relatedwork.visibility
		return visibility

	def gen_target_ntiid(self):
		from nti.ntiids.ntiids import is_valid_ntiid_string

		uri = self.uri
		if is_valid_ntiid_string( uri ):
			self._target_ntiid = uri
			self._targetMimeType = 'application/vnd.nextthought.content'
		else:
			from nti.ntiids.ntiids import make_ntiid, TYPE_UUID
			from hashlib import md5
			# TODO: Hmm, what to use as the provider? Look for a hostname in the
			# URL?
			self._target_ntiid = make_ntiid( provider='NTI',
											nttype=TYPE_UUID,
											specific=md5(uri).hexdigest() )
			self._targetMimeType = 'application/vnd.nextthought.externallink'

###############################################################################
# The following block of commands concern representing forum discussions.
###############################################################################

class ntidiscussionname(Base.Command):
	pass

class ntidiscussionref(Base.Crossref.ref):

	@readproperty
	def discussion(self):
		return self.idref['label']

class ntidiscussion(Base.Environment):
	args = '[ options:dict ] '

	# Only classes with counters can be labeled, and \label sets the
	# id property, which in turn is used as part of the NTIID (when no NTIID is set explicitly)
	counter = 'ntidiscussion'
	blockType = True

	targetMimeType = "application/vnd.nextthought.discussion"
	iconResource = None
	title = ''
	subtitle = ''
	topic_ntiid = ''
	autogenuri = ''

	class discussiontitle(Base.Command):
		args = 'title'

		def digest(self, tokens):
			tok = super(ntidiscussion.discussiontitle,self).digest(tokens)
			self.parentNode.title = self.attributes['title']
			return tok

	class discussionsubtitle(Base.Command):
		args = 'subtitle'

		def digest(self, tokens):
			tok = super(ntidiscussion.discussionsubtitle,self).digest(tokens)
			self.parentNode.subtitle = self.attributes['subtitle']
			return tok

	class discussionuri(Base.Command):
		args = 'uri:url'

		to_replace = ( (' ', '' ), ('\\&', '&' ), ('\\_', '_' ), ( '\\%', '%' ),
					   (u'\u2013', u'--'), (u'\u2014', u'---') )
		
		COURSE_BUNDLE = r'nti-course-bundle://'

		def replacer(self, source):
			for a, b in self.to_replace:
				source = source.replace(a, b)
			return source

		def digest(self, tokens):
			tok = super(ntidiscussion.discussionuri,self).digest(tokens)
			self.parentNode.autogenuri = self.replacer(self.attributes['uri'].source)
			
			# discussion_path
			course_bundle_path = self.ownerDocument.userdata['course_bundle_path']
			discussion_path = self.parentNode.autogenuri.split(self.COURSE_BUNDLE)[1]
			discussion_path = os.path.join(course_bundle_path, discussion_path)
			
			# read discussion
			if os.path.exists(discussion_path):
				with codecs.open(discussion_path, 'rb', 'utf-8') as fp:
					discussion = json.load(fp)
			else:
				discussion = None
				logger.warning( 'Unable to find discussion definition at %s',
								discussion_path)
			if discussion is not None:
				if 'label' in discussion:
					self.parentNode.title = discussion['label']
				if 'title' in discussion:
					self.parentNode.subtitle = discussion['title']
			return tok

	class topicntiid(Base.Command):
		args = 'ntiid:str'

		def digest(self, tokens):
			tok = super(ntidiscussion.topicntiid,self).digest(tokens)
			self.parentNode.topic_ntiid = self.attributes['ntiid']
			return tok

	def digest(self, tokens):
		tok = super(ntidiscussion,self).digest(tokens)

		icons = self.getElementsByTagName('includegraphics')
		if icons:
			self.iconResource = icons[0]
		return tok

class ntisequenceitem(LocalContentMixin, Base.Environment):
	args = '[options:dict]'

	def invoke(self, tex):
		res = super(ntisequenceitem, self).invoke(tex)
		if 'options' not in self.attributes or not self.attributes['options']:
			self.attributes['options'] = {}
		return res

	def digest(self, tokens):
		tok = super(ntisequenceitem, self).digest(tokens)
		if self.macroMode != Base.Environment.MODE_END:
			options = self.attributes.get('options', {}) or {}
			__traceback_info__ = options, self.attributes
			for k, v in options.items():
				setattr(self, k, v)
		return tok

class ntisequence(LocalContentMixin, Base.List):
	args = '[options:dict]'

	def invoke(self, tex):
		res = super(ntisequence, self).invoke(tex)
		if 'options' not in self.attributes or not self.attributes['options']:
			self.attributes['options'] = {}
		return res

	def digest(self, tokens):
		tok = super(ntisequence, self).digest(tokens)
		if self.macroMode != Base.Environment.MODE_END:
			_items = self.getElementsByTagName('ntisequenceitem')
			assert len(_items) >= 1

			options = self.attributes.get('options', {}) or {}
			__traceback_info__ = options, self.attributes
			for k, v in options.items():
				setattr(self, k, v)
		return tok

class ntisequenceref(Base.Crossref.ref):
	args = '[options:dict] label:idref'


class ntidirectionsblock(Base.Command):
	args = 'directions example lang_code:str:source'
	blockType = True

# The sidebar environment is to be the base class for other side types such as those from AoPS.
class sidebarname(Command):
	unicode = ''

class sidebar(Environment, plastexids.NTIIDMixin):
	args = 'title'
	blockType = True

	counter = 'sidebar'
	_ntiid_cache_map_name = '_sidebar_ntiid_map'
	_ntiid_allow_missing_title = True
	_ntiid_suffix = 'sidebar.'
	_ntiid_title_attr_name = 'title'
	_ntiid_type = 'HTML:NTISidebar'
	embedded_doc_cross_ref_url = property(plastexids._embedded_node_cross_ref_url)

class flatsidebar(sidebar):
	pass

class audiosidebar(sidebar):
	args = 'audioref'

class ntigraphicsidebar(sidebar):
	args = 'title graphic_class:str:source'

class ntiidref(Base.Crossref.ref):
	"""
	Used for producing a cross-document link, like a normal
	ref, but output as an NTIID.
	"""
	macroName = 'ntiidref'

@interface.implementer(resource_interfaces.IRepresentableContentUnit,
		       resource_interfaces.IRepresentationPreferences)
class ntifileview(Command, plastexids.NTIIDMixin):
	args = '[options:dict] src:str:source self class'
	resourceTypes = ( 'html_wrapped', )

	counter = 'fileview'
	_ntiid_cache_map_name = '_fileview_ntiid_map'
	_ntiid_allow_missing_title = True
	_ntiid_suffix = 'fileview.'
	_ntiid_title_attr_name = 'src'
	_ntiid_type = 'HTML:FileView'

	def invoke( self, tex ):
		result = super(ntifileview, self).invoke( tex )
		self.attributes['src'] = os.path.join(
			self.ownerDocument.userdata.getPath('working-dir'), self.attributes['src'])
		self.attributes['presentation'] = 'popup'
		return result

class embedwidgetname(Command):
	pass

class ntiembedwidget(Command, plastexids.NTIIDMixin):
	args = '[ options:dict ] url:str:source <splash:str:source>'
	blockType = True

	counter = 'embedwidget'
	_ntiid_type = 'EmbedWidget'
	_ntiid_suffix = 'embedwidget.'
	_ntiid_cache_map_name = '_embedwidget_ntiid_map'

	itemprop = "presentation-embedwidget"
	mimeType = "application/vnd.nextthought.content.embeded.widget"
	
	to_replace = ( (' ', '' ), ('\\&', '&' ), ('\\_', '_' ), ( '\\%', '%' ),
				 (u'\u2013', u'--'), (u'\u2014', u'---') )
		
	def replacer(self, source):
		for a, b in self.to_replace:
			source = source.replace(a, b)
		return source

	def digest(self, tokens):
		res = super(ntiembedwidget, self).digest(tokens)
		options = self.attributes.get( 'options', {} ) or {}
		__traceback_info__ = options, self.attributes

		# process the parsed URI to workaround extra spaces added by the parcer
		self.attributes['url'] = self.replacer(self.attributes['url'])

		itemprop = options.get('show-card')
		if itemprop is not None:
			self.itemprop = 'presentation-card'

		defer = options.get('defer')
		if defer is not None:
			self.attributes['defer'] = defer

		height = options.get('height')
		if height is not None:
			self.attributes['height'] = height

		no_sandboxing = options.get('no-sandboxing')
		if no_sandboxing is not None:
			self.attributes['no-sandboxing'] = self.attributes['no-sandboxing'] = no_sandboxing

		uid = options.get('uid')
		if uid is not None:
			self.attributes['uid'] = uid
		else:
			self.attributes['uid'] = u'widget' + hashlib.md5(self.attributes['url']+self.ntiid).hexdigest()

		uidname = options.get('uid-name') or options.get('uidname') #uidname for legacy
		if uidname is not None:
			self.attributes['uidname'] = self.attributes['uid-name'] = uidname
		return res


def ProcessOptions(options, document):
	document.context.newcounter('nticard')
	document.context.newcounter('sidebar')
	document.context.newcounter('fileview')
	document.context.newcounter('ntiaudio')
	document.context.newcounter('ntivideo')
	document.context.newcounter('embedwidget')
	document.context.newcounter('relatedwork')
	document.context.newcounter('ntivideoroll')
	document.context.newcounter('ntilocalvideo')
	document.context.newcounter('ntidiscussion')
	document.context.newcounter('ntiimagecollection')
	document.context.newcounter('relatedworkref', initial=-1)

from plasTeX.interfaces import IOptionAwarePythonPackage
interface.moduleProvides(IOptionAwarePythonPackage)
