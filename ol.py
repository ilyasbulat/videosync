import json, requests

from os import listdir
from os.path import isfile, join

import glob

import urllib2

import sys
import os

import socket as sk

import hashlib

import datetime

from shutil import copyfile

try:
    from kodi.xbmcclient import *
except:
    sys.path.append(os.path.join(os.path.realpath(os.path.dirname(__file__)), '../../lib/python'))
    from xbmcclient import *

try:
    import json
except ImportError:
    import simplejson as json
import urllib2, base64, time, socket, struct


def getMAC(interface='eth0'):
    # Return the MAC address of named Ethernet interface
    try:
        line = open('/sys/class/net/%s/address' % interface).read()
    except:
        line = "None"
    return line[0:17]


def check_for_files(filepath):
    for filepath_object in glob.glob(filepath):
        if os.path.isfile(filepath_object):
            return filepath_object
    return False


def download(url, path):

    print('Downloading ' + url)

    # response = urllib2.urlopen(url)

    # handle = open(path, 'w')
    # handle.write(response.read())
    # handle.close()

    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url, timeout=3600)
    f = open(path, 'wb')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print("Downloading: %s Bytes: %s" % (file_name, file_size))

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        print status,

    print('Download complete. Url ' + url + 'saved as ' + path)

    f.close()


def download1(url, path):

    print('Downloading ' + url)

    # response = urllib2.urlopen(url)
    #
    # handle = open(path, 'w')
    # handle.write(response.read())
    # handle.close()

    r = requests.get(url)
    with open(path, 'wb') as f:
        f.write(r.content)
        f.close()

    # file_name = url.split('/')[-1]
    # u = urllib2.urlopen(url, timeout=1000)
    # f = open(path, 'wb')
    # meta = u.info()
    # file_size = int(meta.getheaders("Content-Length")[0])
    # print("Downloading: %s Bytes: %s" % (file_name, file_size))
    #
    # file_size_dl = 0
    # block_sz = 8192
    # while True:
    #     buffer = u.read(block_sz)
    #     if not buffer:
    #         break

        # file_size_dl += len(buffer)
        # f.write(buffer)
        # status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
        # status = status + chr(8) * (len(status) + 1)
        # print(status)

    print('Download complete. Url ' + url + ' saved as ' + path)


