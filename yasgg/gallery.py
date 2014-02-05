#-*- coding: utf-8 -*-
import os
import sys
import ConfigParser

import simplejson as json

from shutil import rmtree

from yasgg import logger
from yasgg.utils import ensure_file
from yasgg.settings import DEFAULT_GALLERY_CONFIG, DEFAULT_ALBUMS_LIST, GALLERY_CONFIG, ALBUM_DATA


def initialize_gallery():
    if not os.path.exists(GALLERY_CONFIG):
        ensure_file(GALLERY_CONFIG, DEFAULT_GALLERY_CONFIG)
        ensure_file(ALBUM_DATA, DEFAULT_ALBUMS_LIST)
        logger.info('Initialized gallery. You can start adding albums now.')
    else:
        logger.info('This folder already seems to be a gallery.')


class Gallery(object):
    # Values from config file
    title = None
    theme = None

    # Path data
    base_dir = None
    config_file = GALLERY_CONFIG
    albums_data = ALBUM_DATA
    html_file = 'index.html'

    # Album data
    albums = {}

    def __init__(self):
        self.base_dir = os.getcwd()
        self.check_config()
        self.load_config()
        self.load_albums()

    def check_config(self):
        config_file = os.path.exists(self.config_file)
        album_data = os.path.exists(self.albums_data)
        if not config_file or not album_data:
            logger.info('No gallery was initialized in this directory (%s) yet. Please initialize a gallery first.' % self.base_dir)
            sys.exit(0)

    def load_config(self):
        """
        Loads config file. If config file doesn't exist yet,
        the config file is created with the default values.
        """

        config = ConfigParser.ConfigParser()
        config.read(self.config_file)
        self.title = config.get('gallery', 'title')
        self.theme = config.get('gallery', 'theme')

    def load_albums(self):
        """
        Loads json with albums data. If the file doesn't exist yet,
        an empty list is created as json file.
        """

        with open(self.albums_data, 'rb') as albums_data_file:
            self.albums = json.loads(albums_data_file.read())

    def list_albums(self):
        """ Lists all known albums. """

        if self.albums:
            logger.info('Following albums exist:')
            for album in self.albums.iterkeys():
                print album
        else:
            logger.info('No albums exist in %s', os.getcwd())

    def add_album(self):
        """ Adds an album to the gallery. """

        # If album exists ...
            # Prompt if the album should be added with another slug or if the existing album should be replaced.
        # Else:
            # Create album
            # Add album data to json file
        pass

    def build_index(self):
        # TODO: Build index from json file.
        pass

    def delete_album(self, album_slug):
        """ Deletes an album. """

        if os.path.exists(album_slug):
            rmtree(album_slug)
            del self.albums[album_slug]
            self.write_album_data_to_disk()
            # TODO: rebuild gallery index
            logger.info('Deleted album named %s' % album_slug)
        else:
            logger.error('An album named %s doesn\'t exist.' % album_slug)

    def write_album_data_to_disk(self):
        """ Writes self.albums as json to disk. """

        with open(self.albums_data, 'wb') as albums_data_file:
            for album_key, album in self.albums.iteritems():
                self.albums[album.slug] = {
                    "slug": album.slug,  # = relative path
                    "base_dir": album.base_dir,
                    "title": album.title,
                    "thumbnail": album.thumbnail,
                    "photos": [x for x in album.photos_for_tpl],
                    "description": album.description
                }

            album_data = json.dumps(self.albums, sort_keys=True, indent=4 * ' ')
            albums_data_file.write(album_data)