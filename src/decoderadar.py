# -*- coding: utf-8 -*-
##Copyright (c) 2014, Tarmo Tanilsoo
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

import bz2
from bitprocessing import halfw
from bitprocessing import word
from bitprocessing import floating
from bitprocessing import getbyte
from coordinates import getcoords
from coordinates import parsecoords
import datetime
from math import radians as d2r, cos
import time
from h5py import File as HDF5Fail
from calendar import timegm
import string


def headers(data):
    headerinfo=[]
    call=-1
    if data.find('SDUS') <> -1: #Kui failis sisalduvad WMO päised (SDUS*4 TUNNUS(nt. KBMX) DDHHMM(UTC))
        call=data[7:11]
        data=data.replace(data[0:30],"") #Kõrvalda need enne dekodeerimise alustamist
    product=halfw(data[0:2],False)
    headerinfo.append(product) #Product code [0]
    headerinfo.append((halfw(data[2:4],False)*86400-86400)+word(data[4:8],False)) #Timestamp of message [1]
    headerinfo.append(word(data[8:12],False)) #Length of message [2]
    headerinfo.append(halfw(data[12:14],False)) #Source ID [3]
    headerinfo.append(halfw(data[14:16],False)) #Destination ID [4]
    headerinfo.append(halfw(data[16:18],False)) #Number of blocks [5]
    headerinfo.append("%.3f" % float((word(data[20:24]))/1000.0)) #Latitude of radar [6]
    headerinfo.append("%.3f" % float((word(data[24:28]))/1000.0)) #Longitude of radar [7]
    headerinfo.append("%.2f" % float(halfw(data[28:30])*0.3048)) #Radar height [8]
    headerinfo.append(halfw(data[32:34])) #Operational mode [9]
    headerinfo.append(halfw(data[34:36])) #Volume Coverage Pattern [10]
    headerinfo.append(halfw(data[36:38])) #Sequence number [11]
    headerinfo.append(halfw(data[38:40])) #Volume Scan Number [12]
    headerinfo.append(halfw(data[40:42])) #Volume Scan date [13]
    headerinfo.append(word(data[42:46])) #Volume Scan Time [14]
    headerinfo.append(halfw(data[46:48])) #Generation date of product [15]
    headerinfo.append(word(data[48:52])) #Generation time of product [16]
    headerinfo.append("%.1f" % (halfw(data[58:60])/10.0)) #Antenna elevation [17]
    headerinfo.append(float(halfw(data[60:62]))/10) #Minimum data in dbz [18]
    headerinfo.append(float(halfw(data[62:64]))/10) #dbz increment [19]
    headerinfo.append(halfw(data[64:66])) # Amount of levels [20]
    headerinfo.append((headerinfo[15]*86400-86400)+headerinfo[16]) #Produkti loomise aeg [21]
    headerinfo.append((headerinfo[13]*86400-86400)+headerinfo[14]) #Volume Scan time [22]
    headerinfo.append(halfw(data[92:94])) #halfw 47 - min dual pol value [23]
    headerinfo.append(halfw(data[94:96])) #halfw 48 - max dual pol value [24]
    headerinfo.append(1 if product == 94 else 0.25) #Tühi Level 3 andmete korral [25]
    headerinfo.append(halfw(data[70:72])) #halfw 36 [26]
    headerinfo.append(floating(data[60:64])) #halfw 32,34 [27] (dual pol)
    headerinfo.append(floating(data[64:68])) #halfw 34,36 [28] (dual pol)

    print headerinfo
    return headerinfo
