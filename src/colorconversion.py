# -*- coding: utf-8 -*-

##Copyright (c) 2015, Tarmo Tanilsoo
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

from __future__ import division

from math import floor

def loadcolortable(fail):
    tabel=open(fail,"r")
    read=tabel.readlines()
    tabel.close()
    tabel=[]
    for i in read:
        ridastr=i.strip().split()
        rida=[]
        for j in ridastr:
            rida.append(float(j))
        tabel.append(rida)
    return tabel

def getcolor(tabel,val,smoothing=True):
    if val == "RF": return (125,0,125)
    if val == None: return None
    i=0
    esi=tabel[0]
    viim=tabel[-1]
    if val >= viim[0]:
        r,g,b=viim[1:]
    elif val <= esi[0]:
        r,g,b=esi[1:]
    else:
        tabelisuurus=len(tabel)
        j=1
        for i in tabel:
            if i[0] <= val and tabel[j][0] > val:
                seeval,seer,seeg,seeb=i
                jargmval,jargmr,jargmg,jargmb=tabel[j]
                vahe=val-seeval
            j+=1
        if smoothing == 1:
            maxvahe=jargmval-seeval
            rsamm=(jargmr-seer)/maxvahe
            gsamm=(jargmg-seeg)/maxvahe
            bsamm=(jargmb-seeb)/maxvahe
            r=seer+rsamm*vahe
            g=seeg+gsamm*vahe
            b=seeb+bsamm*vahe
        else:
            r,g,b=seer,seeg,seeb
    return (int(r),int(g),int(b))
