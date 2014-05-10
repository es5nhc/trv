#!/usr/bin/python2
# -*- coding: utf-8 -*-
# Tarmo Tanilsoo, 2013-2014
from __future__ import division

import bz2
from decoderadar import *
from Image import open as laepilt
from Image import new as uuspilt
from ImageDraw import Draw
from ImageTk import PhotoImage, BitmapImage
import ImageFont
from math import floor, sqrt, radians as d2r, degrees as r2d, cos
from colorconversion import *
from coordinates import *
import datetime
import Tkinter
import tkFileDialog
import tkMessageBox
import urllib2
import json
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
print "Põhja-Ameerika maanteed"
import major_NA_roads
class NEXRADChooser(Tkinter.Toplevel): #NEXRAD jaama valik
    def __init__(self, parent, title = None):
        global nexradstn
        Tkinter.Toplevel.__init__(self,parent)
        self.title("NEXRAD jaama valik")
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        self.config(background="#000044")
        jaamatiitel=Tkinter.Label(self,text="Vali jaam:",bg="#000044",fg="#ffff00")
        jaamatiitel.pack()
        jaamavalik=Tkinter.Frame(self)
        kerimisriba=Tkinter.Scrollbar(jaamavalik,bg="#000099",highlightbackground="#000099",activebackground="#0000ff",troughcolor="#000044")
        kerimisriba.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
        self.jaamaentry=Tkinter.Listbox(jaamavalik,width=30,yscrollcommand=kerimisriba.set,fg="#ffff00",bg="#000044",highlightbackground="#000044",selectbackground="#000099",selectforeground="#ffff00")
        self.jaamaentry.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH)
        kerimisriba.config(command=self.jaamaentry.yview)
        jaamavalik.pack()
        jaamad=file_read("nexradstns.txt").split("\n")
        for i in jaamad:
            rida=i.split("|")
            self.jaamaentry.insert(Tkinter.END, rida[0]+" - "+rida[1]+", "+rida[2])
        okbutton=Tkinter.Button(self,text="OK",command=self.newstn,bg="#000044",fg="#ffff00",activebackground="#000099", highlightbackground="#000044", activeforeground="#ffff00")
        okbutton.pack()
        self.mainloop()
    def newstn(self):
        global nexradstn
        selection=self.jaamaentry.curselection()
        if selection != ():
            print selection
            jaam=self.jaamaentry.get(selection)[:4]
            nexradstn=jaam.lower()
            self.onclose()
        else:
            tkMessageBox.showerror("TRV 2014.5","Palun vali jaam!")
    def onclose(self):
        global nexradchooseopen
        nexradchooseopen=0
        self.destroy()
class URLAken(Tkinter.Toplevel): ##Dialog to open a file from the Internet
    def __init__(self, parent, title = None):
        Tkinter.Toplevel.__init__(self,parent)
        self.title("Ava fail internetist")
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        self.config(background="#000044")
        urltitle=Tkinter.Label(self,text="URL:",bg="#000044",fg="#ffff00")
        urltitle.grid(column=0,row=0)
        self.url=Tkinter.StringVar()
        ##self.url.set("YOUR DEFAULT URL HERE")
        urlentry=Tkinter.Entry(self,textvariable=self.url,width=70,fg="#ffff00",bg="#000044",highlightbackground="#000044",selectbackground="#000099",selectforeground="#ffff00")
        urlentry.grid(column=1,row=0)
        downloadbutton=Tkinter.Button(self,text="Ava",command=self.laealla,bg="#000044",fg="#ffff00",activebackground="#000099", highlightbackground="#000044", activeforeground="#ffff00")
        downloadbutton.grid(column=0,row=1,sticky="w")
        self.mainloop()
    def laealla(self):
        aadress=self.url.get()
        try:
            url=urllib2.urlopen(aadress,timeout=10)
            sisu=url.read()
            if aadress[-4:]==".trv":
                fmt=1
            else:
                fmt=0
            self.onclose()
            decodefile(sisu,fmt)
        except:
            tkMessageBox.showerror("TRV 2014.5","Faili allalaadimisel juhtus viga!")
    def onclose(self):
        global urlwindowopen
        urlwindowopen=0
        self.destroy()
