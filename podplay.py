#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import vlc
import time
import curses
import locale
import requests_cache

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
    player.play()
    player.set_position(pos)
    player.pause()

# Creates a curses-menu where, if multiple search results, you can select which show.
# Quits program if list is empty.
# Returns index of the selected title.
# args:
#   win: curses main window
#   titles: list of titles
def select_menu(win, titles):
    win.clear()
    if len(titles) <= 0:
        win.addstr(0, 0, "Search returned no results")
        win.addstr(2, 0, "Press SPACE or Q to exit")
        while 1:
            key = str(win.getkey())
            if key == ' ' or key.lower() == "q":
                quit()

    if len(titles) == 1:
        return 0

    max_y,max_x = win.getmaxyx()
    selected = 0
    start = 0
    end = min(len(titles), max_y)
    while 1:
        win.clear()
        for i in range(start, end):
            win.addstr(i-start, 0, titles[i],
                       curses.A_NORMAL if i != selected else curses.A_BOLD)
        while 1:
            try:
                key = str(win.getkey())
                if key == ' ' or key == "KEY_ENTER":
                    return selected
                elif key == "KEY_UP" and selected > 0:
                    selected = selected-1
                    if selected < start:
                        start -= 1
                        end -= 1
                    break;
                elif key == "KEY_DOWN" and selected < len(titles)-1:
                    selected = selected+1
                    if selected >= end:
                        start += 1
                        end += 1
                    break;
                elif key.lower() == 'q':
                    quit()
            except Exception as e:
                pass

# Wrapper for our wrapper :D
def curses_wraps(fn):
    return lambda *args: curses.wrapper(fn, *args)

# Main event loop
@curses_wraps
def cli(win, args):
    global player

    pods = get_pods(args.podcast)
    pod_titles = list(pods[i]['title'] for i in range(0, len(pods)))
    pod = pods[select_menu(win, pod_titles)]
    if args.episode is not None:
        ep = get_correct_ep_num(pod, args.episode)
    else:
        ep_titles = list(pod['episodes'][i]['title'].encode("utf-8") 
                         for i in range(0, len(pod['episodes'])))
        ep = select_menu(win, ep_titles)

    dur = int(pod['episodes'][ep]['total_time'])
    ep_info = print_ep(pod, ep)

    init_player()
    set_ep(pod, ep, args.seek)
    player.play()
    paused = False

    win.keypad(1)
    win.timeout(500) # Timeout for getkey() in ms
    while 1:
        win.clear()
        win.addstr(ep_info)
        win.addstr(5,0, progress_bar(player.get_time()/1000, dur))
        if paused:
            win.insstr(6, 0, " ===== PAUSE =====")
        try:
            key = str(win.getkey())
            if key == ' ':
                player.pause()
                paused = not paused
            if key == "KEY_UP":
                player.set_time(player.get_time()+60*1000)
            elif key == "KEY_DOWN":
                player.set_time(player.get_time()-60*1000)
            elif key == "KEY_LEFT":
                player.set_time(player.get_time()-10*1000)
            elif key == "KEY_RIGHT":
                player.set_time(player.get_time()+10*1000)
            elif key.lower() == 'q':
                break
        except Exception as e:
            pass

# Main
if __name__ == "__main__":
    locale.setlocale(locale.LC_ALL, '')
    requests_cache.install_cache('itunes_search_cache')

    parser = argparse.ArgumentParser()
    parser.add_argument("podcast", nargs='+')
    parser.add_argument("-e", "--episode", type=int, default=None,
                        help="Choose a specific episode")
    parser.add_argument("-s", "--seek", type=str, default="",
                        help="Seek to given (seconds or hh:mm:ss or percentage) position")
    args = parser.parse_args()

    try:
        cli(args)
    except KeyboardInterrupt:
        pass

