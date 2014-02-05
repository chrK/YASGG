#-*- coding: utf-8 -*-
import os
from . import logger


class Theme(object):
    name = None
    base_dir = None
    album_template = None
    gallery_template = None

    def __init__(self, name):
        self.name = name

        # Set and check theme base directory.
        self.base_dir = '%s%sthemes%s%s%s' % (
            os.path.dirname(os.path.abspath(__file__)), os.sep, os.sep, self.name, os.sep)

        if not os.path.exists(self.base_dir):
            logger.error('Theme %s (%s) does not exist.' % (self.name, self.base_dir))
            exit(1)
        else:
            logger.info('Using theme \'%s\' %s.' % (self.name, self.base_dir))

        # Set and check album template file in template directory.
        self.album_template = '%sindex.html' % self.base_dir

        if not os.path.exists(self.album_template):
            logger.error('Album template file %s does not exist.' % self.album_template)
            exit(1)
        else:
            logger.debug('Using template file %s for albums.' % self.album_template)

        # Set and check gallery template file in template directory.
        self.gallery_template = '%sgallery_index.html' % self.base_dir
        if not os.path.exists(self.album_template):
            logger.error('Gallery template file %s does not exist.' % self.album_template)
            exit(1)
        else:
            logger.debug('Using template file %s for gallery index.' % self.gallery_template)