sizeb4=[] #Viimatised akna dimensioonid funktsiooni on_window_reconf jaoks
rlegend="" #Siia salvestatakse legend PhotoImagena
infotekst="" #Siia salvestatakse info PhotoImagena
clickbox="" #Siia salvestatakse piksliinfo PhotoImagena
rendered="" #Siia salvestatakse renderdatud radaripilt PhotoImagena
rhiout="" #Siia salvestatakse pseudo-RHI PhotoImagena
#Ülaltoodud PIL pildina
rlegend2=uuspilt("RGB",(1,1))
infotekst2=uuspilt("RGB",(1,1))
clickbox2=uuspilt("RGB",(1,1))
rendered2=uuspilt("RGB",(1,1))
rhiout2=uuspilt("RGB",(1,1))
currentfilepath="" #Siia salvestatakse parasjagu avatud faili asukoht
#Pildifontide laadimine
pildifont=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",12)
pildifont2=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",13)
canvasbusy=False
nexradstn="kbmx" #Valitud NEXRAD jaam
urlwindowopen=0 #1 kui URLi avamise aken on lahti
nexradchooseopen=0 #1 kui NEXRADI jaama valimise aken on lahti
confopen=0 #1 kui seadete aken on lahti
zoom=1
info=0
rhi=0
rhiaz=0 ##RHI asimuut -- RHI Azimuth
rhistart=0
rhiend=250
rhishow=0 ##Yes, if RHI is shown
zoomlevel=1
direction=1
renderagain=0 #Need to render again upon loading the PPI view.
canvasdimensions=[600,400]
canvasctr=[300,200]
clickboxloc=[0,0]
paised=[]
radials=[]
rhidata=[]
sweeps=[]
units={94:"dBZ", #Produktidele vastavate ühikute defineerimine
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
colortablenames={94:"dbz",
                 "DBZ":"dbz",
                 "VRAD":"v",
                 "V":"v",
                 99:"v",
                 159:"zdr",
                 "ZDR":"zdr",
                 161:"rhohv",
                 "RHOHV":"rhohv",
                 163:"kdp",
                 "KDP":"kdp",
                 165: "hclass",
                 "HCLASS": "hclass"} #Names for color tables according to product
def choosenexrad(): #NEXRAD jaama valiku akna avamine
    global nexradchooseopen
    if nexradchooseopen == 0:
        nexradchooseopen=1
        NEXRADChooser(output)
def fetchnexrad(product): #Värskeima NEXRAD Level 3 faili alla laadimine NOAA FTP'st
    global nexradstn
    global rhishow
    if rhishow: topan()
    print nexradstn,product
    url="ftp://tgftp.nws.noaa.gov/SL.us008001/DF.of/DC.radar/DS."+product+"/SI."+nexradstn+"/sn.last"
    try:
        ftp=urllib2.urlopen(url,timeout=10)
        sisu=ftp.read()
        decodefile(sisu)
    except:
        tkMessageBox.showerror("TRV 2014.5","Allalaadimine ebaõnnestus!")
def exportimg():
    global rendered2
    global rlegend2
    global infotekst2
    global rhiout
    global clickbox2
    global clickboxloc
    global img_center
    global render_center
    global rhishow
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
    cbh=84 if not rhishow else 45
    filed=tkFileDialog.SaveAs(None,initialdir="../data")
    path=filed.show()
    if path != "":
        try:
            outimage=uuspilt("RGB",(x,y),"#000022")
            joonis=Draw(outimage)
            if not rhishow:
                if rendered != "": outimage.paste(rendered2.crop((cx-halfx,cy-halfy,cx+halfx,cy+halfy)),((0,0,x,y))) #PPI
            else:
                outimage.paste(rhiout2,(0,0,x,y)) #PseudoRHI
            if clickbox != "": outimage.paste(clickbox2,(cbx,cby+1,cbx+170,cby+cbh+1))
            if rlegend != "": outimage.paste(rlegend2,(x-35,halfy-163,x,halfy+162))
            if infotekst != "": outimage.paste(infotekst2,(halfx-250,y-30,halfx+250,y-10))
            outimage.save(path)
            tkMessageBox.showinfo("TRV 2014.5","Eksport edukas")
        except:
            tkMessageBox.showerror("Viga","Valitud vormingusse ei saa salvestada või puudub asukohas kirjutamisõigus.")
    return 0
def getrhibin(h,gr,a):
    global sweeps
    global rhidata
    global paised
    if paised[0] == "DBZ" or paised[0] == "V" or paised[0] == "HCLASS" or paised[0] == "ZDR" or paised[0] == "KDP" or paised[0] == "RHOHV":
        kordaja=1/paised[25]
    if a < 0: return "Andmed puuduvad"
    if a > sweeps[-1]: return "Andmed puuduvad"
    for i in range(len(sweeps)):
        cond=0 if i == 0 else sweeps[i-1]
        if a > cond and a <= sweeps[i]:
            indeks=int(gr*kordaja)
            if len(rhidata[i]) <= indeks:
                val=-999
            else:
                val=rhidata[i][indeks]
            if float(val) != -999 and (paised[0] == 165 or paised[0] == "HCLASS"):
                val=hcanames[int(val)]
            elif float(val) == -999:
                val="Andmed puuduvad"
            return val
def getbin(azr):
    global hcanames
    global paised
    delta=None #Muudatus mitme värava vahel
    h=beamheight(azr[1],float(paised[17])) #Radarikiire kõrgus
    try:
        if paised[0] == 94:
            kordaja=1
        elif paised[0] == "ZDR" or paised[0] == "KDP" or paised[0] == "HCLASS" or paised[0] == "RHOHV" or paised[0] == "DBZ" or paised[0] == "V":
            kordaja=1/paised[25]
        else:
            kordaja=4
        azi=azr[0]-r2d(radials[0][0])
        azi+=360 if azi < 0 else 0
        kaugus=azr[1] if not isinstance(paised[0],int) else azr[1]/cos(d2r(float(paised[17])))
        val=str(radials[int(azi)][2][int(kaugus*kordaja)])
        delta=None
        if float(val) != -999 and (paised[0] == 99 or paised[0] == "V"):
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
    tkMessageBox.showinfo("TRV 2014.5", "TRV\n0.1\nTarmo Tanilsoo, 2013\ntarmotanilsoo@gmail.com")
    return 0
def keys_list():
    tkMessageBox.showinfo("Otseteed klaviatuuril","z - suurendamisrežiimi\np - ringiliikumisrežiimi\ni - infokogumiserežiimi\nr - algsuurendusse tagasi")
    return 0
def shouldirender(path):
    for i in path:
        if i > 0 and i < 2000:
            return True
    return False
def draw_infobox(x,y):
    global clickbox
    global clickbox2
    global clickboxloc
    global units
    global paised
    global rhishow
    andmed=getinfo(x,y)
    azrange=andmed[1]
    data=andmed[2]
    vaartus=data[0] if not rhishow else data
    row0=u"%s %s" % (vaartus, units[paised[0]]) if vaartus != "Andmed puuduvad" else "Andmed puuduvad"
    if not rhishow:        
        coords=andmed[0]
        latletter="N" if coords[0] > 0 else "S"
        lonletter="E" if coords[1] > 0 else "W"
        row1=u"%.5f°%s %.5f°%s" % (abs(coords[0]),latletter,abs(coords[1]),lonletter)
        row2=u"Asimuut: %.1f°" % (azrange[0])
        row3=u"Kaugus: %.3f km" % (azrange[1])
        row4=u"Kiire kõrgus: ~%.1f km" % (data[2])
        row5="" if data[1] == None else "G2G nihe: %.1f m/s" % (data[1])
    else:
        row1=u"Kaugus: %.3f km" % andmed[0]
        row2=u"Kõrgus: %.3f km" % andmed[1]
    kastikorgus=84 if not rhishow else 45
    kast=uuspilt("RGB",(170,kastikorgus),"#0000EE")
    kastdraw=Draw(kast)
    kastdraw.rectangle((0,0,170,16),fill="#000099")
    kastdraw.polygon((0,0,10,0,0,10,0,0),fill="#FFFFFF")
    kastdraw.text((9,1),text=row0, font=pildifont2)
    kastdraw.text((5,17),text=row1, font=pildifont)
    kastdraw.text((5,30),text=row2, font=pildifont)
    if not rhishow:
        kastdraw.text((5,43),text=row3, font=pildifont)
        kastdraw.text((5,56),text=row4, font=pildifont)
        if row5 != "": kastdraw.text((5,69),text=row5, font=pildifont)
    clickbox2=kast
    clickbox=PhotoImage(image=kast)
    clickboxloc=[x,y]
    w.itemconfig(clicktext,image=clickbox)
    w.coords(clicktext,(x+85,y+kastikorgus/2))
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
    global colortablenames
    global units
    tabel=loadcolortable("../colortables/"+colortablenames[product]+".txt")
    unit=units[product]
    tosmooth=1
    if product == 165:
        tosmooth=0
    increment=(maximum-minimum)/300.0
    legendimg=uuspilt("RGB",(35,325),"#000044")
    legenddraw=Draw(legendimg)
    for i in range(300):
        val=minimum+increment*i
        legenddraw.rectangle((25,324-i,35,324-i),fill=getcolor(tabel,val,tosmooth))
    step=1.0/increment
    majorstep=10
    if product == 159 or product == 163 or product == 165:
        majorstep=1
    if product == 161: #RHOHV aka CC
        majorstep=0.1
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
    global canvasdimensions
    coordsenne=""
    pikkus=len(data)
    kordaja=1
    if zoomlevel < 1:
        kordaja=int(1/zoomlevel)
    f=0
    hetkeseisusamm=1/pikkus
    hetkeseis=0
    for joon in data:
        e=0
        for path in joon:
            path0,path1=path
            if abs(path1-rlat) < 10 and abs(path0-rlon) < 10:
                if e % kordaja == 0:
                    posy,posx=geog2polar(path1,path0,rlat,rlon)
                    coords=getcoords(posx,posy,zoomlevel,render_center)
                    x,y=coords
                    if coordsenne=="": coordsenne=coords
                    if x < 3000 and x > -1000 and y < 3000 and y > -1000:
                        joonis.line((coordsenne,coords),fill=drawcolor,width=linewidth)
                        coordsenne=coords
                    else:
                        coordsenne=""
            else:
                coordsenne=""
            e+=1
        f+=1
        coordsenne=""
        if f % 200 == 0: update_progress(hetkeseis*canvasdimensions[0])
        hetkeseis+=hetkeseisusamm
    return 0
def update_progress(x):
    korgus=output.winfo_height()
    w.coords(progress,(0,korgus-66,x,korgus-56))
    w.update()
    return 0
def showrendered(pilt):
    global rendered
    rendered=PhotoImage(image=pilt)
    w.itemconfig(radaripilt,image=rendered)
def render_radials(radials,product=94):
    global rendered
    global rendered2
    global canvasctr
    global img_center
    global canvasbusy
    global canvasdimensions
    global joonis
    global render_center
    canvasbusy=True
    alguses=time.time()
    w.config(cursor="watch")
    w.itemconfig(progress,state=Tkinter.NORMAL)
    msgtostatus("Joonistan... radaripilt")
    pilt=uuspilt("RGB",(2000,2000),"#000022")
    joonis=Draw(pilt)
    current=0.0
    updateiter=0
    samm=1
    tabel=loadcolortable("../colortables/dbz.txt") #Vaikimisi produkt=94
    tosmooth=True
    if product == 99 or product == "V":
        samm=0.25 if product == 99 else paised[25]
        tabel=loadcolortable("../colortables/v.txt")
        drawlegend(99,-63.5,63.5)
    elif product == 159 or product == "ZDR":
        samm=0.25 if product == 159 else paised[25]
        tabel=loadcolortable("../colortables/zdr.txt")
        drawlegend(159,-6,6)
    elif product == 161 or product == "RHOHV":
        samm=0.25 if product == 161 else paised[25]
        tabel=loadcolortable("../colortables/rhohv.txt")
        drawlegend(161,0.2,1.05)
    elif product == 163 or product == "KDP":
        samm=0.25 if product == 163 else paised[25]
        tabel=loadcolortable("../colortables/kdp.txt")
        drawlegend(163,-2,7)
    elif product == 165 or product == "HCLASS":
        samm=0.25 if product == 165 else paised[25]
        tabel=loadcolortable("../colortables/hclass.txt")
        tosmooth=False
        drawlegend(165,0,12)
    elif product == "DBZ":
        samm=paised[25]
        drawlegend(94,-25,75)
    else:
        drawlegend(94,-25,75)
    radialslen=len(radials)
    hetkeseisusamm=1/radialslen
    hetkeseis=0
    for i in radials:
        az,d_az,gate=i
        kiiresuund=leiasuund(az,d_az,0,paised,zoomlevel,render_center,samm)
        x1,x2,y1,y2,dx1,dx2,dy1,dy2=kiiresuund        
        for val in gate:
            x1new=x1+dx1
            x2new=x2+dx2
            y1new=y1+dy1
            y2new=y2+dy2
            if val!= -999:
                path=(x1,y1,x2,y2,x2new,y2new,x1new,y1new)
                if shouldirender(path):
                    joonis.polygon(path, fill=getcolor(tabel,val,tosmooth))
            x1=x1new
            x2=x2new
            y1=y1new
            y2=y2new
        if current % 2==0:
            update_progress(hetkeseis*canvasdimensions[0])
        hetkeseis+=hetkeseisusamm
        current+=1
    #Geoandmete joonistamine
    rlat=float(paised[6])
    rlon=float(paised[7])
    img_center=canvasctr
    showrendered(pilt)
    w.coords(radaripilt,tuple(img_center)) #Tsentreeri pilt
    msgtostatus("Joonistan... rannajooned")
    drawmap(coastlines.points,rlat,rlon,(17,255,17))
    msgtostatus("Joonistan... järved")
    drawmap(lakes.points,rlat,rlon,(0,255,255),1)
    if rlon < 0:
        msgtostatus("Joonistan... Põhja-Ameerika tähtsamad maanteed")
        drawmap(major_NA_roads.points,rlat,rlon,(125,0,0),2)
    msgtostatus("Joonistan... jõed")
    drawmap(rivers.points,rlat,rlon,(0,255,255),1)
    msgtostatus("Joonistan... osariigid/maakonnad")
    drawmap(states.points,rlat,rlon,(255,255,255),1)
    msgtostatus("Joonistan... riigipiirid")
    drawmap(countries.points,rlat,rlon,(255,0,0),2)
    #Radari ikooni joonistamine tsentrisse 
    radaricon=laepilt("../images/radar.png")
    radarx=int(render_center[0])
    radary=int(render_center[1])
    pilt.paste(radaricon,[radarx-8,radary-8,radarx+8,radary+8],radaricon)
    #Kohanimed
    msgtostatus("Joonistan... kohanimed")
    kohanimed=open("places.json","r")
    punktid=json.load(kohanimed)
    kohanimed.close()
    #Kohanimed
    for kohad in punktid:
        if punktid[kohad]["min_zoom"] < zoomlevel:
            loc=geog2polar(punktid[kohad]["lat"],punktid[kohad]["lon"],rlat,rlon)
            coords=getcoords(loc[1],loc[0],zoomlevel,render_center)
            if coords[0] < 2000 and coords[0] > 0 and coords[1] < 2000 and coords[1] > 0:
                if punktid[kohad]["icon"] == None:
                    joonis.rectangle((coords[0]-2,coords[1]-2,coords[0]+2,coords[1]+2),fill="black")
                    joonis.rectangle((coords[0]-1,coords[1]-1,coords[0]+1,coords[1]+1),fill="white")
                    joonis.text((coords[0]+11,coords[1]-2),text=kohad,fill="black",font=pildifont)
                    joonis.text((coords[0]+10,coords[1]-3),text=kohad,font=pildifont)
                else:
                    iconfile=laepilt("../images/"+punktid[kohad]["icon"].lower()+".png")
                    x=int(coords[0])
                    y=int(coords[1])
                    pilt.paste(iconfile,[x-8,y-8,x+8,y+8],iconfile)
    rendered2=pilt
    showrendered(pilt)
    w.itemconfig(progress,state=Tkinter.HIDDEN)
    msgtostatus("Valmis")
    canvasbusy=False
    lopus=time.time()
    print "Aega kulus:", lopus-alguses,"sekundit"
    setcursor()
    return 0
def loadurl():
    global urlwindowopen
    if urlwindowopen == 0:
        urlwindowopen=1
        URLAken(output)
    return 0
def load():
    global paised
    global radials
    global clickbox
    global currentfilepath
    clickbox=""
    filed=tkFileDialog.Open(None,initialdir="../data")
    path=filed.show()
    if path != '': #Kui anti ette mõni fail.
        stream=file_read(path)
        currentfilepath=path
        msgtostatus("Dekodeerin...")
        if path[-4:]==".trv" and stream[0:2] == "BZ": #Kui on kokkupakitud TRV
            stream=bz2.decompress(stream) #Paki enne lahti.
        if path[-3:]!= ".h5" and stream[0:2] != "TT":
            fmt=0
        if path[-4:]==".trv" or stream[0:2] == "TT":
            fmt=1
        if path[-3:] == ".h5":
            fmt=2
        decodefile(stream,fmt)
        #try:
        
        #except Exception, err:
        #    msgtostatus("Programmiviga moodulis load: "+ str(err))
    return 0
def decodefile(stream,fmt=0): #Dekodeerib faili sisu
                            #FMT väärtused:
                            #0 - NEXRAD
                            #1 - TRV
                            #2 - HDF5
    global paised
    global radials
    global rhishow
    global renderagain
    global rhiaz
    if fmt == 0:
        paised=headers(stream)
        print headersdecoded(paised)
        draw_info(headersdecoded(paised))
        if paised[0] > 255:
            #Produkti kood ei saa olla suurem kui 255 (11111111).
            msgtostatus("Viga: Tegemist ei ole õiges formaadis failiga")
        if paised[0] == 94 or paised[0] == 99: 
            radials=valarray(decompress(stream),paised[18],paised[19])
            render_radials(radials,paised[0])
        elif paised[0] == 161 or paised[0] == 159 or paised[0] == 163:
            scale=paised[27]
            offset=paised[28]
            radials=valarray(decompress(stream),offset,scale,paised[0])
            render_radials(radials,paised[0])
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
            if not rhishow:
                render_radials(radials,paised[0])
            else:
                sweeps=tt_sweepslist(stream)
                if len(sweeps) > 1:
                    getrhi(rhiaz)
                    mkrhi(rhiaz)
                    tozoom()
                    renderagain=1
                else:
                    topan()
                    render_radials(radials,paised[0])
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
    global rhi
    zoom=1
    info=0
    rhi=0
    clearclicktext()
    setcursor()
    return 0
def topan(event=None):
    global zoom
    global paised
    global radials
    global info
    global rhi
    global rhishow
    global panimg
    global img_center
    global renderagain
    zoom=0
    info=0
    rhi=0
    clearclicktext()
    setcursor()
    if rhishow:
        w.coords(radaripilt,tuple(img_center))
        taskbarbtn1.config(image=panimg)
        taskbarbtn5.config(state=Tkinter.NORMAL)
        draw_info(headersdecoded(paised))
        if renderagain:
            renderagain=0
            render_radials(radials,paised[0])
        w.itemconfig(radaripilt,image=rendered)
        rhishow=0
    return 0
def toinfo(event=None):
    global zoom
    global info
    global rhi
    zoom=0
    info=1
    rhi=0
    setcursor()
    return 0
def resetzoom(event=None):
    global radials
    global paised
    global zoomlevel
    global canvasctr
    global render_center
    global img_center
    global rhishow
    global rhiaz
    global rhistart
    global rhiend
    if rhishow:
        rhistart=0
        rhiend=250
        mkrhi(rhiaz)
    else:
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
    global rhi
    global rhishow
    x=canvasdimensions[0]
    y=canvasdimensions[1]
    if not canvasbusy:
        if zoom:
            if not rhishow:
                dy=event.y-clickcoords[1]
                w.itemconfig(zoomrect, state=Tkinter.NORMAL)
                w.coords(zoomrect,(clickcoords[0]-dy,clickcoords[1]-dy,clickcoords[0]+dy,event.y))
            else:
                dx=event.x-clickcoords[0]
                w.itemconfig(zoomrect, state=Tkinter.NORMAL)
                w.coords(zoomrect,(clickcoords[0]-dx,-1,clickcoords[0]+dx,canvasdimensions[1]))
        else: #Ei suurenda
            if info: #Kui kogud piksli väärtust
                draw_infobox(event.x,event.y)
            else: #Liigud...
                if not rhishow: #Ning RHI'd pole ees.
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
    global sweeps
    global paised
    global rendered
    global info
    global rhi
    global rhiaz
    global rhishow
    global rhistart
    global rhiend
    if not canvasbusy:
        if zoom: #Kui olin suurendamas
            if not rhishow:
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
            else: #If was zooming among the RHI
                keskpunkt=rhix(clickcoords[0])
                kauguskeskpunktist=abs(rhix(event.x)-keskpunkt)
                samm=paised[25]
                if direction == 1:
                    rhistart=keskpunkt-kauguskeskpunktist
                    rhiend=keskpunkt+kauguskeskpunktist
                else:
                    kauguskeskpunktist*=(rhiend-rhistart)*2/kauguskeskpunktist
                    rhistart=keskpunkt-kauguskeskpunktist
                    rhiend=keskpunkt+kauguskeskpunktist
                if rhistart < 0: rhistart=0
                w.itemconfig(zoomrect, state=Tkinter.HIDDEN)
                mkrhi(rhiaz)
        elif rhi and not rhishow: ##Kui koguti RHI'd
            rhiaz=int(getinfo(event.x,event.y)[1][0])
            getrhi(rhiaz)
            rhistart=0
            rhiend=250
            mkrhi(rhiaz)
            tozoom()
        else: #Kui olin ringi liikumas
            if not info: #Kui ei olnud infokogumise režiimis
                if not rhishow:
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
    global clickboxloc
    global canvasbusy
    global canvasdimensions
    global rhishow
    global rhiagain
    global rhiaz
    dim=[output.winfo_width(),output.winfo_height()]
    if dim != sizeb4: #If there has been change in size...
        canvasdimensions=[dim[0],dim[1]-56]
        cenne=[w.winfo_width(),w.winfo_height()]
        cdim=[dim[0],dim[1]-56] #New dimensions for canvas
        delta=[(cdim[0]-cenne[0])/2,(cdim[1]-cenne[1])/2]
        w.config(width=cdim[0],height=cdim[1])
        w.coords(legend,(cdim[0]-18,cdim[1]/2))
        w.coords(radardetails,(cdim[0]/2,cdim[1]-20))
        img_center=[img_center[0]+delta[0],img_center[1]+delta[1]]
        canvasctr=[cdim[0]/2,cdim[1]/2]
        w.coords(radaripilt,tuple(img_center))
        clickboxloc=[clickboxloc[0]+delta[0],clickboxloc[1]+delta[1]]
        w.coords(clicktext,(clickboxloc[0]+85,clickboxloc[1]+42))
        sizeb4=dim
        if rhishow:
            if not canvasbusy:
                mkrhi(rhiaz)
    return 0
def getinfo(x,y):
    global render_center
    global canvasdimensions
    global zoomlevel
    global paised
    global rhishow
    global rhistart
    global rhiend
    dimx=canvasdimensions[0]
    dimy=canvasdimensions[1]
    pointx=x-dimx/2-(render_center[0]-1000)
    pointy=y-dimy/2-(render_center[1]-1000)
    rlat=paised[6]
    rlon=paised[7]
    if not rhishow:
        azrange=az_range(pointx,pointy,zoomlevel)
        return geocoords(azrange,float(rlat),float(rlon),float(zoomlevel)), azrange, getbin(azrange)
    else:
        gr=rhix(x)
        h=(canvasdimensions[1]-y-80)/((canvasdimensions[1]-120)/17.0)
        r=sqrt(gr**2+h**2)
        a=beamangle(h,r)
        return gr, h, getrhibin(h,gr,a)
def onmousemove(event):
    global canvasbusy
    global rhishow
    try:
        if not canvasbusy:
            x=event.x
            y=event.y
            info=getinfo(x,y)
            if not rhishow:
                lat=info[0][0]
                latl="N" if lat >= 0 else "S"
                lon=info[0][1]
                lonl="E" if lon >= 0 else "W"
                val=info[2][0]
                infostring=u"%.3f°%s %.3f°%s; Asimuut: %.1f°; Kaugus: %.3f km; Väärtus: %s" % (abs(lat),latl,abs(lon),lonl,floor(info[1][0]*10)/10.0,floor(info[1][1]*1000)/1000.0,val)
                msgtostatus(infostring)
            else:
                gr,h,val=info
                msgtostatus(u"x: %.3f km; y: %.3f km; Väärtus: %s" % (gr, h, val))
    except:
        pass
def file_read(path):
    andmefail=open(path,"rb")
    sisu=andmefail.read()
    andmefail.close()
    return sisu
#RHI spetsiiflised funktsioonid
def chooserhi(): #Vali RHI
    global currentfilepath
    global zoom
    global info
    global rhi
    global sweeps
    if paised[0]=="DBZ" or paised[0]=="V" or paised[0]=="HCLASS" or paised[0]=="RHOHV" or paised[0]=="KDP" or paised[0]=="ZDR":
        sisu=file_read(currentfilepath)
        if sisu[0:2]=="BZ": sisu=bz2.decompress(sisu)
        sweeps=tt_sweepslist(sisu)
        if len(sweeps) > 1:
            clearclicktext()
            zoom=0
            info=0
            rhi=1
            msgtostatus("Kliki väraval, millest soovid RHI'd teha")
    else:
        tkMessageBox.showerror("Vale formaat","Esialgu on võimalik luua RHI'd vaid TRV formaadis andmetest")
def rhiypix(h,bottom):
    samm=(bottom-120)/17.0
    return bottom-80-h*samm
def rhiy(r,a,bottom):
    samm=(bottom-120)/17.0
    return bottom-80-beamheight(r,a)*samm
def rhix(x):
    global rhistart
    global rhiend
    global canvasdimensions
    return rhistart+(x-50)*((rhiend-rhistart)/(canvasdimensions[0]-100.0))
##Vastupidised funktsioonid RHI koordinaatidele
##Reverse functions of RHI coords
def getrhi(az):
    global sweeps
    global currentfilepath
    global rhidata
    global canvasbusy
    rhidata=[]
    sisu=file_read(currentfilepath)
    if sisu[0:2] == "BZ": sisu=bz2.decompress(sisu)
    canvasbusy=1
    for i in range(len(sweeps)):
        rhidata.append(tt_singlegate(sisu,az,i))
        msgtostatus("Loen elevatsiooni: "+str(sweeps[i])+u"°")
        w.update()
    canvasbusy=0
    return 0
def mkrhi(az):
    global paised
    global canvasbusy
    global sweeps
    global rhidata
    global rhiout
    global rhiout2
    global ppiimg
    global rhishow
    global canvasctr
    global pildifont
    global rhistart
    global rhiend
    global colortablenames
    if not canvasbusy:
        draw_info(rhiheadersdecoded(paised,az))
        msgtostatus("Joonistan pseudoRHI'd")
        pikkus=int(w.cget("height"))
        laius=int(w.cget("width"))
        pilt=uuspilt("RGB", (laius,pikkus), "#000022") 
        joonis=Draw(pilt)
        samm=paised[25]
        varvitabel=loadcolortable("../colortables/"+colortablenames[paised[0]]+".txt") #Load a color table
        xsamm=(laius-100.0)/((rhiend-rhistart)/samm) if rhiend != rhistart else 0
        a=0
        a0=0
        for i in range(len(sweeps)):
            r=0
            a=sweeps[i]
            x0=50
            first=1
            for j in rhidata[i]:
                if rhistart-r <= samm and r < rhiend:
                    if first:
                        x0+=(r-rhistart)*xsamm/samm
                        first=0
                    x1=x0+xsamm if rhiend-r > samm else laius-50
                    if j != -999.0:
                        if r-rhistart < 0:
                            path=[50,rhiy(r, a0, pikkus),x1,rhiy(r+samm, a0, pikkus),x1,rhiy(r+samm,a,pikkus),50,rhiy(r,a,pikkus)]
                        else:
                            path=[x0,rhiy(r, a0, pikkus),x1,rhiy(r+samm, a0, pikkus),x1,rhiy(r+samm,a,pikkus),x0,rhiy(r,a,pikkus)]
                        joonis.polygon(path,fill=getcolor(varvitabel,j))
                    x0=x1
                r+=samm
            a0=a
        for k in range (0,18):
            korgus=rhiypix(k,pikkus)
            joonis.line((50,korgus,laius-50,korgus),fill="white")
            joonis.text((30,korgus-10),text=str(k),fill="white",font=pildifont)
        ulatus=(rhiend-rhistart)
        teljesamm=ulatus/5.0
        teljexsamm=(laius-100)/5.0
        for l in range(5):
            joonis.line((50+teljexsamm*l,rhiypix(0,pikkus)+10,50+teljexsamm*l,rhiypix(17,pikkus)),fill="white")
            joonis.text((50+teljexsamm*l-10,rhiypix(0,pikkus)+15),text=str(round(rhistart+teljesamm*l,2)),fill="white",font=pildifont)
        joonis.line((50,rhiypix(0,pikkus),50,rhiypix(17,pikkus)),fill="white")
        joonis.text((laius/2,pikkus-50),text="r (km)",fill="white",font=pildifont) #x telje silt
        joonis.text((10,5),text="h (km)", fill="white", font=pildifont)
        rhiout2=pilt
        rhiout=PhotoImage(image=rhiout2)
        pilt.save("../../rhitest.png")
        taskbarbtn1.config(image=ppiimg)
        taskbarbtn5.config(state=Tkinter.DISABLED)
        w.coords(radaripilt,tuple(canvasctr))
        w.itemconfig(radaripilt, image=rhiout)
        msgtostatus("Valmis")
        rhishow=1
    return 0
clickcoords=[]
output=Tkinter.Tk()
output.title("TRV 2014.5")
output.bind("<Configure>",on_window_reconf)
output.config(background="#000044")
##Drawing the menu
menyy = Tkinter.Menu(output,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
output.config(menu=menyy)
failimenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
radarmenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
abimenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
menyy.add_cascade(label="Fail", menu=failimenyy)
menyy.add_cascade(label="NEXRAD", menu=radarmenyy)
menyy.add_cascade(label="Abi", menu=abimenyy)
failimenyy.add_command(label="Ava andmefail", command=load)
failimenyy.add_command(label="Ava URL", command=loadurl)
failimenyy.add_separator()
failimenyy.add_command(label="Ekspordi pilt", command=exportimg)
failimenyy.add_separator()
failimenyy.add_command(label="Lõpeta", command=output.destroy)
radarmenyy.add_command(label="0.5° peegelduvus", command=lambda: fetchnexrad("p94r0"))
radarmenyy.add_command(label="0.5° radiaalkiirus", command=lambda: fetchnexrad("p99v0"))
radarmenyy.add_command(label="0.5° diferentsiaalne peegelduvus", command=lambda: fetchnexrad("159x0"))
radarmenyy.add_command(label="0.5° korrelatsioonikoefitsent", command=lambda: fetchnexrad("161c0"))
radarmenyy.add_command(label="0.5° spetsiifiline diferentsiaalne faas", command=lambda: fetchnexrad("163k0"))
radarmenyy.add_command(label="0.5° hüdrometeoori klassifikatsioon", command=lambda: fetchnexrad("165h0"))
radarmenyy.add_separator()
radarmenyy.add_command(label="Jaama valik",command=choosenexrad)
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
output.bind("h",chooserhi)
kyljeraam=Tkinter.Frame(output)
kyljeraam.grid(row=2,column=0,sticky="n")
moderaam=Tkinter.Frame(kyljeraam)
moderaam.grid(row=1,column=0)
panimg=PhotoImage(file="../images/pan.png")
zoomimg=PhotoImage(file="../images/zoom.png")
resetzoomimg=PhotoImage(file="../images/resetzoom.png")
infoimg=PhotoImage(file="../images/info.png")
rhiimg=PhotoImage(file="../images/rhi.png")
ppiimg=PhotoImage(file="../images/ppi.png")
taskbarbtn1=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=panimg, command=topan)
taskbarbtn1.grid(row=0,column=0)
taskbarbtn2=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=zoomimg, command=tozoom)
taskbarbtn2.grid(row=0,column=1)
taskbarbtn3=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=resetzoomimg, command=resetzoom)
taskbarbtn3.grid(row=0,column=2)
taskbarbtn4=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=infoimg, command=toinfo)
taskbarbtn4.grid(row=0,column=3)
taskbarbtn5=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=rhiimg, command=chooserhi)
taskbarbtn5.grid(row=0,column=4)
status=Tkinter.Label(output, text="", justify=Tkinter.LEFT, anchor="w", fg="yellow", bg="#000044")
status.grid(row=3,column=0,sticky="w")
output.mainloop()

