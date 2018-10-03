#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import print_function, unicode_literals, absolute_import, division
__docformat__ = "restructuredtext en"

logger = __import__('logging').getLogger(__name__)

# BWC
from nti.contentrendering.plastexpackages.extractors.course import _CourseExtractor

from nti.contentrendering.plastexpackages.extractors.media import _NTIAudioExtractor
from nti.contentrendering.plastexpackages.extractors.media import _NTIVideoExtractor

from nti.contentrendering.plastexpackages.extractors.discussion import _DiscussionExtractor

from nti.contentrendering.plastexpackages.extractors.related_work import _RelatedWorkExtractor

from nti.contentrendering.plastexpackages.extractors.content_unit_statistics import _ContentUnitStatistics