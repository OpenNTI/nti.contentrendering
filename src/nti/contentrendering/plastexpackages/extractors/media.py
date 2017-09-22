#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import simplejson as json
from collections import namedtuple
from collections import defaultdict
from collections import OrderedDict

from zope import component
from zope import interface

from plasTeX.Base.LaTeX import Document as LaTexDocument

from ordered_set import OrderedSet

from nti.contentrendering.plastexpackages.ntimedia import ntimedia

from ._utils import _render_children

from ...interfaces import IRenderedBook
from ...interfaces import INTIAudioExtractor
from ...interfaces import INTIVideoExtractor

_Reference = namedtuple('Reference', 'media containers')

@component.adapter(IRenderedBook)
class _NTIMediaExtractor(object):

	ntimedia = u'ntimedia'
	ntimediaref = u'ntimediaref'
	index_file = u'media_index.json'
	media_mimeType = u'application/vnd.nextthought.ntimedia'
	index_mimeType = u'application/vnd.nextthought.mediaindex'

	def __init__(self, book=None):
		pass

	def transform(self, book, savetoc=True, outpath=None):
		outpath = outpath or book.contentLocation
		outpath = os.path.expanduser(outpath)

		dom = book.toc.dom
		media_els = book.document.getElementsByTagName(self.ntimedia)
		reference_els = book.document.getElementsByTagName(self.ntimediaref)
		if not (reference_els or media_els):
			return

		# cache topics
		topic_map = self._get_topic_map(dom)
		references = self._process_references(dom, reference_els, topic_map)
		self._process_media_els(dom, media_els, references, topic_map, outpath)
		if savetoc:
			book.toc.save()

	def _get_topic_map(self, dom):
		result = {}
		for topic_el in dom.getElementsByTagName('topic'):
			ntiid = topic_el.getAttribute('ntiid')
			if ntiid:
				result[ntiid] = topic_el
		return result

	def _find_toc_media(self, topic_map):

		def  _add_2_od(od, key, value):
			s = od.get(key)
			if s is None:
				s = od[key] = OrderedSet()
			s.add(value)

		result = OrderedDict()
		inverted = OrderedDict()
		for topic_ntiid, topic_el in topic_map.items():
			for obj in topic_el.getElementsByTagName('object'):
				if obj.getAttribute('mimeType') != self.media_mimeType:
					continue
				ntiid = obj.getAttribute('ntiid')
				if ntiid and topic_ntiid:
					_add_2_od(result, ntiid, topic_ntiid)
					_add_2_od(inverted, topic_ntiid, ntiid)

		return result, inverted

	def _get_parent_node(self, node, topic_map):
		parent = node.parentNode
		while parent is not None and not isinstance(parent, LaTexDocument.document):
			ntiid = getattr(parent, 'ntiid', None) or u''
			if ntiid in topic_map:
				break
			else:
				parent = parent.parentNode
		return parent

	def _get_parent_node_ntiid(self, node, topic_map):
		parent = self._get_parent_node(node, topic_map)
		return getattr(parent, 'ntiid', None)

	def _get_media_entry(self, media):
		entry = {'sources':[], 'transcripts':[]}

		entry['ntiid'] = media.ntiid
		entry['creator'] = media.creator
		if hasattr(media.title, 'textContent'):
			entry['title'] = media.title.textContent
		else:
			entry['title'] = media.title

		entry['MimeType'] = entry['mimeType'] = media.mimeType
		for transcript in media.getElementsByTagName('mediatranscript'):
			val = {}
			val['src'] = transcript.raw.url
			val['srcjsonp'] = transcript.wrapped.url
			val['lang'] = transcript.attributes['lang']
			val['type'] = transcript.transcript_mime_type
			val['purpose'] = transcript.attributes['purpose']
			entry['transcripts'].append(val)
		return entry

	def _process_media_els(self, dom, elements, references, topic_map, outpath):
		filename = self.index_file

		# In practice, it's not nearly that simple because of the
		# "overrides". In practice, all ntivideo elements are children
		# of the document for some reason, and ntivideoref elements
		# are scattered about through the content to refer to these
		# elements. In turn, these ntivideoref elements get added to
		# the ToC dom (NOT the content dom) as "<object>" tags...we go
		# through and "re-parent" ntivideo elements in the Containers
		# collection based on where references appear to them

		items = {}
		inverted = defaultdict(set)
		containers = defaultdict(set)
		doc_ntiid = dom.documentElement.getAttribute('ntiid')

		# parse all elements
		for element in elements:
			entry = self._get_media_entry(element)
			ntiid = entry.get('ntiid')
			if not ntiid:
				continue
			items[ntiid] = entry

			containerId = self._get_parent_node_ntiid(element, topic_map)
			if containerId:
				inverted[ntiid].add(containerId)
				containers[containerId].add(ntiid)

		# add references to items
		for ntiid, reference in references.items():
			entry = items.get(ntiid)
			if entry is None:
				entry = self._get_media_entry(reference.media)
				items[ntiid] = entry
			inverted[ntiid].update(reference.containers)
			for containerId in reference.containers:
				containers[containerId].add(ntiid)

		# add video objects to toc
		overrides = defaultdict(set)
		media_in_toc, _ = self._find_toc_media(topic_map)
		for media_ntiid, container_ntiids in tuple(inverted.items()): # mutating
			toc_entries = media_in_toc.get(media_ntiid)
			if toc_entries:
				for toc_container_id in toc_entries:
					overrides[media_ntiid].add(toc_container_id)
			else:
				for container_ntiid in tuple(container_ntiids): # mutating
					if container_ntiid == doc_ntiid:
						parent = dom.documentElement
						# remove reference from the main container
						# iff it shows somewhere else
						if len(inverted[media_ntiid]) > 1:
							containers[doc_ntiid].discard(media_ntiid)
							inverted[media_ntiid].discard(doc_ntiid)
					else:
						parent = topic_map.get(container_ntiid)
					if parent is None:  # check
						continue
					# check element has not already been added
					reference = references.get(media_ntiid)
					if reference and container_ntiid in reference.containers:
						continue
					# create new elemenet
					media = items.get(media_ntiid)
					obj_el = dom.createElement('object')
					obj_el.setAttribute(u'label', media.get('title') or u'')
					obj_el.setAttribute(u'ntiid', media_ntiid)
					obj_el.setAttribute(u'mimeType', self.media_mimeType)

					# add to parent
					parent.childNodes.append(obj_el)

		# apply overrides, remove all existing. TOC always win # legacy
		for media_ntiid, container_ntiids in overrides.items():
			for container in containers.values():
				container.discard(media_ntiid)
			for container_ntiid in container_ntiids:
				containers[container_ntiid].add(media_ntiid)

		# make JSON serializable
		json_containers = {}
		for containerId, media_ntiids in containers.items():
			if media_ntiids:
				json_containers[containerId] = list(media_ntiids)

		# write the normal version
		media_index = {'Items': items, 'Containers':json_containers}
		with open(os.path.join(outpath, filename), "wb") as fp:
			json.dump(media_index, fp, indent=4)

		# write the JSONP version
		with open(os.path.join(outpath, filename + 'p'), "wb") as fp:
			fp.write('jsonpReceiveContent(')
			json.dump({'ntiid': dom.childNodes[0].getAttribute('ntiid'),
					   'Content-Type': 'application/json',
					   'Content-Encoding': 'json',
					   'content': media_index,
					   'version': '1'}, fp, indent=4)
			fp.write(');')

		toc_el = dom.createElement('reference')
		toc_el.setAttribute('href', filename)
		toc_el.setAttribute('type', self.index_mimeType)

		dom.childNodes[0].appendChild(toc_el)

	def _get_title(self, element, media_title):
		renderer = None
		try:
			renderer = element.media.renderer
		except AttributeError:
			try:
				renderer = element.renderer
			except AttributeError:
				pass
		if renderer is not None:
			title = _render_children(renderer, media_title)
		else:
			title = media_title
		return title

	def _process_references(self, dom, elements, topic_map):

		def _set_attributes(source, target, *names):
			for name in names:
				if hasattr(source, name):
					target.setAttribute(name, getattr(source, name))

		result = {}
		for element in elements:
			parent = self._get_parent_node(element, topic_map)
			if 	isinstance(parent, LaTexDocument.document) or \
				not getattr(parent, 'ntiid', None):
				continue

			ntiid = getattr(element.media, 'ntiid', None)
			# If not a dom, skip.
			if not ntiid or not isinstance(element.media, ntimedia):
				continue

			toc_el = dom.createElement('object')
			media_title = getattr(element.media, 'title', u'')
			title = self._get_title(element, media_title)
			toc_el.setAttribute('label', title)

			_set_attributes(element, toc_el, 'visibility')
			_set_attributes(element.media, toc_el, 'poster', 'ntiid', 'mimeType')

			# add to course/section
			parent.appendChild(toc_el)

			# if topic in ToC is not parent then added to TOC
			# this will cause and override
			# topic = topic_map.get(parent.ntiid)
			# if topic is not None and parent is not topic:
			# 	topic.appendChild(toc_el)

			ref = result.get(ntiid)
			if ref is None:
				ref = _Reference(element.media, set())
				result[ntiid] = ref
			ref.containers.add(parent.ntiid)

		return result