def productname(jarjend):
    products={94:"peegelduvus",## if jarjend[6] != "58.482" else "pCAPPI",
              99:"radiaalkiirus",
              159:"diferentsiaalne peegelduvus",
              161:"korrelatsioonikoefitsent",
              163:"spetsiifiline diferentsiaalne faas",
              165:u"hüdrometeoori klassifikatsioon",
              "DBZ":"peegelduvus",
              "REF":"peegelduvus",
              "ZDR":"diferentsiaalne peegelduvus",
              "RHOHV":"korrelatsioonikoefitsent",
              "RHO":"korrelatsioonikoefitsent",
              "KDP":"spetsiifiline diferentsiaalne faas",
              "HCLASS":u"hüdrometeoori klassifikatsioon",
              "V":"radiaalkiirus",
              "VEL":"radiaalkiirus",
              "VRAD":"radiaalkiirus",
              "PHI":"diferentsiaalne faas",
              "SW":"spektrilaius"
              }
    return products[jarjend[0]]
def hdf5_headers(fail,product="DBZ",h=0.5):
    andmed=HDF5Fail(fail)
    aeg=andmed["/how"].attrs.get(u"startepochs")
    whereattrs=andmed["/where"].attrs
    lat=float(whereattrs.get(u"lat"))
    lon=float(whereattrs.get(u"lon"))
    step=float(whereattrs.get(u"xscale"))/1000
    headers=[product,aeg,0,0,0,0,lat,lon,0,0,0,0,0,0,0,0,0,h,0,0,0,0,0,0,0,step]
    andmed.close()
    return headers
def hdf5_sweepslist(fail):
    andmefail=HDF5Fail(fail)
    nimekiri=list(andmefail["/how"].attrs.get(u"angles"))
    andmefail.close()
    out=[]
    for i in nimekiri:
        out.append(float(i))
    return out
def hdf5_productlist(fail):
    andmefail=HDF5Fail(fail)
    produktid=[]
    for i in andmefail.keys():
        if i[0:4] == "scan":
            produkt=andmefail[i+"/what"].attrs.get("quantity")
            try:
                produktid.index(produkt)
            except:
                produktid.append(produkt)
    andmefail.close()
    return produktid
def hdf5_leiaskann(fail,produkt="DBZ",angleindex=0):
    andmefail=HDF5Fail(fail)
    for i in andmefail.keys():
        if i[0:4] == "scan" or i[0:7]== "dataset":
            if andmefail[i+"/what"].attrs.get("quantity") == produkt and andmefail[i+"/how"].attrs.get("angleindex") == int(angleindex)+1:
                andmefail.close()
                return i
def tonone(x): #Convert fill values used in hdf5_vallarray to Python None.
    if x == -999:
        return None
    else:
        return x
def hdf5_valarray(fail,scan="scan1",rhiaz=None):
    andmefail=HDF5Fail(fail)
    dataraw=andmefail["/"+scan+"/data"]
    angle=0
    d_angle=d2r(360.0/len(dataraw))
    if rhiaz != None: #If was collecting single gates for a whole RHI
        dataraw=[dataraw[int(rhiaz*len(dataraw)/360.0)]]
    whatattrs=andmefail["/"+scan+"/what"].attrs
    gain=whatattrs.get(u"gain")
    offset=whatattrs.get(u"offset")
    nodata=whatattrs.get(u"nodata")
    undetect=whatattrs.get(u"undetect")
    dataarray=[]
    for i in dataraw:
        rida=i*1.0
        rida*=gain
        rida[rida == undetect*gain]=-999
        rida[rida == nodata*gain]=-999
        rida[rida != -999]+=offset
        if rhiaz != None:
            return rida
        else:
            dataarray.append([angle,d_angle,map(tonone,rida.tolist()),0])
        angle+=d_angle
    andmefail.close()
    return dataarray        
def rhiheadersdecoded(jarjend, az):
    aeg=datetime.datetime.utcfromtimestamp(jarjend[1])
    msg=productname(jarjend).capitalize()+" | Asimuut: "+str(az)+u"° | "+str(aeg)+" UTC"
    return msg
def headersdecoded(jarjend):
    aeg=datetime.datetime.utcfromtimestamp(jarjend[1])
    msg=str(float(jarjend[17]))+u"° "+productname(jarjend)+" | "+str(aeg)+" UTC"
    return msg
