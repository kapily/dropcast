"""
Flags:
--path: the path where the file is

"""

import gflags
import json
import os
import re
import sys
import taglib
import pytz
from datetime import datetime, timedelta
from dateutil import parser
from lxml import etree

from podgen import Podcast, Episode, Media
from dropbox_lib import DropboxSharedLinkFetcher

IMAGE_FILES = frozenset(['.jpg', '.jpeg', '.png', '.gif'])
AUDIO_FILES = frozenset(['.mp3', '.m4a', '.ogg'])
CONFIG_FILE = 'config.json'

FLAGS = gflags.FLAGS
GLOBAL_CONFIG_FILE_NAME = 'global_config.json'
GLOBAL_CONFIG = None

gflags.DEFINE_string('dir', None, 'Directory with folders of podcasts')

# NOTE:

SHARED_LINK_FETCHER = None


def get_direct_download_url(relative_file_path):
    return SHARED_LINK_FETCHER.url_for_file(relative_file_path).direct_download_url

def get_download_url(relative_file_path):
    return SHARED_LINK_FETCHER.url_for_file(relative_file_path).download_url

def get_image_download_url(relative_file_path):
    p = get_download_url(relative_file_path)
    print "original download url: ", p
    return p


"""
class CutomEpisode(Episode):
    def rss_entry(self):
        entry = super(Episode, self).rss_entry()
        itunes_summary = etree.SubElement(entry, 'itunes:summary')
"""

class Track(object):
    def __init__(self, relative_path, song, image_url=None):
        # {u'TRACKNUMBER': [u'1/17'], u'COMPILATION': [u'0'], u'TITLE': [u'Introduction'],
        #  u'ARTIST': [u'Andrew Weil, MD & Rubin Naiman, PhD']}
        tags = song.tags
        self.full_path = os.path.join(FLAGS.dir, relative_path)
        self.file_name = os.path.basename(relative_path)
        self.relative_path = relative_path
        if 'TRACKNUMBER' in tags:
            self.track_number = int(tags['TRACKNUMBER'][0].split('/')[0])
        else:
            self.track_number = 1  # by default, if only one file, we'll set it to 1. We check for dups later, so it's ok
        # Use file name instead of title if title doesn't exist, but that
        # probably never happens
        if 'TITLE' in tags:
            self.title = tags['TITLE']
            self.title = self.title[0]
        else:
            self.title = self.file_name.split('.')[0]
        if 'ARTIST' in tags:
            self.artist = tags.get('ARTIST')[0]

        self.subtitle = tags.get('COMMENT')
        if self.subtitle:
            self.subtitle = self.subtitle[0]

        # PODCASTDESC - optional, full description
        self.summary = self.subtitle
        if tags.get('PODCASTDESC'):
            self.summary = tags.get('PODCASTDESC')[0]

        self.image_url = image_url

        # date of the podcast
        date = None
        if 'RELEASEDATE' in tags:
            date = tags.get('RELEASEDATE')[0]

        self.publication_date = None
        if date:
            self.publication_date = parser.parse(date)

        self.duration_seconds = song.length

    def get_episode(self):
        media = Media(get_download_url(self.relative_path), os.path.getsize(self.full_path), duration=timedelta(seconds=self.duration_seconds))
        return Episode(title=self.title, media=media, summary=self.summary, explicit=False,
                       image=self.image_url, publication_date=self.publication_date, subtitle=self.subtitle)

