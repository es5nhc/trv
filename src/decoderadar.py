# -*- coding: utf-8 -*-

# Tarmo Tanilsoo, 2013
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
from calendar import timegm
import string


def headers(data):
    headerinfo=[]
    call=-1
    if data.find('SDUS') <> -1: #Kui failis sisalduvad WMO päised (SDUS*4 TUNNUS(nt. KBMX) DDHHMM(UTC))
        call=data[7:11]
        data=data.replace(data[0:30],"") #Kõrvalda need enne dekodeerimise alustamist
    headerinfo.append(halfw(data[0:2],False)) #Product code [0]
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
    headerinfo.append(None) #Tühi Level 3 andmete korral [25]
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
              "ZDR":"diferentsiaalne peegelduvus",
              "RHOHV":"korrelatsioonikoefitsent",
              "KDP":"spetsiifiline diferentsiaalne faas",
              "HCLASS":u"hüdrometeoori klassifikatsioon",
              "V":"radiaalkiirus"
              }
    return products[jarjend[0]]
def rhiheadersdecoded(jarjend, az):
    aeg=datetime.datetime.utcfromtimestamp(jarjend[1])
    msg=productname(jarjend).capitalize()+" | Asimuut: "+str(az)+u"° | "+str(aeg)+" UTC"
    return msg
def headersdecoded(jarjend):
    aeg=datetime.datetime.utcfromtimestamp(jarjend[1])
    msg=str(jarjend[17])+u"° "+productname(jarjend)+" | "+str(aeg)+" UTC"
    return msg
def decompress(data):
    location=data.find("BZ") #Leia BZipi päise algus
    bins= bz2.decompress(data[location:])
    bins2=bins[28:]
    return bins2

def tt_headers(filecontent,sweepnr=0):
    row=filecontent.splitlines()[0].split()
    h=str(float(filecontent.split("!?")[sweepnr+1].splitlines()[0]))
    aeg=timegm(time.strptime(row[5]+row[6],"%d%m%Y%H%M%S"))
    step=float(row[4])
    headers=[row[1],aeg,0,0,0,0,row[2],row[3],0,0,0,0,0,0,0,0,0,h,0,0,0,0,0,0,0,step]
    return headers
def tt_sweepslist(filecontent):
    sweeps=[]
    for i in filecontent.split("!?")[1:]:
        try: sweeps.append(float(i.splitlines()[0]))
        except: pass
    return sweeps
def convhca(val): #Convert IRIS HCA to NEXRAD Level 3 HCA
    val=int(val)
    if val == 1: return 1
    elif val == 2: return 5
    elif val == 3: return 4
    elif val == 4: return 3
    elif val == 5: return 8
    elif val == 6: return 9
    else: return -999
def tt_singlegate(filecontent,az,sweepnr):
    additional=0
    product=filecontent.splitlines()[0].split()[1]
    sweeps=filecontent.split("!?")[sweepnr+1]
    subsweeps=sweeps.split("?")
    gates=[]
    while len(gates) < 360:
        gates+=subsweeps[additional].split("+")[1:]
        additional+=1
        if additional == len(subsweeps): break
    rows=gates[az].splitlines() #Eeldus: Andmed 1 kraadise sammuga!!!
    az=rows[0]
    datarow=[]
    for i in rows[1:]:
        try:
            if product != "HCLASS":
                datarow.append(float(i))
            else:
                datarow.append(convhca(float(i)))
        except:
            pass
    return datarow
def tt_array(filecontent,sweepnr=0):
    additional=0
    product=filecontent.splitlines()[0].split()[1]
    sweeps=filecontent.split("!?")[sweepnr+1]
    subsweeps=sweeps.split("?")
    gates=[]
    while len(gates) < 360:
        gates+=subsweeps[additional].split("+")[1:]
        additional+=1
        if additional == len(subsweeps): break
    dataarray=[]
    for i in gates:
        rows=i.splitlines()
        az=float(rows[0])
        datarow=[]
        for j in rows[1:]:
            try:
                if product != "HCLASS":
                    datarow.append(float(j))
                else:
                    datarow.append(convhca(float(j)))
            except:
                pass
        dataarray.append([d2r(az),d2r(1.0),datarow])
    return dataarray
def valarray(stream,min_val=-32,increment=0.5,product=94): #Peegelduvuse järjend (produkt 94)
    '''Array of reflectivity values (data stream, minimum dBz value, dBZ increment, amount of radials)'''
    dataarray=[]
    radials_count=int(halfw(stream[0:2])) #Võta radiaalide hulk
    p=2 #pointer
    for i in range(radials_count):
        amt=int(halfw(stream[p:p+2]))
        az=int(halfw(stream[p+2:p+4]))/10.0
        d_az=int(halfw(stream[p+4:p+6]))/10.0
        datarow=[]
        p+=6
        if product == 159 or product == 161 or product == 163:
            #If Dual pol products with scale and offset
            #scale=increment
            #offset=min_val
            for j in range(p,p+amt):
                val=getbyte(stream[j])
                if val > 1:
                    datarow.append((val-min_val)/increment)
                else:
                    datarow.append(-999)
        elif product == 165: #If HCA
            #Override usual decoding system and plot them as numbers
            for j in range(p,p+amt):
                val=getbyte(stream[j])
                if val == 0: datarow.append(-999)
                elif val > 0 and val < 140: datarow.append(val/10-1)
                elif val >= 140: datarow.append(val/10-4)
        else:
            for j in range(p,p+amt):
                val=getbyte(stream[j])
                if val > 1:
                    datarow.append(min_val+increment*(val-2))
                else:
                    datarow.append(-999)
        dataarray.append([d2r(az),d2r(d_az),datarow])
        p+=amt
    return dataarray
def leiasuund(rad,rad2,y,paised,zoom=1,center=[1000,1000],samm=1):
    '''makepath(algasimuut, (asimuudi) samm, kaugus radarist, suurendusaste, renderduse keskpunkti asukoht), kauguse samm'''
    koosinus=1 if not isinstance(paised[0],int) else cos(d2r(float(paised[17])))#Kui on nexradi produktid, arvesta nurga muutusega!
    coords1=getcoords(rad,(y*samm+samm)*koosinus,zoom,center)
    coords2=getcoords(rad+rad2,(y*samm+samm)*koosinus,zoom,center)
    coords3=getcoords(rad,y*samm*koosinus,zoom,center)
    coords4=getcoords(rad+rad2,y*samm*koosinus,zoom,center)
    startx1,starty1=coords3
    startx2,starty2=coords4
    endx1,endy1=coords1
    endx2,endy2=coords2
    dx1=endx1-startx1
    dx2=endx2-startx2
    dy1=endy1-starty1
    dy2=endy2-starty2
    return [startx1,startx2,starty1,starty2,dx1,dx2,dy1,dy2]
