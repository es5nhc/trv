#!/usr/bin/python2
# -*- coding: utf-8 -*-
#


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
#

from __future__ import division

import bz2
from decoderadar import *
import translations
from PIL.Image import open as laepilt
from PIL.Image import new as uuspilt
from PIL.ImageDraw import Draw
from PIL.ImageTk import PhotoImage, BitmapImage
from PIL import ImageFont
from math import floor, sqrt, radians as d2r, degrees as r2d, cos, copysign
from colorconversion import *
from coordinates import *
import sys
import datetime
import Tkinter
import tkFileDialog
import tkMessageBox
import urllib2
import json
import os
from nexrad_level2 import NEXRADLevel2File
configfile=open("config.json","r")
conf=json.load(configfile)
configfile.close()
fraasid=translations.phrases[conf["lang"]]
#Importing geodata
print fraasid["loading_states"]
import states
print fraasid["coastlines"]
import coastlines
print fraasid["countries"]
import countries
print fraasid["lakes"]
import lakes
print fraasid["rivers"]
import rivers
print fraasid["NA_roads"]
import major_NA_roads
class AddRMAXChooser(Tkinter.Toplevel):
    def __init__(self, parent, title = None):
        global paised
        Tkinter.Toplevel.__init__(self,parent)
        self.title(fraasid["add_rmax"])
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        #Labels
        az0title=Tkinter.Label(self,text=fraasid["az0"])
        az0title.grid(column=0,row=0,sticky="e")
        az1title=Tkinter.Label(self,text=fraasid["az1"])
        az1title.grid(column=0,row=1,sticky="e")
        r0title=Tkinter.Label(self,text=fraasid["r0"])
        r0title.grid(column=0,row=2,sticky="e")
        r1title=Tkinter.Label(self,text=fraasid["r1"])
        r1title.grid(column=0,row=3,sticky="e")
        prftitle=Tkinter.Label(self,text=fraasid["prf"])
        prftitle.grid(column=0,row=4,sticky="e")
        #Text variables
        self.az0=Tkinter.StringVar()
        self.az1=Tkinter.StringVar()
        self.r0=Tkinter.StringVar()
        self.r1=Tkinter.StringVar()
        self.prf=Tkinter.StringVar()
        self.prf.set("570")
        #Text fields
        az0field=Tkinter.Entry(self,textvariable=self.az0)
        az0field.grid(column=1,row=0,sticky="w")
        az1field=Tkinter.Entry(self,textvariable=self.az1)
        az1field.grid(column=1,row=1,sticky="w")
        r0field=Tkinter.Entry(self,textvariable=self.r0)
        r0field.grid(column=1,row=2,sticky="w")
        r1field=Tkinter.Entry(self,textvariable=self.r1)
        r1field.grid(column=1,row=3,sticky="w")
        prffield=Tkinter.Entry(self,textvariable=self.prf)
        prffield.grid(column=1,row=4,sticky="w")
        #Button
        liidabutton=Tkinter.Button(self,command=self.addrmax,text=fraasid["add"])
        liidabutton.grid(column=1,row=5,sticky="w")
        #And now the main loop
        self.mainloop()
    def processgate(self,i,paddingamt,rmaxbins,slicestart,sliceend):
        global paised
        global radials
        for j in xrange(paddingamt):
            radials[i][2].append(None)
        for k in xrange(slicestart,sliceend,1):
            radials[i][2][k+rmaxbins]=radials[i][2][k]
            radials[i][2][k]=None
        return 0
    def addrmax(self):
        global radials
        az0=round(d2r(float(self.az0.get())),7)
        az1=round(d2r(float(self.az1.get())),7)
        r0=float(self.r0.get())
        r1=float(self.r1.get())
        prf=float(self.prf.get())
        rmax=299792.458/prf/2
        if isinstance(paised[0],int): rmax*=cos(d2r(float(paised[17])))
        r0new=r0+rmax
        r1new=r1+rmax
        for i in xrange(len(radials)):
            r=radials[i]
            curaz=round(r[0],7)
            slicestart=int(r0/paised[25])
            sliceend=int(r1/paised[25])
            rmaxbins=int(round(rmax/paised[25])) #Amount of bins that coorespond to Rmax
            paddingamt=int(round(r1new/paised[25]))-len(r[2])
            if az0 < az1:
                if curaz >= az0 and curaz < az1:
                    self.processgate(i,paddingamt,rmaxbins,slicestart,sliceend)
            else:
                if curaz >= az0 or curaz < az1:
                    self.processgate(i,paddingamt,rmaxbins,slicestart,sliceend)
        self.onclose()
        render_radials()
    def onclose(self):
        global rmaxaddopen
        rmaxaddopen=0
        self.destroy()
class NEXRADChooser(Tkinter.Toplevel): #Choice of NEXRAD station
    def __init__(self, parent, title = None):
        global conf
        Tkinter.Toplevel.__init__(self,parent)
        self.title(fraasid["nexrad_choice"])
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        jaamatiitel=Tkinter.Label(self,text=fraasid["choose_station"])
        jaamatiitel.pack()
        jaamavalik=Tkinter.Frame(self)
        kerimisriba=Tkinter.Scrollbar(jaamavalik)
        kerimisriba.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
        self.jaamaentry=Tkinter.Listbox(jaamavalik,width=30,yscrollcommand=kerimisriba.set)
        self.jaamaentry.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH)
        kerimisriba.config(command=self.jaamaentry.yview)
        jaamavalik.pack()
        jaamad=file_read("nexradstns.txt").split("\n")
        for i in jaamad:
            rida=i.split("|")
            self.jaamaentry.insert(Tkinter.END, rida[0]+" - "+rida[1]+", "+rida[2])
        okbutton=Tkinter.Button(self,text=fraasid["okbutton"],command=self.newstn)
        okbutton.pack()
        self.mainloop()
    def newstn(self):
        global conf
        selection=self.jaamaentry.curselection()
        if selection != ():
            print selection
            jaam=self.jaamaentry.get(selection)[:4]
            conf["nexradstn"]=jaam.lower()
            save_config_file()
            self.onclose()
        else:
            tkMessageBox.showerror(fraasid["name"],fraasid["choose_station_error"])
    def onclose(self):
        global nexradchooseopen
        nexradchooseopen=0
        self.destroy()
