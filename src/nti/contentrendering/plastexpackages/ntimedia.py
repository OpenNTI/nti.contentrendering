#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from zope.cachedescriptors.property import readproperty

from plasTeX import Base
from plasTeX import Command

from plasTeX.Renderers import render_children

from nti.contentfragments.interfaces import HTMLContentFragment

from nti.contentrendering import plastexids

from nti.contentrendering.plastexpackages._util import LocalContentMixin
from nti.contentrendering.plastexpackages._util import incoming_sources_as_plain_text


class ntimediaref(Base.Crossref.ref):

    args = '[options:dict] label:idref'

    _options = {}
    to_render = False

    def digest(self, tokens):
        tok = super(ntimediaref, self).digest(tokens)
        self._options = self.attributes.get('options', {}) or {}
        if 'to_render' in self._options.keys():
            if self._options['to_render'] in [u'true', u'True']:
                self.to_render = True
        return tok

    @readproperty
    def media(self):
        return self.idref['label']

    @readproperty
    def visibility(self):
        visibility = self._options.get('visibility') or None
        if visibility is None:
            return self.media.visibility
        return visibility


class ntimedia(LocalContentMixin, Base.Float, plastexids.NTIIDMixin):

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
        args = '[ options:dict ] service:str id:str'
        blockType = True

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
            # Try to extract the text children, ignoring the caption and label...
            if      child.nodeType == self.TEXT_NODE \
                and (child.parentNode == self or child.parentNode.nodeName == 'par'):
                texts.append(unicode(child))

        return incoming_sources_as_plain_text(texts)

    @readproperty
    def audio_sources(self):
        sources = self.getElementsByTagName('ntiaudiosource')
        output = render_children(self.renderer, sources)
        return HTMLContentFragment(''.join(output).strip())

    @readproperty
    def transcripts(self):
        sources = self.getElementsByTagName('mediatranscript')
        output = render_children(self.renderer, sources)
        return HTMLContentFragment(''.join(output).strip())


class ntiaudioref(ntimediaref):
    pass
