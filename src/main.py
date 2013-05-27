#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Tarmo Tanilsoo, 2013


global zoom
from decoderadar import *
from Image import new as uuspilt
from ImageDraw import Draw
from ImageTk import PhotoImage, BitmapImage
import ImageFont
import numpy
from math import floor, radians as d2r, cos
from colorconversion import *
from coordinates import *
import colorsys
import datetime
import Tkinter
import tkFileDialog
import tkMessageBox
#Geoandmete importimine
print "Laen andmeid... Osariigid"
import states
print "Rannajooned"
import coastlines
print "Maismaapiirid"
import countries
print "Järved"
import lakes
print "Jõed"
import rivers
print "Kohanimed"
import places
print "Põhja-Ameerika maanteed"
import major_NA_roads
sizeb4=[] #Viimatised akna dimensioonid funktsiooni on_window_reconf jaoks
rlegend="" #Siia salvestatakse legend PhotoImagena
infotekst="" #Siia salvestatakse info PhotoImagena
clickbox="" #Siia salvestatakse piksliinfo PhotoImagena
rendered="" #Siia salvestatakse renderdatud radaripilt PhotoImagena
#Ülaltoodud PIL pildina
rlegend2=uuspilt("RGB",(1,1))
infotekst2=uuspilt("RGB",(1,1))
clickbox2=uuspilt("RGB",(1,1))
rendered2=uuspilt("RGB",(1,1))
#Pildifontide laadimine
pildifont=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",12)
pildifont2=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",13)
canvasbusy=False
zoom=1
info=0
zoomlevel=1
direction=1
canvasdimensions=[600,400]
canvasctr=[300,200]
clickboxloc=[0,0]
paised=[]
radials=[]
units={94:"dBZ", #Produktidele vastavate ühikute definieerimine
       99:"m/s",
       159:"dBZ",
       161:"",
       163:u"°/km",
       165:"",
       "DBZ":"dBZ",
       "ZDR":"dBZ",
       "RHOHV": "",
       "HCLASS":"",
       "KDP":u"°/km",
       "V":"m/s"}
img_center=[300,200]
render_center=[1000,1000]
hcanames=["Bioloogiline", #Hüdrometeoori klassifikatsioonid WSR-88D's
          "Anomaalne levi/pinnamüra",
          u"Jääkristallid",
          "Kuiv lumi",
          u"Märg lumi",
          "Vihm",
          "Tugev vihm",
          "Suured piisad",
          "Lumekruubid",
          "Rahe",
          "Tundmatu",
          "RF"]
def exportimg():
    global rendered2
    global rlegend2
    global infotekst2
    global clickbox2
    global clickboxloc
    global img_center
    global render_center
    y=int(w.cget("height"))
    if y % 2 != 0: y+=1
    x=int(w.cget("width"))
    if x % 2 != 0: x+=1
    halfx=int(x/2.0)
    halfy=int(y/2.0)
    cy=int(1000-img_center[1]+halfy)
    cx=int(1000-img_center[0]+halfx)
    cbx=clickboxloc[0]
    cby=clickboxloc[1]
    filed=tkFileDialog.SaveAs(None,initialdir="../data")
    path=filed.show()
    if path != "":
        try:
            outimage=uuspilt("RGB",(x,y),"#000022")
            joonis=Draw(outimage)
            if rendered != "": outimage.paste(rendered2.crop((cx-halfx,cy-halfy,cx+halfx,cy+halfy)),((0,0,x,y))) #Radaripilt
            if clickbox != "": outimage.paste(clickbox2,(cbx,cby,cbx+170,cby+84))
            if rlegend != "": outimage.paste(rlegend2,(x-35,halfy-163,x,halfy+162))
            if infotekst != "": outimage.paste(infotekst2,(halfx-250,y-30,halfx+250,y-10))
            outimage.save(path)
            tkMessageBox.showinfo("Radari vaatur","Eksport edukas")
        except:
            tkMessageBox.showerror("Viga","Valitud vormingusse ei saa salvestada või puudub asukohas kirjutamisõigus.")
    return 0
