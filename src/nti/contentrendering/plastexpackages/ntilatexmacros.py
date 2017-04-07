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
import hashlib

from zope import interface

from zope.cachedescriptors.property import readproperty

from plasTeX import Base
from plasTeX import Command 
from plasTeX import Environment 
from plasTeX import TeXFragment

from plasTeX.Base import TextCommand

from plasTeX.Packages.hyperref import href as base_href
		
from nti.contentrendering import plastexids

from nti.contentrendering.plastexpackages._util import _OneText
from nti.contentrendering.plastexpackages._util import incoming_sources_as_plain_text

from nti.contentrendering.plastexpackages.graphicx import includegraphics

from nti.contentrendering.resources import interfaces as resource_interfaces

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

# sectioning 

from nti.contentrendering.plastexpackages.ntisectioning import fakesection
from nti.contentrendering.plastexpackages.ntisectioning import fakesubsection

fakesection = fakesection
fakesubsection = fakesubsection

from nti.contentrendering.plastexpackages.ntisectioning import paragraphtitle
from nti.contentrendering.plastexpackages.ntisectioning import subsubsectiontitle

fakeparagraph = paragraphtitle
fakesubsubsection = subsubsectiontitle

from nti.contentrendering.plastexpackages.ntisectioning import chaptertitlesuppressed
from nti.contentrendering.plastexpackages.ntisectioning import sectiontitlesuppressed

chaptertitlesuppressed = chaptertitlesuppressed
sectiontitlesuppressed = sectiontitlesuppressed

from nti.contentrendering.plastexpackages.ntisectioning import pageref

pageref = pageref

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

# refs

class simpleref(base_href):
	pass


###############################################################################
# The following block of commands concern media resource handling
###############################################################################

# legacy 

from nti.contentrendering.plastexpackages.ntimedia import ntiincludevideo
from nti.contentrendering.plastexpackages.ntimedia import ntiincludekalturavideo

ntiincludevideo = ntiincludevideo
ntiincludekalturavideo = ntiincludekalturavideo

# media resources

from nti.contentrendering.plastexpackages.ntimedia import DeclareMediaResource

DeclareMediaResource = DeclareMediaResource

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
from nti.contentrendering.plastexpackages.ntimedia import ntilocalvideo
from nti.contentrendering.plastexpackages.ntimedia import ntilocalvideoname

ntivideo = ntivideo
ntivideoref = ntivideoref
ntivideoname = ntivideoname
ntilocalvideo = ntilocalvideo
ntilocalvideoname = ntilocalvideoname

# include raphics

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

# Sequence

from nti.contentrendering.plastexpackages.ntisequence import ntisequence
from nti.contentrendering.plastexpackages.ntisequence import ntisequenceref
from nti.contentrendering.plastexpackages.ntisequence import ntisequenceitem

ntisequence = ntisequence
ntisequenceref = ntisequenceref
ntisequenceitem = ntisequenceitem

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

# Relatedwork

from nti.contentrendering.plastexpackages.ntirelatedwork import relatedwork
from nti.contentrendering.plastexpackages.ntirelatedwork import relatedworkref
from nti.contentrendering.plastexpackages.ntirelatedwork import relatedworkname
from nti.contentrendering.plastexpackages.ntirelatedwork import relatedworkrefname

relatedwork = relatedwork
relatedworkref = relatedworkref
relatedworkname = relatedworkname
relatedworkrefname = relatedworkrefname

# Discussions

from nti.contentrendering.plastexpackages.ntidiscussion import ntidiscussion
from nti.contentrendering.plastexpackages.ntidiscussion import ntidiscussionref
from nti.contentrendering.plastexpackages.ntidiscussion import ntidiscussionname

ntidiscussion = ntidiscussion
ntidiscussionref = ntidiscussionref
ntidiscussionname = ntidiscussionname

# Refs

from nti.contentrendering.plastexpackages.ntihyperref import ntihref
from nti.contentrendering.plastexpackages.ntihyperref import ntiidref
from nti.contentrendering.plastexpackages.ntihyperref import simpleref
from nti.contentrendering.plastexpackages.ntihyperref import ntifancyhref
from nti.contentrendering.plastexpackages.ntihyperref import ntiimagehref

ntihref = ntihref
ntiidref = ntiidref
simpleref = simpleref
ntifancyhref = ntifancyhref
ntiimagehref = ntiimagehref

# side bars

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
