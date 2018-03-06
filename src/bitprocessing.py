##Copyright (c) 2018, Tarmo Tanilsoo
##All rights reserved.
##
##Redistribution and use in source and binary forms, with or without
##modification, are permitted provided that the following conditions are met:
##
##1. Redistributions of source code must retain the above copyright notice,
##this list of conditions and the following disclaimer.
##
##2. Redistributions in binary form must reproduce the above copyright notice,
##this list of conditions and the following disclaimer in the documentation
##and/or other materials provided with the distribution.
##
##3. Neither the name of the copyright holder nor the names of its contributors
##may be used to endorse or promote products derived from this software without
##specific prior written permission.
##
##THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
##AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
##IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
##ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
##LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
##CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
##SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
##INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
##CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
##ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
##POSSIBILITY OF SUCH DAMAGE.

# -*- coding: utf-8 -*-
from struct import *
import sys

class BitStream(): #FOR BUFR's. Variables whose bit length are not multiple of 8. Yuck!
    def __init__(self, dataBytes):
        if sys.version_info[0] == 2: dataBytes = map(ord, dataBytes)
        self._bitsInBuffer = 8 #Counter of bits in buffer
        self.stream = dataBytes #Data stream in bytes
        self.dataPointer = 0 #Byte pointer in stream
        self.buffer = dataBytes[0] #Buffer of numeric data where we'll do operations
        self.streamLength = len(dataBytes)
    def getBits(self,amount):
        while amount > self._bitsInBuffer:
            self.dataPointer+=1
            if self.dataPointer >= self.streamLength:
                break
            self.buffer <<= 8
            self.buffer += self.stream[self.dataPointer]
            self._bitsInBuffer += 8
        bitsRemaining=(self._bitsInBuffer-amount) if self._bitsInBuffer >= amount else amount
        queriedData=self.buffer >> bitsRemaining
        self.buffer-=(queriedData << bitsRemaining)
        self._bitsInBuffer-=amount
        return queriedData
    def getBytes(self,amount):
        if sys.version_info[0] == 2:
            byteStream=""
            for i in range(amount):            
                byteStream+=str(chr(self.getBits(8)))
                if self.dataPointer >= self.streamLength: break
            return byteStream
        else:
            return self.getBits(amount*8).to_bytes(amount,"big")

def convertToSigned(value,bitLength=8):
    ''' Convert unsigned integer to signed '''
    if (value >> (bitLength-1)):
        return -(value - (1 << (bitLength-1)))
    else:
        return value
    
def halfw(halfw,signed=True):
    '''Read half word'''
    if len(halfw) != 2: return 0
    if signed: return unpack(">h",halfw)[0]
    else: return unpack(">H",halfw)[0]
def floating(f,signed=True):
    ''' Read a float '''
    if len(f) != 4: return 0
    if signed: return unpack(">f",f)[0]
    else: return unpack(">F",f)[0]
def word(sona,signed=True):
    '''Read a word'''
    if len(sona) != 4: return 0
    if signed: return unpack(">i",sona)[0]
    else: return unpack(">I", sona)[0]
def beword(sona,signed=True):
    '''Read a word in Big Endian bit order'''
    if len(sona) != 4: return 0
    if signed: return unpack("<i",sona)[0]
    else: return unpack("<I", sona)[0]
