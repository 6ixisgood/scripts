#!/usr/bin/python3
import sys, os
import requests
import re
import json
from mutagen.mp3 import MP3
from mutagen.id3 import ID3NoHeaderError, APIC, TIT2, TPE1


class Ripper:
    def __init__(self, song_url):
        self.song_url = song_url
        self.client_id = None
        self.json_data = None
        self.mp3_data = None

    def get_client_id(self):
        if self.client_id is None:
            widget_url = "https://w.soundcloud.com/player/?url="

            # get the page for the song's widget
            widget_response = requests.get(widget_url+self.song_url)
            widget_response_text = widget_response.text
            # find the url that will get you the client ID
            client_id_url = re.findall(r'https://widget.sndcdn.com/widget[^"]*', widget_response_text)[2]
            # get that new page .js file from the link above
            client_id_response = requests.get(client_id_url)
            client_id_response_text = client_id_response.text
            # search for the client ID
            client_id_long = re.findall(r'client_id:u\?[^,]*', client_id_response_text)[0]
            # split on the :" characters and take second half, then trim off end
            self.client_id = client_id_long.split(":\"")[1][:-1]

        return self.client_id

    # get the json info about the song by using the api with client id generated
    def get_json_data(self, count=0):
        if self.json_data is None:
            url = "https://api-widget.soundcloud.com/resolve?url=" + \
                  self.song_url+"&format=json&client_id=" + self.get_client_id() + "&app_version=1586353690"
            res = requests.get(url) 
            res_json = res.json()
            if (res.status_code == 403 or len(res_json) == 0) and count <=5:
                # don't know what's going on here. Just keep retrying
                return self.get_json_data(count+1) 
            self.json_data = res_json

        return self.json_data

    def get_mp3_data(self, f, count=0):
        if self.mp3_data is None:

            # first get the request playlist url
            playlist_request_url = self.get_json_data()['media']['transcodings'][0]['url']
            # now get the playlist link
            get_playlist_url = f"{playlist_request_url}?client_id={self.get_client_id()}"
            get_playlist_url_res = requests.get(get_playlist_url)
            if (get_playlist_url_res.status_code == 403 or len(get_playlist_url_res.json()) == 0) and count <=15:
                # just retry this becaue I don't know what's going on 
                return self.get_mp3_data(f, count+1)
            playlist_url = get_playlist_url_res.json()['url']
            # download the pl   aylist file and parse it for the mp3 file link
            playlist_text = requests.get(playlist_url).text
            endbit = str(16*self.get_json_data()['full_duration'])
            mp3_urls = re.findall(".*https://cf-hls-media.sndcdn.com/media/[^\n]*", playlist_text)
            for u in mp3_urls:
                content = requests.get(u).content
                f.write(content)
            #mp3_url = re.sub(r'(.*/media/\d+/\d+)/\d+/(.*)', r'\1/{end}/\2'.format(end=endbit), mp3_url)

            #self.mp3_data = requests.get(mp3_url).content

        return f


def main(url, directory="."):
    print(url, directory)
    # slice off the trailing slash
    directory = directory[:-1] if (directory[-1] == '/') else directory
    # find out if path is relative or not
    if directory[0:1] == '..':
        directory = '{}/{}'.format(os.getcwd(), directory)
    elif directory[0] == '.':
        directory = '{}{}'.format(os.getcwd(), directory[1:] if len(directory) > 1 else '')

    # # get necessary mp3 info
    r = Ripper(url)
    #mp3_data = r.get_mp3_data()
    artist = r.get_json_data()['user']['username']
    title = r.get_json_data()['title']
    title_filename = title.replace(' ', '-')
    filename = "{}/{}-{}.mp3".format(directory, title_filename, artist)
    # write to file
    with open(filename, "wb+") as f:
        r.get_mp3_data(f)
        #f.write(mp3_data)

    # get album cover
    artwork_url = r.get_json_data()['artwork_url']
    if (artwork_url is not None):
        cover = requests.get(artwork_url.replace("-large", "-t500x500")).content

    # edit mp3 tags
    mp3 = MP3(filename)
    try:
        mp3.add_tags()
    except ID3NoHeaderError:
        pass

    mp3.tags.add(TIT2(text=title))
    mp3.tags.add(TPE1(text=artist))
    if (artwork_url is not None):
        mp3.tags.add(
            APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc=u'Cover',
                data=cover
            )
    )
    mp3.save()


if __name__ == '__main__':
    if len(sys.argv) > 2:
        main(sys.argv[1], sys.argv[2])
    elif len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        print("Usage: sc-ripper.py url dir")
