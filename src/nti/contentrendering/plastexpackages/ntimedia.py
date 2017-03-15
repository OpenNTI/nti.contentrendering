#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os

from zope import interface

from zope.cachedescriptors.property import readproperty

from plasTeX import Base
from plasTeX import Command
from plasTeX import Environment

from plasTeX.Renderers import render_children

from nti.contentfragments.interfaces import HTMLContentFragment

from nti.contentrendering.plastexids import NTIIDMixin

from nti.contentrendering.resources.interfaces import IRepresentableContentUnit
from nti.contentrendering.resources.interfaces import IRepresentationPreferences

from nti.contentrendering.plastexpackages._util import LocalContentMixin
from nti.contentrendering.plastexpackages._util import incoming_sources_as_plain_text


@interface.implementer(IRepresentableContentUnit,
                       IRepresentationPreferences)
class DeclareMediaResource(Command):
    """
    This command is extremely experimental and should be avoided for now.
    """

    args = 'src:str label:id'
    resourceTypes = ('jsonp', )

    def invoke(self, tex):
        result = super(DeclareMediaResource, self).invoke(tex)
        wk_dir = self.ownerDocument.userdata.getPath('working-dir')
        self.attributes['src'] = os.path.join(wk_dir, self.attributes['src'])
        return result


@interface.implementer(IRepresentableContentUnit,
                       IRepresentationPreferences)
class mediatranscript(Command):

    blockType = True
    resourceTypes = ('jsonp', )
    args = 'src:str type:str lang:str purpose:str'

    transcript_mime_type = 'text/plain'

    def invoke(self, tex):
        result = super(mediatranscript, self).invoke(tex)
        source = self.attributes['src']
        working_dir = self.ownerDocument.userdata.getPath('working-dir')
        self.attributes['src'] = os.path.join(working_dir, source)
        return result

    def digest(self, tokens):
        res = super(mediatranscript, self).digest(tokens)
        if self.attributes['type'] == 'webvtt':
            self.transcript_mime_type = 'text/vtt'
        return res


class ntimediaref(Base.Crossref.ref):

    args = '[options:dict] label:idref'

    _options = {}
    to_render = False

    def digest(self, tokens):
        tok = super(ntimediaref, self).digest(tokens)
        self._options = self.attributes.get('options', {}) or {}
        if 'to_render' in self._options:
            if self._options['to_render'] in [u'true', u'True']:
                self.to_render = True
        return tok

    @readproperty
    def media(self):
        return self.idref['label']

    @readproperty
    def visibility(self):
        visibility = self._options.get('visibility')
        if visibility is None:
            return self.media.visibility
        return visibility


class ntimedia(LocalContentMixin, Base.Float, NTIIDMixin):

    blockType = True
    args = '[ options:dict ]'

    _ntiid_title_attr_name = 'ref'
    _ntiid_allow_missing_title = False

    creator = None
    num_sources = 0
    closed_caption = None

    title = 'No Title'

    @readproperty
    def description(self):
        return None

    @readproperty
    def transcripts(self):
        return None


# audio


class ntiaudioname(Command):
    unicode = ''


class ntiaudio(ntimedia):

    counter = 'ntiaudio'

    _ntiid_type = 'NTIAudio'
    _ntiid_suffix = 'ntiaudio.'
    _ntiid_allow_missing_title = True
    _ntiid_cache_map_name = '_ntiaudio_ntiid_map'

    itemprop = "presentation-audio"
    mime_type = mimeType = "application/vnd.nextthought.ntiaudio"

    # A Float subclass to get \caption handling
    class caption(Base.Floats.Caption):
        counter = 'figure'

    class ntiaudiosource(Command):

        blockType = True
        args = '[ options:dict ] service:str id:str'

        priority = 0
        thumbnail = None

        def digest(self, tokens):
            """
            Handle creating the necessary datastructures for each audio type.
            """
            super(ntiaudio.ntiaudiosource, self).digest(tokens)

            self.priority = self.parentNode.num_sources
            self.parentNode.num_sources += 1

            self.src = {}
            if self.attributes['service']:
                if self.attributes['service'] == 'html5':
                    self.service = 'html5'
                    self.src['mp3'] = self.attributes['id'] + '.mp3'
                    # self.src['m4a'] = self.attributes['id'] + '.m4a'
                    self.src['wav'] = self.attributes['id'] + '.wav'
                    # self.src['ogg'] = self.attributes['id'] + '.ogg'
                    self.thumbnail = self.attributes['id'] + '-thumb.jpg'
                else:
                    logger.warning('Unknown audio type: %s',
                                   self.attributes['service'])

    def digest(self, tokens):
        res = super(ntiaudio, self).digest(tokens)
        if self.macroMode == self.MODE_BEGIN:
            options = self.attributes.get('options', {}) or {}
            __traceback_info__ = options, self.attributes

            if 'show-card' in options:
                self.itemprop = 'presentation-card'

            if 'creator' in options:
                self.creator = options['creator']

            self.visibility = u'everyone'
            if 'visibility' in options.keys():
                self.visibility = options['visibility']

        return res

    @readproperty
    def description(self):
        texts = []
        for child in self.allChildNodes:
            # Try to extract the text children, ignoring the caption and
            # label...
            if      child.nodeType == self.TEXT_NODE \
                    and (child.parentNode == self or child.parentNode.nodeName == 'par'):
                texts.append(unicode(child))
        return incoming_sources_as_plain_text(texts)

    @readproperty
    def audio_sources(self):
        sources = self.getElementsByTagName('ntiaudiosource')
        output = render_children(self.renderer, sources or ())
        return HTMLContentFragment(''.join(output).strip())

    @readproperty
    def transcripts(self):
        sources = self.getElementsByTagName('mediatranscript')
        output = render_children(self.renderer, sources or ())
        return HTMLContentFragment(''.join(output).strip())


