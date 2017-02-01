# -*- coding: utf-8 -*-

import requests
import urllib
import podcastparser
import datetime

ITUNES_URL = "https://itunes.apple.com/search"

# Returns a list of parsed pod-dicts by using the iTunes Search API.
def get_pods(search_str):
    payload = {'term': search_str, 'media': 'podcast'}
    r = requests.get(ITUNES_URL, params=payload)
    pods = []
    for p in r.json()['results']:
        feed_url = p['feedUrl']
        pods.append(podcastparser.parse(feed_url, urllib.urlopen(feed_url)))
    return pods

# Pretty prints episode information
def print_ep(pod, num=0):
    num_eps = len(pod['episodes'])
    ep = pod['episodes'][num]
    time = ep['total_time'] / 60
    date = datetime.datetime.fromtimestamp(int(
            ep['published'])
           ).strftime("%Y-%m-%d %H:%M:%S")

    string = pod['title'].encode("utf-8") + '\n'
    string = ep['title'].encode("utf-8") + '\n'
    if (ep['description'] != ""):
        string += ep['description'].encode("utf-8")[:79] + '\n'
    string += date + '\n'
    string += str(time) + " minutes"
    return string

# Returns a very pretty progress bar given current time and total time
# Looks kinda like this "[XXXXXXXX____________________________] 0:20:05 / 1:02:45
def progress_bar(time, total_time):
    ratio = time / float(total_time)
    m, s = divmod(time, 60)
    h, m = divmod(m, 60)
    hr_time = "%d:%02d:%02d" % (h, m, s)
    m, s = divmod(total_time, 60)
    h, m = divmod(m, 60)
    hr_total = "%d:%02d:%02d" % (h, m, s)
    return '[' + 'X'*int(50*ratio) + '_'*int(50-50*ratio) + '] ' + hr_time + ' / ' + hr_total

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

