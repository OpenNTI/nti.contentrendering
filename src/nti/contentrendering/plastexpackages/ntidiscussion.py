#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

import os
import codecs

import simplejson as json

from zope.cachedescriptors.property import readproperty

from plasTeX.Base import Command
from plasTeX.Base import Crossref
from plasTeX.Base import Environment


class ntidiscussionname(Command):
    pass


class ntidiscussionref(Crossref.ref):

    @readproperty
    def discussion(self):
        return self.idref['label']


class ntidiscussion(Environment):

    blockType = True
    args = '[ options:dict ] '

    # Only classes with counters can be labeled, and \label sets the
    # id property, which in turn is used as part of the NTIID (when no NTIID
    # is set explicitly)
    counter = 'ntidiscussion'

    title = ''
    subtitle = ''
    autogenuri = ''
    topic_ntiid = ''
    iconResource = None

    targetMimeType = "application/vnd.nextthought.discussion"

    class discussiontitle(Command):

        args = 'title'

        def digest(self, tokens):
            tok = super(ntidiscussion.discussiontitle, self).digest(tokens)
            self.parentNode.title = self.attributes['title']
            return tok

    class discussionsubtitle(Command):

        args = 'subtitle'

        def digest(self, tokens):
            tok = super(ntidiscussion.discussionsubtitle, self).digest(tokens)
            self.parentNode.subtitle = self.attributes['subtitle']
            return tok

    class discussionuri(Command):

        args = 'uri:url'

        to_replace = ((' ', ''), ('\\&', '&'), ('\\_', '_'), ('\\%', '%'),
                      (u'\u2013', u'--'), (u'\u2014', u'---'))

        COURSE_BUNDLE = r'nti-course-bundle://'

        def replacer(self, source):
            for a, b in self.to_replace:
                source = source.replace(a, b)
            return source

        def digest(self, tokens):
            tok = super(ntidiscussion.discussionuri, self).digest(tokens)
            uri = self.attributes['uri']
            self.parentNode.autogenuri = self.replacer(uri.source)

            # discussion_path
            parent = self.parentNode
            userdata = self.ownerDocument
            course_bundle_path = userdata['course_bundle_path']
            discussion_path = parent.autogenuri.split(self.COURSE_BUNDLE)[1]
            discussion_path = os.path.join(course_bundle_path, discussion_path)

            # read discussion
            if os.path.exists(discussion_path):
                with codecs.open(discussion_path, 'rb', 'utf-8') as fp:
                    discussion = json.load(fp)
            else:
                discussion = None
                logger.warning('Unable to find discussion definition at %s',
                               discussion_path)
            if discussion is not None:
                if 'label' in discussion:
                    parent.title = discussion['label']
                if 'title' in discussion:
                    parent.subtitle = discussion['title']
            return tok

    class topicntiid(Command):

        args = 'ntiid:str'

        def digest(self, tokens):
            tok = super(ntidiscussion.topicntiid, self).digest(tokens)
            self.parentNode.topic_ntiid = self.attributes['ntiid']
            return tok

    def digest(self, tokens):
        tok = super(ntidiscussion, self).digest(tokens)
        icons = self.getElementsByTagName('includegraphics') \
             or self.getElementsByTagName('ntiexternalgraphics')
        if icons:
            self.iconResource = icons[0]
        return tok