class ntiaudioref(ntimediaref):
    pass


# video

class ntivideoname(Command):
    unicode = ''


class ntivideo(ntimedia):

    counter = 'ntivideo'

    _ntiid_type = 'NTIVideo'
    _ntiid_suffix = 'ntivideo.'
    _ntiid_cache_map_name = '_ntivideo_ntiid_map'

    itemprop = "presentation-video"
    mimeType = "application/vnd.nextthought.ntivideo"

    subtitle = None

    _poster_override = None
    _thumb_override = None

    # A Float subclass to get \caption handling
    class caption(Base.Floats.Caption):
        counter = 'ntivideo'

    class ntivideosource(Command):

        blockType = True
        args = '[ options:dict ] service:str id:str'

        poster = None
        thumbnail = None

        width = 640
        height = 480
        priority = 0

        def process_options(self):
            self.src = {}
            self.parentNode.num_sources += 1
            self.priority = self.parentNode.num_sources
            if self.attributes['service']:
                vid = self.attributes.get('id')
                if self.attributes['service'] == 'youtube':
                    self.width = 640
                    self.height = 360
                    self.src['other'] = vid
                    self.service = 'youtube'
                    self.poster = '//img.youtube.com/vi/' + vid + '/0.jpg'
                    self.thumbnail = '//img.youtube.com/vi/' + vid + '/1.jpg'
                elif self.attributes['service'] == 'html5':
                    self.service = 'html5'
                    self.src['mp4'] = vid + '.mp4'
                    self.src['webm'] = vid + '.webm'
                    self.poster = vid + '-poster.jpg'
                    self.thumbnail = vid + '-thumb.jpg'
                elif self.attributes['service'] == 'kaltura':
                    self.service = 'kaltura'
                    self.src['other'] = vid
                    partnerId, entryId = vid.split(':')
                    self.poster = ('//www.kaltura.com/p/' + partnerId +
                                   '/thumbnail/entry_id/' + entryId +
                                   '/width/1280/')
                    self.thumbnail = ('//www.kaltura.com/p/' + partnerId +
                                      '/thumbnail/entry_id/' + entryId +
                                      '/width/640/')
                elif self.attributes['service'] == 'vimeo':
                    self.service = 'vimeo'
                    self.src['other'] = vid
                else:
                    logger.warning('Unknown video type: %s',
                                   self.attributes['service'])

        def digest(self, tokens):
            """
            Handle creating the necessary datastructures for each video type.
            """
            super(ntivideo.ntivideosource, self).digest(tokens)
            self.process_options()

    class ntiposteroverride(Command):

        blockType = True
        args = '[ options:dict ] url:str:source'

        def digest(self, tokens):
            tok = super(ntivideo.ntiposteroverride, self).digest(tokens)
            self.parentNode._poster_override = self.attributes['url']
            sources = self.parentNode.getElementsByTagName('ntivideosource')
            for source in sources or ():
                source.poster = self.attributes['url']
            return tok

    class ntithumbnailoverride(Command):

        blockType = True
        args = '[ options:dict ] url:str:source'

        def digest(self, tokens):
            tok = super(ntivideo.ntithumbnailoverride, self).digest(tokens)
            self.parentNode._thumb_override = self.attributes['url']
            sources = self.parentNode.getElementsByTagName('ntivideosource')
            for source in sources or ():
                source.thumbnail = self.attributes['url']
            return tok

    def digest(self, tokens):
        res = super(ntivideo, self).digest(tokens)
        if self.macroMode == self.MODE_BEGIN:
            options = self.attributes.get('options', {}) or {}
            __traceback_info__ = options, self.attributes

            if 'show-card' in options:
                self.itemprop = 'presentation-card'

            if not getattr(self, 'title', ''):
                raise ValueError("Must specify a title using \\caption")

            if 'creator' in options:
                self.creator = options['creator']

            self.visibility = u'everyone'
            if 'visibility' in options:
                self.visibility = options['visibility']

        return res

    @readproperty
    def description(self):
        texts = []
        for child in self.allChildNodes:
            # Try to extract the text children, ignoring the caption and label
            if     child.nodeType == self.TEXT_NODE and \
                    (child.parentNode == self or child.parentNode.nodeName == 'par'):
                texts.append(unicode(child))
        return incoming_sources_as_plain_text(texts)

    @readproperty
    def poster(self):
        if not self._poster_override:
            sources = self.getElementsByTagName('ntivideosource')
            return sources[0].poster
        return self._poster_override

    @readproperty
    def thumbnail(self):
        if not self._thumbnail_override:
            sources = self.getElementsByTagName('ntivideosource')
            return sources[0].thumbnail
        return self._thumbnail_override

    @readproperty
    def video_sources(self):
        sources = self.getElementsByTagName('ntivideosource')
        output = render_children(self.renderer, sources or ())
        return HTMLContentFragment(''.join(output).strip())

    @readproperty
    def transcripts(self):
        sources = self.getElementsByTagName('mediatranscript')
        output = render_children(self.renderer, sources or ())
        return HTMLContentFragment(''.join(output).strip())