def getbin(azr):
    global hcanames
    global paised
    delta=None #Muudatus mitme värava vahel
    h=beamheight(azr[1],float(paised[17]),paised[0]) #Radarikiire kõrgus
    try:
        if paised[0] == 94:
            kordaja=1
        elif paised[0] == "ZDR" or paised[0] == "KDP" or paised[0] == "HCLASS" or paised[0] == "RHOHV" or paised[0] == "DBZ" or paised[0] == "V":
            kordaja=1/paised[25]
        else:
            kordaja=4
        azi=azr[0]-radials[0][0]
        azkordaja=1 #Eesti produktide jaoks
        if paised[6]=="58.482" and paised[0] == 94: azkordaja=2 #Aga ainult siis kui tegu on tuletatud Level3 andmetega, mis on 0.5° x 1 km
        azi+=360 if azi < 0 else 0
        kaugus=azr[1] if not isinstance(paised[0],int) else azr[1]/cos(d2r(float(paised[17])))
        val=str(radials[int(azi*azkordaja)][2][int(kaugus*kordaja)])
        delta=None
        if float(val) != -999 and paised[0] == 99:
            valprev=radials[int(azi)-1][2][int(azr[1]*kordaja)]
            delta=abs(float(val)-valprev) if valprev != -999 else None
        elif float(val) != -999 and paised[0] == 165 or paised[0] == "HCLASS":
            val=hcanames[int(val)]
        elif float(val) == -999: val = "Andmed puuduvad"
    except: val = "Andmed puuduvad"
    return val, delta, h
def msgtostatus(msg):
    status.config(text=msg)
    return 0
def about_program():
    tkMessageBox.showinfo("TRV v0.1", "TRV\n0.1\nTarmo Tanilsoo, 2013\ntarmotanilsoo@gmail.com")
    return 0
def keys_list():
    tkMessageBox.showinfo("Otseteed klaviatuuril","z - suurendamisrežiimi\np - ringiliikumisrežiimi\ni - infokogumiserežiimi\nr - algsuurendusse tagasi")
    return 0
def shouldirender(path):
    for i in path:
        for j in i:
            if j > 0 and j < 2000:
                return True
    return False
def draw_infobox(x,y):
    global clickbox
    global clickbox2
    global clickboxloc
    global units
    global paised
    andmed=getinfo(x,y)
    coords=andmed[0]
    latletter="N" if coords[0] > 0 else "S"
    lonletter="E" if coords[1] > 0 else "W"
    azrange=andmed[1]
    data=andmed[2]
    row0=u"%s %s" % (data[0], units[paised[0]]) if data[0] != "Andmed puuduvad" else "Andmed puuduvad"
    row1=u"%.5f°%s %.5f°%s" % (abs(coords[0]),latletter,abs(coords[1]),lonletter)
    row2=u"Asimuut: %.1f°" % (azrange[0])
    row3=u"Kaugus: %.3f km" % (azrange[1])
    row4=u"Kiire kõrgus: ~%.1f km" % (data[2])
    row5="" if data[1] == None else "G2G nihe: %.1f m/s" % (data[1])
    kast=uuspilt("RGB",(170,84),"#0000EE")
    kastdraw=Draw(kast)
    kastdraw.rectangle((0,0,170,16),fill="#000099")
    kastdraw.polygon((0,0,10,0,0,10,0,0),fill="#FFFFFF")
    kastdraw.text((9,1),text=row0, font=pildifont2)
    kastdraw.text((5,17),text=row1, font=pildifont)
    kastdraw.text((5,30),text=row2, font=pildifont)
    kastdraw.text((5,43),text=row3, font=pildifont)
    kastdraw.text((5,56),text=row4, font=pildifont)
    if row5 != "": kastdraw.text((5,69),text=row5, font=pildifont)
    clickbox2=kast
    clickbox=PhotoImage(image=kast)
    clickboxloc=[x,y]
    w.itemconfig(clicktext,image=clickbox)
    w.coords(clicktext,(x+85,y+42))
    return 0
