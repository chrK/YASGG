#-*- coding: utf-8 -*-
import os
import ConfigParser

from yasgg import logger
from yasgg.settings import DEFAULT_GALLERY_CONFIG


class Gallery(object):
    title = None
    albums = []

    base_dir = None
    config_file = 'gallery.cfg'

    html_file = None

    def __init__(self):
        self.load_config()
        self.base_dir = os.getcwd()
        self.html_file = 'index.html'

    def load_config(self):
        # Ensure config file
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'wb') as config_file:
                config_file.write(DEFAULT_GALLERY_CONFIG)

        # Read config file
        config = ConfigParser.ConfigParser()
        config.read(self.config_file)
        self.title = config.get('gallery', 'title')
