#-*- coding: utf-8 -*-
import codecs
import sys
import os
import hashlib
import markdown

from slugify import slugify
from zipfile import ZipFile

from yasgg.photo import Photo
from yasgg.settings import IMAGE_FILE_EXTENSIONS_2_IMPORT
from yasgg.utils import walkdir, ensure_dir

from . import logger


class Album(object):
    ALBUM_INFO_FILE = 'info.md'

    # Visible meta data
    title = None
    slug = None
    basedir = None
    description = None
    thumbnail = None
    date_range = None  # TODO: Get date range from info file, else from exif data.

    # File handling
    import_dir = None
    photos_dir = None
    photos = {}
    zip_file = None
    assets_dir_name = 'assets'  # TODO: This should be non-relevant for the album, shouldn't it?

    # Crypto
    password = None
    password_hashed = None

    # Template
    html_file = None
    photos_for_tpl = []

    @property
    def assets_dir(self):
        return self.basedir + self.assets_dir_name + os.sep

    def __init__(self, import_dir):
        if os.path.exists(import_dir):
            self.import_dir = import_dir
        else:
            logger.error('The directory to import (%s) does not exist. No album creation is possible and I\'ve to exit' % import_dir)
            sys.exit(0)

        self.get_self_informed()

        ensure_dir(self.basedir)
        ensure_dir(self.photos_dir)

    def get_self_informed(self):
        """
        Collects all info an album can get from self.ALBUM_INFO_FILE as far as possible
        and fills the rest with fallback values.
        """

        # Look for the album info file.
        info_file = os.path.join(self.import_dir, self.ALBUM_INFO_FILE)
        if os.path.isfile(info_file):
            with codecs.open(info_file, "r", "utf-8") as f:
                text = f.read()
            md = markdown.Markdown(extensions=['meta'])
            html = md.convert(text)

            md_title = md.Meta.get('title', [''])[0]
            md_description = html
            md_thumbnail = md.Meta.get('thumbnail', [''])[0]
            md_date = md.Meta.get('date', [''])[0]
            md_password = md.Meta.get('password', [''])[0]

            # Set values from album info file
            if md_title:
                self.title = md_title
            if md_description:
                self.description = md_description
            if md_thumbnail:
                self.thumbnail = md_thumbnail
            if md_date:
                self.date_range = md_date
            if md_password:
                self.password = md_password

        # Fill with fallback values
        if not self.title:
            self.title = self.import_dir.split(os.sep).pop()

        # Create slug
        self.slug = slugify(self.title)

        # Set directories
        self.basedir = os.path.abspath('.%s%s' % (os.sep, self.slug)) + os.sep
        self.photos_dir = '%sphotos%s' % (self.basedir, os.sep)

        # Set template file
        self.html_file = '%sindex.html' % self.basedir

        # Build md5 hash of password to get len 32 key
        if self.password:
            self.password_hashed = hashlib.md5(self.password).hexdigest()

    def create_zipped_version(self):
        """
        Creates a zip of all self.photos if self is not encrypted and returns the relative path of the zip
        """

        if not self.password:
            zip_file_name = '%s%s.zip' % (self.photos_dir, self.slug)

            with ZipFile(zip_file_name, 'w') as album_zip:
                for file_name in self.photos.itervalues():
                    arc_name = file_name.split('/').pop()
                    album_zip.write(file_name, arcname=arc_name)

            # Make relative path
            self.zip_file = os.sep.join(zip_file_name.split(os.sep)[-2:])

    def import_photos(self):
        logger.info('Searching for photos in %s' % self.import_dir)
        self.photos = {}
        exif_date_for_all_photos = True
        for photo_2_import in walkdir(dir_2_walk=self.import_dir):
            extension = os.path.splitext(photo_2_import)[1][1:]
            if extension.lower() not in IMAGE_FILE_EXTENSIONS_2_IMPORT:
                continue
            photo = Photo(image_file_original=photo_2_import, album=self)
            exif_date = photo.exif_date
            if exif_date:
                self.photos[exif_date + photo_2_import] = photo_2_import
            else:
                exif_date_for_all_photos = False
                self.photos[photo_2_import] = photo_2_import

        # If there is not an exif date on all photos, use path instead
        if not exif_date_for_all_photos:
            for photo_key, photo_file in self.photos.items():
                del self.photos[photo_key]
                self.photos[photo_file] = photo_file

        for photo_key in sorted(self.photos.iterkeys()):
            logger.debug('Processing %s' % (photo_2_import))
            photo_2_import = self.photos[photo_key]
            photo = Photo(image_file_original=photo_2_import, album=self)

            # Create thumbnail and main image
            thumbnail_data = photo.create_thumbnail()
            image_file_data = photo.provide()

            # Make photo path relative
            thumbnail_data['thumbnail_file'] = os.sep.join(thumbnail_data['thumbnail_file'].split(os.sep)[-2:])
            image_file_data['file'] = os.sep.join(image_file_data['file'].split(os.sep)[-2:])

            # Merge two data dicts into one
            tpl_photo_data = dict(thumbnail_data.items() + image_file_data.items())

            self.photos_for_tpl.append(tpl_photo_data)