def draw_info(tekst):
    global infotekst
    global infotekst2
    textimg=uuspilt("RGB",(500,20), "#000044")
    textdraw=Draw(textimg)
    textdraw.text((5,3),text=tekst, font=pildifont)
    infotekst2=textimg
    infotekst=PhotoImage(image=textimg)
    w.itemconfig(radardetails,image=infotekst)
    return 0
def drawlegend(product,minimum,maximum):
    global rlegend
    global rlegend2
    global units
    tabel=0
    unit=units[product]
    if product == 99:
        tabel=1
    elif product == 159:
        tabel=3
    elif product == 161:
        tabel=2
    elif product == 163:
        tabel=4
    elif product == 165:
        tabel=5
    increment=(maximum-minimum)/300.0
    legendimg=uuspilt("RGB",(35,325),"#000044")
    legenddraw=Draw(legendimg)
    tosmooth=True
    if product == 165: tosmooth=False
    for i in range(300):
        val=minimum+increment*i
        legenddraw.rectangle((25,324-i,35,324-i),fill=getcolor(val,tabel,tosmooth))
    step=1.0/increment
    majorstep=10
    if product == 159 or product == 163 or product == 165:
        majorstep=1
    if product == 161: #RHOHV aka CC
        majorstep=0.1
    #    minimum*=100
    #    maximum*=100
    #    step/=100
    firstten=int(majorstep+minimum-minimum%majorstep)
    if firstten == majorstep+minimum: firstten = minimum
    ystart=324-(firstten-minimum)*step
    lastten=int(maximum-maximum%majorstep)
    hulk=int((lastten-firstten)/majorstep)
    yend=ystart-majorstep*step*hulk #Kui viimane täissamm on servale liiga lähedal
    if yend < 30: hulk-=1 #Jätame selle viimase punkti legendile panemata
    legenddraw.text((5,0),text=unit, font=pildifont)
    for j in range(hulk+1):
        y=ystart-majorstep*step*j
        if product != 165: #Muude produktide puhul on numbriline väärtus
            legendtext=str(firstten+j*majorstep)
        else:
            legendlist=["BI","AP","IC","DS","WS","RA","+RA","BDR","GR","HA","UNK","RF"]; #Klassifikatsioonide järjend
            legendtext=legendlist[int(firstten+j*majorstep)]
        legenddraw.line((0,y,35,y),fill="white")
        legenddraw.text((0,y-15),text=legendtext,font=pildifont)
    
    #legendimg.save("legend.png")
    rlegend2=legendimg
    rlegend=PhotoImage(image=legendimg)
    w.itemconfig(legend,image=rlegend)
    return 0     
def drawmap(data,rlat,rlon,drawcolor,linewidth=1):
    coordsenne=""
    pikkus=len(data)
    for joon in range(pikkus):
        e=0
        for path in data[joon]:
            if abs(path[1]-rlat) < 10 and abs(path[0]-rlon) < 10:
                kordaja=1
                if zoomlevel < 1:
                    kordaja=int(1/zoomlevel)
                if e % kordaja == 0:
                    pos=geog2polar(path[1],path[0],rlat,rlon)
                    coords=getcoords(pos[1]+180,pos[0],zoomlevel,render_center)
                    if coordsenne=="": coordsenne=coords
                    if coords[0] < 3000 and coords[0] > -1000 and coords[1] < 3000 and coords[1] > -1000:
                        joonis.line((coordsenne,coords),fill=drawcolor,width=linewidth)
                        coordsenne=coords
                    else:
                        coordsenne=""
            else:
                coordsenne=""
            e+=1
        coordsenne=""
        if joon % 50 == 0: update_progress(joon/float(pikkus)*output.winfo_width())
    return 0
def update_progress(x):
    w.coords(progress,(0,output.winfo_height()-66,x,output.winfo_height()-56))
    w.update()
    return 0
