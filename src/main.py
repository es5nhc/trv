#!/usr/bin/python2
# -*- coding: utf-8 -*-
#


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
#

from __future__ import division

import bz2
from decoderadar import *
from PIL.Image import open as laepilt
from PIL.Image import new as uuspilt
from PIL.ImageDraw import Draw
from PIL.ImageTk import PhotoImage, BitmapImage
from PIL import ImageFont
from math import floor, sqrt, radians as d2r, degrees as r2d, cos
from colorconversion import *
from coordinates import *
import sys
import datetime
import Tkinter
import tkFileDialog
import tkMessageBox
import urllib2
import json
from nexrad_level2 import NEXRADLevel2File
#Importing geodata
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
class AddRMAXChooser(Tkinter.Toplevel):
    def __init__(self, parent, title = None):
        global paised
        Tkinter.Toplevel.__init__(self,parent)
        self.title("Liida Rmax")
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        self.config(background="#000044")
        #Labels
        az0title=Tkinter.Label(self,text="Algasimuut(°):",bg="#000044",fg="#ffff00")
        az0title.grid(column=0,row=0,sticky="e")
        az1title=Tkinter.Label(self,text="Lõppasimuut(°):",bg="#000044",fg="#ffff00")
        az1title.grid(column=0,row=1,sticky="e")
        r0title=Tkinter.Label(self,text="Algkaugus(km):",bg="#000044",fg="#ffff00")
        r0title.grid(column=0,row=2,sticky="e")
        r1title=Tkinter.Label(self,text="Lõppkaugus(km):",bg="#000044",fg="#ffff00")
        r1title.grid(column=0,row=3,sticky="e")
        prftitle=Tkinter.Label(self,text="PRF(Hz):",bg="#000044",fg="#ffff00")
        prftitle.grid(column=0,row=4,sticky="e")
        #Text variables
        self.az0=Tkinter.StringVar()
        self.az1=Tkinter.StringVar()
        self.r0=Tkinter.StringVar()
        self.r1=Tkinter.StringVar()
        self.prf=Tkinter.StringVar()
        self.prf.set("570")
        #Text fields
        az0field=Tkinter.Entry(self,textvariable=self.az0,fg="#ffff00",bg="#000044",highlightbackground="#000044",selectbackground="#000099",selectforeground="#ffff00")
        az0field.grid(column=1,row=0,sticky="w")
        az1field=Tkinter.Entry(self,textvariable=self.az1,fg="#ffff00",bg="#000044",highlightbackground="#000044",selectbackground="#000099",selectforeground="#ffff00")
        az1field.grid(column=1,row=1,sticky="w")
        r0field=Tkinter.Entry(self,textvariable=self.r0,fg="#ffff00",bg="#000044",highlightbackground="#000044",selectbackground="#000099",selectforeground="#ffff00")
        r0field.grid(column=1,row=2,sticky="w")
        r1field=Tkinter.Entry(self,textvariable=self.r1,fg="#ffff00",bg="#000044",highlightbackground="#000044",selectbackground="#000099",selectforeground="#ffff00")
        r1field.grid(column=1,row=3,sticky="w")
        prffield=Tkinter.Entry(self,textvariable=self.prf,fg="#ffff00",bg="#000044",highlightbackground="#000044",selectbackground="#000099",selectforeground="#ffff00")
        prffield.grid(column=1,row=4,sticky="w")
        #Button
        liidabutton=Tkinter.Button(self,command=self.addrmax,text="Liida",bg="#000044",fg="#ffff00",activebackground="#000099", highlightbackground="#000044", activeforeground="#ffff00")
        liidabutton.grid(column=1,row=5,sticky="w")
        #And now the main loop
        self.mainloop()
    def addrmax(self):
        global radials
        az0=d2r(float(self.az0.get()))
        az1=d2r(float(self.az1.get()))
        r0=float(self.r0.get())
        r1=float(self.r1.get())
        prf=float(self.prf.get())
        rmax=299792.458/prf/2
        if isinstance(paised[0],int): rmax*=cos(d2r(float(paised[17])))
        r0new=r0+rmax
        r1new=r1+rmax
        for i in xrange(len(radials)):
            r=radials[i]
            if az0 < az1:
                if r[0] > az0 and not r[0] >= az1:
                    slicestart=int(r0/paised[25])
                    sliceend=int(r1/paised[25])
                    rmaxbins=int(round(rmax/paised[25])) #Amount of bins that coorespond to Rmax
                    paddingamt=int(round(r1new/paised[25]))-len(r[2])
                    for j in xrange(paddingamt):
                        radials[i][2].append(None)
                    for k in xrange(slicestart,sliceend,1):
                        radials[i][2][k+rmaxbins]=radials[i][2][k]
                        radials[i][2][k]=None
        self.onclose()
        render_radials()
    def onclose(self):
        global rmaxaddopen
        rmaxaddopen=0
        self.destroy()
