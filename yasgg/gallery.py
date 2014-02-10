#-*- coding: utf-8 -*-
import codecs
import ConfigParser
import os
import simplejson as json
import sys
import time

from distutils.dir_util import copy_tree
from jinja2 import Template
from shutil import rmtree, copy

from yasgg import logger
from yasgg.theme import Theme
from yasgg.utils import ensure_file
from yasgg.settings import DEFAULT_GALLERY_CONFIG, DEFAULT_ALBUMS_LIST, GALLERY_CONFIG, ALBUM_DATA


def initialize_gallery():
    if not os.path.exists(GALLERY_CONFIG) or not os.path.exists(ALBUM_DATA):
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

    def add_album(self, album):
        """ Adds an album to the gallery. """

        # TODO: Should check for existing album be here? (And not in yasgg?)
        slug = album.slug
        self.albums[slug] = album

    def delete_album(self, album_slug):
        """ Deletes an album. """

        logger.error('This feature is not implemented yet.' % album_slug)
        return

        if album_slug in self.albums:
            choice = raw_input("Are you sure you want to delete the album '%s%s'? Y/N [N]: " % (os.path.join(os.getcwd(), album_slug), os.sep))
            choice = choice or 'N'
            if choice == 'Y':
                try:
                    rmtree(album_slug)
                except OSError:
                    pass
                del self.albums[album_slug]
                # TODO: This is bugged ...
                self.write_album_data_to_disk()
                logger.info('Deleted album named %s' % album_slug)
        else:
            logger.error('An album named %s doesn\'t exist.' % album_slug)

    def write_album_data_to_disk(self):
        """ Writes self.albums as json to disk. """

        with open(self.albums_data, 'w') as albums_data_file:
            print self.albums

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

    def write_gallery(self):
        theme = Theme(name=self.theme)

        # Copy theme data
        copy_tree(theme.base_dir, os.path.join(self.base_dir, 'assets'))
        assets_dir_for_all = '%s%s' % (os.path.join(theme.base_dir, '..', '_assets_for_all_themes'), os.sep)
        copy_tree(assets_dir_for_all, '%s%s%s' % (self.base_dir, os.sep, 'assets'))

        # Write gallery HTML
        gallery_template = Template(codecs.open(theme.gallery_template, 'r', 'utf8').read())
        copy(theme.gallery_template, 'index.html')
        with open(self.html_file, 'wb') as html_file:
            logger.info('Writing html file %s' % self.html_file)
            html = gallery_template.render(gallery=self)
            html_file.write(html.encode('utf-8'))

        # Write albums HTML
        for album in self.albums.itervalues():
            album_template = Template(codecs.open(theme.album_template, 'r', 'utf8').read())
            copy(theme.album_template, os.path.join(album['slug'], 'index.html'))
            with open(os.path.join(album['slug'], 'index.html'), 'wb') as html_file:
                logger.info('Writing html file %s' % os.path.join(album['slug'], 'index.html'))
                html = album_template.render(album=album, gallery=self, timestamp=int(time.time()))
                html_file.write(html.encode('utf-8'))