def render_radials(radials,product=94):
    global rendered
    global rendered2
    global canvasctr
    global img_center
    global canvasbusy
    global joonis
    global render_center
    canvasbusy=True
    w.config(cursor="watch")
    w.itemconfig(progress,state=Tkinter.NORMAL)
    msgtostatus("Joonistan... radaripilt")
    pilt=uuspilt("RGB",(2000,2000),"#000022")
    joonis=Draw(pilt)
    current=0.0
    updateiter=0
    samm=1
    tabel=0 #Vaikimisi produkt=94
    if product == 99 or product == "V":
        samm=0.25 if product == 99 else paised[25]
        tabel=1
        drawlegend(99,-63.5,63.5)
    elif product == 159 or product == "ZDR":
        samm=0.25 if product == 159 else paised[25]
        tabel=3
        drawlegend(159,-6,6)
    elif product == 161 or product == "RHOHV":
        samm=0.25 if product == 161 else paised[25]
        tabel=2
        drawlegend(161,0.2,1.05)
    elif product == 163 or product == "KDP":
        samm=0.25 if product == 163 else paised[25]
        tabel=4
        drawlegend(163,-2,7)
    elif product == 165 or product == "HCLASS":
        samm=0.25 if product == 165 else paised[25]
        tabel=5
        drawlegend(165,0,12)
    else:
        if product == "DBZ": samm=paised[25]
        drawlegend(94,-25,75)
    radialslen=len(radials)
    for i in radials:
        az=i[0]
        d_az=i[1]
        containssomething=False
        for j in range(len(i[2])):
            val=i[2][j]
            if val!= -999:
                path=makepath(az,d_az,j,paised,zoomlevel,render_center,samm)
                if shouldirender(path):
                    joonis.polygon(path, fill=getcolor(val,tabel))
                    containssomething=True
        if containssomething:
            updateiter+=1
            if updateiter == 1:
                updateiter=0
                update_progress(current/radialslen*output.winfo_width())
        current+=1
    #Geoandmete joonistamine
    rlat=float(paised[6])
    rlon=float(paised[7])
    msgtostatus("Joonistan... rannajooned")
    drawmap(coastlines.points,rlat,rlon,"green")
    msgtostatus("Joonistan... järved")
    drawmap(lakes.points,rlat,rlon,"cyan",1)
    if rlon < 0:
        msgtostatus("Joonistan... Põhja-Ameerika tähtsamad maanteed")
        drawmap(major_NA_roads.points,rlat,rlon,"brown",2)
    msgtostatus("Joonistan... jõed")
    drawmap(rivers.points,rlat,rlon,"cyan",1)
    msgtostatus("Joonistan... osariigid/maakonnad")
    drawmap(states.points,rlat,rlon,"white",1)
    msgtostatus("Joonistan... riigipiirid")
    drawmap(countries.points,rlat,rlon,"red",2)
    #Kohanimed
    msgtostatus("Joonistan... kohanimed")
    for kohad in places.points:
        if kohad[3] < zoomlevel:
            loc=geog2polar(kohad[1],kohad[2],rlat,rlon)
            coords=getcoords(loc[1]+180,loc[0],zoomlevel,render_center)
            if coords[0] < 2000 and coords[0] > 0 and coords[1] < 2000 and coords[1] > 0:
                joonis.rectangle((coords[0]-2,coords[1]-2,coords[0]+2,coords[1]+2),fill="black")
                joonis.rectangle((coords[0]-1,coords[1]-1,coords[0]+1,coords[1]+1),fill="white")
                joonis.text((coords[0]+11,coords[1]-2),text=kohad[0],fill="black",font=pildifont)
                joonis.text((coords[0]+10,coords[1]-3),text=kohad[0],font=pildifont)
    rendered2=pilt
    rendered=PhotoImage(image=pilt) #Teen Tkinteri joonistusala jaoks Photoimage versiooni
    #pilt.save("radar_new.png")
    w.itemconfig(radaripilt,image=rendered)
    img_center=canvasctr
    w.coords(radaripilt,tuple(img_center)) #Tsentreeri pilt
    w.itemconfig(progress,state=Tkinter.HIDDEN)
    msgtostatus("Valmis")
    canvasbusy=False
    setcursor()
    return 0
