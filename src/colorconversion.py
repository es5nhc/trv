# -*- coding: utf-8 -*-
##Colorconversion.py uus versioon
## Tarmo Tanilsoo, 2014

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
