
import re
import os
import urllib
from collections import namedtuple

DropboxLink = namedtuple('DropboxLink', ['shmodel_token', 'file_id', 'file_path', 'file_path_url_encoded', 'is_dir', 'view_url', 'download_url'])

DROPBOX_VIEW_URL = 'https://www.dropbox.com/sh/%s/%s/%s?dl=0'
DROPBOX_DOWNLOAD_URL = 'https://www.dropbox.com/sh/%s/%s/%s?dl=1'
DROPBOX_DIRECT_DOWNLOAD_URL = 'https://dl.dropboxusercontent.com/sh/%s/%s/%s?dl=1'
REGEX = 'https://www.dropbox.com/sh/(?P<shmodel_token>[^/]+)/(?P<file_id>[^/]+)/(?P<file_path>\S+)\?dl=0'


class DropboxSharedLinkFetcher(object):

    def __init__(self, base_url):
        self.cache = {}
        self.base_url = base_url

    @staticmethod
    def get_dropbox_links_in_webpage(url):
        print "about to fetch URL: ", url
        assert isinstance(url, basestring)
        opener = urllib.FancyURLopener({})
        f = opener.open(url)
        content = f.read()
        results = re.findall(REGEX, content)
        results = list(set(results))
        final_results = []
        for result in results:
            shmodel_token = result[0]
            file_id = result[1]
            file_path_url_encoded = result[2]

            original_filpath = urllib.unquote(file_path_url_encoded)
            # note, we expect all non-directories to have a . in their name
            # this assumption may break things
            is_dir = '.' not in original_filpath
            view_url = DROPBOX_VIEW_URL % (shmodel_token, file_id, file_path_url_encoded)
            download_url = DROPBOX_DOWNLOAD_URL % (shmodel_token, file_id, file_path_url_encoded)
            direct_download_url = DROPBOX_DIRECT_DOWNLOAD_URL % (shmodel_token, file_id, file_path_url_encoded)
            final_results.append(DropboxLink(shmodel_token, file_id, original_filpath, file_path_url_encoded, is_dir, view_url, download_url, direct_download_url))
        return final_results

    @staticmethod
    def _get_file_link(dropbox_links, file_path):
        """Given a list of DropboxSharedLinks, return the one with the given filename"""
        for link in dropbox_links:
            if link.file_path == file_path:
                return link
        #print "filename: ", file_path
        #print dropbox_links
        raise Exception('Could not find link for filename: ' + file_path)

    def url_for_file(self, relative_path):
        """Dropbox Shared Link URL for file with path (relative to folder link in self.base_url)"""
        #filename = os.path.basename(relative_path)
        #assert '.' in filename  # files have extensions

        current_folder_links = self._links_in_dropbox_shared_folder(relative_path)
        return self._get_file_link(current_folder_links, relative_path)

    def lookup_cached(self, key_, url):
        if key_ not in self.cache:
            self.cache[key_] = self.get_dropbox_links_in_webpage(url)
        return self.cache[key_]

    def _links_in_dropbox_shared_folder(self, path):
        assert path != ''
        # print "trying to find shared links for: ", path
        # Returns links to all files in a Dropbox shared folder
        if path in self.cache:
            return self.cache[path]

        last_folder_links = self.lookup_cached('', self.base_url)

        folders = self._path_to_folder_list(path)
        for idx, folder_name in enumerate(folders):

            # full path to current folder
            current_folders = folders[:idx+1]
            current_path = os.path.join(*current_folders)

            # get the URL of the file we're looking for
            dropbox_link = self._get_file_link(last_folder_links, current_path)
            last_folder_links = self.lookup_cached(current_path, dropbox_link.view_url)

        return last_folder_links

    @staticmethod
    def _path_to_folder_list(path):
        # Examples:
        # (/a/b/c/d.txt) => (d.txt, [a, b, c])
        # (/a/b/c/d) => (None, [a, b, c, d])
        # should terminate with a file, not a folder

        folders = []
        while 1:
            path, path_tail = os.path.split(path)
            # NOTE: we're making the assumption that . does not show up in folder names
            if '.' not in path_tail and path_tail != '':
                folders.append(path_tail)
            if path == '' or path == '/':
                # we're done here
                break
        folders.reverse()
        return folders
