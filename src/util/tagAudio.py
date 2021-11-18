# -*- coding: utf-8 -*-
# @Time    : 2021/11/18 11:33
# @Author  : airoucat
# @Filename: tagAudio.py

from mutagen.flac import FLAC,Picture
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TDRC, TCON, TALB
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover


def modify(file_path, title='',artist='',album='',img_path=None,others:dict= None):
    image = None
    if img_path:
        try:
            with open(img_path, 'rb') as f:
                image = f.read()
        except Exception as e:
            print(str(e))
    if (file_path.endswith('.mp3')):
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except:
            pass
        if image:
            audio.tags.add(
                APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc=u'Cover',
                    data=image
                )
            )
        audio.tags["TIT2"] = TIT2(encoding=3, text=title)
        audio.tags["TPE1"] = TPE1(encoding=3, text=artist)
        audio.tags["TALB"] = TALB(encoding=3, text=album)
        audio.save()
    elif (file_path.endswith('.flac')):
        audio = FLAC(file_path)
        try:
            audio.add_tags()
        except:
            pass
        audio.tags['title'] = title
        audio.tags['artist'] = artist
        audio.tags['album'] = album
        if image:
            pic = Picture()
            pic.data = image
            pic.type = 3
            pic.mime = u"image/jpeg"
            audio.add_picture(pic)
        audio.save()
    elif (file_path.endswith('.m4a')):
        audio = MP4(file_path)
        try:
            audio.add_tags()
        except:
            pass
        covr = []
        covr.append(MP4Cover(image, MP4Cover.FORMAT_JPEG))
        audio.tags['covr'] = covr
        audio.tags['title'] = title
        audio.tags['artist'] = artist
        audio.tags['album'] = album
        audio.save()