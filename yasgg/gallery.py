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
        self.load_albums_from_json()

    @staticmethod
    def initialize_gallery():
        if not os.path.exists(GALLERY_CONFIG) or not os.path.exists(ALBUM_DATA):
            ensure_file(GALLERY_CONFIG, DEFAULT_GALLERY_CONFIG)
            ensure_file(ALBUM_DATA, DEFAULT_ALBUMS_LIST)
            logger.info('Initialized gallery. You can start adding albums now.')
        else:
            logger.info('This folder already seems to be a gallery.')

    def check_config(self):
        config_file = os.path.exists(self.config_file)
        album_data = os.path.exists(self.albums_data)
        if not config_file or not album_data:
            logger.info('No gallery was initialized in this directory (%s) yet. Please initialize a gallery first.'
                        % self.base_dir)
            sys.exit(0)

    def load_config(self):
        config = ConfigParser.ConfigParser()
        config.read(self.config_file)
        self.title = config.get('gallery', 'title')
        self.theme = config.get('gallery', 'theme')

    def load_albums_from_json(self):
        with open(self.albums_data, 'rb') as albums_data_file:
            self.albums = json.loads(albums_data_file.read())

    def list_albums(self):
        if self.albums:
            logger.info('Following albums exist:')
            for album in self.albums.iterkeys():
                print album
        else:
            logger.info('No albums exist in \'%s\'', os.getcwd())

    def add_album(self, album_to_add):
        album_to_add.get_photos_to_import()
        album_to_add.import_photos()
        #album.create_zipped_version()
        self.albums[album_to_add.slug] = album_to_add.serialized_version()
        self.update_album_json_data()

    def delete_album(self, album_slug, prompt_for_delete=True):
        if album_slug in self.albums:
            if prompt_for_delete:
                choice = raw_input("Are you sure you want to delete the album '%s%s'? Y/N [N]: "
                                   % (os.path.join(os.getcwd(), album_slug), os.sep))
                choice = choice or 'N'
                if choice == 'N':
                    return
            try:
                rmtree(album_slug)
            except OSError:
                pass
            del self.albums[album_slug]
            self.update_album_json_data()
            logger.info('Deleted album named \'%s\'.' % album_slug)
        else:
            logger.error('An album named %s doesn\'t exist.' % album_slug)

    def update_album_json_data(self):
        with open(self.albums_data, 'w') as albums_data_file:
            for album_key, album in self.albums.iteritems():
                self.albums[album_key] = {
                    "base_dir": album['base_dir'],
                    "date_range": album['date_range'],
                    "description": album['description'],
                    "photos": [x for x in album['photos']],
                    "slug": album['slug'],
                    "sort_key": album['sort_key'],
                    "title": album['title'],
                    "thumbnail": album['thumbnail'],
                }
            albums_data = json.dumps(self.albums, sort_keys=True, indent=4 * ' ')
            albums_data_file.write(albums_data)

    def get_sorted_album_list(self):
        return sorted(self.albums.items(), key=lambda x: x[1]['sort_key'], reverse=True)

    def album_exists(self, slug):
        if slug in self.albums.iterkeys():
            return True
        else:
            return False

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
            html = gallery_template.render(gallery=self, albums=self.get_sorted_album_list())
            html_file.write(html.encode('utf-8'))

        # Write albums HTML
        for album in self.albums.itervalues():
            print album['title']
            print album['photos']
            album_template = Template(codecs.open(theme.album_template, 'r', 'utf8').read())
            copy(theme.album_template, os.path.join(album['slug'], 'index.html'))
            with open(os.path.join(album['slug'], 'index.html'), 'wb') as html_file:
                logger.info('Writing html file %s' % os.path.join(album['slug'], 'index.html'))
                html = album_template.render(album=album, gallery=self, timestamp=int(time.time()))
                html_file.write(html.encode('utf-8'))