class NEXRADChooser(Tkinter.Toplevel): #Choice of NEXRAD station
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
            tkMessageBox.showerror("TRV 2014.6","Palun vali jaam!")
    def onclose(self):
        global nexradchooseopen
        nexradchooseopen=0
        self.destroy()
class URLAken(Tkinter.Toplevel): ##Dialog to open a web URL
    def __init__(self, parent, title = None):
        Tkinter.Toplevel.__init__(self,parent)
        self.title("Ava fail internetist")
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        self.config(background="#000044")
        urltitle=Tkinter.Label(self,text="URL:",bg="#000044",fg="#ffff00")
        urltitle.grid(column=0,row=0)
        self.url=Tkinter.StringVar()
        self.url.set("http://laguja.no-ip.org:9875/radar/sn.emhi")
        urlentry=Tkinter.Entry(self,textvariable=self.url,width=70,fg="#ffff00",bg="#000044",highlightbackground="#000044",selectbackground="#000099",selectforeground="#ffff00")
        urlentry.grid(column=1,row=0)
        downloadbutton=Tkinter.Button(self,text="Ava",command=self.laealla,bg="#000044",fg="#ffff00",activebackground="#000099", highlightbackground="#000044", activeforeground="#ffff00")
        downloadbutton.grid(column=0,row=1,sticky="w")
        self.mainloop()
    def laealla(self):
        global currentfilepath
        aadress=self.url.get()
        try:
            url=urllib2.urlopen(aadress,timeout=10)
            sisu=url.read()
            if aadress[-3:]==".h5":
                fmt=1
            else:
                fmt=0
            self.onclose()
            #Save received content into a file cache
            currentfilepath="../cache/urlcache"
            cachefile=open(currentfilepath,"wb")
            cachefile.write(sisu)
            cachefile.close()
            load(currentfilepath)
        except:
            print sys.exc_info()
            tkMessageBox.showerror("TRV 2014.6","Faili allalaadimisel juhtus viga!")
    def onclose(self):
        global urlwindowopen
        urlwindowopen=0
        self.destroy()
sizeb4=[] #Latest window dimensions for on_window_reconf 
rlegend=None #Legend as PhotoImage
infotekst=None #Information as PhotoImage
clickbox=None #Pixel information as PhotoImage
rendered=None #Rendered radar image as PhotoImage
rhiout=None #PseudoRHI as PhotoImage
#Above as an PIL/Pillow image.
rlegend2=uuspilt("RGB",(1,1))
infotekst2=uuspilt("RGB",(1,1))
clickbox2=uuspilt("RGB",(1,1))
rendered2=uuspilt("RGB",(1,1))
rhiout2=uuspilt("RGB",(1,1))
currentfilepath=None #Path to presently open file
#Pildifontide laadimine
pildifont=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",12)
pildifont2=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",13)
canvasbusy=False
nexradstn="kbmx" #Chosen NEXRAD station
urlwindowopen=0 #1 if dialog to open an URL is open
nexradchooseopen=0 #1 if dialog to choose a nexrad station is open
rmaxaddopen=0 #1 if configuration window to add Rmax to chunk of data is open.
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
level2fail=False #Placeholder for pyart.io.nexrad_level2.NEXRADLevel2File object
canvasdimensions=[600,400]
canvasctr=[300,200]
clickboxloc=[0,0]
paised=[]
radials=[]
rhidata=[]
sweeps=[] #All elevation levels
productsweeps=[] #Only the elevation levels for a particular product
units={94:"dBZ", #Defining units for particular products
       99:"m/s",
       159:"dBZ",
       161:None,
       163:u"°/km",
       165:None,
       "DBZ":"dBZ",
       "REF":"dBZ",
       "ZDR":"dBZ",
       "RHOHV": None,
       "RHO": None,
       "HCLASS":None,
       "KDP":u"°/km",
       "V":"m/s",
       "VEL":"m/s",
       "VRAD": "m/s",
       "SW": "m/s",
       "WRAD": "m/s",
       "PHI": u"°",
       "PHIDP": u"°"}
img_center=[300,200]
render_center=[1000,1000]
hcanames=["Bioloogiline", #Hydrometeor classifications in WSR-88D
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
                 "REF":"dbz",
                 "VRAD":"v",
                 "V":"v",
                 "VEL":"v",
                 99:"v",
                 159:"zdr",
                 "ZDR":"zdr",
                 161:"rhohv",
                 "RHOHV":"rhohv",
                 "RHO":"rhohv",
                 163:"kdp",
                 "KDP":"kdp",
                 165: "hclass",
                 "HCLASS": "hclass",
                 "PHI": "phi",
                 "PHIDP": "phidp",
                 "WRAD": "sw",
                 "SW": "sw"} #Names for color tables according to product
def configrmaxadd():
    global rmaxaddopen
    if rmaxaddopen == 0:
        rmaxaddopen=1
        AddRMAXChooser(output)
    return 0
