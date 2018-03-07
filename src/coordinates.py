# -*- coding: utf-8 -*-
##Copyright (c) 2016, Tarmo Tanilsoo
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


from math import sin, cos, sqrt, atan2, asin, pi, floor, degrees as r2d, radians as d2r
from itertools import groupby
def parsecoords(lat,lon):
    la="N"
    if lat < 0: la="S"
    lo="E"
    if lon < 0: lo="W"
    lat=abs(lat)
    lon=abs(lon)
    la_d=int(lat)
    lo_d=int(lon)
    la_m=int((lat-la_d)*60)
    lo_m=int((lon-lo_d)*60)
    la_s=int((((lat-la_d)*60)-la_m)*60)
    lo_s=int((((lon-lo_d)*60)-lo_m)*60)
    string="%d°%d'%d\" %s, %d°%d'%d\" %s" % (la_d, la_m, la_s, la, lo_d, lo_m, lo_s, lo)
    return string
def beamheight(GR,alpha):
    r=6371.0 #Earth radius
    a=d2r(alpha) #Antenna angle in radians
    R=GR/cos(a)
    return R*sin(a)+(R**2)/(2*1.21*r) #WSR-88D height
def beamangle(h,R):
    r=6371.0 #Earth radius
    return r2d(asin(h/R-R/(2*1.21*r)))
def geocoords(azrange,rlat,rlon,zoomlevel):
    R=6371.0
    az=d2r(azrange[0]) #Azimuth in radians
    r=azrange[1]
    rlat=d2r(rlat) #To radians
    lat=asin(sin(rlat)*cos(r/R)+cos(rlat)*sin(r/R)*cos(az))
    lon=rlon+r2d(atan2(sin(az)*sin(r/R)*cos(rlat),cos(r/R)-sin(rlat)*sin(lat)))
    return round(r2d(lat),5),round(lon,5)
def az_range(x,y,zoomlevel):
    angle=180-r2d(atan2(x,y))
    r=sqrt(x**2+y**2)/zoomlevel
    return angle, r
def getcoords(polar,zoom=1,center=[1000,1000]):
    ''' Get coords '''
    r,angle=polar
    k=r*zoom
    cx,cy=center
    x=(sin(angle))*k
    y=-(cos(angle))*k
    return (x+cx,y+cy)
def getmapcoords(placecoords,zoom,center,radarcoords):
    plat,plong=placecoords
    rlat,rlong=radarcoords
    R = 6371.0
    dLat = plat-rlat
    dLon = plong-rlong
    #Intermediate_calcs
    #Instead of sin(0.5*dLat)**2
    shd=sin(0.5*dLat)
    #Instead of sin(0.5*dLon)**2
    shd2=sin(0.5*dLon)
    ##
    a = shd*shd+cos(rlat)*cos(plat)*shd2*shd2
    c = 2.0*atan2(a**0.5,(1.0-a)**0.5) ##
    d = R*c*zoom
    #Bearing
    y = sin(dLon)*cos(plat)
    x = cos(rlat)*sin(plat)-sin(rlat)*cos(plat)*cos(dLon)
    suund = atan2(y,x)
    cx,cy=center
    x=(sin(suund))*d
    y=-(cos(suund))*d
    return (x+cx,y+cy)

    ''' functions getcoords and geog2polar combined in order to save CPU time on function calls'''
def geog2polar(placecoords,radarcoords,radians=True):
    '''Usage: geog2polar(place latitude, place longitude, radar latitude, radar longitude)'''
    plat,plong=placecoords
    rlat,rlong=radarcoords
    R = 6371.0
    dLat = plat-rlat
    dLon = plong-rlong
    #Pre-calculating reused trig functions
    cosPlat = cos(plat)
    cosRlat = cos(rlat)
    #Intermediate_calcs
    #Instead of sin(0.5*dLat)**2
    shd=sin(0.5*dLat)
    #Instead of sin(0.5*dLon)**2
    shd2=sin(0.5*dLon)
    ##
    a = shd*shd+cosRlat*cosPlat*shd2*shd2
    c = 2.0*atan2(a**0.5,(1.0-a)**0.5) ##
    d = R*c
    #Bearing
    y = sin(dLon)*cosPlat
    x = cosRlat*sin(plat)-sin(rlat)*cosPlat*cos(dLon)
    suund = atan2(y,x)
    return d, suund

def coordsFilter(data,radarcoords):
    '''Returns true if latitude and/or longitude is within 10° of that of the radar'''
    rlat,rlon=radarcoords
    listid=()
    for k,i in groupby(data,lambda x,a=rlat,b=rlon,:abs(x[0]-a) < 0.08726646259971647 and abs(x[1]-b) < 0.17453292519943295):
        if k: listid+=[x for x in i],
    return listid
def mapcoordsFilter(coords): #Remove path nodes that are off screen:
    listid=()
    for k,i in groupby(coords,lambda x:min(x)>=0 and max(x)<=2000):
        if k:
            listid+=[x for x in i],
    return listid
