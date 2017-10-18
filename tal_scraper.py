import urllib2
from bs4 import BeautifulSoup
import json
episode_page = 'https://www.thisamericanlife.org/radio-archives/episode/%i'
DOWNLOAD_URL = 'http://audio.thisamericanlife.org/jomamashouse/ismymamashouse/%i.mp3'
import re


def get_episode_info(episode_id):
    req = urllib2.Request(episode_page % episode_id, headers={'User-Agent' : "Magic Browser"})
    con = urllib2.urlopen( req )
    page = con.read()
    soup = BeautifulSoup(page, 'html.parser')
    episode_info = {'acts': []}

    raw_title = soup.find('h1', {'class': 'node-title'}).text.strip()
    match = re.search('(?P<number>\d+): (?P<title>.*)', raw_title)
    episode_info['number'] = int(match.group('number'))
    episode_info['title'] = match.group('title')
    episode_info['date'] = soup.find('div', {'id': 'content'}).find('div', {'class': 'date'}).text.strip()
    episode_info['subtitle'] = soup.find('div', {'class': 'description'}).text.strip()
    episode_info['media_url'] = DOWNLOAD_URL % episode_id  # CURRENTLY NOT USED...

    # Download the file to get the media url?
    # episode_info['minutes'] = DOWNLOAD_URL % episode_id
    # print soup.find('div', {'class': 'top'}).find('div', {'class': 'image'})
    if episode_id in frozenset([599, 600, 601]):
        # special case for weird one
        episode_info['image_square'] = '//files.thisamericanlife.org/vote/img/this-american-vote-01.gif'
    else:
        episode_info['image_square'] = soup.find('div', {'class': 'top'}).find('div', {'class': 'image'}).find('img')['src']
    assert episode_info['image_square'][:2] == '//'
    episode_info['image_square'] = episode_info['image_square'][2:]

    act_block = soup.find('ul', {'id': 'episode-acts'})

    # Examples: 66, 628
    whole_episode_header = soup.find('div', {'id': 'content'}).find('div', {'class': 'content'}).find('div', {'class': 'radio-header'})
    if whole_episode_header:
        act_info = {
            'header': 'Info',
            'body': str(whole_episode_header)  # whole_episode_header.text.strip()
        }
        episode_info['acts'].append(act_info)

    if episode_id in frozenset([66]):
        acts = []
    else:
        acts = act_block.find_all('li', recursive=False)

    for act in acts:
        act_info = {}

        act_head = act.find('div', {'class': 'act-head'})
        if act_head.find('h3'):
            act_info['header'] = act_head.find('h3').find('a').text.strip()
        else:
            act_info['header'] = 'Act ?'

        if act_head.find('h4'):
            act_info['subtext'] = act_head.find('h4').text.strip()

        # tags
        tags_block = act.find('span', {'class': 'tags'})
        if tags_block:
            act_info['tags'] = [x.text.strip() for x in tags_block.find_all('a')]
            # Get rid of tags before reading body
            tags_block.decompose()

        # Contributors
        contributors_block = act.find('ul', {'class': 'act-contributors'})
        if contributors_block:
            act_info['contributors'] = [x.text.strip() for x in act.find('ul', {'class': 'act-contributors'}).find_all('a')]
            # Get rid of tags before reading body
            contributors_block.decompose()

        # Songs
        songs_block = act.find('div', {'class': 'song'})
        if songs_block:
            act_info['songs'] = [x.text.strip() for x in songs_block.find('ul').find_all('li', recursive=False)]
            songs_block.decompose()

        # Read body last after decomposing other stuff

        # Minutes
        act_body_div = act.find('div', {'class': 'act-body'})

        minutes_regex = r' \((?P<minutes>\d+) minutes\)'
        act_body_html = unicode(act_body_div)
        match = re.search(minutes_regex, act_body_html)
        if match:
            # print "found match!"
            act_info['minutes'] = int(match.group('minutes'))
        act_info['body'] = re.sub(minutes_regex, '', act_body_html)  # act_body_div.text.strip()
        episode_info['acts'].append(act_info)

    return episode_info

def podcast_description(d):
    l = []
    l.append(u'%s' % d['subtitle'])
    l.append(u'')
    l.append(u'')
    for act in d['acts']:
        l.append(u'<b>%s: %s</b>' % (act['header'], act.get('subtext', '')))
        if 'minutes' in act:
            l.append(u'<i>%i minutes</i>' % act['minutes'])
        # print act['body']
        l.append(act['body'])
        #if 'contributors' in act:
        #    l[-1] += '-- %s' % (', '.join(act['contributors']))
        if 'songs' in act:
            l.append('Songs: %s' % (', '.join(act['songs'])))
        l.append(u'')
    return u'<br>'.join(l)

def pretty_str(d):
    return json.dumps(d, indent=4, sort_keys=True)
