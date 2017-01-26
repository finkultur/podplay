#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import vlc
import time
import curses
import locale

from utils import *

# Init VLC player and instance
def init_player():
    global player, instance
    instance = vlc.Instance()
    player = instance.media_player_new()

# Set podcast episode and initial position
def set_ep(pod, num=0, pos_str=""):
    global player, instance
    audio_url = pod['episodes'][num]['enclosures'][0]['url']
    dur = pod['episodes'][num]['total_time']
    pos = parse_pos(pos_str, dur)

    media = instance.media_new(audio_url)
    player.set_media(media)
    player.set_position(pos)

# Wrapper for our wrapper :D
def curses_wraps(fn):
    return lambda *args: curses.wrapper(fn, *args)

# Main event loop
@curses_wraps
def cli(win, args):
    global player
    pod = get_pod(get_feed_url(args.podcast))
    ep = get_correct_ep_num(pod, args.episode)
    init_player()
    set_ep(pod, ep, args.seek)

    player.play()
    paused = False
 
    #win.nodelay(True)
    key=""
    while 1:
        win.clear()
        win.addstr(print_ep(pod, 0))
        if paused:
            win.insstr(5, 0, " ===== PAUSE =====")
        try:
            key = win.getkey()
            if str(key) == ' ':
                player.pause()
                paused = not paused
        except Exception as e:
            pass

# Main
if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, '')

    parser = argparse.ArgumentParser()
    parser.add_argument("podcast")
    parser.add_argument("-e", "--episode", type=int, default=0, help="Choose a specific episode")
    parser.add_argument("-s", "--seek", type=str, default="",
                        help="Seek to given (seconds or hh:mm:ss or percentage) position")
    parser.add_argument("-i", "--info", action="store_true",
                        help="Only print information, do not play")
    args = parser.parse_args()

    try:
        cli(args)
    except KeyboardInterrupt:
        pass