class DynamicLabelEditor(Tkinter.Toplevel):
    def __init__(self, parent, title = None):
        global conf
        Tkinter.Toplevel.__init__(self,parent)
        self.title(fraasid["dyn_labels"])
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        self.dataPath=Tkinter.StringVar()
        self.updateInterval=Tkinter.StringVar()
        self.sourceType=Tkinter.IntVar()
        self.enabled=Tkinter.IntVar()
        if parent.allikaIndeks == -1:
            self.dataPath.set("")
            self.updateInterval.set("")
            self.sourceType.set(0)
            self.enabled.set(1)
        else:
            values=conf["placesources"][parent.allikaIndeks]
            self.sourceType.set(values[0])
            self.dataPath.set(values[1])
            self.updateInterval.set(values[2])
            self.enabled.set(values[4])
        label1=Tkinter.Label(self,text="Type")
        label1.grid(column=0,row=0,sticky=Tkinter.E)
        type1=Tkinter.Radiobutton(self,text=fraasid["dyn_online"],variable=self.sourceType,value=0,command=self.goonline)
        type1.grid(column=1,row=0)
        type2=Tkinter.Radiobutton(self,text=fraasid["dyn_local"],variable=self.sourceType,value=1,command=self.pickfile)
        type2.grid(column=2,row=0)
        label2=Tkinter.Label(self,text=fraasid["dyn_path"])
        label2.grid(column=0,row=1,sticky=Tkinter.E)
        self.pathentry=Tkinter.Entry(self,width=40,textvariable=self.dataPath)
        self.pathentry.grid(column=1,row=1,columnspan=2)
        label3=Tkinter.Label(self,text=fraasid["dyn_interval"])
        label3.grid(column=0,row=2,sticky=Tkinter.E)
        self.intervalentry=Tkinter.Entry(self,textvariable=self.updateInterval)
        self.intervalentry.grid(column=1,row=2,columnspan=2,sticky=Tkinter.W)
        self.enabledcheck=Tkinter.Checkbutton(self, variable=self.enabled, text=fraasid["dyn_enabled"])
        self.enabledcheck.grid(column=2,row=2)
        okbutton=Tkinter.Button(self,text="OK",command=lambda: self.submit_source(parent))
        okbutton.grid(column=2,row=3)
        self.mainloop()
    def pickfile(self): #Pick a source file
        self.intervalentry.config(state=Tkinter.DISABLED)
        pathd=tkFileDialog.Open(None,initialdir="../places")
        path=pathd.show()
        self.dataPath.set(path)
    def goonline(self): #Ensure the update interval selection is active
        self.dataPath.set("")
        self.intervalentry.config(state=Tkinter.NORMAL)
    def submit_source(self,parent):
        global conf
        if parent.allikaIndeks == -1:
            conf["placesources"].append([self.sourceType.get(),self.dataPath.get(),self.updateInterval.get(),-1,self.enabled.get()]) #New
        else:
            conf["placesources"][parent.allikaIndeks]=[self.sourceType.get(),self.dataPath.get(),self.updateInterval.get(),-1,self.enabled.get()] #Edit
        ##Format of dynamic information setting [Online/Local, path, update interval if relevant, last download timestamp if online content]
        save_config_file()
        parent.listsources() #Update sources listing
        self.onclose()
    def onclose(self):
        self.destroy()
class DynamicLabelWindow(Tkinter.Toplevel):
    def __init__(self, parent, title = None):
        Tkinter.Toplevel.__init__(self,parent)
        self.title(fraasid["dyn_labels"])
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        nimekiri=Tkinter.Frame(self)
        #List of files
        kerimisriba=Tkinter.Scrollbar(nimekiri)
        kerimisriba.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
        self.customfileslist=Tkinter.Listbox(nimekiri,width=60,yscrollcommand=kerimisriba.set)
        self.customfileslist.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH)
        kerimisriba.config(command=self.customfileslist.yview)
        nimekiri.pack()
        self.listsources() #List all sources
        #Command buttons
        nupud=Tkinter.Frame(self)
        nupp1=Tkinter.Button(nupud, text=fraasid["dyn_new"],command=self.add)
        nupp1.pack(side=Tkinter.LEFT)
        nupp2=Tkinter.Button(nupud, text=fraasid["dyn_edit"],command=self.edit)
        nupp2.pack(side=Tkinter.LEFT)
        nupp3=Tkinter.Button(nupud, text=fraasid["dyn_rm"],command=self.delete)
        nupp3.pack(side=Tkinter.LEFT)
        nupud.pack()
        self.mainloop()
    def listsources(self):
        global conf
        types=[fraasid["dyn_online"],fraasid["dyn_local"]]
        self.customfileslist.delete(0,Tkinter.END)
        for i in conf["placesources"]:
            if i[4] == 1:
                check=u"☑ "
            else:
                check=u"☐ "
            liststring=check+types[i[0]]+" - "+i[1]
            self.customfileslist.insert(Tkinter.END,liststring)
    def add(self):
        self.allikaIndeks=-1 #index of selected item. -1 means the option is to be created.
        DynamicLabelEditor(self)
    def edit(self):
        self.allikaIndeks=self.customfileslist.curselection()[0]
        DynamicLabelEditor(self)
    def delete(self):
        global conf
        self.allikaIndeks=self.customfileslist.curselection()[0]
        if tkMessageBox.askyesno(fraasid["name"],fraasid["dyn_rm_sure"]):
            conf["placesources"].pop(self.allikaIndeks)
            save_config_file()
            self.customfileslist.delete(self.allikaIndeks)
    def onclose(self):
        global dynlabelsopen
        dynlabelsopen=0
        self.destroy()