if __name__ == "__main__":

    print('Video updating from API')

    url = 'https://media-service.kz/api/videolist/' + getMAC('wlan0')

    print(url)

    try:
        resp = requests.get(url=url, timeout=600)
        data = json.loads(resp.text)
    except OSError:
        sys.exit(errno.EACCES)

    server_list = []
    updated = 0

    dir = "/home/pi/chronos/video/"

    # for videorecord in data['videorecords']:
    #     # print original_name + " https://chronos.adcentre.kz/storage/" + download_link
    #     id = str(videorecord['id'])
    #     order = str(videorecord['order'])
    #     name = str(order).zfill(4) + "_" + id + ".mp4"
    #     path = dir + name
    #     server_list.append(name)
    #
    # if updated > 0:
    #
    #     print('Updating videolist in KODI...')
    #
    #     ip = "localhost"
    #     port = 9777
    #     actions = ['xbmc.PlayMedia("/home/pi/chronos/video/","isdir")', 'xbmc.PlayerControl(repeatall)',
    #                'ActivateWindow(9506)']
    #
    #     addr = (ip, port)
    #     sock = sk.socket(AF_INET, SOCK_DGRAM)
    #
    #     for action in actions:
    #         print('Sending action: %s' % action)
    #         packet = PacketACTION(actionmessage=action, actiontype=ACTION_BUTTON)
    #         packet.send(sock, addr)
    #
    # server_list = []
    # updated = 0

    for videorecord in data['videorecords']:
        record = json.loads(videorecord['records'])[0]

        # original_name = str(record['original_name'])
        download_link = str(record['download_link'])

        # print original_name + " https://chronos.adcentre.kz/storage/" + download_link
        id = str(videorecord['id'])

        md5 = str(videorecord['md5'])

        # print md5

        order = str(videorecord['order'])

        url = "https://media-service.kz/storage/" + download_link

        name = str(order).zfill(4) + "_" + id + ".mp4"

        if id == '1348':
            traur_file_1 = name
            path_traur_file_1 = dir + name

        if id == '1349':
            traur_file_2 = name
            path_traur_file_2 = dir + name

        path = dir + name

        shortpath = dir + id + ".mp4"

        shortpathmask = dir + '*' + id + ".mp4"

        oldfile = check_for_files(shortpathmask)

        server_list.append(name)

        if not os.path.isfile(path):

            if oldfile != False:
                # print 'Yes ' + shortpathmask + ' in ' + oldfile

                if oldfile != path:
                    os.rename(oldfile, path)
                    print('Rename ' + oldfile + ' to ' + path)
                    updated += 1

            else:

                # if id == 896 or id == 897:
                download(url, path)
                localmd5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
                if md5 != localmd5:
                    print('After download bad MD5 hash in file ' + path)
                    os.system("sudo shutdown -r now")  # this has to be run as sudo

                updated += 1

        else:

            localmd5 = hashlib.md5(open(path, 'rb').read()).hexdigest()

            if md5 != localmd5:

                print('Bad MD5 hash in file ' + path)
                os.remove(path)
                print('Deleted ' + path)

                #if id == 896 or id == 897:
                download(url, path)
                localmd5 = hashlib.md5(open(path, 'rb').read()).hexdigest()
                if md5 != localmd5:
                    print('After download bad MD5 hash in file ' + path)
                    os.system("sudo shutdown -r now")  # this has to be run as sudo

                updated += 1

            else:
                print('Skipped ' + name)

    if len(server_list) > 0:
        osfiles = [f for f in listdir(dir) if isfile(join(dir, f))]
        remove_files = list(set(osfiles) - set(server_list))
        for remove_file in remove_files:
            try:
                os.remove(dir + remove_file)
                print('Deleted ' + remove_file)
                updated += 1

            except OSError:
                pass

    date_start_traur = datetime.datetime(2020, 7,13, 0, 0, 0)
    date_end_traur = datetime.datetime(2020, 7, 14, 0, 0, 0)
    now = datetime.datetime.now()
    print(now)
    print(date_start_traur)
    print(date_end_traur)

    if (now > date_start_traur) and (now < date_end_traur):
        traur_dir = '/home/pi/chronos/video/traur2/'
        if not os.path.exists(traur_dir):
            os.makedirs(traur_dir)	
        
        if path_traur_file_1:
            if not os.path.isfile(traur_dir+traur_file_1):
                print('Copy traur file 1 from ' + path_traur_file_1 + ' to ' +traur_dir+traur_file_1)
                copyfile(path_traur_file_1, traur_dir+traur_file_1)
                updated = 1

        if path_traur_file_2:
            if not os.path.isfile(traur_dir+traur_file_2):
                print('Copy traur file 2 from ' + path_traur_file_2 + ' to ' +traur_dir+traur_file_2)
                copyfile(path_traur_file_2, traur_dir+traur_file_2)
                updated = 1
        
    if updated > 0:

        ip = "localhost"
        port = 9777
        
        if (now >= date_start_traur) and (now <= date_end_traur):
            print('Action traur videolist')
            actions = ['xbmc.PlayMedia("/home/pi/chronos/video/traur2/","isdir")', 'xbmc.PlayerControl(repeatall)','ActivateWindow(9506)']
        else:
            print('Action no traur videolist')
            actions = ['xbmc.PlayMedia("/home/pi/chronos/video/","isdir")', 'xbmc.PlayerControl(repeatall)','ActivateWindow(9506)']

        print('Updating videolist in KODI...')

        addr = (ip, port)
        sock = sk.socket(AF_INET, SOCK_DGRAM)

        for action in actions:
            print('Sending action: %s' % action)
            packet = PacketACTION(actionmessage=action, actiontype=ACTION_BUTTON)
            packet.send(sock, addr)