class ntivideoref(ntimediaref):

    @readproperty
    def poster(self):
        poster = self._options.get('poster')
        if poster is None:
            return self.media.poster
        return poster


class ntilocalvideoname(Command):
    unicode = ''


class ntilocalvideo(Environment):

    blockType = True
    args = '[ options:dict ]'
    counter = "ntilocalvideo"

    def invoke(self, tex):
        result = super(ntilocalvideo, self).invoke(tex)
        if 'options' not in self.attributes or not self.attributes['options']:
            self.attributes['options'] = {}
        return result

    def digest(self, tex):
        super(ntilocalvideo, self).digest(tex)
        video = self.getElementsByTagName('ntiincludelocalvideo')[0]
        self.src = {'mp4': video.attributes['src'] + u'.mp4',
                    'webm':  video.attributes['src'] + u'.webm'}
        self.title = video.attributes['title']
        self.poster = video.attributes['poster']
        if 'width' in video.attributes['options']:
            self.width = video.attributes['options']['width']
        if 'height' in video.attributes['options']:
            self.height = video.attributes['options']['height']
        self.id = video.id

    class ntiincludelocalvideo(Command):
        args = '[ options:dict ] src title poster'


# Media collection


class ntimediacollection(Environment, NTIIDMixin):

    blockType = True
    args = '[options] <title:str:source>'

    _poster_override = None

    def digest(self, tokens):
        tok = super(ntimediacollection, self).digest(tokens)
        self.options = self.attributes.get('options', {}) or {}
        self.title = self.attributes.get('title')
        return tok

    @readproperty
    def description(self):
        description = u''
        descriptions = self.getElementsByTagName('ntidescription')
        if descriptions:
            description = descriptions[0].attributes.get('content')
        return description

    class ntiposteroverride(Command):

        blockType = True
        args = '[ options:dict ] url:str:source'

        def digest(self, tokens):
            tok = Command.digest(self, tokens)
            self.parentNode._poster_override = self.attributes['url']
            return tok

    @readproperty
    def poster(self):
        return self._poster_override


class ntivideorollname(Command):
    pass


class ntivideoroll(ntimediacollection):
    counter = "ntivideoroll"

    _ntiid_type = 'NTIVR'
    _ntiid_suffix = 'ntivideoroll.'
    _ntiid_title_attr_name = 'ref'
    _ntiid_allow_missing_title = True
    _ntiid_cache_map_name = '_ntivideoroll_ntiid_map'

    @readproperty
    def poster(self):
        _first = None
        contents = self.getElementsByTagName('ntivideoref')
        if contents:
            _first = contents[0].media.poster
        return self._poster_override if self._poster_override else _first
