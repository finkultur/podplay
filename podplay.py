#!/usr/bin/env python
import sys
import argparse
import datetime
import requests
import urllib
import podcastparser
import vlc
import time

import pprint

ITUNES_URL = "https://itunes.apple.com/search"

# Returns the feed url using the itunes search api. Simply takes the first hit.
def get_feed_url(search_str):
    payload = {'term': search_str, 'media': 'podcast'}
    r = requests.get(ITUNES_URL, params=payload)
    return r.json()['results'][0]['feedUrl']

# Parses a feed_url to a dict
def get_pod(feed_url):
    return podcastparser.parse(feed_url, urllib.urlopen(feed_url))

# Pretty prints episode information
def print_ep(pod, num=0):
    num_eps = len(pod['episodes'])
    ep = pod['episodes'][num]
    time = ep['total_time'] / 60
    date = datetime.datetime.fromtimestamp(int(
            ep['published'])
           ).strftime("%Y-%m-%d %H:%M:%S")
    print(pod['title'])
    print(ep['title'])
    if (ep['description'] != ""): print(ep['description'])
    print(date)
    print(str(time) + " minutes")

# Simply plays an episode
# TODO: Implement pause
def play_ep(pod, num=0, pos_str=""):
    audio_url = pod['episodes'][num]['enclosures'][0]['url']
    dur = pod['episodes'][num]['total_time']
    pos = parse_pos(pos_str, dur)
    if pos >= 1.0: return

    instance = vlc.Instance()
    player = instance.media_player_new()
    media = instance.media_new(audio_url)
    player.set_media(media)
    # Apparently VLC wont seek to position if we do not play, pause, set & play
    player.play()
    player.pause()
    player.set_position(pos)
    player.play()
    time.sleep(dur-pos*dur)

# Parses a position string to a float. Input may be:
# A percentage such as "12%"
# A time such as "hh:mm:ss" or "m:ss"
# A number of seconds such as "123"
def parse_pos(pos_str, total_dur):
    pos = 0.0
    # If given a percentage
    if pos_str.endswith('%'):
        try:
            return float(pos_str.strip('%'))/100
        except ValueError:
            print("Invalid input, starting podcast from beginning")
            return 0.0
    # If given a string such as hh:mm:ss or m:ss, calculate total seconds
    elif ':' in pos_str:
        try:
            # hh:mm:ss to seconds
            for s in pos_str.split(':'):
                pos = pos*60 + int(s)
        except ValueError:
            print("Invalid input, starting podcast from beginning")
            return 0.0
    # Convert seconds to percentage
    return float(pos)/total_dur



# Since all feeds are latest first, this is done
# -x = x:th latest
# 0 = latest released
# x = x:th episode
def get_correct_ep_num(pod, num):
    if num == 0: return 0
    num_eps = len(pod['episodes'])
    if num > 0: return num_eps-num
    if num < 0: return abs(num)
 
# Usage:
# podplay "string": Play latest episode of first hit
# podplay -ep <x> "string": Play x:th episode
# podplay -ep <-x> "string": Play x:th latest episode
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("podcast")
    parser.add_argument("-e", "--episode", type=int, default=0, help="Choose a specific episode")
    parser.add_argument("-s", "--seek", type=str, default="",
                        help="Seek to given (seconds or hh:mm:ss or percentage) position")
    parser.add_argument("-i", "--info", action="store_true",
                        help="Only print information, do not play")
    args = parser.parse_args()

    pod = get_pod(get_feed_url(args.podcast))
    ep = get_correct_ep_num(pod, args.episode)
    print_ep(pod, ep)
    if not args.info:
        play_ep(pod, ep, args.seek)

