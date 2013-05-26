# -*- coding: utf-8 -*-
# Tarmo Tanilsoo, 2013

from math import sin, cos, sqrt, atan2, asin, pi, floor, degrees as r2d, radians as d2r
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
def beamheight(GR,alpha,product):
    r=6371.0 #Maa raadius
    a=d2r(alpha) #Antenni kaldenurk radiaanides
    R=GR/cos(a)
    return R*sin(a)+(R**2)/(2*1.21*r) #WSR-88D height 
def geocoords(azrange,rlat,rlon,zoomlevel):
    R=6371.0
    az=azrange[0]
    r=azrange[1]
    lat=asin(sin(d2r(rlat))*cos(r/R)+cos(d2r(rlat))*sin(r/R)*cos(d2r(az)))
    lon=rlon+r2d(atan2(sin(d2r(az))*sin(r/R)*cos(d2r(rlat)),cos(r/R)-sin(d2r(rlat))*sin(lat)))
    return round(r2d(lat),5),round(lon,5)
def az_range(x,y,zoomlevel):
    angle=180-r2d(atan2(x,y))
    r=sqrt(x**2+y**2)/zoomlevel
    return angle, r
def getcoords(angle,r,zoom=1,center=[1000,1000]):
    ''' Get coords '''
    x=(sin(d2r(angle))*r)*zoom
    y=(cos(d2r(angle-180))*r)*zoom
    return (x+center[0],y+center[1])

def geog2polar(plat,plong,rlat,rlong):
    '''Usage: geog2polar(place latitude, place longitude, radar latitude, radar longitude)'''
    #Distance
    R = 6371
    dLat = d2r(float(plat)-float(rlat))
    dLon = d2r(float(plong)-float(rlong))
    a = sin(0.5*dLat)**2+cos(d2r(rlat))*cos(d2r(plat))*sin(0.5*dLon)**2
    c = 2*atan2(sqrt(a),sqrt(1-a))
    d = R*c
    #Bearing
    y = sin(dLon)*cos(d2r(plat))
    x = cos(d2r(rlat))*sin(d2r(plat))-sin(d2r(rlat))*cos(d2r(plat))*cos(dLon)
    suund = (r2d(atan2(y,x))+540) % 360
    return d, suund