@interface.implementer(INTIVideoExtractor)
class _NTIVideoExtractor(_NTIMediaExtractor):

	ntimedia = u'ntivideo'
	ntimediaref = u'ntivideoref'
	index_file = u"video_index.json"
	media_mimeType = u'application/vnd.nextthought.ntivideo'
	index_mimeType = u'application/vnd.nextthought.videoindex'

	def _get_media_entry(self, video):
		entry = super(_NTIVideoExtractor, self)._get_media_entry(video)
		entry['description'] = video.description
		entry['closedCaptions'] = video.closed_caption
		if hasattr(video, 'slidedeck'):
			entry['slidedeck'] = video.slidedeck

		for source in video.getElementsByTagName('ntivideosource'):
			val = {'source':[], 'type':[]}

			val['width'] = source.width
			val['poster'] = source.poster
			val['height'] = source.height
			val['service'] = source.service
			val['thumbnail'] = source.thumbnail

			if source.service == 'html5':
				val['type'].append('video/mp4')
				val['type'].append('video/webm')
				val['source'].append(source.src['mp4'])
				val['source'].append(source.src['webm'])
			elif source.service == 'youtube':
				val['type'].append('video/youtube')
				val['source'].append(source.src['other'])
			elif source.service == 'kaltura':
				val['type'].append('video/kaltura')
				val['source'].append(source.src['other'])
			elif source.service == 'vimeo':
				val['type'].append('video/vimeo')
				val['source'].append(source.src['other'])
			entry['sources'].append(val)
		return entry

@interface.implementer(INTIAudioExtractor)
class _NTIAudioExtractor(_NTIMediaExtractor):

	ntimedia = u'ntiaudio'
	ntimediaref = u'ntiaudioref'
	index_file = u'audio_index.json'
	media_mimeType = u'application/vnd.nextthought.ntiaudio'
	index_mimeType = u'application/vnd.nextthought.audioindex'

	def _get_media_entry(self, audio):
		entry = super(_NTIAudioExtractor, self)._get_media_entry(audio)
		entry['description'] = getattr(audio, 'description', None)
		for source in audio.getElementsByTagName('ntiaudiosource'):
			val = {'source':[], 'type':[]}
			val['service'] = source.service
			val['thumbnail'] = source.thumbnail
			if source.service == 'html5':
				val['type'].append('audio/mp3')
				val['type'].append('audio/wav')
				val['source'].append(source.src['mp3'])
				val['source'].append(source.src['wav'])
			entry['sources'].append(val)
		return entry