def decompress(data):
    location=data.find("BZ") #Leia BZipi päise algus
    bins= bz2.decompress(data[location:])
    bins2=bins[28:]
    return bins2
def level2_sweepslist(fileobject):
    sweeps=[]
    for i in xrange(fileobject.nscans):
        rida=fileobject.get_elevation_angles([i])
        keskmine=round(sum(rida)/len(rida),2)
        sweeps.append(keskmine)
    return sweeps
def level2_headers(fileobject,moment="REF",scan=0):
    steps=fileobject.get_range(scan,moment)
    samm=(steps[2]-steps[1])/1000.0
    volume_header=fileobject.volume_header
    aeg=(volume_header["date"]-1)*86400+volume_header["time"]/1000
    h=level2_sweepslist(fileobject)[scan]
    return [moment,aeg,0,0,0,0,fileobject.location()[0],fileobject.location()[1],0,0,0,0,0,0,0,0,0,h,0,0,0,0,0,0,0,samm]
def level2_valarray(fileobject,moment="REF",scan=0,rhiaz=False):
    omadused=fileobject.scan_info()[scan]
    try:
        momentindex=omadused["moments"].index(moment)
    except:
        return None
    varavatehulk=omadused["ngates"][momentindex]
    asimuudid=list(fileobject.get_azimuth_angles([scan]))
    andmed=fileobject.get_data(moment,varavatehulk,[scan])
    steps=fileobject.get_range(scan,moment)
    samm=(steps[2]-steps[1])/1000.0 #Derive xrange resolution in kms
    mindistance=(steps[0]/1000.0-samm/2.0)
    dataarray=[]
    vanapiir=(asimuudid[-1]+asimuudid[0])/2.0 #Computing azimuth boundaries for gates
    for i in xrange(len(andmed)):
        jargmine = i+1 if i < len(andmed)-1 else 0
        praeguneaz=asimuudid[i]
        jargmineaz=asimuudid[jargmine]
        if jargmineaz < praeguneaz:
            jargmineaz+=360
        uuspiir=(praeguneaz+jargmineaz)/2.0
        d_az=uuspiir-vanapiir
        if not rhiaz:
            dataarray.append([d2r(vanapiir),d2r(d_az),andmed[i].tolist(None),mindistance])
        else:
            if (praeguneaz <= rhiaz and jargmineaz > rhiaz) or (jargmineaz > 360 and rhiaz < d_az):
                return andmed[i].tolist(None)
        vanapiir=uuspiir
    return dataarray