class URLAken(Tkinter.Toplevel): ##Dialog to open a web URL
    def __init__(self, parent, title = None):
        Tkinter.Toplevel.__init__(self,parent)
        self.title(fraasid["name"])
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        urltitle=Tkinter.Label(self,text="URL:")
        urltitle.grid(column=0,row=0)
        self.url=Tkinter.StringVar()
        self.url.set("")
        urlentry=Tkinter.Entry(self,textvariable=self.url,width=70)
        urlentry.grid(column=1,row=0)
        downloadbutton=Tkinter.Button(self,text=fraasid["open"],command=self.laealla)
        downloadbutton.grid(column=0,row=1,sticky="w")
        self.mainloop()
    def laealla(self):
        global currentfilepath
        global currenturl
        currenturl=self.url.get()
        download_file(currenturl)
        currentfilepath="../cache/urlcache"
        load(currentfilepath)
       # try:
      #  except:
      #      print sys.exc_info()
      #      tkMessageBox.showerror(fraasid["name"],fraasid["download_failed"])
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
currenturl=None
nexradstn=conf["nexradstn"] #Chosen NEXRAD station
urlwindowopen=0 #1 if dialog to open an URL is open
nexradchooseopen=0 #1 if dialog to choose a nexrad station is open
rmaxaddopen=0 #1 if configuration window to add Rmax to chunk of data is open.
dynlabelsopen=0 #same rule as above for selection of dynamic labels
zoom=1
info=0
rhi=0
rhiaz=0 ##RHI asimuut -- RHI Azimuth
rhistart=0
rhiend=250
rhishow=0 ##Yes, if RHI is shown
zoomlevel=1
direction=1
fmt=0 #Data format indicator
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
       159:"dB",
       161:"",
       163:u"°/km",
       165:"",
       "DBZ":"dBZ",
       "DBZH":"dBZ",
       "DBZV":"dBZ",
       "TH":"dBZ",
       "TV":"dBZ",
       "REF":"dBZ",
       "ZDR":"dB",
       "LZDR":"dB",
       "RHOHV": "",
       "RHO": "",
       "SQI": "",
       "SQIH": "",
       "SQIV": "",
       "QIDX": "",
       "HCLASS": "",
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
hcanames=fraasid["hca_names"] #Hydrometeor classifications
colortablenames={94:"dbz",
                 "DBZ":"dbz",
                 "TH":"dbz",
                 "TV":"dbz",
                 "DBZH":"dbz",
                 "DBZHC":"dbzh",
                 "DBZV":"dbz",
                 "REF":"dbz",
                 "SQI":"sqi",
                 "SQIH":"sqi",
                 "SQIV":"sqi",
                 "QIDX":"sqi",
                 "VRAD":"v",
                 "VRADH":"v",
                 "VRADV":"v",
                 "V":"v",
                 "VEL":"v",
                 99:"v",
                 159:"zdr",
                 "ZDR":"zdr",
                 "LZDR":"zdr",
                 161:"rhohv",
                 "RHOHV":"rhohv",
                 "RHO":"rhohv",
                 163:"kdp",
                 "KDP":"kdp",
                 165: "hca",
                 "HCLASS": "hclass",
                 "PHI": "phi",
                 "PHIDP": "phi",
                 "WRAD": "sw",
                 "SW": "sw"} #Names for color tables according to product
customcolortable=None
def download_file(url,dst="../cache/urlcache"):
    req=urllib2.urlopen(url,timeout=10)
    sisu=req.read()
    req.close()
    cache=open(dst,"wb")
    cache.write(sisu)
    cache.close()
    return 0
def save_config_file(): #Saves config.json according to current config
    global conf
    configfile=open("config.json","w")
    json.dump(conf,configfile)
    configfile.close()
def configrmaxadd():
    global rmaxaddopen
    if rmaxaddopen == 0:
        rmaxaddopen=1
        AddRMAXChooser(output)
    return 0
def dynlabels_settings():#Configuration for dynamic labels
    global dynlabelsopen
    if dynlabelsopen == 0:
        dynlabelsopen == 1
        DynamicLabelWindow(output)
def choosenexrad(): #Opening NEXRAD station selection window
    global nexradchooseopen
    if nexradchooseopen == 0:
        nexradchooseopen=1
        NEXRADChooser(output)
def fetchnexrad(product): #Downloading a current NEXRAD Level 3 file from NOAA's FTP
    global conf
    global rhishow
    global currentfilepath
    global currenturl
    if rhishow: topan()    
    product_choice.config(state=Tkinter.NORMAL)
    elevation_choice.config(state=Tkinter.NORMAL)
    populatenexradmenus(product)
    currenturl="ftp://tgftp.nws.noaa.gov/SL.us008001/DF.of/DC.radar/DS."+product+"/SI."+conf["nexradstn"]+"/sn.last"
    try:
        download_file(currenturl,"../cache/nexradcache/"+product)
        currentfilepath="../cache/nexradcache/"+product
        load(currentfilepath)
    except:
        print sys.exc_info()
        tkMessageBox.showerror(fraasid["name"],fraasid["download_failed"])
def activatecurrentnexrad():
    product_choice.config(state=Tkinter.NORMAL)
    elevation_choice.config(state=Tkinter.NORMAL)
    fetchnexrad("p94r0")
    return 0
def populatenexradmenus(product="p94r0"):
    ids={"p94":"DBZ",
         "p99":"VRAD",
         "159":"ZDR",
         "161":"RHOHV",
         "163":"KDP",
         "165":"HCLASS"}
    elevation_choice["menu"].delete(0, 'end')
    for i in xrange(4):
        productcode=product[:-1]+str(i)
        elevation_choice["menu"].add_command(label=fraasid["level3_slice"].replace("/NR/",str(i+1)),command=lambda x=productcode: fetchnexrad(x))
    index=product[-1]
    chosen_elevation.set(fraasid["level3_slice"].replace("/NR/",str(int(product[-1])+1)))
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
    global radials
    if len(radials) > 0:
        y=int(w.cget("height"))
        if y % 2 != 0 and not rhishow: y+=1
        x=int(w.cget("width"))
        if x % 2 != 0 and not rhishow: x+=1
        halfx=int(x/2.0)
        halfy=int(y/2.0)
        cy=int(1000-img_center[1]+halfy)
        cx=int(1000-img_center[0]+halfx)
        cbx=clickboxloc[0]
        cby=clickboxloc[1]
        cbh=84 if not rhishow else 45
        filed=tkFileDialog.SaveAs(None,initialdir="../radar_images")
        path=filed.show()
        if path != "":
            try:
                outimage=uuspilt("RGB",(x,y),"#000025")
                joonis=Draw(outimage)
                if not rhishow:
                    if rendered != None: outimage.paste(rendered2.crop((cx-halfx,cy-halfy,cx+halfx,cy+halfy)),((0,0,x,y))) #PPI
                else:
                    outimage.paste(rhiout2,(0,0,x,y)) #PseudoRHI
                if clickbox != None: outimage.paste(clickbox2,(cbx,cby+1,cbx+170,cby+cbh+1))
                if rlegend != None: outimage.paste(rlegend2,(x-35,halfy-163,x,halfy+162))
                if infotekst != None: outimage.paste(infotekst2,(halfx-250,y-30,halfx+250,y-10))
                outimage.save(path)
                tkMessageBox.showinfo(fraasid["name"],fraasid["export_success"])
            except:
                tkMessageBox.showerror(fraasid["name"],fraasid["export_format_fail"])
        return 0
    else:
        tkMessageBox.showerror(fraasid["name"],fraasid["no_data_loaded"])