def choosenexrad(): #NEXRAD jaama valiku akna avamine
    global nexradchooseopen
    if nexradchooseopen == 0:
        nexradchooseopen=1
        NEXRADChooser(output)
def fetchnexrad(product): #Downloading a current NEXRAD Level 3 file from NOAA's FTP
    global nexradstn
    global rhishow
    global currentfilepath
    if rhishow: topan()    
    product_choice.config(state=Tkinter.NORMAL)
    elevation_choice.config(state=Tkinter.NORMAL)
    populatenexradmenus(product)
    print nexradstn,product
    url="ftp://tgftp.nws.noaa.gov/SL.us008001/DF.of/DC.radar/DS."+product+"/SI."+nexradstn+"/sn.last"
    try:
        ftp=urllib2.urlopen(url,timeout=10)
        sisu=ftp.read()
        ftp.close()
        #Caching
        currentfilepath="../cache/nexradcache/"+product
        cachefile=open(currentfilepath,"wb")
        cachefile.write(sisu)
        cachefile.close()
        load(currentfilepath,True)
    except:
        print sys.exc_info()
        tkMessageBox.showerror("TRV 2014.6","Allalaadimine ebaõnnestus!")
def activatecurrentnexrad():
    product_choice.config(state=Tkinter.NORMAL)
    elevation_choice.config(state=Tkinter.NORMAL)
    fetchnexrad("p94r0")
    return 0
def populatenexradmenus(product="p94r0"):
    level3elevs=["Lõik 1","Lõik 2","Lõik 3","Lõik 4"]
    ids={"p94":"DBZ",
         "p99":"VRAD",
         "159":"ZDR",
         "161":"RHOHV",
         "163":"KDP",
         "165":"HCLASS"}
    elevation_choice["menu"].delete(0, 'end')
    for i in xrange(4):
        productcode=product[:-1]+str(i)
        elevation_choice["menu"].add_command(label=level3elevs[i],command=lambda x=productcode: fetchnexrad(x))
    index=product[-1]
    chosen_elevation.set(str(level3elevs[int(product[-1])]))
    chosen_product.set(ids[product[0:3]])
    product_choice["menu"].delete(0, 'end')
    product_choice["menu"].add_command(label="DBZ",command=lambda x=index: fetchnexrad("p94r"+index))
    product_choice["menu"].add_command(label="VRAD",command=lambda x=index: fetchnexrad("p99v"+index))
    product_choice["menu"].add_command(label="ZDR",command=lambda x=index: fetchnexrad("159x"+index))
    product_choice["menu"].add_command(label="RHOHV",command=lambda x=index: fetchnexrad("161c"+index))
    product_choice["menu"].add_command(label="KDP",command=lambda x=index: fetchnexrad("163k"+index))
    product_choice["menu"].add_command(label="HCLASS",command=lambda x=index: fetchnexrad("165h"+index))
    return 0
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
    if path != None:
        try:
            outimage=uuspilt("RGB",(x,y),"#000022")
            joonis=Draw(outimage)
            if not rhishow:
                if rendered != None: outimage.paste(rendered2.crop((cx-halfx,cy-halfy,cx+halfx,cy+halfy)),((0,0,x,y))) #PPI
            else:
                outimage.paste(rhiout2,(0,0,x,y)) #PseudoRHI
            if clickbox != None: outimage.paste(clickbox2,(cbx,cby+1,cbx+170,cby+cbh+1))
            if rlegend != None: outimage.paste(rlegend2,(x-35,halfy-163,x,halfy+162))
            if infotekst != None: outimage.paste(infotekst2,(halfx-250,y-30,halfx+250,y-10))
            outimage.save(path)
            tkMessageBox.showinfo("TRV 2014.6","Eksport edukas")
        except:
            tkMessageBox.showerror("Viga","Valitud vormingusse ei saa salvestada või puudub asukohas kirjutamisõigus.")
    return 0
def getrhibin(h,gr,a):
    global productsweeps
    global rhidata
    global paised
    kordaja=1/paised[25]
    if a < 0: return "Andmed puuduvad"
    if a > productsweeps[-1]: return "Andmed puuduvad"
    for i in xrange(len(productsweeps)):
        cond=0 if i == 0 else productsweeps[i-1]
        if a > cond and a <= productsweeps[i]:
            indeks=int(gr*kordaja)
            if len(rhidata[i]) <= indeks:
                val=None
            else:
                val=rhidata[i][indeks]
            if float(val) != None and (paised[0] == 165 or paised[0] == "HCLASS"):
                val=hcanames[int(val)]
            elif float(val) == None:
                val="Andmed puuduvad"
            return val