def main(argv):
    FLAGS(argv)
    global GLOBAL_CONFIG
    GLOBAL_CONFIG = json.loads(open(os.path.join(FLAGS.dir, GLOBAL_CONFIG_FILE_NAME)).read())
    print GLOBAL_CONFIG
    global SHARED_LINK_FETCHER
    SHARED_LINK_FETCHER = DropboxSharedLinkFetcher(GLOBAL_CONFIG['dropbox_link'])

    for dir_, dirs, file_names in os.walk(FLAGS.dir):
        current_folder_name = os.path.basename(os.path.normpath(dir_))
        # We only process files if they contain at least one audio file
        has_audio = False
        for fname in file_names:
            for audio_ext in AUDIO_FILES:
                if fname.endswith(audio_ext):
                    has_audio = True

        # Process if it has an audio file
        if has_audio:
            relative_path = os.path.relpath(dir_, FLAGS.dir)
            print "---------------------------------------------------"
            print "Creating Podcast for path: ", relative_path

            # Read params from config file if it exists
            title = current_folder_name
            description = None
            config_file_path = os.path.join(dir_, CONFIG_FILE)
            if os.path.isfile(config_file_path):
                config = json.loads(open(config_file_path).read())
                if 'title' in config:
                    title = config['title']
                if 'description' in config:
                    description = config['description']

            if not description:
                description = 'No description provided.'

            # Create a podcast here
            p = Podcast(
                name=title, description=description, explicit=False, website='http://google.com',
                withhold_from_itunes=True)

            audio_files = []

            # Get all files needed for the podcast
            for file_name in file_names:
                filename_without_extension = os.path.splitext(file_name)[0]
                relative_file_path = os.path.join(relative_path, file_name)
                full_path = os.path.join(dir_, file_name)
                full_path_without_extension, file_extension = os.path.splitext(full_path)
                if file_extension in AUDIO_FILES:
                    print "Adding episode: ", relative_file_path
                    # add it
                    # print mutagen.File(full_path)

                    # Check to see if there's a corresponding image file
                    image_url = None
                    relative_image_path = None
                    png_file_name = filename_without_extension + '.png'
                    jpg_file_name = filename_without_extension + '.jpg'
                    png_path = os.path.join(dir_, png_file_name)
                    jpg_path = os.path.join(dir_, jpg_file_name)
                    if os.path.isfile(png_path):
                        relative_image_path = os.path.join(
                            relative_path, png_file_name)
                    if os.path.isfile(jpg_path):
                        relative_image_path = os.path.join(
                            relative_path, jpg_file_name)
                    if relative_image_path:
                        image_url = get_image_download_url(relative_image_path)
                    audio_files.append(Track(
                        relative_file_path, taglib.File(full_path), image_url=image_url))
                elif file_extension in IMAGE_FILES and filename_without_extension == 'podcast':
                    # image for the podcast should be named podcast.jpg
                    # this mean your audio files should not be named "podcast.mp3"
                    # if you have per-episode images
                    p.image = get_image_download_url(relative_file_path)

            # sort the tracks we found by their track number
            audio_files.sort(key=lambda x: x.track_number)

            # ensure that we don't have duplicate track numbers
            track_numbers = [x.track_number for x in audio_files]
            assert len(set(track_numbers)) == len(track_numbers)

            # Commented out check below because sometimes we have only a few tracks available
            #for i in range(0, len(audio_files)):
            #    assert audio_files[i].track_number == i + 1, "Error with podcast: " + relative_path

            # add episodes
            current_date_time = datetime(2016, 12, 31, 12, 0, tzinfo=pytz.utc)
            position = 1
            for audio_file in audio_files:
                episode = audio_file.get_episode()
                episode.position = position
                position += 1
                if episode.publication_date is None:
                    episode.publication_date = current_date_time

                # We do this so that episodes appear in order
                current_date_time -= timedelta(days=1)
                p.episodes.append(episode)

            # We only write the file if there are any changes to not spam the Dropbox recent
            # files section

            # write the file if there are any changes
            rss_path = os.path.join(dir_, 'feed.rss')
            old_rss_file_contents_date_removed = None
            if os.path.exists(rss_path):
                old_rss_file_contents = open(rss_path, 'r').read()
                old_rss_file_contents_date_removed = re.sub(r'<lastBuildDate>.*</lastBuildDate>', '', old_rss_file_contents)
            new_rss_file_contents = unicode(p).encode('utf8')
            new_rss_file_contents_date_removed = re.sub(r'<lastBuildDate>.*</lastBuildDate>', '', new_rss_file_contents)
            if old_rss_file_contents_date_removed != new_rss_file_contents_date_removed:
                with open(rss_path, 'wb') as w:
                    w.write(new_rss_file_contents)
            feed_relative_path = os.path.join(relative_path, 'feed.rss')

            # Write Readme file if there are any changes
            readme_path = os.path.join(dir_, 'README.txt')
            old_readme_file_contents = None
            if os.path.exists(readme_path):
                old_readme_file_contents = open(readme_path, 'r').read()
            new_readme_file_contents = 'You can find the feed for your podcast here:\n\n%s\n' % get_download_url(feed_relative_path)
            new_readme_file_contents += '\n\nOtherwise, try this link:\n\n%s' % get_direct_download_url(feed_relative_path)

            if old_readme_file_contents != new_readme_file_contents:
                with open(readme_path, 'wb') as w:
                    # We use a try/except here because there's a race condition here the first time you
                    # run this because the .rss file doesn't exist in Dropbox at this point. So on the
                    # first run, we won't write the feed.rss file (or any number of runs until the
                    # .rss files are synced)
                    try:
                        w.write(new_readme_file_contents)
                    except:
                        pass


if __name__ == '__main__':
    main(sys.argv)
