#!/usr/bin/env python
import sys
import argparse
import datetime
import requests
import urllib
import podcastparser
import vlc

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
def play_ep(pod, num=0):
    mp3 = pod['episodes'][num]['enclosures'][0]['url']
    p = vlc.MediaPlayer(mp3)
    p.play()
    while True:
        continue

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
    parser.add_argument("-i", "--info", action="store_true",
                        help="Only print information, do not play")
    args = parser.parse_args()

    pod = get_pod(get_feed_url(args.podcast))
    ep = get_correct_ep_num(pod, args.episode)
    print_ep(pod, ep)
    if not args.info:
        play_ep(pod, ep)

