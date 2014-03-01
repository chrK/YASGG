#-*- coding: utf-8 -*-
import codecs
import operator
import os
import hashlib
import markdown

from dateutil import parser as dateutil_parser
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
    sort_key = None
    date_range = None

    photos = []
    html_file = None

    # File handling
    import_dir = None
    photos_dir = None
    zip_file = None
    import_list_photos = []

    # Crypto
    password = None
    password_hashed = None

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
            md_date = md.Meta.get('date', [''])[0]
            md_password = md.Meta.get('password', [''])[0]

            # Set values from album info file
            if md_title:
                self.title = md_title
            if md_description:
                self.description = md_description
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
        self.html_file = '%salbum_index.html' % self.base_dir

        # Build md5 hash of password to get len 32 key
        if self.password:
            self.password_hashed = hashlib.md5(self.password).hexdigest()

    def get_photos_to_import(self):
        logger.info('Looking for photos in %s' % self.import_dir)
        for image_file in walkdir(dir_2_walk=self.import_dir):
            image_file_extension = os.path.splitext(image_file)[1][1:]
            if image_file_extension.lower() in IMAGE_FILE_EXTENSIONS_TO_IMPORT:
                self.import_list_photos.append(image_file)

    def set_album_thumbnail(self):
        for image in self.import_list_photos:
            file_name = os.path.split(image)[1]
            if file_name.startswith('thumbnail_'):
                self.thumbnail = image
                self.import_list_photos.remove(image)
                break

        # If no explicit thumbnail was found, set first image as thumbnail.
        self.thumbnail = self.import_list_photos[0]

    def import_photos(self):
        for photo_to_import in self.import_list_photos:
            logger.debug('Processing %s' % photo_to_import)
            photo = Photo(image_file_original=photo_to_import, album=self)

            # Create thumbnail and main image
            thumbnail_data = photo.create_thumbnail()
            image_file_data = photo.provide()

            # Make photo path relative
            thumbnail_data['thumbnail_file'] = os.sep.join(thumbnail_data['thumbnail_file'].split(os.sep)[-2:])
            image_file_data['absolute_path'] = image_file_data['file']
            image_file_data['file'] = os.sep.join(image_file_data['file'].split(os.sep)[-2:])

            # Merge two data dicts into one and add to album.photos
            self.photos.append(dict(thumbnail_data.items() + image_file_data.items()))

        self._sort_photos_by_date()
        self._set_sort_key()
        self._set_date_range()

    def _sort_photos_by_date(self):
        self.photos = sorted(self.photos, key=operator.itemgetter('date'))

    def create_zipped_version(self):
        """ Creates a zip of all album photos if the album is not encrypted. """

        if not self.password:
            zip_file_name = '%s%s.zip' % (self.photos_dir, self.slug)

            with ZipFile(zip_file_name, 'w') as album_zip:
                for photo in self.photos:
                    arc_name = photo['absolute_path'].split('/').pop()
                    album_zip.write(photo['absolute_path'], arcname=arc_name)

            # Make relative path
            self.zip_file = os.sep.join(zip_file_name.split(os.sep)[-2:])

    def _set_sort_key(self):
        self.sort_key = self.first_photo_date().strftime("%Y%m%d")

    def _set_date_range(self):
        sort_date_format = "%Y-%m-%d"
        if self.first_photo_date().strftime(sort_date_format) == self.last_photo_date().strftime(sort_date_format):
            self.date_range = self.first_photo_date().strftime("%d.%m.%Y")
        else:
            date_range_format = "%d.%m.%Y"
            self.date_range = ("%s - %s" % (self.first_photo_date().strftime(date_range_format),
                                            self.last_photo_date().strftime(date_range_format)))

    @staticmethod
    def exif_date_to_datetime(exif_date):
        return dateutil_parser.parse(exif_date)

    def first_photo_date(self):
        return self.exif_date_to_datetime(self.photos[0]['date'])

    def last_photo_date(self):
        return self.exif_date_to_datetime(self.photos[-1]['date'])

    def serialized_version(self):
        serialized_album = {}
        serialized_album['title'] = self.title
        serialized_album['slug'] = self.slug
        serialized_album['base_dir'] = self.base_dir
        serialized_album['description'] = self.description
        serialized_album['thumbnail'] = self.thumbnail
        serialized_album['sort_key'] = self.sort_key
        serialized_album['date_range'] = self.date_range
        serialized_album['photos'] = self.photos
        serialized_album['html_file'] = self.html_file
        serialized_album['zip_file'] = self.zip_file
        serialized_album['password'] = self.password

        return serialized_album

