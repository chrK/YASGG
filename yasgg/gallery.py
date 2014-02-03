#-*- coding: utf-8 -*-
import sys
import os
import ConfigParser
import cPickle as pickle

from yasgg.photo import Photo
from yasgg.settings import IMAGE_FILE_EXTENSIONS_2_IMPORT
from yasgg.utils import walkdir, ensure_dir


DEFAULT_CONFIG = """
[gallery]
name = Gallery Name
"""


class Gallery(object):
    name = None
    albums = []

    pickle_file = 'gallery.pk'
    config_file = 'gallery.cfg'

    html_file = None

    def __init__(self):
        self.load()
        self.load_config()
        self.update()

        self.html_file = 'index.html'

    def load(self):
        if not os.path.exists(self.pickle_file):
            with open(self.pickle_file, 'wb') as pickle_file:
                pickle.dump(self, pickle_file)

        with open(self.pickle_file, 'rb') as pickle_file:
            self = pickle.load(pickle_file)

    def update(self):
        with open(self.pickle_file, 'wb') as pickle_file:
            pickle.dump(self, pickle_file)

    def load_config(self):
        # Ensure config file
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'wb') as config_file:
                config_file.write(DEFAULT_CONFIG)

        # Read config file
        config = ConfigParser.ConfigParser()
        config.read(self.config_file)

        self.name = config.get('gallery', 'name')