def load():
    global paised
    global radials
    global zoomlevel
    global render_center
    global clickbox
    blickbox=""
    #zoomlevel=1
    #render_center=[1000,1000]
    filed=tkFileDialog.Open(None,initialdir="../data")
    path=filed.show()
    if path != '': #Kui anti ette mõni fail.
        datafile=open(path, "rb")
        stream=datafile.read()
        datafile.close()
        msgtostatus("Dekodeerin...")
        #try:
        if path[-3:]!= ".h5" and stream[0:2] != "TT":
            paised=headers(stream)
            print headersdecoded(paised)
            draw_info(headersdecoded(paised))
            if paised[0] > 255:
                #Produkti kood ei saa olla suurem kui 255 (11111111).
                msgtostatus("Viga: Tegemist ei ole õiges formaadis failiga")
            if paised[0] == 94 or paised[0] == 99: 
                radials=valarray(decompress(stream),paised[18],paised[19])
                render_radials(radials,paised[0])
            elif paised[0] == 161 or paised[0] == 159 or paised[0] == 163 or paised[0] == 165:
                kordaja=0.1
                if paised[0] == 161: kordaja=0.00333
                if paised[0] == 163: kordaja=0.05
                minval=paised[23]*kordaja
                increment=(paised[24]*kordaja-minval)/253.0
                if paised[0] == 163: increment=(paised[24]*kordaja*2-minval)/254.0
                if paised[0] == 165:
                    minval=0
                    increment=1
                radials=valarray(decompress(stream),minval,increment,paised[0])
                render_radials(radials,paised[0])
        else:
            if stream[0:2] == "TT": #Kui oli minu kiirelt loodud formaat radarmeteoroloogia kodutöö jaoks
                paised=tt_headers(stream)
                radials=tt_array(stream)
                draw_info(headersdecoded(paised))
                render_radials(radials,paised[0])
        #except Exception, err:
        #    msgtostatus("Programmiviga moodulis load: "+ str(err))
    return 0
def setcursor():
    global zoom
    global info
    if zoom==1:
        w.config(cursor="crosshair")
    else:
        if not info:
            w.config(cursor="fleur")
        else:
            w.config(cursor="")
    return 0
def clearclicktext():
    global clickbox
    clickbox=""
    return 0
def tozoom(event=None):
    global zoom
    global info
    zoom=1
    info=0
    clearclicktext()
    setcursor()
    return 0
def topan(event=None):
    global zoom
    global info
    zoom=0
    info=0
    clearclicktext()
    setcursor()
    return 0
def toinfo(event=None):
    global zoom
    global info
    zoom=0
    info=1
    setcursor()
    return 0
def resetzoom(event=None):
    global radials
    global paised
    global zoomlevel
    global canvasctr
    global render_center
    global img_center
    clearclicktext()
    render_center=[1000,1000]
    img_center=canvasctr
    zoomlevel=1
    if len(paised) != 0:
        render_radials(radials,paised[0])
    return 0
#joonistusala sündmused
def mouseclick(event):
    global clickcoords
    global canvasdimensions
    global canvasctr
    global img_center
    global render_center
    if not canvasbusy:
        x=int(w.cget("width"))
        y=int(w.cget("height"))
        canvasdimensions=[x,y]
        canvasctr=[x/2,y/2]
        clickcoords=[event.x,event.y]
    return 0
def leftclick(event):
    global direction
    mouseclick(event)
    direction=1
    return 0
def rightclick(event):
    global direction
    mouseclick(event)
    direction=-1
    return 0