def getrhibin(h,gr,a):
    global productsweeps
    global rhidata
    global paised
    kordaja=paised[25]**-1
    if a < 0: return fraasid["no_data"]
    if a > productsweeps[-1]: return fraasid["no_data"]
    for i in xrange(len(productsweeps)):
        cond=0 if i == 0 else productsweeps[i-1]
        if a > cond and a <= productsweeps[i]:
            indeks=int(gr*kordaja)
            if len(rhidata[i]) <= indeks:
                val=None
            else:
                val=rhidata[i][indeks]
            if val != None and (paised[0] == 165 or paised[0] == "HCLASS"):
                val=hcanames[int(val)]
            elif val == None:
                val=fraasid["no_data"]
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
        kordaja=paised[25]**-1
        kaugus=azr[1] if not isinstance(paised[0],int) else azr[1]/cos(d2r(float(paised[17])))
        mindistance=radials[int(azi)][3]
        if kaugus >= mindistance:
            val=radials[int(azi)][2][int((kaugus-mindistance)*kordaja)]
        else:
            val=None
        delta=None
        if val != None and (paised[0] == 99 or paised[0] == "V" or paised[0] == "VRAD" or paised[0] == "VEL"):
            valprev=radials[int(azi)-1][2][int((kaugus-mindistance)*kordaja)]
            delta=abs(float(val)-valprev) if valprev != None else None
        elif val != None and paised[0] == 165 or paised[0] == "HCLASS":
            val=hcanames[int(val)]
        elif val == None:
            val=fraasid["no_data"]
    except: val = fraasid["no_data"]
    return val, delta, h
def msgtostatus(msg):
    status.config(text=msg)
    return 0
def about_program():
    tkMessageBox.showinfo(fraasid["name"], fraasid["name"]+"\n"+fraasid["about_text"])
    return 0
def keys_list():
    tkMessageBox.showinfo(fraasid["name"], fraasid["key_shortcuts_dialog_text"])
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
    row0=u"%s %s" % (vaartus, units[paised[0]]) if vaartus != fraasid["no_data"] else fraasid["no_data"]
    if not rhishow:        
        coords=andmed[0]
        latletter="N" if coords[0] > 0 else "S"
        lonletter="E" if coords[1] > 0 else "W"
        row1=u"%.5f°%s %.5f°%s" % (abs(coords[0]),latletter,abs(coords[1]),lonletter)
        row2=u"%s: %.1f°" % (fraasid["azimuth"],azrange[0])
        row3=u"%s: %.3f km" % (fraasid["range"],azrange[1])
        row4=u"%s: ~%.1f km" % (fraasid["beam_height"],data[2])
        row5=None if data[1] == None else fraasid["g2g_shear"]+": %.1f m/s" % (data[1])
    else:
        row1=u"%s: %.3f km" % (fraasid["range"],andmed[0])
        row2=u"%s: %.3f km" % (fraasid["height"],andmed[1])
    kastikorgus=84 if not rhishow else 45
    kast=uuspilt("RGB",(170,kastikorgus),"#44ccff")
    kastdraw=Draw(kast)
    kastdraw.rectangle((0,0,170,16),fill="#0033ee")
    kastdraw.polygon((0,0,10,0,0,10,0,0),fill="#FFFFFF")
    kastdraw.text((9,1),text=row0, font=pildifont2)
    kastdraw.text((5,17),text=row1, fill="#000000", font=pildifont)
    kastdraw.text((5,30),text=row2, fill="#000000", font=pildifont)
    if not rhishow:
        kastdraw.text((5,43),text=row3, fill="#000000", font=pildifont)
        kastdraw.text((5,56),text=row4, fill="#000000", font=pildifont)
        if row5 != None: kastdraw.text((5,69),text=row5, fill="#000000", font=pildifont)
    clickbox2=kast
    clickbox=PhotoImage(image=kast)
    clickboxloc=[x,y]
    w.itemconfig(clicktext,image=clickbox)
    w.coords(clicktext,(x+85,y+kastikorgus/2))
    return 0
def draw_info(tekst):
    global infotekst
    global infotekst2
    textimg=uuspilt("RGB",(500,20), "#0033ee")
    textdraw=Draw(textimg)
    textdraw.text((5,3),text=tekst, font=pildifont)
    infotekst2=textimg
    infotekst=PhotoImage(image=textimg)
    w.itemconfig(radardetails,image=infotekst)
    return 0
def listcolortables():
    global colortablemenu
    failid=os.listdir("../colortables")
    for i in failid:
        colortablemenu.add_command(label=i, command=lambda x=i:change_colortable(x))
    return 0
def drawlegend(product,minimum,maximum,colortable):
    global rlegend
    global rlegend2
    global colortablenames
    global units
    tabel=colortable
    unit=units[product]
    tosmooth=1
    if product == 165 or product == "HCLASS":
        tosmooth=0
    increment=(maximum-minimum)/300.0
    legendimg=uuspilt("RGB",(35,325),"#0033ee")
    legenddraw=Draw(legendimg)
    for i in xrange(300):
        val=minimum+increment*i
        legenddraw.rectangle((25,324-i,35,324-i),fill=getcolor(tabel,val,tosmooth))
    step=1.0/increment
    majorstep=10
    if product == "PHI":
        majorstep=45
    if product == 159 or product == 163 or product == 165 or product == "HCLASS":
        majorstep=1
    if product == 161: #RHOHV aka CC
        majorstep=0.1
    if product == "SQI" or product == "QIDX" or product == "SQIH" or product == "SQIV":
        majorstep=0.1
    firstten=majorstep+minimum-minimum%majorstep
    if firstten == majorstep+minimum: firstten = minimum
    ystart=324-(firstten-minimum)*step
    lastten=maximum-maximum%majorstep
    hulk=int((lastten-firstten)/majorstep)
    yend=ystart-majorstep*step*hulk #If the next full step is too close to the edge.
    if yend < 30: hulk-=1 #Let's not list this last point on legend
    legenddraw.text((5,0),text=unit, font=pildifont)
    for j in xrange(hulk+1):
        y=ystart-majorstep*step*j
        if product == 165: #Other products have a numeric value
            legendlist=["BI","AP","IC","DS","WS","RA","+RA","BDR","GR","HA","UNK","RF"]; #List of classifications
            legendtext=legendlist[int(firstten+j*majorstep)]
        elif product == "HCLASS":
            legendlist=["NM","RA","WS","SN","GR","HA"]
            legendtext=legendlist[int(firstten+j*majorstep)-1]
        else:
            legendval=firstten+j*majorstep
            if legendval % 1 == 0: #If a full integer, strip decimals.
                legendtext=str(int(legendval))
            else:
                legendtext=str(legendval)
        legenddraw.line((0,y,35,y),fill="white")
        legenddraw.text((0,y-15),text=legendtext,font=pildifont)
    rlegend2=legendimg
    rlegend=PhotoImage(image=legendimg)
    w.itemconfig(legend,image=rlegend)
    return 0
