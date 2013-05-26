# Tarmo Tanilsoo, 2013
# -*- coding: utf-8 -*-
from struct import *
def getbyte(bait,unsigned=True):
    '''Read a byte'''
    if len(bait) <> 1: return 0
    if unsigned: return unpack(">B",bait)[0]
    else: return unpack(">b",bait)[0]
    
def halfw(halfw,signed=True):
    '''Read half word'''
    if len(halfw) <> 2: return 0
    if signed: return unpack(">h",halfw)[0]
    else: return unpack(">H",halfw)[0]
def word(sona,signed=True):
    '''Read a word'''
    if len(sona) <> 4: return 0
    if signed: return unpack(">i",sona)[0]
    else: return unpack(">I", sona)[0]

