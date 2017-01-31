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
    player.play()
    player.set_position(pos)
    player.pause()

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

# Creates a curses-menu where, if multiple search results, you can select which show.
# Quits program if hits is empty.
# args:
#   win: curses main window
#   hits: list of parsed pod-dicts
def select_pod(win, hits):
    win.clear()
    if len(hits) <= 0:
        win.addstr(0, 0, "Search returned no results")
        win.addstr(2, 0, "Press SPACE or Q to exit")
        while 1:
            key = str(win.getkey())
            if key == ' ' or key.lower() == "q":
                quit()

    if len(hits) == 1:
        return hits[0]

    selected = 0
    while 1:
        for i in range(0, len(hits)):
            win.addstr(i, 0, hits[i]['title'],
                       curses.A_NORMAL if i != selected else curses.A_BOLD)
        key = ""
        try:
            key = str(win.getkey())
            if key == ' ' or key == "KEY_ENTER":
                return hits[selected]
            elif key == "KEY_UP" and selected > 0:
                selected = selected-1
            elif key == "KEY_DOWN" and selected < len(hits):
                selected = selected+1
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

    pod = select_pod(win, get_pods(args.podcast))
    ep = get_correct_ep_num(pod, args.episode)
    dur = int(pod['episodes'][ep]['total_time'])
    ep_info = print_ep(pod, ep)

    init_player()
    set_ep(pod, ep, args.seek)

    player.play()
    paused = False

    win.keypad(1)
    win.timeout(500)
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

