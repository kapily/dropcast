"""
Flags:
--path: the path where the file is

"""

import gflags
import json
import os
import sys
import taglib
import pytz
from datetime import datetime, timedelta

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

class Track(object):
    def __init__(self, relative_path, tags):
        # {u'TRACKNUMBER': [u'1/17'], u'COMPILATION': [u'0'], u'TITLE': [u'Introduction'],
        #  u'ARTIST': [u'Andrew Weil, MD & Rubin Naiman, PhD']}
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
            self.title = self.file_name
        if 'ARTIST' in tags:
            self.artist = tags.get('ARTIST')[0]
        self.description = tags.get('COMMENT')
        if self.description:
            self.description = self.description[0]

    def get_episode(self):
        media = Media(get_download_url(self.relative_path), os.path.getsize(self.full_path))
        return Episode(title=self.title, media=media, summary=self.description, explicit=False)

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
            config_file_path = os.path.join(dir_, CONFIG_FILE)
            if os.path.isfile('config_file_path'):
                config = json.loads(open(config_file_path).read())
                title = config['title']
                description = config.get('description')
            else:
                title = current_folder_name
                description = None

            if not description:
                description = 'No description provided.'

            # Create a podcast here
            p = Podcast(name=title, description=description, explicit=False, website='http://google.com', withhold_from_itunes=True)

            audio_files = []

            # Get all files needed for the podcast
            for file_name in file_names:
                relative_file_path = os.path.join(relative_path, file_name)
                full_path = os.path.join(dir_, file_name)
                filename, file_extension = os.path.splitext(full_path)
                if file_extension in AUDIO_FILES:
                    print "Adding episode: ", relative_file_path
                    # add it
                    # print mutagen.File(full_path)
                    audio_files.append(Track(relative_file_path, taglib.File(full_path).tags))
                elif file_extension in IMAGE_FILES:
                    # NOTE: this means that if we have more than one image in a directory, we use
                    # the last one we encounter
                    print "Adding image: ", relative_file_path
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
            current_date_time = datetime(2016, 12, 31, 0, 0, tzinfo=pytz.utc)
            position = 1
            for audio_file in audio_files:
                episode = audio_file.get_episode()
                episode.position = position
                position += 1
                episode.publication_date = current_date_time
                # We do this so that episodes appear in order
                current_date_time -= timedelta(days=1)
                p.episodes.append(episode)


            # write the file
            with open(os.path.join(dir_, 'feed.rss'), 'wb') as w:
                rss = str(p)
                w.write(rss)

            feed_relative_path = os.path.join(relative_path, 'feed.rss')
            with open(os.path.join(dir_, 'README.txt'), 'wb') as w:
                # We use a try/except here because there's a race condition here the first time you
                # run this because the .rss file doesn't exist in Dropbox at this point. So on the
                # first run, we won't write the feed.rss file (or any number of runs until the
                # .rss files are synced)
                try:
                    text = 'You can find the feed for your podcast here:\n\n%s\n' % get_download_url(feed_relative_path)
                    w.write(text)
                    w.write('\n\nOtherwise, try this link:\n\n%s' % get_direct_download_url(feed_relative_path))
                except:
                    pass


if __name__ == '__main__':
    main(sys.argv)
