#-*- coding: utf-8 -*-
import codecs
import sys
import os
import hashlib
import markdown

from slugify import slugify
from zipfile import ZipFile

from yasgg.photo import Photo
from yasgg.settings import IMAGE_FILE_EXTENSIONS_TO_IMPORT
from yasgg.utils import walkdir, ensure_dir

from . import logger


class Album(object):
    ALBUM_INFO_FILE = 'info.md'

    # Visible meta data
    title = None
    slug = None
    base_dir = None
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
    photos_for_tpl = []

    @property
    def assets_dir(self):
        return self.base_dir + self.assets_dir_name + os.sep

    def __init__(self, import_dir):
        self.import_dir = import_dir
        self.get_self_informed()

        ensure_dir(self.base_dir)
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
        self.base_dir = os.path.abspath('.%s%s' % (os.sep, self.slug)) + os.sep
        self.photos_dir = '%sphotos%s' % (self.base_dir, os.sep)

        # Set template file
        self.html_file = '%sindex.html' % self.base_dir

        # Build md5 hash of password to get len 32 key
        if self.password:
            self.password_hashed = hashlib.md5(self.password).hexdigest()

    def import_photos(self):
        logger.info('Looking for photos in %s' % self.import_dir)
        self.photos = {}
        exif_date_for_all_photos = True
        for photo_to_import in walkdir(dir_2_walk=self.import_dir):
            extension = os.path.splitext(photo_to_import)[1][1:]
            if extension.lower() not in IMAGE_FILE_EXTENSIONS_TO_IMPORT:
                continue
            photo = Photo(image_file_original=photo_to_import, album=self)
            exif_date = photo.exif_date
            if exif_date:
                self.photos[exif_date + photo_to_import] = photo_to_import
            else:
                exif_date_for_all_photos = False
                self.photos[photo_to_import] = photo_to_import

        # If there is not an exif date on all photos, use path instead
        if not exif_date_for_all_photos:
            for photo_key, photo_file in self.photos.items():
                del self.photos[photo_key]
                self.photos[photo_file] = photo_file

        i = 1
        self.photos_for_tpl = []
        for photo_key in sorted(self.photos.iterkeys()):
            photo_to_import = self.photos[photo_key]
            logger.debug('Processing %s' % photo_to_import)
            photo = Photo(image_file_original=photo_to_import, album=self)

            # Create thumbnail and main image
            thumbnail_data = photo.create_thumbnail()
            image_file_data = photo.provide()

            # Make photo path relative
            thumbnail_data['thumbnail_file'] = os.sep.join(thumbnail_data['thumbnail_file'].split(os.sep)[-2:])
            image_file_data['file'] = os.sep.join(image_file_data['file'].split(os.sep)[-2:])

            # Set thumbnail if necessary
            if i == 1 and not self.thumbnail:
                self.thumbnail = os.path.join(self.slug, thumbnail_data['thumbnail_file'])

            # Merge two data dicts into one
            tpl_photo_data = dict(thumbnail_data.items() + image_file_data.items())

            self.photos_for_tpl.append(tpl_photo_data)
            i += 1

    def create_zipped_version(self):
        """ Creates a zip of all album photos if the album is not encrypted. """

        if not self.password:
            zip_file_name = '%s%s.zip' % (self.photos_dir, self.slug)

            with ZipFile(zip_file_name, 'w') as album_zip:
                for file_name in self.photos.itervalues():
                    arc_name = file_name.split('/').pop()
                    album_zip.write(file_name, arcname=arc_name)

            # Make relative path
            self.zip_file = os.sep.join(zip_file_name.split(os.sep)[-2:])