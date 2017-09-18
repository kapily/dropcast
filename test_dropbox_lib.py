
from dropbox_lib import DropboxSharedLinkFetcher


def test_file_paths():
    assert DropboxSharedLinkFetcher._path_to_folder_list('/a/b/c/d.txt') == ['a', 'b', 'c']
    assert DropboxSharedLinkFetcher._path_to_folder_list('a/b/c/d.txt') == ['a', 'b', 'c']
    assert DropboxSharedLinkFetcher._path_to_folder_list('/a/b/c/d/') == ['a', 'b', 'c', 'd']
    assert DropboxSharedLinkFetcher._path_to_folder_list('/a/b/c/d') == ['a', 'b', 'c', 'd']
    assert DropboxSharedLinkFetcher._path_to_folder_list('a/b/c/d/') == ['a', 'b', 'c', 'd']
    assert DropboxSharedLinkFetcher._path_to_folder_list('a/b/c/d') == ['a', 'b', 'c', 'd']
    assert DropboxSharedLinkFetcher._path_to_folder_list('') == []
    assert DropboxSharedLinkFetcher._path_to_folder_list('/') == []

