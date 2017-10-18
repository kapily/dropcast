"""
Flags:
--path: the path where the file is

"""

import gflags
import sys

import urllib2
import os
import taglib
import json
from tal_scraper import get_episode_info, podcast_description
from dateutil import parser
import copy

FLAGS = gflags.FLAGS
gflags.DEFINE_string('dir', None, 'Directory to download into')

DESCRIPTION_URL = 'http://api.thisamericanlife.co/%i'
DESCRIPTION_URL_BACKUP = 'http://api.thisamericanlife.co/q?q=%i'
DOWNLOAD_URL = 'http://audio.thisamericanlife.org/jomamashouse/ismymamashouse/%i.mp3'
DOWNLOAD_URL_BACKUP = 'http://assets.thisamericanlife.co/podcasts/%i.mp3'
MAX_EPISODE_NUMBER = 2000


def main(argv):
    FLAGS(argv)
    # Check if the file exists
    for episode_number in range(1, MAX_EPISODE_NUMBER):
        # check if
        json_filename = '%s.json' % episode_number
        json_filepath = os.path.join(FLAGS.dir, json_filename)
        if not os.path.isfile(json_filepath):
            # download
            with open(json_filepath, 'w') as f:
                json.dump(get_episode_info(episode_number), f)
        with open(json_filepath, 'r') as json_file:
            episode = json.load(json_file)
        assert episode['number'] == episode_number

        mp3_filename = '%s.mp3' % episode_number
        image_filename = '%s.jpg' % episode_number
        mp3_filepath = os.path.join(FLAGS.dir, mp3_filename)
        image_filepath = os.path.join(FLAGS.dir, image_filename)

        # Only download image once
        if not os.path.isfile(mp3_filepath):
            try:
                mp3file = urllib2.urlopen(DOWNLOAD_URL % episode_number)
            except urllib2.HTTPError:
                mp3file = urllib2.urlopen(DOWNLOAD_URL_BACKUP % episode_number)
            with open(mp3_filepath, 'wb') as output:
                output.write(mp3file.read())

        if not os.path.isfile(image_filepath):
            imagefile = urllib2.urlopen(episode['image_square'])
            with open(image_filepath, 'wb') as output:
                output.write(imagefile.read())

        # Write the description into the file
        song = taglib.File(mp3_filepath)
        old_tags = copy.deepcopy(song.tags)
        song.tags['TRACKNUMBER'] = [unicode(episode['number'])]
        song.tags['TITLE'] = ['#%i: ' % episode_number + episode['title']]
        song.tags['COMMENT'] = [episode['subtitle']]
        song.tags['PODCASTDESC'] = [podcast_description(episode)]
        song.tags['RELEASEDATE'] = [unicode(parser.parse(episode['date']).strftime('%Y-%m-%d') + 'T12:00:00Z')]
        if old_tags != song.tags:  # only save if we need to write
            assert song.save() == {}


if __name__ == '__main__':
    main(sys.argv)