def getbin(azr):
    global hcanames
    global paised
    global radials
    delta=None #Difference between adjacent azimuths
    h=beamheight(azr[1],float(paised[17])) #Radar beam height
    try:
        azalg=d2r(azr[0])
        for i in xrange(len(radials)):
            vahe=azalg-radials[i][0]
            if vahe < radials[i][1] and vahe > 0:
                azi=i
                break
        if paised[0] == 94:
            kordaja=1
        elif paised[0] == "ZDR" or paised[0] == "KDP" or paised[0] == "HCLASS" or paised[0] == "RHOHV" or paised[0] == "DBZ" or paised[0] == "V" or paised[0] == "VRAD":
            kordaja=1/paised[25]
        else:
            kordaja=4
        kaugus=azr[1] if not isinstance(paised[0],int) else azr[1]/cos(d2r(float(paised[17])))
        mindistance=radials[int(azi)][3]
        if kaugus >= mindistance:
            val=str(radials[int(azi)][2][int((kaugus-mindistance)*kordaja)])
        else:
            val=None
        delta=None
        if float(val) != None and (paised[0] == 99 or paised[0] == "V" or paised[0] == "VRAD" or paised[0] == "VEL"):
            valprev=radials[int(azi)-1][2][int(azr[1]*kordaja)]
            delta=abs(float(val)-valprev) if valprev != None else None
        elif float(val) != None and paised[0] == 165 or paised[0] == "HCLASS":
            val=hcanames[int(val)]
        elif float(val) == None: val = "Andmed puuduvad"
    except: val = "Andmed puuduvad"
    return val, delta, h
def msgtostatus(msg):
    status.config(text=msg)
    return 0
def about_program():
    tkMessageBox.showinfo("TRV 2014.6", "TRV\n2014.6\nTarmo Tanilsoo, 2014\ntarmotanilsoo@gmail.com")
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
        row5=None if data[1] == None else "G2G nihe: %.1f m/s" % (data[1])
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
        if row5 != None: kastdraw.text((5,69),text=row5, font=pildifont)
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
    for i in xrange(300):
        val=minimum+increment*i
        legenddraw.rectangle((25,324-i,35,324-i),fill=getcolor(tabel,val,tosmooth))
    step=1.0/increment
    majorstep=10
    if product == "PHI":
        majorstep=45
    if product == 159 or product == 163 or product == 165:
        majorstep=1
    if product == 161: #RHOHV aka CC
        majorstep=0.1
    firstten=int(majorstep+minimum-minimum%majorstep)
    if firstten == majorstep+minimum: firstten = minimum
    ystart=324-(firstten-minimum)*step
    lastten=int(maximum-maximum%majorstep)
    hulk=int((lastten-firstten)/majorstep)
    yend=ystart-majorstep*step*hulk #If the next full step is too close to the edge.
    if yend < 30: hulk-=1 #Let's not list this last point on legend
    legenddraw.text((5,0),text=unit, font=pildifont)
    for j in xrange(hulk+1):
        y=ystart-majorstep*step*j
        if product != 165: #Other products have a numeric value
            legendtext=str(firstten+j*majorstep)
        else:
            legendlist=["BI","AP","IC","DS","WS","RA","+RA","BDR","GR","HA","UNK","RF"]; #List of classifications
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
    coordsenne=None
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
                    if coordsenne==None: coordsenne=coords
                    if x < 3000 and x > -1000 and y < 3000 and y > -1000:
                        joonis.line((coordsenne,coords),fill=drawcolor,width=linewidth)
                        coordsenne=coords
                    else:
                        coordsenne=None
            else:
                coordsenne=None
            e+=1
        f+=1
        coordsenne=None
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
def render_radials():
    global rendered
    global rendered2
    global canvasctr
    global img_center
    global canvasbusy
    global radials
    global paised
    global canvasdimensions
    global joonis
    global render_center
    product=paised[0]
    canvasbusy=True
    alguses=time.time()
    w.config(cursor="watch")
    w.itemconfig(progress,state=Tkinter.NORMAL)
    msgtostatus("Joonistan... radaripilt")
    pilt=uuspilt("RGB",(2000,2000),"#000022")
    joonis=Draw(pilt)
    current=0.0
    updateiter=0
    samm=paised[25]
    tabel=loadcolortable("../colortables/"+colortablenames[product]+".txt")
    tosmooth=True
    if product == 99 or product == "V" or product == "VRAD" or product == "VEL":
        drawlegend(99,-63.5,63.5)
    elif product == 159 or product == "ZDR":
        drawlegend(159,-6,6)
    elif product == 161 or product == "RHOHV" or product == "RHO":
        drawlegend(161,0.2,1.05)
    elif product == 163 or product == "KDP":
        drawlegend(163,-2,7)
    elif product == 165 or product == "HCLASS":
        tosmooth=False
        drawlegend(165,0,12)
    elif product == "DBZ" or product == "REF":
        drawlegend(94,-25,75)
    elif product == "SW" or product == "WRAD":
        drawlegend("SW",0,30)
    elif product == "PHI":
        drawlegend("PHI",0,180)
    else:
        drawlegend(94,-25,75)
    radialslen=len(radials)
    hetkeseisusamm=1/radialslen
    hetkeseis=0
    for i in radials:
        az,d_az,gate,mindistance=i
        kiiresuund=leiasuund(az,d_az,mindistance,paised,zoomlevel,render_center,samm)
        x1,x2,y1,y2,dx1,dx2,dy1,dy2=kiiresuund
        varvid=map(lambda y,x=tabel,z=tosmooth: getcolor(x,y,z),gate)
        for val in varvid:
            x1new=x1+dx1
            x2new=x2+dx2
            y1new=y1+dy1
            y2new=y2+dy2
            if val!= None:
                path=(x1,y1,x2,y2,x2new,y2new,x1new,y1new)
                if shouldirender(path):
                    joonis.polygon(path, fill=val)
            x1=x1new
            x2=x2new
            y1=y1new
            y2=y2new
        if current % 2==0:
            update_progress(hetkeseis*canvasdimensions[0])
        hetkeseis+=hetkeseisusamm
        current+=1
    #Drawing geodata
    rlat=float(paised[6])
    rlon=float(paised[7])
    img_center=canvasctr
    showrendered(pilt)
    w.coords(radaripilt,tuple(img_center)) #Center image
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
    #Drawing radar icon into the center
    radaricon=laepilt("../images/radar.png")
    radarx=int(render_center[0])
    radary=int(render_center[1])
    pilt.paste(radaricon,[radarx-8,radary-8,radarx+8,radary+8],radaricon)
    #Placenames
    msgtostatus("Joonistan... kohanimed")
    kohanimed=open("places.json","r")
    punktid=json.load(kohanimed)
    kohanimed.close()
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
def reloadfile():
    global currentfilepath
    if currentfilepath != "":
        load(currentfilepath)
    return 0
