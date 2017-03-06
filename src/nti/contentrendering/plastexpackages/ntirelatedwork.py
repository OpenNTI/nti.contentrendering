#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Define NTI Latex Macros

.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

from hashlib import md5

from zope import interface

from zope.cachedescriptors.property import readproperty

from plasTeX import Command
from plasTeX import Environment
from plasTeX import TeXFragment
from plasTeX.Base import Crossref

from nti.contentrendering.interfaces import IEmbeddedContainer

from nti.contentrendering.plastexids import NTIIDMixin

from nti.contentrendering.plastexpackages._util import LocalContentMixin

from nti.ntiids.ntiids import TYPE_UUID
from nti.ntiids.ntiids import make_ntiid
from nti.ntiids.ntiids import get_specific
from nti.ntiids.ntiids import is_valid_ntiid_string


class relatedworkname(Command):
    pass


@interface.implementer(IEmbeddedContainer)
class relatedwork(LocalContentMixin,
                  Environment,
                  NTIIDMixin):

    blockType = True
    args = '[ options:dict ]'

    # Only classes with counters can be labeled, and \label sets the
    # id property, which in turn is used as part of the NTIID (when no NTIID
    # is set explicitly)
    counter = 'relatedwork'

    _ntiid_type = 'RelatedWork'
    _ntiid_suffix = 'relatedwork.'
    _ntiid_allow_missing_title = False
    _ntiid_cache_map_name = '_relatedwork_ntiid_map'

    #: Use our counter to generate IDs if no ID is given
    _ntiid_title_attr_name = 'ref'

    #: From IEmbeddedContainer
    mimeType = "application/vnd.nextthought.relatedwork"
    targetMimeType = "application/vnd.nextthought.content"

    icon = None
    iconResource = None
    target_ntiid = None

    _uri = u''
    _description = None

    node_types = ('label', 'worktitle', 'workcreator',
                  'worksource', 'worksourceref', 'includegraphics')

    class worktitle(Command):

        args = 'title'

        def digest(self, tokens):
            tok = super(relatedwork.worktitle, self).digest(tokens)
            self.parentNode.title = self.attributes['title']
            return tok

    class workcreator(Command):

        args = 'creator'

        def digest(self, tokens):
            tok = super(relatedwork.workcreator, self).digest(tokens)
            self.parentNode.creator = self.attributes['creator']
            return tok

    class worksource(Command):

        args = 'uri:url'

        tokens = ((' ', ''), ('\\&', '&'), ('\\_', '_'), ('\\%', '%'),
                  (u'\u2013', u'--'), (u'\u2014', u'---'))

        def replacer(self, source):
            for a, b in self.tokens:
                source = source.replace(a, b)
            return source

        def digest(self, tokens):
            tok = super(relatedwork.worksource, self).digest(tokens)
            self.attributes['uri'] = self.replacer(
                self.attributes['uri'].source)
            return tok

    class worksourceref(Crossref.ref):
        args = 'target:idref'

    def digest(self, tokens):
        tok = super(relatedwork, self).digest(tokens)

        options = self.attributes.get('options', {}) or {}
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
            for child in self.childNodes or ():
                if child.nodeName not in self.node_types:
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

    def gen_target_ntiid(self, uri=None):
        uri = uri or self.uri
        if is_valid_ntiid_string(uri):
            self.target_ntiid = uri
            self.targetMimeType = 'application/vnd.nextthought.content'
            ntiid_specific = get_specific(uri)
            self.icon = '/'.join([u'..', ntiid_specific.split('.')
                                  [0], 'icons', 'chapters', 'generic_book.png'])

        else:
            # TODO: Hmm, what to use as the provider?
            # Look for a hostname in the  URL?
            self.target_ntiid = make_ntiid(provider='NTI',
                                           nttype=TYPE_UUID,
                                           specific=md5(uri).hexdigest())
            self.targetMimeType = 'application/vnd.nextthought.externallink'


class relatedworkrefname(Command):
    pass


@interface.implementer(IEmbeddedContainer)
class relatedworkref(Crossref.ref, NTIIDMixin):

    blockType = True

    args = '[ options:dict ] label:idref uri:url desc < NTIID:str >'

    counter = 'relatedworkref'

    _ntiid_type = 'RelatedWorkRef'
    _ntiid_suffix = 'relatedworkref.'
    _ntiid_title_attr_name = 'label'
    _ntiid_allow_missing_title = False
    _ntiid_cache_map_name = '_relatedworkref_ntiid_map'

    #: From IEmbeddedContainer
    mimeType = "application/vnd.nextthought.relatedworkref"

    _target_ntiid = None
    _targetMimeType = None

    def digest(self, tokens):
        tok = super(relatedworkref, self).digest(tokens)
        # nti-requirements
        key_nti = 'nti-requirements'
        self.attributes[key_nti] = u''
        self._options = self.attributes.get('options', {}) or {}
        requirements = self._options.get(key_nti, u'').split()
        for requirement in requirements:
            if requirement == u'flash':
                requirement = u'mime-type:application/x-shockwave-flash'
            self.attributes[key_nti] = ' '.join(
                [self.attributes[key_nti], requirement])
        self.attributes[key_nti] = self.attributes[key_nti].strip()
        if self.attributes[key_nti] == u'':
            self.attributes[key_nti] = None
        # label
        self.label = self.attributes.get('label')
        # uri
        self._uri = self.attributes['uri']
        if hasattr(self._uri, 'source'):
            self._uri = self._uri.source.replace(' ', '') \
                .replace('\\&', '&') \
                .replace('\\_', '_') \
                .replace('\\%', '%') \
                .replace(u'\u2013', u'--') \
                .replace(u'\u2014', u'---')
        # rest
        self._title = None
        self._creator = None
        self._description = None
        self.relatedwork = self.idref['label']
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

    def gen_target_ntiid(self, uri=None):
        uri = uri or self.uri
        if is_valid_ntiid_string(uri):
            self._target_ntiid = uri
            self._targetMimeType = 'application/vnd.nextthought.content'
        else:
            # TODO: Hmm, what to use as the provider?
            # Look for a hostname in the URL?
            self._target_ntiid = make_ntiid(provider='NTI',
                                            nttype=TYPE_UUID,
                                            specific=md5(uri).hexdigest())
            self._targetMimeType = 'application/vnd.nextthought.externallink'