def onmotion(event):
    #Kuna siin on tegu visuaalsete muudatustega, siis kasutan mõlema hiireklahvi jaoks sama alamfunktsiooni
    global clickcoords
    global zoom
    global zoomlevel
    global canvasdimensions
    global img_center
    global render_center
    x=canvasdimensions[0]
    y=canvasdimensions[1]
    if not canvasbusy:
        if zoom:
            dy=event.y-clickcoords[1]
            w.itemconfig(zoomrect, state=Tkinter.NORMAL)
            w.coords(zoomrect,(clickcoords[0]-dy,clickcoords[1]-dy,clickcoords[0]+dy,event.y))
        else: #Ei suurenda
            if info: #Kui kogud piksli väärtust
                draw_infobox(event.x,event.y)
            else: #Liigud...
                if direction==1: #Kui all oli vasak hiireklahv
                    dx=event.x-clickcoords[0]
                    dy=event.y-clickcoords[1]
                    w.coords(radaripilt, (img_center[0]+dx,img_center[1]+dy))
    return 0
def onrelease(event):
    global clickcoords
    global img_center
    global render_center
    global canvasdimensions
    global canvasctr
    global zoomlevel
    global direction
    global radials
    global paised
    global info
    if not canvasbusy:
        if zoom: #Kui olin suurendamas
            #Suurendusastme arvutamine
            dy=event.y-clickcoords[1] 
            if dy!=0:
                newzoom=(float(canvasdimensions[1])/(abs(dy*2)))**direction
            else: newzoom=2**direction
            #Andmete keskme uute koordinaatide leidmine
            pdx=canvasctr[0]-clickcoords[0]
            pdy=canvasctr[1]-clickcoords[1]
            render_center[0]=1000+newzoom*(pdx+render_center[0]-1000)
            render_center[1]=1000+newzoom*(pdy+render_center[1]-1000)
            zoomlevel*=newzoom
            w.itemconfig(zoomrect, state=Tkinter.HIDDEN)
            if len(paised) != 0: render_radials(radials,paised[0])
        else: #Kui olin ringi liikumas
            if not info: #Kui ei olnud infokogumise režiimis
                if direction == 1: #Kui all oli vasak hiireklahv
                    dx_2=event.x-clickcoords[0]
                    dy_2=event.y-clickcoords[1]
                    img_center[0]+=dx_2
                    img_center[1]+=dy_2
                    render_center[0]+=dx_2
                    render_center[1]+=dy_2
                    #Kui hakkab renderdusalast välja minema
                    if img_center[0] > 1000 or img_center[0] < -600  or img_center[1] > 1000 or img_center[1] < -600:
                        if len(paised) != 0: render_radials(radials,paised[0])
            else: #Kui taheti infot
                draw_infobox(event.x,event.y)
    return 0
def on_window_reconf(event):
    global sizeb4
    global img_center
    global canvasctr
    dim=[output.winfo_width(),output.winfo_height()]
    if dim != sizeb4: #If there has been change in size...
        cenne=[w.winfo_width(),w.winfo_height()]
        cdim=[dim[0],dim[1]-56] #New dimensions for canvas
        delta=[(cdim[0]-cenne[0])/2,(cdim[1]-cenne[1])/2]
        w.config(width=cdim[0],height=cdim[1])
        w.coords(legend,(cdim[0]-18,cdim[1]/2))
        w.coords(radardetails,(cdim[0]/2,cdim[1]-20))
        img_center=[img_center[0]+delta[0],img_center[1]+delta[1]]
        canvasctr=[cdim[0]/2,cdim[1]/2]
        w.coords(radaripilt,tuple(img_center))
        sizeb4=dim
    return 0
def getinfo(x,y):
    global render_center
    global canvasdimensions
    global zoomlevel
    global paised
    dimx=canvasdimensions[0]
    dimy=canvasdimensions[1]
    pointx=x-dimx/2-(render_center[0]-1000)
    pointy=y-dimy/2-(render_center[1]-1000)
    azrange=az_range(pointx,pointy,zoomlevel)
    rlat=paised[6]
    rlon=paised[7]
    return geocoords(azrange,float(rlat),float(rlon),float(zoomlevel)), azrange, getbin(azrange)