def load(path=None,current=False):
    global paised
    global radials
    global clickbox
    global currentfilepath
    global level2fail #Linguistic note: "Fail" in the variable name does not
                      #imply failure - it is Estonian for "file."
    clickbox=None
    level2fail=None #Clear the old level 2 file in case one was opened
    if path == None:
        filed=tkFileDialog.Open(None,initialdir="../data")
        path=filed.show()
    if path != '': #If a file was given
        stream=file_read(path)
        currentfilepath=path
        msgtostatus("Dekodeerin...")
        if not current: #If not loading current NEXRAD data
            if path[-3:]== ".h5":
                product_choice.config(state=Tkinter.NORMAL)
                elevation_choice.config(state=Tkinter.NORMAL)
                fmt=1
            elif stream[0:4] == "AR2V":
                product_choice.config(state=Tkinter.NORMAL)
                elevation_choice.config(state=Tkinter.NORMAL)
                level2fail=NEXRADLevel2File(currentfilepath) #Load a Level 2 file
                fmt=2
            else:
                product_choice.config(state=Tkinter.DISABLED)
                elevation_choice.config(state=Tkinter.DISABLED)
                product_choice['menu'].delete(0, 'end')
                elevation_choice['menu'].delete(0, 'end')
                chosen_product.set(None)
                chosen_elevation.set(None)
                fmt=0
        else:
            fmt=0
        decodefile(stream,fmt)
    return 0
def decodefile(stream,fmt=0): #Decodes file content
                            #FMT values:
                            #0 - NEXRAD Level 3
                            #1 - HDF5
                            #2 - NEXRAD Level 2
    global paised
    global radials
    global sweeps
    global rhishow
    global renderagain
    global chosen_elevation
    global currentfilepath
    global rhiaz
    global level2fail
    if fmt == 0:
        paised=headers(stream)
        print headersdecoded(paised)
        draw_info(headersdecoded(paised))
        if paised[0] > 255:
            #As far as Level 3 goes, the product code cannot exceed 255 (11111111).
            msgtostatus("Viga: Tegemist ei ole õiges formaadis failiga")
        if paised[0] == 94 or paised[0] == 99: 
            radials=valarray(decompress(stream),paised[18],paised[19])
            render_radials()
        elif paised[0] == 161 or paised[0] == 159 or paised[0] == 163:
            scale=paised[27]
            offset=paised[28]
            radials=valarray(decompress(stream),offset,scale,paised[0])
            render_radials()
        if paised[0] == 165:
            minval=0
            increment=1
            radials=valarray(decompress(stream),minval,increment,paised[0])
            render_radials()
    elif fmt == 1:
        produktid=hdf5_productlist(currentfilepath)
        sweeps=hdf5_sweepslist(currentfilepath)
        paised=hdf5_headers(currentfilepath,produktid[0],sweeps[0])
        print paised
        draw_info(headersdecoded(paised))
        radials=hdf5_valarray(currentfilepath)
        product_choice['menu'].delete(0, 'end')
        elevation_choice['menu'].delete(0, 'end')
        for i in produktid:
            product_choice['menu'].add_command(label=i, command=lambda produkt=i: change_product(produkt))
        chosen_product.set(produktid[0])
        for j in xrange(len(sweeps)):
            elevation_choice['menu'].add_command(label=str(float(sweeps[j])), command=lambda index=j: change_elevation(index))
        chosen_elevation.set(str(float(sweeps[0])))
        if not rhishow:
            render_radials()
        else:
            if len(sweeps) > 1:
                getrhi(rhiaz)
                mkrhi(rhiaz)
                tozoom()
                renderagain=1
            else:
                topan()
                render_radials()
    elif fmt == 2:
        product_choice['menu'].delete(0, 'end')
        elevation_choice['menu'].delete(0, 'end')
        sweeps=level2_sweepslist(level2fail)
        for i in xrange(len(sweeps)):
            elevation_choice['menu'].add_command(label=str(round(float(sweeps[i]),2)), command=lambda index=i: change_elevation(index))
        firstmoments=level2fail.scan_info()[0]["moments"] #First moments of the first scan, as that is going to be loaded by default.
        for j in firstmoments:
            product_choice["menu"].add_command(label=j, command=lambda moment=j: change_product(moment,0))
        chosen_elevation.set(str(sweeps[0]))
        chosen_product.set("REF")
        paised=level2_headers(level2fail)
        draw_info(headersdecoded(paised))
        radials=level2_valarray(level2fail)
        render_radials()
    return 0
