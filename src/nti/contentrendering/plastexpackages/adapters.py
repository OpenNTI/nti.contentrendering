# -*- coding: utf-8 -*-
"""
adapters for externalizing plasTeX objects

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import six

from zope import interface

from zope.cachedescriptors.property import Lazy

from plasTeX.Renderers import render_children

from nti.contentrendering.interfaces import IJSONTransformer

from nti.externalization.interfaces import StandardExternalFields

from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import get_provider
from nti.ntiids.ntiids import get_specific
from nti.ntiids.ntiids import make_specific_safe


HREF = StandardExternalFields.HREF
ITEMS = StandardExternalFields.ITEMS
NTIID = StandardExternalFields.NTIID
MIMETYPE = StandardExternalFields.MIMETYPE

#: Course Overview Group NTIID Type
NTI_COURSE_OVERVIEW_GROUP = u'NTICourseOverviewGroup'

def _render_children(renderer, nodes, strip=True):
	if not isinstance(nodes, six.string_types):
		result = unicode(''.join(render_children(renderer, nodes)))
	else:
		result = nodes.decode("utf-8") if isinstance(nodes, bytes) else nodes
	return result.strip() if result and strip else result

@interface.implementer(IJSONTransformer)
class _CourseLessonJSONTransformer(object):

	def __init__(self, element):
		self.el = element

	@Lazy
	def ntiid(self):
		return self.el.ntiid

	@Lazy
	def _specific(self):
		return get_specific(self.ntiid)

	@Lazy
	def _provider(self):
		return get_provider(self.ntiid)

	def group_ntiid(self, idx):
		prov = self._provider
		spec = make_specific_safe(self._specific + (".%s" % idx))
		result = make_ntiid(base=self.ntiid, 
							provider=prov,
							specific=spec,
							nttype=NTI_COURSE_OVERVIEW_GROUP)
		return result

	def transform(self):
		output = {}
		output[ITEMS] = items = []
		output[NTIID] = self.el.ntiid
		output[MIMETYPE] = u"application/vnd.nextthought.ntilessonoverview"
		output['title'] = _render_children(self.el.renderer, self.el.title, False)
		group_els = self.el.getElementsByTagName('courseoverviewgroup')
		for idx, group_el in enumerate(group_els):
			trx = IJSONTransformer(group_el, None)
			if trx is not None:
				ntiid = self.group_ntiid(idx)
				items.append(trx.transform(ntiid))
		return output

@interface.implementer(IJSONTransformer)
class _CourseOverviewGroupJSONTransformer(object):

	def __init__(self, element):
		self.el = element

	def transform(self, ntiid=None):
		output = {}
		output[MIMETYPE] = self.el.mime_type
		if ntiid:
			output[NTIID] = ntiid
		output['title'] = _render_children(self.el.renderer, self.el.title, False)
		output['accentColor'] = _render_children(self.el.renderer,
												 self.el.title_background_color,
												 False)
		output[ITEMS] = items = []
		for child in self.el.childNodes:
			trx = IJSONTransformer(child, None)
			if trx is not None:
				items.append(trx.transform())
		return output

@interface.implementer(IJSONTransformer)
class _CourseOverviewSpacerJSONTransformer(object):

	def __init__(self, element):
		self.el = element

	def transform(self):
		output = {}
		output[MIMETYPE] = self.el.mime_type
		return output

@interface.implementer(IJSONTransformer)
class _DiscussionRefJSONTransformer(object):

	def __init__(self, element):
		self.el = element

	def transform(self):
		output = {}
		output[MIMETYPE] = self.el.discussion.targetMimeType
		output['icon'] = self.el.discussion.iconResource.image.url
		output['label'] = _render_children(self.el.discussion.renderer,
										   self.el.discussion.title)
		output[NTIID] = self.el.discussion.topic_ntiid
		output['title'] = _render_children(self.el.discussion.renderer,
										   self.el.discussion.subtitle)
		if self.el.discussion.autogenuri:
			output['id'] = self.el.discussion.autogenuri
		return output

@interface.implementer(IJSONTransformer)
class _NTIMediaRefJSONTransformer(object):

	def __init__(self, element):
		self.el = element

	def do_transform(self):
		output = {}
		output['label'] = _render_children(self.el.media.renderer, self.el.media.title)
		output[MIMETYPE] = self.el.media.mimeType
		output[NTIID] = self.el.media.ntiid
		output['visibility'] = self.el.visibility
		return output
	
	def transform(self):
		try:
			return self.do_transform()
		except Exception:
			logger.info("MediaRef %s, %s", self.el.__dict__, self.el.media.__dict__)
			raise

@interface.implementer(IJSONTransformer)
class _NTIAudioRefJSONTransformer(_NTIMediaRefJSONTransformer):
	pass

@interface.implementer(IJSONTransformer)
class _NTIVideoRefJSONTransformer(_NTIMediaRefJSONTransformer):

	def do_transform(self):
		output = super(_NTIVideoRefJSONTransformer, self).do_transform()
		output['poster'] = self.el.media.poster
		return output

@interface.implementer(IJSONTransformer)
class _RelatedWorkRefJSONTransformer(object):

	def __init__(self, element):
		self.el = element

	def transform(self):
		output = {}
		output['creator'] = _render_children(self.el.relatedwork.renderer,
											 self.el.creator)
		output['desc'] = _render_children(self.el.relatedwork.renderer,
										  self.el.description)
		output[HREF] = self.el.uri
		output[MIMETYPE] = self.el.mimeType
		output['targetMimeType'] = self.el.targetMimeType
		output['icon'] = self.el.relatedwork.iconResource.image.url
		output['label'] = _render_children(self.el.relatedwork.renderer,
										   self.el.title)
		output[NTIID] = self.el.ntiid
		output['target-NTIID'] = self.el.target_ntiid
		output['section'] = self.el.category
		output['visibility'] = self.el.visibility
		if self.el.attributes.get('nti-requirements') is not None:
			output['nti-requirements'] = self.el.attributes.get('nti-requirements')
		return output

@interface.implementer(IJSONTransformer)
class _TimelineJSONTransformer(object):

	def __init__(self, element):
		self.el = element

	def transform(self):
		output = {}
		output['desc'] = _render_children(self.el.renderer, self.el.description)
		output[HREF] = self.el.uri
		output[MIMETYPE] = self.el.mime_type
		output['icon'] = self.el.icon.image.url
		output['label'] = _render_children(self.el.renderer, self.el.title)
		output[NTIID] = self.el.ntiid
		output['suggested-inline'] = self.el.suggested_inline
		if self.el.suggested_height:
			output['suggested-height'] = self.el.suggested_height
		if self.el.suggested_width:
			output['suggested-width'] = self.el.suggested_width
		return output