def onmousemove(event):
    global canvasbusy
    try:
        if not canvasbusy:
            x=event.x
            y=event.y
            info=getinfo(x,y)
            lat=info[0][0]
            latl="N" if lat >= 0 else "S"
            lon=info[0][1]
            lonl="E" if lon >= 0 else "W"
            val=info[2][0]
            infostring=u"%.3f°%s %.3f°%s; Asimuut: %.1f°; Kaugus: %.3f km; Väärtus: %s" % (abs(lat),latl,abs(lon),lonl,floor(info[1][0]*10)/10.0,floor(info[1][1]*1000)/1000.0,val)
            msgtostatus(infostring)
    except:
        pass
clickcoords=[]
output=Tkinter.Tk()
output.title("TRV v0.1")
output.bind("<Configure>",on_window_reconf)
output.config(background="#000044")
##Drawing the menu
menyy = Tkinter.Menu(output,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
output.config(menu=menyy)
failimenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
abimenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
menyy.add_cascade(label="Fail", menu=failimenyy)
menyy.add_cascade(label="Abi", menu=abimenyy)
failimenyy.add_command(label="Ava andmefail", command=load)
failimenyy.add_separator()
failimenyy.add_command(label="Ekspordi pilt", command=exportimg)
failimenyy.add_separator()
failimenyy.add_command(label="Lõpeta", command=output.destroy)
abimenyy.add_command(label="Otseteed klaviatuuril", command=keys_list)
abimenyy.add_separator()
abimenyy.add_command(label="Info programmi kohta", command=about_program)
##Joonistusala
w = Tkinter.Canvas(output,width=600,height=400,highlightthickness=0)
w.bind("<Button-1>",leftclick)
w.bind("<Button-3>",rightclick)
w.bind("<B1-Motion>",onmotion)
w.bind("<B3-Motion>",onmotion)
w.bind("<ButtonRelease-1>",onrelease)
w.bind("<ButtonRelease-3>",onrelease)
w.bind("<Motion>",onmousemove)
w.config(background="#000022")
w.config(cursor="crosshair")
w.grid(row=0,rowspan=2,column=0)
radaripilt=w.create_image(tuple(img_center))
clicktext=w.create_image((300,300))
legend=w.create_image((582,200))
radardetails=w.create_image((300,380))
zoomrect=w.create_rectangle((0,0,200,200),outline="white",state=Tkinter.HIDDEN) #Ristkülik, mis joonistatakse ekraanile suurendamise ajal.
progress=w.create_rectangle((0,390,400,400),fill="#0000ff",state=Tkinter.HIDDEN)
#Klahvivajutuste sidumine
output.bind("r",resetzoom)
output.bind("i",toinfo)
output.bind("p",topan)
output.bind("z",tozoom)
kyljeraam=Tkinter.Frame(output)
kyljeraam.grid(row=2,column=0,sticky="n")
moderaam=Tkinter.Frame(kyljeraam)
moderaam.grid(row=1,column=0)
panimg=PhotoImage(file="../images/pan.png")
zoomimg=PhotoImage(file="../images/zoom.png")
resetzoomimg=PhotoImage(file="../images/resetzoom.png")
infoimg=PhotoImage(file="../images/info.png")
taskbarbtn1=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=panimg, command=topan)
taskbarbtn1.grid(row=0,column=0)
taskbarbtn2=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=zoomimg, command=tozoom)
taskbarbtn2.grid(row=0,column=1)
taskbarbtn3=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=resetzoomimg, command=resetzoom)
taskbarbtn3.grid(row=0,column=2)
taskbarbtn4=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=infoimg, command=toinfo)
taskbarbtn4.grid(row=0,column=3)
status=Tkinter.Label(output, text="", justify=Tkinter.LEFT, anchor="w", fg="yellow", bg="#000044")
status.grid(row=3,column=0,sticky="w")
output.mainloop()