def change_elevation(index):
    global radials
    global canvasbusy
    global sweeps
    global currentfilepath
    global level2fail
    if not canvasbusy:
        if currentfilepath[-3:]== ".h5":
            paised[17]=sweeps[index]
            chosen_elevation.set(str(float(paised[17])))
            try:
                radials=hdf5_valarray(currentfilepath,hdf5_leiaskann(currentfilepath,paised[0],index))
                draw_info(headersdecoded(paised))
                render_radials()
            except:
                msgtostatus("Sellel kõrgustasemel seda produkti ei leitud.")
        elif level2fail:
            paised[17]=sweeps[index]
            chosen_elevation.set(str(float(paised[17])))
            product_choice['menu'].delete(0, 'end') #Clean up products menu for below.
            #Moments available for a particular scan
            moments=level2fail.scan_info()[index]["moments"] #First moments of the first scan, as that is going to be loaded by default.
            for j in moments:
                product_choice["menu"].add_command(label=j, command=lambda scan=index, moment=j: change_product(moment,index))
            #Load data.
            try:
                radials=level2_valarray(level2fail, paised[0], index)
            except: #Most likely not found, defaulting back to reflectivity product, which should be present at all scans.
                radials=level2_valarray(level2fail, "REF", index)
                chosen_product.set("REF")
            draw_info(headersdecoded(paised))
            if radials != None: render_radials() #If the data is in fact there..
    return 0
def change_product(newproduct,level2scan=0):
    global sweeps
    global radials
    global paised
    global canvasbusy
    global currentfilepath
    global level2fail
    if not canvasbusy:
        if currentfilepath[-3:] == ".h5":
            chosen_product.set(newproduct)
            paised[0]=newproduct
            try:
                radials=hdf5_valarray(currentfilepath,hdf5_leiaskann(currentfilepath,newproduct,sweeps.index(float(chosen_elevation.get()))))
                draw_info(headersdecoded(paised))
                render_radials()
            except:
                msgtostatus("Sellel kõrgustasemel seda produkti ei leitud.")
        elif level2fail:
            chosen_product.set(newproduct)
            paised[0]=newproduct
            try:
                radials=level2_valarray(level2fail,newproduct,level2scan)
                draw_info(headersdecoded(paised))
                render_radials()
            except:
                msgtotatus("Laadimisel juhtus viga") #Different kind of error because on Level 2, the product HAS to be there!(Product list is reloaded every elevation change)
    return 0
def setcursor():
    global zoom
    global info
    global rhi
    if zoom or info or rhi:
        w.config(cursor="crosshair")
    else:
        if not info:
            w.config(cursor="fleur")
        else:
            w.config(cursor=None)
    return 0
def clearclicktext():
    global clickbox
    clickbox=None
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
        product_choice.config(state=Tkinter.NORMAL)
        elevation_choice.config(state=Tkinter.NORMAL)
        draw_info(headersdecoded(paised))
        if renderagain:
            renderagain=0
            render_radials()
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
            render_radials()
    return 0