##def tt_headers(filecontent,sweepnr=0):
##    row=filecontent.splitlines()[0].split()
##    h=str(float(filecontent.split("!?")[sweepnr+1].splitlines()[0]))
##    aeg=timegm(time.strptime(row[5]+row[6],"%d%m%Y%H%M%S"))
##    step=float(row[4])
##    headers=[row[1],aeg,0,0,0,0,row[2],row[3],0,0,0,0,0,0,0,0,0,h,0,0,0,0,0,0,0,step]
##    return headers
##def tt_sweepslist(filecontent):
##    sweeps=[]
##    for i in filecontent.split("!?")[1:]:
##        try: sweeps.append(float(i.splitlines()[0]))
##        except: pass
##    return sweeps
##def convhca(val): #Convert IRIS HCA to NEXRAD Level 3 HCA
##    val=int(val)
##    if val == 1: return 1
##    elif val == 2: return 5
##    elif val == 3: return 4
##    elif val == 4: return 3
##    elif val == 5: return 8
##    elif val == 6: return 9
##    else: return -999
##def tt_singlegate(filecontent,az,sweepnr):
##    additional=0
##    product=filecontent.splitlines()[0].split()[1]
##    sweeps=filecontent.split("!?")[sweepnr+1]
##    subsweeps=sweeps.split("?")
##    gates=[]
##    while len(gates) < 360:
##        gates+=subsweeps[additional].split("+")[1:]
##        additional+=1
##        if additional == len(subsweeps): break
##    rows=gates[az].splitlines() #Eeldus: Andmed 1 kraadise sammuga!!!
##    az=rows[0]
##    datarow=[]
##    for i in rows[1:]:
##        try:
##            if product != "HCLASS":
##                datarow.append(float(i))
##            else:
##                datarow.append(convhca(float(i)))
##        except:
##            pass
##    return datarow
##def tt_array(filecontent,sweepnr=0):
##    additional=0
##    product=filecontent.splitlines()[0].split()[1]
##    sweeps=filecontent.split("!?")[sweepnr+1]
##    subsweeps=sweeps.split("?")
##    gates=[]
##    while len(gates) < 360:
##        gates+=subsweeps[additional].split("+")[1:]
##        additional+=1
##        if additional == len(subsweeps): break
##    dataarray=[]
##    for i in gates:
##        rows=i.splitlines()
##        az=float(rows[0])
##        datarow=[]
##        for j in rows[1:]:
##            try:
##                if product != "HCLASS":
##                    datarow.append(float(j))
##                else:
##                    datarow.append(convhca(float(j)))
##            except:
##                pass
##        dataarray.append([d2r(az),d2r(1.0),datarow])
##    return dataarray
def valarray(stream,min_val=-32,increment=0.5,product=94): #Values array for NEXRAD Level 3
    '''Array of reflectivity values (data stream, minimum dBz value, dBZ increment, amount of radials)'''
    dataarray=[]
    radials_count=int(halfw(stream[0:2])) #Get amount of radials
    p=2 #pointer
    for i in xrange(radials_count):
        amt=int(halfw(stream[p:p+2]))
        az=int(halfw(stream[p+2:p+4]))/10.0
        d_az=int(halfw(stream[p+4:p+6]))/10.0
        mindistance=0
        datarow=[]
        p+=6
        if product == 159 or product == 161 or product == 163:
            #If Dual pol products with scale and offset
            #scale=increment
            #offset=min_val
            for j in xrange(p,p+amt):
                val=getbyte(stream[j])
                if val > 1:
                    datarow.append((val-min_val)/increment)
                else:
                    datarow.append(None)
        elif product == 165: #If HCA
            #Override usual decoding system and plot them as numbers
            for j in xrange(p,p+amt):
                val=getbyte(stream[j])
                if val == 0: datarow.append(None)
                elif val > 0 and val < 140: datarow.append(val/10-1)
                elif val >= 140: datarow.append(val/10-4)
        else:
            for j in xrange(p,p+amt):
                val=getbyte(stream[j])
                if val > 1:
                    datarow.append(min_val+increment*(val-2))
                else:
                    datarow.append(None)
        dataarray.append([d2r(az),d2r(d_az),datarow,mindistance])
        p+=amt
    return dataarray
def leiasuund(rad,rad2,y,paised,zoom=1,center=[1000,1000],samm=1):
    '''makepath(algasimuut, (asimuudi) samm, kaugus radarist, suurendusaste, renderduse keskpunkti asukoht), kauguse samm'''
    koosinus=1 if not isinstance(paised[0],int) else cos(d2r(float(paised[17])))#Kui on nexradi produktid, arvesta nurga muutusega!
    coords1=getcoords(rad,(y+samm)*koosinus,zoom,center)
    coords2=getcoords(rad+rad2,(y+samm)*koosinus,zoom,center)
    coords3=getcoords(rad,y*koosinus,zoom,center)
    coords4=getcoords(rad+rad2,y*koosinus,zoom,center)
    startx1,starty1=coords3
    startx2,starty2=coords4
    endx1,endy1=coords1
    endx2,endy2=coords2
    dx1=endx1-startx1
    dx2=endx2-startx2
    dy1=endy1-starty1
    dy2=endy2-starty2
    return [startx1,startx2,starty1,starty2,dx1,dx2,dy1,dy2]