def drawmap(data,radarcoords,drawcolor,linewidth=1):
    global canvasdimensions
    paths=map(lambda x,y=radarcoords:coordsFilter(x,y),data) #Pass geo data through filter so we don't need to render the whole world!
    coordsenne=None
    pikkus=len(data)
    kordaja=1
    f=0
    hetkeseisusamm=pikkus**-1
    hetkeseis=0
    teejoon=joonis.line
    for joon in paths:
        f+=1
        for rada in joon:
            coords=mapcoordsFilter(map(lambda x,y=zoomlevel,z=render_center,a=radarcoords:getmapcoords(x,y,z,a),rada)) #To polar coords
            for i in coords:
                teejoon(i,fill=drawcolor,width=linewidth)
        if f % 800 == 0: update_progress(hetkeseis*canvasdimensions[0])
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
def init_drawlegend(product,tabel):
    if product == 99 or product == "V" or product == "VRAD" or product == "VEL":
        drawlegend(99,-63.5,63.5,tabel)
    elif product == 159 or product == "ZDR" or product == "LZDR":
        drawlegend(159,-6,6,tabel)
    elif product == 161 or product == "RHOHV" or product == "RHO":
        drawlegend(161,0.2,1.05,tabel)
    elif product == 163 or product == "KDP":
        drawlegend(163,-2,7,tabel)
    elif product == 165:
        drawlegend(165,0,12,tabel)
    elif product == "HCLASS":
        drawlegend("HCLASS",1,7,tabel)
    elif product == "DBZ" or product == "REF" or product == "TH" or product == "TV" or product == "DBZH" or product == "DBZV":
        drawlegend(94,-25,75,tabel)
    elif product == "SW" or product == "WRAD":
        drawlegend("SW",0,30,tabel)
    elif product == "PHI" or product =="PHIDP":
        drawlegend("PHI",0,180,tabel)
    elif product == "SQI" or product == "QIDX":
        drawlegend("SQI",0,1,tabel)
    else:
        drawlegend(94,-25,75,tabel)
