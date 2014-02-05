#-*- coding: utf-8 -*-
import os
from . import logger


class Theme(object):
    name = None
    basedir = None
    template = None
    gallery_template = None

    def __init__(self, name):
        self.name = name

        # set and check for tpl dir
        self.basedir = '%s%sthemes%s%s%s' % (
            os.path.dirname(os.path.abspath(__file__)), os.sep, os.sep, self.name, os.sep)
        if not os.path.exists(self.basedir):
            logger.error('Theme %s (%s) does not exist.' % (self.name, self.basedir))
            exit(1)
        else:
            logger.info('Using theme %s (%s).' % (self.name, self.basedir))

        # set and check template.html in tpl dir
        self.template = '%sindex.html' % self.basedir
        self.gallery_template = '%sgallery_index.html' % self.basedir
        if not os.path.exists(self.template):
            logger.error('Template file %s does not exist.' % self.template)
            exit(1)
        else:
            logger.debug('Using template file %s.' % self.template)





