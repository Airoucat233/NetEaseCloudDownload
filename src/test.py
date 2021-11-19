# -*- coding: utf-8 -*-
# @Time    : 2021/11/19 10:05
# @Author  : huwei
# @FileName: test.py

import os
def generate_pattern(str):
    pattern = ''
    for c in str:
        if c in ['\\', '/', '*', '?', '"', '<', '>', '|']:
            pattern += '.'
        elif c in ['.','+']:
            pattern += f'\{c}'
        else:
            pattern += c
    return pattern


print(generate_pattern('ECHO - +α/あるふぁきゅん。.flac'))