def render_radials():
    global rendered
    global rendered2
    global canvasctr
    global conf
    global img_center
    global canvasbusy
    global radials
    global paised
    global canvasdimensions
    global joonis
    global render_center
    global currentfilepath
    global customcolortable
    product=paised[0]
    canvasbusy=True
    alguses=time.time()
    w.config(cursor="watch")
    w.itemconfig(progress,state=Tkinter.NORMAL)
    msgtostatus(fraasid["drawing"]+" "+fraasid["radar_image"])
    pilt=uuspilt("RGB",(2000,2000),"#000025")
    joonis=Draw(pilt)
    hulknurk=joonis.polygon
    current=0.0
    updateiter=0
    samm=paised[25]
    if customcolortable:
        tabel=loadcolortable("../colortables/"+customcolortable)
    else:
        tabel=loadcolortable("../colortables/"+colortablenames[product]+".txt")
    tosmooth=True #True if transitions in color table are to be smooth.
    if product == 165 or product == "HCLASS":
        tosmooth=False
    init_drawlegend(product,tabel) #Start drawing the color legend
    radialslen=len(radials) #Length of radials
    #Some variables for feedback on drawing progress
    hetkeseisusamm=radialslen**-1 
    hetkeseis=0
    #Setting Drawing resolution
    res=zoomlevel*samm
    aste=int((res)**-1)
    for i in radials:
        az,d_az,gate,mindistance=i
        kiiresuund=leiasuund(az,d_az,mindistance,paised,zoomlevel,render_center,samm)
        x1,x2,y1,y2,dx1,dx2,dy1,dy2=kiiresuund
        if aste > 1:
            gate=gate[::aste]
            dx1*=aste
            dx2*=aste
            dy1*=aste
            dy2*=aste
        tegelikkevaartusi=len([x for x in gate if x is not None]) #Count of actual values
        loetudtegelikke=0 #Count of actual values pressed
        varvid=map(lambda y,x=tabel,z=tosmooth: getcolor(x,y,z),gate)
        jubarenderdanud=False
        for val in varvid:
            if loetudtegelikke==tegelikkevaartusi: break #Mosey along, nothing to render at this azimuth anymore.
            x1new=x1+dx1
            x2new=x2+dx2
            y1new=y1+dy1
            y2new=y2+dy2
            if val!= None:
                path=(x1,y1,x2,y2,x2new,y2new,x1new,y1new)
                if shouldirender(path):
                    hulknurk(path, fill=val)
                    loetudtegelikke+=1
                    jubarenderdanud=True
                elif jubarenderdanud:
                    break
            x1=x1new
            x2=x2new
            y1=y1new
            y2=y2new
        if current % 2==0:
            update_progress(hetkeseis*canvasdimensions[0])
        hetkeseis+=hetkeseisusamm
        current+=1
    #Drawing geodata
    rlat=d2r(float(paised[6]))
    rlon=d2r(float(paised[7]))
    img_center=canvasctr
    showrendered(pilt)
    w.coords(radaripilt,tuple(img_center)) #Center image
    msgtostatus(fraasid["drawing"]+" "+fraasid["coastlines"].lower())
    drawmap(coastlines.points,(rlat,rlon),(17,255,17))
    msgtostatus(fraasid["drawing"]+" "+fraasid["lakes"].lower())
    drawmap(lakes.points,(rlat,rlon),(0,255,255),1)
    if rlon < 0:
        msgtostatus(fraasid["drawing"]+" "+fraasid["NA_roads"])
        drawmap(major_NA_roads.points,(rlat,rlon),(125,0,0),2)
    msgtostatus(fraasid["drawing"]+" "+fraasid["rivers"].lower())
    drawmap(rivers.points,(rlat,rlon),(0,255,255),1)
    msgtostatus(fraasid["drawing"]+" "+fraasid["states_counties"])
    drawmap(states.points,(rlat,rlon),(255,255,255),1)
    msgtostatus(fraasid["drawing"]+" "+fraasid["country_boundaries"])
    drawmap(countries.points,(rlat,rlon),(255,0,0),2)
    #Dynamic information
    for entry in xrange(len(conf["placesources"])):
        i=conf["placesources"][entry]
        if i[4] != 1: continue #If the data source has been disabled, skip.
        msgtostatus(fraasid["drawing"]+" "+fraasid["placenames"]+" - "+i[1])
        filepath=i[1]
        internetOkay=False
        if i[0] == 0: #If it is internet content
            filepath="../cache/"+i[1].replace("/","_") #Path of file in cache
            try:
                if (time.time()-float(i[3]))>int(i[2])*60: #If sufficient amount has passed since last download
                    download_file(i[1],filepath) #Download the file
                    conf["placesources"][entry][3]=time.time() #Save last time of download
                    save_config_file()
                internetOkay=True
            except:
                tkMessageBox.showerror(fraasid["name"],fraasid["download_failed"]+"\nURL:"+i[1]) #Something went south with download.
        if not internetOkay and i[0] == 0: continue #Okay, something went wrong with data file download. Onward to next data file.
        allikas=open(filepath,"r")
        punktid=json.load(allikas)
        allikas.close()
        for kohad in punktid:
            if punktid[kohad]["min_zoom"] < zoomlevel:
                pointsamt=len(punktid[kohad]["lat"]) #Amount of coordinate points
                if pointsamt==1:
                    loc=geog2polar((d2r(punktid[kohad]["lat"][0]),d2r(punktid[kohad]["lon"][0])),(rlat,rlon))
                    coords=getcoords((loc[0],loc[1]),zoomlevel,render_center)
                    if coords[0] < 2000 and coords[0] > 0 and coords[1] < 2000 and coords[1] > 0:
                        x=int(coords[0])
                        y=int(coords[1])
                        if punktid[kohad]["label"]:
                            fontsize=int(punktid[kohad]["size"])
                            teksty=y-int(fontsize/2)
                            joonis.text((x+11,teksty+1),text=kohad,fill="black",font=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",fontsize))
                            joonis.text((x+10,teksty),text=kohad,fill=punktid[kohad]["color"],font=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",fontsize))
                        if punktid[kohad]["icon"] == None:
                            joonis.rectangle((x-2,y-2,x+2,y+2),fill="black")
                            joonis.rectangle((x-1,y-1,x+1,y+1),fill="white")
                        else:
                            iconfile=laepilt("../images/"+punktid[kohad]["icon"].lower()+".png")
                            pilt.paste(iconfile,[x-8,y-8,x+8,y+8],iconfile)
                else: #More than one point in set. Therefore polygon
                    path=[]
                    for p in range(pointsamt):
                        lat=punktid[kohad]["lat"][p]
                        lon=punktid[kohad]["lon"][p]
                        loc=geog2polar((d2r(lat),d2r(lon)),(rlat,rlon))
                        coords=getcoords((loc[0],loc[1]),zoomlevel,render_center)
                        for p2 in coords:
                            path.append(p2)
                    if punktid[kohad]["connect"]: path+=path[0:2] #Connect the line to the beginning if requested
                    joonis.line(path,fill="#000000",width=int(punktid[kohad]["width"])+2) #Shadow
                    joonis.line(path,fill=punktid[kohad]["color"],width=int(punktid[kohad]["width"])) #The line itself
    rendered2=pilt
    showrendered(pilt)
    w.itemconfig(progress,state=Tkinter.HIDDEN)
    msgtostatus(fraasid["ready"])
    canvasbusy=False
    lopus=time.time()
    print "Time elapsed:", lopus-alguses,"seconds"
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
    global currenturl
    if currenturl:
        download_file(currenturl,currentfilepath)
    if currentfilepath != "":
        load(currentfilepath)
    return 0
def load(path=None):
    global paised
    global radials
    global clickbox
    global currenturl
    global currentfilepath
    global hcanames
    global fmt
    global level2fail #Language note: "Fail" in the variable name does not
                      #imply failure - it is Estonian for "file."
    clickbox=None
    level2fail=None #Clear the old level 2 file in case one was opened
    if path == None:
        filed=tkFileDialog.Open(None,initialdir="../data")
        path=filed.show()
        currenturl=None
    if path != "": #If a file was given
        stream=file_read(path)
        currentfilepath=path
        msgtostatus(fraasid["decoding"])
        if path[-3:]== ".h5" or stream[1:4]=="HDF":
            product_choice.config(state=Tkinter.NORMAL)
            elevation_choice.config(state=Tkinter.NORMAL)
            hcanames=fraasid["iris_hca"]
            fmt=1
        elif stream[0:4] == "AR2V":
            product_choice.config(state=Tkinter.NORMAL)
            elevation_choice.config(state=Tkinter.NORMAL)
            level2fail=NEXRADLevel2File(path) #Load a Level 2 file
            fmt=2
        else:
            hcanames=fraasid["hca_names"]
            if not currenturl or currenturl.find("ftp://tgftp.nws.noaa.gov/SL.us008001/DF.of/DC.radar/") == -1: #Do not clear elevation and product choices when viewing current NOAA Level 3 data
                product_choice.config(state=Tkinter.DISABLED)
                elevation_choice.config(state=Tkinter.DISABLED)
                product_choice['menu'].delete(0, 'end')
                elevation_choice['menu'].delete(0, 'end')
                chosen_product.set(None)
                chosen_elevation.set(None)
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
        draw_info(headersdecoded(paised,fraasid))
        if paised[0] > 255:
            #As far as Level 3 goes, the product code cannot exceed 255 (11111111).
            msgtostatus(fraasid["incorrect_format"])
            return None
        if paised[0] == 94 or paised[0] == 99: 
            radials=valarray(decompress(stream),paised[18],paised[19])
        elif paised[0] == 161 or paised[0] == 159 or paised[0] == 163:
            scale=paised[27]
            offset=paised[28]
            radials=valarray(decompress(stream),offset,scale,paised[0])
        if paised[0] == 165:
            minval=0
            increment=1
            radials=valarray(decompress(stream),minval,increment,paised[0])
    elif fmt == 1:
        produktid=hdf5_productlist(currentfilepath)
        sweeps=hdf5_sweepslist(currentfilepath)
        print produktid, sweeps
        paised=hdf5_headers(currentfilepath,produktid[0],sweeps[0])
        print paised
        draw_info(headersdecoded(paised,fraasid))
        radials=hdf5_valarray(currentfilepath)
        product_choice['menu'].delete(0, 'end')
        elevation_choice['menu'].delete(0, 'end')
        for i in produktid:
            product_choice['menu'].add_command(label=i, command=lambda produkt=i: change_product(produkt))
        chosen_product.set(produktid[0])
        for j in xrange(len(sweeps)):
            elevation_choice['menu'].add_command(label=str(float(sweeps[j])), command=lambda index=j: change_elevation(index))
        chosen_elevation.set(str(float(sweeps[0])))
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
        paised=level2_headers(level2fail,"REF",0)
        print paised
        draw_info(headersdecoded(paised,fraasid))
        radials=level2_valarray(level2fail,"REF",0)
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
    return 0
def reset_colortable():
    global customcolortable
    global rhishow
    global rhiaz
    global renderagain
    customcolortable=None
    if rhishow:
        mkrhi(rhiaz)
        renderagain=1
    else:
        render_radials()
def change_colortable(tabel):
    global rhishow
    global rhiaz
    global customcolortable
    global renderagain
    customcolortable=tabel
    if rhishow:
        mkrhi(rhiaz)
        renderagain=1
    else:
        render_radials()
def change_elevation(index):
    global radials
    global canvasbusy
    global sweeps
    global currentfilepath
    global level2fail
    global fmt
    global paised
    if not canvasbusy:
        if fmt == 1:
            paised[17]=sweeps[index]
            paised[0]=chosen_product.get()
            chosen_elevation.set(str(float(paised[17])))
            skanniarv=hdf5_leiaskann(currentfilepath,paised[0],sweeps[index])
            if skanniarv != None:
                radials=hdf5_valarray(currentfilepath,skanniarv)
                draw_info(headersdecoded(paised,fraasid))
                render_radials()
            else:
                msgtostatus(fraasid["not_found_at_this_level"])
        elif level2fail:            
            #Load data.
            try:
                chosen_elevation.set(str(float(sweeps[index])))
                product_choice['menu'].delete(0, 'end') #Clean up products menu for below.
                #Moments available for a particular scan
                moments=level2fail.scan_info()[index]["moments"] #First moments of the first scan, as that is going to be loaded by default.
                for j in moments:
                    product_choice["menu"].add_command(label=j, command=lambda scan=index, moment=j: change_product(moment,index))
                paised=level2_headers(level2fail, paised[0], index)
                print paised
                radials=level2_valarray(level2fail, paised[0], index)
            except: #Most likely not found, defaulting back to reflectivity product, which should be present at all scans.
                radials=level2_valarray(level2fail, "REF", index)
                chosen_product.set("REF")
            draw_info(headersdecoded(paised,fraasid))
            if radials != None: render_radials() #If the data is in fact there..
    return 0
def change_product(newproduct,level2scan=0):
    global sweeps
    global radials
    global paised
    global canvasbusy
    global currentfilepath
    global level2fail
    global fmt
    if not canvasbusy:
        if fmt == 1:
            chosen_product.set(newproduct)
            skanniarv=hdf5_leiaskann(currentfilepath,newproduct,float(chosen_elevation.get()))
            if skanniarv != None:
                radials=hdf5_valarray(currentfilepath,skanniarv)
                paised[0]=newproduct
                draw_info(headersdecoded(paised,fraasid))
                render_radials()
            else:
                msgtostatus(fraasid["not_found_at_this_level"])
        elif level2fail:
            chosen_product.set(newproduct)
            paised=level2_headers(level2fail,newproduct,level2scan)
            print paised
            try:
                radials=level2_valarray(level2fail,newproduct,level2scan)
                draw_info(headersdecoded(paised,fraasid))
                render_radials()
            except:
                msgtostatus(fraasid["error_during_loading"]) #Different kind of error because on Level 2, the product HAS to be there!(Product list is reloaded every elevation change)
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
        draw_info(headersdecoded(paised,fraasid))
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
    if sizeb4 == []: sizeb4=dim #If sizeb4 is empty, assume previous size was current one.
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
    if not canvasbusy and len(paised) > 0:
        x=event.x
        y=event.y
        info=getinfo(x,y)
        if not rhishow:
            lat=info[0][0]
            latl="N" if lat >= 0 else "S"
            lon=info[0][1]
            lonl="E" if lon >= 0 else "W"
            val=info[2][0]
            infostring=u"%.3f°%s %.3f°%s; %s: %.1f°; %s: %.3f km; %s: %s" % (abs(lat),latl,abs(lon),lonl,fraasid["azimuth"],floor(info[1][0]*10)/10.0,fraasid["range"],floor(info[1][1]*1000)/1000.0,fraasid["value"],val)
            msgtostatus(infostring)
        else:
            gr,h,val=info
            msgtostatus(u"x: %.3f km; y: %.3f km; %s: %s" % (gr, h, fraasid["value"], val))
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
        if len(sweeps) > 1:
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
                msgtostatus(fraasid["choose_pseudorhi_status"])
        else:
            tkMessageBox.showerror(fraasid["name"],fraasid["cant_make_pseudorhi"])
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
        if currentfilepath[-3:]==".h5" or sisu[1:4]=="HDF":
            try:
                skanniarv=hdf5_leiaskann(currentfilepath,paised[0],sweeps[i])
                rhidata.append(hdf5_valarray(currentfilepath,skanniarv,az))
                productsweeps.append(sweeps[i])
            except:
                pass
        elif level2fail:
            rida=level2_valarray(level2fail,paised[0],i,az)
            if rida != None:
                if sweeps[i] > sweeps[i-1] or sweeps[i]-sweeps[i-1] < 0.2:
                    productsweeps.append(sweeps[i])
                    #Additional check for SAILS scans.
                    if len(productsweeps) > 1 and productsweeps[-2]-productsweeps[-1] > 1: #If reduction of elevation over a degree, normally would indicate SAILS scan
                        productsweeps.pop(-1) #Don't add it to the list
                    else:
                        rhidata.append(level2_valarray(level2fail,paised[0],i,az))
        msgtostatus(fraasid["reading_elevation"]+str(sweeps[i])+u"°")
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
    global customcolortable
    if not canvasbusy:
        draw_info(rhiheadersdecoded(paised,az,fraasid))
        msgtostatus(fraasid["drawing_pseudorhi"])
        pikkus=int(w.cget("height"))
        laius=int(w.cget("width"))
        pilt=uuspilt("RGB", (laius,pikkus), "#000025") 
        joonis=Draw(pilt)
        samm=paised[25]
        if customcolortable: #If color table has been overridden by user
            varvitabel=loadcolortable("../colortables/"+customcolortable) #Load a custom color table
        else:
            varvitabel=loadcolortable("../colortables/"+colortablenames[paised[0]]+".txt") #Load a color table
        init_drawlegend(paised[0],varvitabel) #Redraw color table just in case it is changed in RHI mode.
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
        taskbarbtn1.config(image=ppiimg)
        taskbarbtn5.config(state=Tkinter.DISABLED)
        product_choice.config(state=Tkinter.DISABLED)
        elevation_choice.config(state=Tkinter.DISABLED)
        w.coords(radaripilt,tuple(canvasctr))
        w.itemconfig(radaripilt, image=rhiout)
        msgtostatus(fraasid["ready"])
        rhishow=1
    return 0
def change_language(lang):
    global conf
    conf["lang"]=lang
    save_config_file()
    tkMessageBox.showinfo(fraasid["name"],translations.phrases[lang]["conf_restart_required"])
clickcoords=[]
output=Tkinter.Tk()
output.title(fraasid["name"])
output.bind("<Configure>",on_window_reconf)
##Drawing the menu
menyy = Tkinter.Menu(output)
output.config(menu=menyy)
failimenyy = Tkinter.Menu(menyy,tearoff=0)
radarmenyy = Tkinter.Menu(menyy,tearoff=0)
toolsmenyy = Tkinter.Menu(menyy,tearoff=0)
abimenyy = Tkinter.Menu(menyy,tearoff=0)
languagemenyy=Tkinter.Menu(menyy,tearoff=0)
menyy.add_cascade(label=fraasid["file"], menu=failimenyy)
menyy.add_cascade(label=fraasid["nexrad"], menu=radarmenyy)
menyy.add_cascade(label=fraasid["tools"], menu=toolsmenyy)
menyy.add_cascade(label=fraasid["current_language"], menu=languagemenyy)
menyy.add_cascade(label=fraasid["help"], menu=abimenyy)
failimenyy.add_command(label=fraasid["open_datafile"], command=load)
failimenyy.add_command(label=fraasid["open_url"], command=loadurl)
failimenyy.add_separator()
failimenyy.add_command(label=fraasid["export_img"], command=exportimg)
failimenyy.add_separator()
failimenyy.add_command(label=fraasid["quit"], command=output.destroy)
radarmenyy.add_command(label=fraasid["current_data"], command=activatecurrentnexrad)
radarmenyy.add_separator()
radarmenyy.add_command(label=fraasid["level3_station_selection"],command=choosenexrad)
toolsmenyy.add_command(label=fraasid["add_rmax"],command=configrmaxadd)
colortablemenu=Tkinter.Menu(toolsmenyy,tearoff=0) #Custom color tables menu
listcolortables() #Adds all available color tables to the menu
colortablemenu.add_separator()
colortablemenu.add_command(label=fraasid["default_colors"],command=reset_colortable)
toolsmenyy.add_cascade(label=fraasid["color_table"], menu=colortablemenu, underline=0)
toolsmenyy.add_command(label=fraasid["dyn_labels"],command=dynlabels_settings)
abimenyy.add_command(label=fraasid["key_shortcuts_menuentry"], command=keys_list)
abimenyy.add_separator()
abimenyy.add_command(label=fraasid["about_program"], command=about_program)
languagemenyy.add_command(label=fraasid["language_estonian"], command=lambda: change_language("estonian"))
languagemenyy.add_command(label=fraasid["language_english"], command=lambda: change_language("english"))
##Drawing area
w = Tkinter.Canvas(output,width=600,height=400,highlightthickness=0)
w.bind("<Button-1>",leftclick)
w.bind("<Button-3>",rightclick)
w.bind("<B1-Motion>",onmotion)
w.bind("<B3-Motion>",onmotion)
w.bind("<ButtonRelease-1>",onrelease)
w.bind("<ButtonRelease-3>",onrelease)
w.bind("<Motion>",onmousemove)
w.config(background="#000025")
w.config(cursor="crosshair")
w.grid(row=0,column=0)
radaripilt=w.create_image(tuple(img_center))
clicktext=w.create_image((300,300))
legend=w.create_image((582,200))
radardetails=w.create_image((300,380))
zoomrect=w.create_rectangle((0,0,200,200),outline="white",state=Tkinter.HIDDEN) #Ristkülik, mis joonistatakse ekraanile suurendamise ajal.
progress=w.create_rectangle((0,390,400,400),fill="#0044ff",state=Tkinter.HIDDEN)
#Key bindings
output.bind("r",resetzoom)
output.bind("i",toinfo)
output.bind("p",topan)
output.bind("z",tozoom)
output.bind("h",chooserhi)
moderaam=Tkinter.Frame(output)
moderaam.grid(row=1,column=0,sticky="we")
moderaam.config(bg="#0099ff")
panimg=PhotoImage(file="../images/pan.png")
zoomimg=PhotoImage(file="../images/zoom.png")
resetzoomimg=PhotoImage(file="../images/resetzoom.png")
infoimg=PhotoImage(file="../images/info.png")
rhiimg=PhotoImage(file="../images/rhi.png")
ppiimg=PhotoImage(file="../images/ppi.png")
reloadimg=PhotoImage(file="../images/reload.png")
taskbarbtn1=Tkinter.Button(moderaam, bg="#0099ff",activebackground="#0044ff", highlightbackground="#0044ff", image=panimg, command=topan)
taskbarbtn1.grid(row=0,column=0)
taskbarbtn2=Tkinter.Button(moderaam, bg="#0099ff",activebackground="#0044ff", highlightbackground="#0044ff", image=zoomimg, command=tozoom)
taskbarbtn2.grid(row=0,column=1)
taskbarbtn3=Tkinter.Button(moderaam, bg="#0099ff",activebackground="#0044ff", highlightbackground="#0044ff", image=resetzoomimg, command=resetzoom)
taskbarbtn3.grid(row=0,column=2)
taskbarbtn4=Tkinter.Button(moderaam, bg="#0099ff",activebackground="#0044ff", highlightbackground="#0044ff", image=infoimg, command=toinfo)
taskbarbtn4.grid(row=0,column=3)
taskbarbtn5=Tkinter.Button(moderaam, bg="#0099ff",activebackground="#0044ff", highlightbackground="#0044ff", image=rhiimg, command=chooserhi)
taskbarbtn5.grid(row=0,column=4)
taskbarbtn6=Tkinter.Button(moderaam, bg="#0099ff",activebackground="#0044ff", highlightbackground="#0044ff", image=reloadimg, command=reloadfile)
taskbarbtn6.grid(row=0,column=5)
chosen_elevation = Tkinter.StringVar(moderaam)
elevation_choice=Tkinter.OptionMenu(moderaam, chosen_elevation,None)
elevation_choice.config(bg="#44bbff",activebackground="#55ccff",highlightbackground="#55ccff",state=Tkinter.DISABLED)
elevation_choice.grid(row=0,column=6)
chosen_product= Tkinter.StringVar(moderaam)
product_choice=Tkinter.OptionMenu(moderaam, chosen_product,None)
product_choice.config(bg="#44bbff",activebackground="#55ccff",highlightbackground="#55ccff",state=Tkinter.DISABLED)
product_choice.grid(row=0,column=7)
status=Tkinter.Label(output, text=None, justify=Tkinter.LEFT, anchor="w")
status.grid(row=2,column=0,sticky="w")
output.mainloop()