#Drawing area events
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
    #Since only visual changes take place, I use the same function for both mouse keys.
    global clickcoords
    global zoom
    global zoomlevel
    global canvasdimensions
    global img_center
    global render_center
    global rhi
    global rhishow
    global radials
    x=canvasdimensions[0]
    y=canvasdimensions[1]
    if canvasbusy == False and radials != []:
        if zoom:
            if not rhishow:
                dy=event.y-clickcoords[1]
                w.itemconfig(zoomrect, state=Tkinter.NORMAL)
                w.coords(zoomrect,(clickcoords[0]-dy,clickcoords[1]-dy,clickcoords[0]+dy,event.y))
            else:
                dx=event.x-clickcoords[0]
                w.itemconfig(zoomrect, state=Tkinter.NORMAL)
                w.coords(zoomrect,(clickcoords[0]-dx,-1,clickcoords[0]+dx,canvasdimensions[1]))
        else: #Not zooming
            if info: #If gathering pixel value
                draw_infobox(event.x,event.y)
            else: #Moving
                if not rhishow: #And no RHI is being displayed
                    if direction==1: #If left mouse button was clicked
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
    if canvasbusy == False and radials != []:
        if zoom: #If was zooming
            if not rhishow:
                #Calculating zoom level
                dy=event.y-clickcoords[1] 
                if dy!=0:
                    newzoom=(float(canvasdimensions[1])/(abs(dy*2)))**direction
                else: newzoom=2**direction
                #Finding new coordinates for the center of data
                pdx=canvasctr[0]-clickcoords[0]
                pdy=canvasctr[1]-clickcoords[1]
                render_center[0]=1000+newzoom*(pdx+render_center[0]-1000)
                render_center[1]=1000+newzoom*(pdy+render_center[1]-1000)
                zoomlevel*=newzoom
                w.itemconfig(zoomrect, state=Tkinter.HIDDEN)
                if len(paised) != 0: render_radials()
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
        elif rhi and not rhishow: ##If was choosing an azimuth for PseudoRHI
            rhiaz=int(getinfo(event.x,event.y)[1][0])
            getrhi(rhiaz)
            rhistart=0
            rhiend=250
            mkrhi(rhiaz)
            tozoom()
        else: #If I was moving around
            if not info: #If was not gathering info
                if not rhishow:
                    if direction == 1: #On left mouseclick
                        dx_2=event.x-clickcoords[0]
                        dy_2=event.y-clickcoords[1]
                        img_center[0]+=dx_2
                        img_center[1]+=dy_2
                        render_center[0]+=dx_2
                        render_center[1]+=dy_2
                        #If going out of rendering area
                        if img_center[0] > 1000 or img_center[0] < -600  or img_center[1] > 1000 or img_center[1] < -600:
                            if len(paised) != 0: render_radials()
            else: #If information was queried.
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
        return gr, h, getrhibin(h,gr,float(a))
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
#RHI speficic functions
def chooserhi(): #Choose RHI
    global currentfilepath
    global zoom
    global info
    global rhi
    global sweeps
    global radials
    global level2fail
    if radials!=[]:
        if paised[0]=="DBZ" or paised[0]=="V" or paised[0]=="VRAD" or paised[0]=="HCLASS" or paised[0]=="RHOHV" or paised[0]=="KDP" or paised[0]=="ZDR" or level2fail:
            if currentfilepath[-3:]==".h5":
                sweeps=hdf5_sweepslist(currentfilepath)
            elif level2fail:
                sweeps=level2_sweepslist(level2fail)
            if len(sweeps) > 1:
                clearclicktext()
                zoom=0
                info=0
                rhi=1
                setcursor()
                msgtostatus("Kliki asimuudil, millest soovid PseudoRHI'd teha")
        else:
            tkMessageBox.showerror("Vale formaat","PseudoRHI'd ei ole nende andmetega võimalik teha")
def rhiypix(h,bottom):
    samm=(bottom-120)/17.0
    return bottom-80-h*samm
def rhiy(r,a,bottom):
    samm=(bottom-120)/17.0
    return bottom-80-beamheight(r,float(a))*samm
def rhix(x):
    global rhistart
    global rhiend
    global canvasdimensions
    return rhistart+(x-50)*((rhiend-rhistart)/(canvasdimensions[0]-100.0))
##Vastupidised funktsioonid RHI koordinaatidele
##Reverse functions of RHI coords
def getrhi(az):
    global sweeps
    global productsweeps
    global currentfilepath
    global rhidata
    global canvasbusy
    global level2fail
    rhidata=[]
    if not currentfilepath[-3:]==".h5": sisu=file_read(currentfilepath)
    canvasbusy=1
    productsweeps=[]
    for i in xrange(len(sweeps)):
        if currentfilepath[-3:]==".h5":
            try:
                rhidata.append(hdf5_valarray(currentfilepath,hdf5_leiaskann(currentfilepath,paised[0],i),az))
                productsweeps.append(sweeps[i])
            except:
                pass
        elif level2fail:
            rida=level2_valarray(level2fail,paised[0],i,az)
            if rida != None:
                if sweeps[i] > sweeps[i-1] or sweeps[i]-sweeps[i-1] < 0.2:
                    rhidata.append(level2_valarray(level2fail,paised[0],i,az))
                    productsweeps.append(sweeps[i])
        msgtostatus("Loen elevatsiooni: "+str(sweeps[i])+u"°")
        w.update()
    canvasbusy=0
    return 0
def mkrhi(az):
    global paised
    global canvasbusy
    global productsweeps
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
        for i in xrange(len(productsweeps)):
            r=0
            a=float(productsweeps[i])
            x0=50
            first=1
            for j in rhidata[i]:
                if rhistart-r <= samm and r < rhiend:
                    if first:
                        x0+=(r-rhistart)*xsamm/samm
                        first=0
                    x1=x0+xsamm if rhiend-r > samm else laius-50
                    if j != None:
                        if r-rhistart < 0:
                            path=[50,rhiy(r, a0, pikkus),x1,rhiy(r+samm, a0, pikkus),x1,rhiy(r+samm,a,pikkus),50,rhiy(r,a,pikkus)]
                        else:
                            path=[x0,rhiy(r, a0, pikkus),x1,rhiy(r+samm, a0, pikkus),x1,rhiy(r+samm,a,pikkus),x0,rhiy(r,a,pikkus)]
                        joonis.polygon(path,fill=getcolor(varvitabel,j))
                    x0=x1
                r+=samm
            a0=a
        for k in xrange (0,18):
            korgus=rhiypix(k,pikkus)
            joonis.line((50,korgus,laius-50,korgus),fill="white")
            joonis.text((30,korgus-10),text=str(k),fill="white",font=pildifont)
        ulatus=(rhiend-rhistart)
        teljesamm=ulatus/5.0
        teljexsamm=(laius-100)/5.0
        for l in xrange(5):
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
        product_choice.config(state=Tkinter.DISABLED)
        elevation_choice.config(state=Tkinter.DISABLED)
        w.coords(radaripilt,tuple(canvasctr))
        w.itemconfig(radaripilt, image=rhiout)
        msgtostatus("Valmis")
        rhishow=1
    return 0
clickcoords=[]
output=Tkinter.Tk()
output.title("TRV 2014.6")
output.bind("<Configure>",on_window_reconf)
output.config(background="#000044")
##Drawing the menu
menyy = Tkinter.Menu(output,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
output.config(menu=menyy)
failimenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
radarmenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
toolsmenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
abimenyy = Tkinter.Menu(menyy,tearoff=0,bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
menyy.add_cascade(label="Fail", menu=failimenyy)
menyy.add_cascade(label="NEXRAD", menu=radarmenyy)
menyy.add_cascade(label="Tööriistad", menu=toolsmenyy)
menyy.add_cascade(label="Abi", menu=abimenyy)
failimenyy.add_command(label="Ava andmefail", command=load)
failimenyy.add_command(label="Ava URL", command=loadurl)
failimenyy.add_separator()
failimenyy.add_command(label="Ekspordi pilt", command=exportimg)
failimenyy.add_separator()
failimenyy.add_command(label="Lõpeta", command=output.destroy)
radarmenyy.add_command(label="Jooksvad andmed", command=activatecurrentnexrad)
radarmenyy.add_separator()
radarmenyy.add_command(label="Jaama valik",command=choosenexrad)
toolsmenyy.add_command(label="Liida Rmax",command=configrmaxadd)
abimenyy.add_command(label="Otseteed klaviatuuril", command=keys_list)
abimenyy.add_separator()
abimenyy.add_command(label="Info programmi kohta", command=about_program)
##Drawing area
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
#Key bindings
output.bind("r",resetzoom)
output.bind("i",toinfo)
output.bind("p",topan)
output.bind("z",tozoom)
output.bind("h",chooserhi)
kyljeraam=Tkinter.Frame(output)
kyljeraam.grid(row=2,column=0,sticky="n")
moderaam=Tkinter.Frame(kyljeraam)
moderaam.config(bg="#000044")
moderaam.grid(row=1,column=0)
panimg=PhotoImage(file="../images/pan.png")
zoomimg=PhotoImage(file="../images/zoom.png")
resetzoomimg=PhotoImage(file="../images/resetzoom.png")
infoimg=PhotoImage(file="../images/info.png")
rhiimg=PhotoImage(file="../images/rhi.png")
ppiimg=PhotoImage(file="../images/ppi.png")
reloadimg=PhotoImage(file="../images/reload.png")
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
taskbarbtn5=Tkinter.Button(moderaam, bg="#000044",activebackground="#000099", highlightbackground="#000044", image=reloadimg, command=reloadfile)
taskbarbtn5.grid(row=0,column=5)
chosen_elevation = Tkinter.StringVar(moderaam)
elevation_choice=Tkinter.OptionMenu(moderaam, chosen_elevation,None)
elevation_choice.config(bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow",highlightbackground="#000044",state=Tkinter.DISABLED)
elevation_choice.grid(row=0,column=6)
elevation_choice["menu"].config(bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
chosen_product= Tkinter.StringVar(moderaam)
product_choice=Tkinter.OptionMenu(moderaam, chosen_product,None)
product_choice.config(bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow",highlightbackground="#000044",state=Tkinter.DISABLED)
product_choice.grid(row=0,column=7)
product_choice["menu"].config(bg="#000044",fg="yellow",activebackground="#000099",activeforeground="yellow")
status=Tkinter.Label(output, text=None, justify=Tkinter.LEFT, anchor="w", fg="yellow", bg="#000044")
status.grid(row=3,column=0,sticky="w")
output.mainloop()

