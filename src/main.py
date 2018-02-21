#!/usr/bin/python3
# -*- coding: utf-8 -*-
#


##Copyright (c) 2018, Tarmo Tanilsoo
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
####3. Neither the name of the copyright holder nor the names of its contributors
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
from PIL.Image import merge as yhendapilt
from PIL.ImageDraw import Draw
from PIL.ImageTk import PhotoImage, BitmapImage
from PIL import ImageFont
from math import floor, sqrt, radians as d2r, degrees as r2d, cos, copysign, pi
from colorconversion import *
from coordinates import *
import sys
import datetime
if sys.version_info[0] > 2:
    import tkinter as Tkinter
    from tkinter import filedialog as tkFileDialog
    from tkinter import messagebox as tkMessageBox
    import urllib.request as urllibRequest
else:
    import Tkinter
    import tkFileDialog
    import tkMessageBox
    import urllib2 as urllibRequest
import json
import os
configfile=open("config.json","r")
conf=json.load(configfile)
configfile.close()
fraasid=translations.phrases[conf["lang"]]
#Importing geodata
print(fraasid["loading_states"])
import states
print(fraasid["coastlines"])
import coastlines
print(fraasid["countries"])
import countries
print(fraasid["lakes"])
import lakes
print(fraasid["rivers"])
import rivers
print(fraasid["NA_roads"])
import major_NA_roads
class Display(): #Class for storing properties of current display
    def __init__(self):
        self.quantity=None
        self.elevationNumber=None
        self.softElIndex=None
        self.elevation=None
        self.productTime=None
        self.scanTime=None
        self.fileType=None
        self.data=None
        self.rhiAzimuth=None
        self.rhiData=None
        self.rhiElevations=None
        self.isRHI=False
        self.rhiStart=0
        self.rhiEnd=250
        self.gain=None
        self.offset=None
        self.nodata=None
        self.undetect=None
        self.rangefolding=None
        self.rstart=None
        self.rscale=None
        #former separate globals
        self.imageCentre=[300,200]
        self.renderCentre=[1000,1000] #former currentDisplay.renderCentre
        self.zoomLevel=1
        self.isSameMap=False #If True, don't render the map again on a new render - Condition: if the resultant map is expected to be identical to previous renders
        self.renderAgain=False #If true, product, colour table etc as been changed while in PseudoRHI view. Need to render again upon returning to PPI
        self.isCanvasBusy=False
class BatchExportWindow(Tkinter.Toplevel): #Window for batch export
    def __init__(self, parent, title = None):
        Tkinter.Toplevel.__init__(self,parent)
        self.title(fraasid["batch_export"])
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        self.datadir=None
        self.outdir=None
        self.outfmt=Tkinter.StringVar()
        self.outfmt.set("png") #PNG output by default
        self.outprod=Tkinter.StringVar()
        self.outprod.set("DBZH")
        self.outel=Tkinter.StringVar()
        self.outel.set("0.5")
        #Input and output directories
        frame1=Tkinter.Frame(self)
        label1=Tkinter.Label(frame1,text=fraasid["batch_input"])
        label1.grid(column=0,row=0)
        self.btn1=Tkinter.Button(frame1,text=fraasid["batch_pick"],width=30,command=lambda: self.pickdir(0))
        self.btn1.grid(column=1,row=0)
        label2=Tkinter.Label(frame1,text=fraasid["batch_output"])
        label2.grid(column=0,row=1)
        self.btn2=Tkinter.Button(frame1,text=fraasid["batch_pick"],width=30,command=lambda: self.pickdir(1))
        self.btn2.grid(column=1,row=1)
        frame1.grid(column=0,row=0)
        #Output format
        frame2=Tkinter.Frame(self,relief=Tkinter.SUNKEN,borderwidth=1)
        label3=Tkinter.Label(frame2,text=fraasid["batch_fmt"])
        label3.grid(column=0,row=0,columnspan=2)
        radio1=Tkinter.Radiobutton(frame2,text="GIF",variable=self.outfmt,value="gif")
        radio1.grid(column=0,row=1)
        radio2=Tkinter.Radiobutton(frame2,text="PNG",variable=self.outfmt,value="png")
        radio2.grid(column=1,row=1)
        frame2.grid(column=1,row=0)
        #Product and sweep selection.
        frame3=Tkinter.Frame(self)
        label4=Tkinter.Label(frame3,text="Product")
        label4.grid(column=0,row=0)
        list1=Tkinter.Entry(frame3,textvariable=self.outprod,width=7)
        list1.grid(column=1,row=0)
        label5=Tkinter.Label(frame3,text="Elevation")
        label5.grid(column=2,row=0)
        list2=Tkinter.Entry(frame3,textvariable=self.outel,width=7)
        list2.grid(column=3,row=0)
        frame3.grid(column=0,row=1)
        #OK button
        okbutton=Tkinter.Button(self,text="OK",command=self.exportdir)
        okbutton.grid(column=1,row=1)
        self.mainloop()
    def pickdir(self,value):
        dirs=["../data","../radar_images"]
        directory=tkFileDialog.askdirectory(initialdir=dirs[value])
        if directory: #If something was entered
            if value: #If setting output directory (1)
                button=self.btn2
                self.outdir=directory
            else:
                button=self.btn1
                self.datadir=directory
            button.config(text=directory)
        return 0
    def exportdir(self): #Process the data files
        global currentlyOpenData
        global currentDisplay
        global radarposprev
        global level2fail
        if self.outdir and self.datadir:
            files=sorted(os.listdir(self.datadir))
            counter=1
            for i in files:
                path=self.datadir+"/"+i
                currentfilepath=path
                stream=file_read(path)
                if path[-3:]== ".h5" or stream[1:4]==b"HDF":
                    productChoice.config(state=Tkinter.NORMAL)
                    elevationChoice.config(state=Tkinter.NORMAL)
                    hcanames=fraasid["iris_hca"]
                    currentlyOpenData=HDF5(path)
                elif stream[0:4] == b"AR2V" or stream[0:8] == b"ARCHIVE2":
                    productChoice.config(state=Tkinter.NORMAL)
                    elevationChoice.config(state=Tkinter.NORMAL)
                    currentlyOpenData=NEXRADLevel2(path)
                else:
                    hcanames=fraasid["hca_names"]
                    currentlyOpenData=NEXRADLevel3(path)
                #Getting elevation index
                for j in range(len(currentlyOpenData.nominalElevations)):
                    if abs(float(self.outel.get())-currentlyOpenData.nominalElevations[j]) < 0.05:
                        if self.outprod.get() in currentlyOpenData.data[j]:
                            if not (currentlyOpenData.type=="NEXRAD2" and "VRAD" in currentlyOpenData.data[j]):
                                loadData(self.outprod.get(),j)
                                drawInfo()
                                renderRadarData()
                                exportimg(self.outdir+"/"+str(counter).zfill(4)+"."+self.outfmt.get(),False)
                                counter+=1
            self.onclose()
            load(path) #Open the last rendered file properly.
        else:
            tkMessageBox.showwarning(fraasid["name"],fraasid["batch_notfilled"])
        return 0
    def detectfmt(self, path, stream):
        if path[-3:]== ".h5" or stream[1:4]=="HDF":
            return 1
        elif stream[0:4] == "AR2V" or stream[0:8]=="ARCHIVE2":
            return 2
        else:
            return 0
    def onclose(self):
        global batchexportopen
        batchexportopen=0
        self.destroy()
        return 0
class AddRMAXChooser(Tkinter.Toplevel):
    def __init__(self, parent, title = None):
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
        global currentDisplay
        for j in range(paddingamt):
            currentDisplay.data[i].append(None)
        for k in range(slicestart,sliceend,1):
            currentDisplay.data[i][k+rmaxbins]=currentDisplay.data[i][k]
            currentDisplay.data[i][k]=None
        return 0
    def addrmax(self):
        global currentlyOpenData
        global currentDisplay
        az0=round(float(self.az0.get()),7)
        az1=round(float(self.az1.get()),7)
        r0=float(self.r0.get())
        r1=float(self.r1.get())
        prf=float(self.prf.get())
        rmax=299792.458/prf/2
        if currentlyOpenData.type == "NEXRAD3": rmax*=cos(d2r(float(paised[17])))
        r0new=r0+rmax
        r1new=r1+rmax
        asimuudid=currentlyOpenData.azimuths[currentDisplay.softElIndex]
        for i in range(len(currentDisplay.data)):
            r=currentDisplay.data[i]
            curaz=asimuudid[i]
            firstBinOffset=int((currentDisplay.rstart/currentDisplay.rscale)) #Correct range to a particular bin!
            slicestart=int(r0/currentDisplay.rscale)-firstBinOffset
            sliceend=int(r1/currentDisplay.rscale)-firstBinOffset
            if slicestart < 0: slicestart=0
            if sliceend < 0: sliceend=0 #Seems like overkill but these days always pays to check everything that is related to user input
            rmaxbins=int(round(rmax/currentDisplay.rscale)) #Amount of bins that coorespond to Rmax
            paddingamt=int(round(r1new/currentDisplay.rscale)-firstBinOffset)-len(r)
            if az0 < az1:
                if curaz >= az0 and curaz < az1:
                    self.processgate(i,paddingamt,rmaxbins,slicestart,sliceend)
            else:
                if curaz >= az0 or curaz < az1:
                    self.processgate(i,paddingamt,rmaxbins,slicestart,sliceend)
        self.onclose()
        renderRadarData()
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
        jaamad=file_read("nexradstns.txt").decode("utf-8").split("\n")
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
            print(selection)
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
        self.updateInterval=0
        self.sourceType=Tkinter.IntVar()
        self.enabled=Tkinter.IntVar()
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
        self.enabledcheck=Tkinter.Checkbutton(self, variable=self.enabled, text=fraasid["dyn_enabled"])
        self.enabledcheck.grid(column=1,row=2)
        okbutton=Tkinter.Button(self,text="OK",command=lambda: self.submit_source(parent))
        okbutton.grid(column=2,row=3)

        if parent.allikaIndeks == -1:
            self.dataPath.set("")
            self.sourceType.set(0)
            self.enabled.set(1)
        else:
            values=conf["placesources"][parent.allikaIndeks]
            self.sourceType.set(values[0])
            self.dataPath.set(values[1])
            self.updateInterval=values[2]
            self.enabled.set(values[4])
            self.dataName=values[5]
        self.mainloop()
    def pickfile(self): #Pick a source file
        pathd=tkFileDialog.Open(None,initialdir="../places")
        path=pathd.show()
        self.dataPath.set(path)
    def goonline(self): #Ensure the update interval selection is active
        self.dataPath.set("")
    def submit_source(self,parent):
        global conf
        if parent.allikaIndeks == -1:
            try:
                if self.sourceType.get() == 1:
                    name=json.loads(file_read(self.dataPath.get()))["name"]
                else:
                    name=self.dataPath.get()
            except:
                pass
            conf["placesources"].append([self.sourceType.get(),self.dataPath.get(),self.updateInterval,-1,self.enabled.get(),name]) #New
        else:
            conf["placesources"][parent.allikaIndeks]=[self.sourceType.get(),self.dataPath.get(),self.updateInterval,-1,self.enabled.get(),self.dataName] #Edit
        ##Format of dynamic information setting [Online/Local, path, update interval if relevant, last download timestamp if online content]
        ##Open the file to fetch the name.
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
            liststring=check+types[i[0]]+" - "+i[5]
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
        try:
            self.onclose()
            download_file(currenturl)
            currentfilepath="../cache/urlcache"
            load(currentfilepath)
        except:
            print(sys.exc_info())
            tkMessageBox.showerror(fraasid["name"],fraasid["download_failed"])
    def onclose(self):
        global urlwindowopen
        urlwindowopen=0
        self.destroy()
sizeb4=[] #Latest window dimensions for on_window_reconf 
currentDisplay=Display()
rlegend=None #Legend as PhotoImage
infotekst=None #Information as PhotoImage
clickbox=None #Pixel information as PhotoImage
rendered=None #Rendered radar image as PhotoImage
rhiout=None #PseudoRHI as PhotoImage
#Above as an PIL/Pillow image.
rlegend2=uuspilt("RGBA",(1,1))
infotekst2=uuspilt("RGBA",(1,1))
clickbox2=uuspilt("RGBA",(1,1))
rendered2=uuspilt("RGBA",(1,1))
rhiout2=uuspilt("RGBA",(1,1))
currentfilepath=None #Path to presently open file
#Pildifontide laadimine
pildifont=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",12)
pildifont2=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",13)
currenturl=None
nexradstn=conf["nexradstn"] #Chosen NEXRAD station
urlwindowopen=0 #1 if dialog to open an URL is open
nexradchooseopen=0 #1 if dialog to choose a nexrad station is open
rmaxaddopen=0 #1 if configuration window to add Rmax to chunk of data is open.
dynlabelsopen=0 #same rule as above for selection of dynamic labels
batchexportopen=0 #same as when batch export window is open.
zoom=1
info=0
rhi=0
direction=1
currentlyOpenData=None #Object storing unscaled data from the opened file.
radarposprev=None #Radar position during previous render
canvasdimensions=[600,600]
canvasctr=[300,300]
clickboxloc=[0,0]
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
       "VRAD": "m/s",
       "VRADH": "m/s",
       "VRADV": "m/s",
       "VRADDH": "m/s",
       "VRADDV": "m/s",
       "WRAD": "m/s",
       "WRADH": "m/s",
       "WRADV": "m/s",
       "PHIDP": u"°"}
hcanames=fraasid["hca_names"] #Hydrometeor classifications
colortablenames={"DBZ":"dbz",
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
                 "VRADDH":"v",
                 "VRADDV":"v",
                 "V":"v",
                 "VEL":"v",
                 "ZDR":"zdr",
                 "LZDR":"zdr",
                 "RHOHV":"rhohv",
                 "RHO":"rhohv",
                 "KDP":"kdp",
                 "HCLASS": "hclass", #hca kui level 3!"
                 "PHIDP": "phi",
                 "WRAD": "sw",
                 "WRADH": "sw",
                 "WRADV": "sw",
                 "SW": "sw"} #Names for color tables according to product
customcolortable=None
def download_file(url,dst="../cache/urlcache"):
    req=urllibRequest.Request(url)
    req.add_header("User-agent","TRV/"+fraasid["name"].split()[1])
    res=urllibRequest.urlopen(req,timeout=10)
    sisu=res.read()
    res.close()
        
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
def batch_export(): #Batch export
    global batchexportopen
    if batchexportopen == 0:
        batchexportopen=1
        BatchExportWindow(output)
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
    global currentDisplay
    global currentfilepath
    global currenturl
    if currentDisplay.isRHI: topan()    
    productChoice.config(state=Tkinter.NORMAL)
    elevationChoice.config(state=Tkinter.NORMAL)
    populatenexradmenus(product)
    currenturl="ftp://tgftp.nws.noaa.gov/SL.us008001/DF.of/DC.radar/DS."+product+"/SI."+conf["nexradstn"]+"/sn.last"
    try:
        download_file(currenturl,"../cache/nexradcache/"+product)
        currentfilepath="../cache/nexradcache/"+product
        load(currentfilepath)
    except:
        print(sys.exc_info())
        tkMessageBox.showerror(fraasid["name"],fraasid["download_failed"])
def activatecurrentnexrad():
    productChoice.config(state=Tkinter.NORMAL)
    elevationChoice.config(state=Tkinter.NORMAL)
    fetchnexrad("p94r0")
    return 0
def populatenexradmenus(product="p94r0"):
    ids={"p94":"DBZ",
         "p99":"VRADDH", #[sic!] - Level 3 product 99 is dealiased radial velocity
         "159":"ZDR",
         "161":"RHOHV",
         "163":"KDP",
         "165":"HCLASS"}
    elevationChoice["menu"].delete(0, 'end')
    for i in range(4):
        productcode=product[:-1]+str(i)
        elevationChoice["menu"].add_command(label=fraasid["level3_slice"].replace("/NR/",str(i+1)),command=lambda x=productcode: fetchnexrad(x))
    index=product[-1]
    chosenElevation.set(fraasid["level3_slice"].replace("/NR/",str(int(product[-1])+1)))
    chosenProduct.set(ids[product[0:3]])
    productChoice["menu"].delete(0, 'end')
    productChoice["menu"].add_command(label="DBZ",command=lambda x=index: fetchnexrad("p94r"+index))
    productChoice["menu"].add_command(label="VRADDH",command=lambda x=index: fetchnexrad("p99v"+index))
    productChoice["menu"].add_command(label="ZDR",command=lambda x=index: fetchnexrad("159x"+index))
    productChoice["menu"].add_command(label="RHOHV",command=lambda x=index: fetchnexrad("161c"+index))
    productChoice["menu"].add_command(label="KDP",command=lambda x=index: fetchnexrad("163k"+index))
    productChoice["menu"].add_command(label="HCLASS",command=lambda x=index: fetchnexrad("165h"+index))
    return 0
def exportimg(path=None,GUI=True):
    global rendered2
    global rlegend2
    global infotekst2
    global rhiout
    global clickbox2
    global clickboxloc
    global currentDisplay
    if len(currentDisplay.data) > 0:
        y=int(w.cget("height"))
        if y % 2 != 0 and not currentDisplay.isRHI: y+=1
        x=int(w.cget("width"))
        if x % 2 != 0 and not currentDisplay.isRHI: x+=1
        halfx=int(x/2.0)
        halfy=int(y/2.0)
        cy=int(1000-currentDisplay.imageCentre[1]+halfy)
        cx=int(1000-currentDisplay.imageCentre[0]+halfx)
        cbx=clickboxloc[0]
        cby=clickboxloc[1]
        cbh=84 if not currentDisplay.isRHI else 45
        if not path:
            filed=tkFileDialog.SaveAs(None,initialdir="../radar_images")
            path=filed.show()
        if path != "":
            try:
                outimage=uuspilt("RGB",(x,y),"#000025")
                joonis=Draw(outimage)
                if not currentDisplay.isRHI:
                    if rendered != None: outimage.paste(rendered2.crop((cx-halfx,cy-halfy,cx+halfx,cy+halfy)),((0,0,x,y))) #PPI
                else:
                    outimage.paste(rhiout2,(0,0,x,y)) #PseudoRHI
                if clickbox != None: outimage.paste(clickbox2,(cbx,cby+1,cbx+170,cby+cbh+1))
                if rlegend != None: outimage.paste(rlegend2,(x-35,halfy-213,x,halfy+212))
                if infotekst != None: outimage.paste(infotekst2,(halfx-250,y-30,halfx+250,y-10))
                outimage.save(path)
                if GUI: tkMessageBox.showinfo(fraasid["name"],fraasid["export_success"])
            except:
                tkMessageBox.showerror(fraasid["name"],fraasid["export_format_fail"])
        return 0
    else:
        tkMessageBox.showerror(fraasid["name"],fraasid["no_data_loaded"])
def getrhibin(h,gr,a):
    global currentDisplay
    kordaja=currentDisplay.rscale**-1
    lowestBeamStart=min(currentDisplay.rhiElevations)-0.5 #Assuming beamwidth of 1°
    highestBeamEnd=max(currentDisplay.rhiElevations)+0.5
    if a < lowestBeamStart: return fraasid["no_data"]
    if a >= highestBeamEnd: return fraasid["no_data"]
    elevationsCount=len(currentDisplay.rhiElevations)
    for i in range(elevationsCount):
        condition1=lowestBeamStart if i == 0 else (currentDisplay.rhiElevations[i-1]+currentDisplay.rhiElevations[i])/2
        condition2=(currentDisplay.rhiElevations[i]+currentDisplay.rhiElevations[i+1])/2 if i < elevationsCount-1 else highestBeamEnd
        if a >= condition1 and a < condition2:
            indeks=int(gr*kordaja)
            if len(currentDisplay.rhiData[i]) <= indeks:
                val=None
            else:
                val=currentDisplay.rhiData[i][indeks]
            if val != None and (currentDisplay.quantity == "HCLASS"):
                val=hcanames[int(val)]
            elif val == None:
                val=fraasid["no_data"]
            return val
def getbin(azr):
    global hcanames
    global currentDisplay
    global currentlyOpenData
    delta=None #Difference between adjacent azimuths
    h=beamheight(azr[1],currentDisplay.elevation) #Radar beam height
    try:
        selected_az=azr[0]
        elIndex=currentDisplay.softElIndex
        for i in range(len(currentDisplay.data)):
            previous=currentlyOpenData.azimuths[elIndex][i-1]
            current=currentlyOpenData.azimuths[elIndex][i]
            if previous-current > 350:  #Great reason to believe we've crossed North
                current+=360
            if selected_az >= previous and selected_az < current:
                azi=i-1
                break
        kordaja=currentDisplay.rscale**-1
        kaugus=azr[1] if not currentlyOpenData.type == "NEXRAD3" else azr[1]/cos(d2r(currentDisplay.elevation))
        mindistance=currentDisplay.rstart
        if kaugus >= mindistance:
            val=currentDisplay.data[int(azi)][int((kaugus-mindistance)*kordaja)]
        else:
            val=None
        delta=None
        if val != currentDisplay.nodata and val != currentDisplay.undetect and val != currentDisplay.rangefolding and (currentDisplay.quantity == "VRAD"):
            valprev=currentDisplay.data[int(azi)-1][int((kaugus-mindistance)*kordaja)]
            delta=abs(float(val)-valprev) if (valprev != None and valprev != "RF") else None
        elif val != currentDisplay.nodata and currentDisplay.quantity == "HCLASS":
            val=hcanames[int(val)]
        elif val == currentDisplay.nodata or val == None:
            val=fraasid["no_data"]
    except:
        val = fraasid["no_data"]
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
def drawInfobox(x,y):
    global clickbox
    global clickbox2
    global clickboxloc
    global units
    global currentDisplay
    andmed=getinfo(x,y)
    azrange=andmed[1]
    data=andmed[2]
    vaartus=data[0] if not currentDisplay.isRHI else data
    if vaartus == "RF":
        row0="RF"
    elif vaartus == fraasid["no_data"]:
        row0=fraasid["no_data"]
    else:
        row0=u"%s %s" % (vaartus, units[currentDisplay.quantity]) 
    if not currentDisplay.isRHI:        
        coords=andmed[0]
        latletter="N" if coords[0] > 0 else "S"
        lonletter="E" if coords[1] > 0 else "W"
        row1=u"%.5f°%s %.5f°%s" % (abs(coords[0]),latletter,abs(coords[1]),lonletter)
        row2=u"%s: %.1f°" % (fraasid["azimuth"],azrange[0])
        row3=u"%s: %.3f km" % (fraasid["range"],azrange[1])
        row4=u"%s: ~%.1f km" % (fraasid["beam_height"],data[2])
        row5=None if (data[1] == None or data[1] == "RF") else fraasid["g2g_shear"]+": %.1f m/s" % (data[1])
    else:
        row1=u"%s: %.3f km" % (fraasid["range"],andmed[0])
        row2=u"%s: %.3f km" % (fraasid["height"],andmed[1])
    kastikorgus=84 if not currentDisplay.isRHI else 45
    kast=uuspilt("RGB",(170,kastikorgus),"#44ccff")
    kastdraw=Draw(kast)
    kastdraw.rectangle((0,0,170,16),fill="#0033ee")
    kastdraw.polygon((0,0,10,0,0,10,0,0),fill="#FFFFFF")
    kastdraw.text((9,1),text=row0, font=pildifont2)
    kastdraw.text((5,17),text=row1, fill="#000000", font=pildifont)
    kastdraw.text((5,30),text=row2, fill="#000000", font=pildifont)
    if not currentDisplay.isRHI:
        kastdraw.text((5,43),text=row3, fill="#000000", font=pildifont)
        kastdraw.text((5,56),text=row4, fill="#000000", font=pildifont)
        if row5 != None: kastdraw.text((5,69),text=row5, fill="#000000", font=pildifont)
    clickbox2=kast
    clickbox=PhotoImage(image=kast)
    clickboxloc=[x,y]
    w.itemconfig(clicktext,image=clickbox)
    w.coords(clicktext,(x+85,y+kastikorgus/2))
    return 0
def drawInfo():
    global infotekst
    global infotekst2
    global currentDisplay
    global fraasid
    if currentDisplay.isRHI:
        tekst=rhiheadersdecoded(currentDisplay,fraasid)
    else:
        tekst=headersdecoded(currentDisplay,fraasid)
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
        colortablemenu.add_command(label=i, command=lambda x=i:changeColourTable(x))
    return 0
def drawlegend(product,minimum,maximum,colortable):
    global rlegend
    global rlegend2
    global colortablenames
    global units
    global customcolortable
    global currentDisplay
    tabel=colortable
    unit=units[product]
    tosmooth=1
    if product == 165 or product == "HCLASS":
        tosmooth=0
    increment=(maximum-minimum)/400.0
    legendimg=uuspilt("RGB",(35,425),"#0033ee")
    legenddraw=Draw(legendimg)
    for i in range(400):
        val=minimum+increment*i
        legenddraw.rectangle((25,424-i,35,424-i),fill=getcolor(tabel,val,tosmooth))
    step=1.0/increment
    majorstep=10
    if customcolortable == "hurricane.txt": majorstep=20
    if product == "PHIDP":
        majorstep=45
    if product in [159, 163, 165, "HCLASS"]:
        majorstep=1
    if product in [161, "SQI"]: #RHOHV aka CC
        majorstep=0.1
    firstten=majorstep+minimum-minimum%majorstep
    if firstten == majorstep+minimum: firstten = minimum
    ystart=424-(firstten-minimum)*step
    lastten=maximum-maximum%majorstep
    hulk=int((lastten-firstten)/majorstep)
    yend=ystart-majorstep*step*hulk #If the next full step is too close to the edge.
    if yend < 30: hulk-=1 #Let's not list this last point on legend
    legenddraw.text((5,0),text=unit, font=pildifont)
    for j in range(hulk+1):
        y=ystart-majorstep*step*j
        if product == "HCLASS" and currentDisplay.fileType=="NEXRAD3": #Other products have a numeric value
            legendlist=["BI","AP","IC","DS","WS","RA","+RA","BDR","GR","HA","UNK","RF"]; #List of classifications
            legendtext=legendlist[int(firstten+j*majorstep)]
        elif product == "HCLASS" and currentDisplay.fileType=="HDF5":
            legendlist=["NM","RA","WS","SN","GR","HA"]
            legendtext=legendlist[int(firstten+j*majorstep)-1]
        else:
            legendval=round(firstten+j*majorstep,4)
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
    teejoon=kaardijoonis.line
    for joon in paths:
        f+=1
        for rada in joon:
            coords=mapcoordsFilter(map(lambda x,y=currentDisplay.zoomLevel,z=currentDisplay.renderCentre,a=radarcoords:getmapcoords(x,y,z,a),rada)) #To polar coords
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
def image_alpha(i1,i2,start=(0,0)): #Alpha blend two images
    r,g,b,a=i2.split()
    m=yhendapilt("RGB",(r,g,b))
    mm=yhendapilt("L",(a,))
    i1.paste(m,start,mm)
def showrendered(pilt):
    global rendered
    rendered=PhotoImage(image=pilt)
    w.itemconfig(radaripilt,image=rendered)
def init_drawlegend(product,tabel):
    global currentDisplay
    if product in [99, "VRAD", "VRADH", "VRADV", "VRADDH", "VRADDV"]:
        drawlegend(99,-63.5,63.5,tabel)
    elif product in [159, "ZDR", "LZDR"]:
        drawlegend(159,-6,6,tabel)
    elif product in [161, "RHOHV", product == "RHO"]:
        drawlegend(161,0.2,1.05,tabel)
    elif product in [163, "KDP"]:
        drawlegend(163,-2,7,tabel)
    elif product == "HCLASS" and currentDisplay.fileType=="NEXRAD3":
        drawlegend("HCLASS",0,12,tabel)
    elif product == "HCLASS" and currentDisplay.fileType=="HDF5":
        drawlegend("HCLASS",1,7,tabel)
    elif product in ["DBZ", "TH", "TV", "DBZH", "DBZV"]:
        drawlegend(94,-25,75,tabel)
    elif product == ["WRAD","WRADH","WRADV"]:
        drawlegend("SW",0,30,tabel)
    elif product == "PHIDP":
        drawlegend("PHIDP",0,180,tabel)
    elif product in ["SQI","QIDX","SQIH","SQIV"]:
        drawlegend("SQI",0,1,tabel)
    else:
        drawlegend(94,-25,75,tabel)
def renderRadarData():
    global rendered
    global rendered2
    global canvasctr
    global conf
    global canvasdimensions
    global joonis
    global kaardijoonis
    global kaart
    global currentfilepath
    global customcolortable
    global currentDisplay
    global currentlyOpenData
    product=currentDisplay.quantity
    elIndex=currentlyOpenData.elevationNumbers.index(currentDisplay.elevationNumber)
    currentDisplay.isCanvasBusy=True
    alguses=time.time()
    w.config(cursor="watch")
    w.itemconfig(progress,state=Tkinter.NORMAL)
    msgtostatus(fraasid["drawing"]+" "+fraasid["radar_image"])
    pilt=uuspilt("RGBA",(2000,2000),"#000025") #Image for image itself
    joonis=Draw(pilt)
    if not currentDisplay.isSameMap:
        kaart=uuspilt("RGBA",(2000,2000),(0,0,0,0)) #Image for map contours
        kaardijoonis=Draw(kaart)
    hulknurk=joonis.polygon
    current=0.0
    updateiter=0
    mindistance=currentDisplay.rstart
    samm=currentDisplay.rscale
    selectedColorTable=colortablenames[product]
    if currentDisplay.quantity == "HCLASS" and currentDisplay.fileType == "NEXRAD3":
        selectedColorTable="hca" #Override for HCLASS in NEXRAD Level 3
    if customcolortable:
        tabel=loadcolortable("../colortables/"+customcolortable)
    else:
        tabel=loadcolortable("../colortables/"+selectedColorTable+".txt")
    tosmooth=True #True if transitions in color table are to be smooth.
    if product == 165 or product == "HCLASS":
        tosmooth=False
    init_drawlegend(product,tabel) #Start drawing the color legend
    radarData=currentDisplay.data
    radarDatalen=len(radarData) #Length of radarData
    #Some variables for feedback on drawing progress
    hetkeseisusamm=radarDatalen**-1 
    hetkeseis=0
    #Setting Drawing resolution
    res=currentDisplay.zoomLevel*samm
    aste=int((res)**-1)
    #Get constants to avoid excessive calls.
    azimuths=[x for x in map(d2r,currentlyOpenData.azimuths[elIndex])]
    for i in range(radarDatalen):
        az=azimuths[i-1]
        d_az=azimuths[i]-az
        if d_az < -6: #We are crossing North
            d_az+=2*pi
        gate=radarData[i-1]
        kiiresuund=leiasuund(az,d_az,mindistance,currentDisplay,currentDisplay.zoomLevel,currentDisplay.renderCentre,samm)
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
                    hulknurk(path, fill=val) #PROBABLY MOST CPU-EXPENSIVE PART OF PLOTTING!!! HOW TO IMPROVE??
                    loetudtegelikke+=1
                    jubarenderdanud=True #Sign that we have already rendered at least part of this ray.
                elif jubarenderdanud: #We've gone out of drawing area
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
    rlat=d2r(float(currentlyOpenData.headers["latitude"]))
    rlon=d2r(float(currentlyOpenData.headers["longitude"]))
    currentDisplay.imageCentre=canvasctr
    showrendered(pilt)
    w.coords(radaripilt,tuple(currentDisplay.imageCentre)) #centre image
    if not currentDisplay.isSameMap:
        msgtostatus(fraasid["drawing"]+" "+fraasid["coastlines"].lower())
        drawmap(coastlines.points,(rlat,rlon),(17,255,17,255))
        msgtostatus(fraasid["drawing"]+" "+fraasid["lakes"].lower())
        drawmap(lakes.points,(rlat,rlon),(0,255,255,255),1)
        if rlon < 0:
            msgtostatus(fraasid["drawing"]+" "+fraasid["NA_roads"])
            drawmap(major_NA_roads.points,(rlat,rlon),(125,0,0,255),2)
        msgtostatus(fraasid["drawing"]+" "+fraasid["rivers"].lower())
        drawmap(rivers.points,(rlat,rlon),(0,255,255,255),1)
        msgtostatus(fraasid["drawing"]+" "+fraasid["states_counties"])
        drawmap(states.points,(rlat,rlon),(255,255,255,255),1)
        msgtostatus(fraasid["drawing"]+" "+fraasid["country_boundaries"])
        drawmap(countries.points,(rlat,rlon),(255,0,0,255),2)
    image_alpha(pilt,kaart)
    currentDisplay.isSameMap=True #Don't render the map contours again unless the view has changed(pan, zoom)
    #Dynamic information
    for entry in range(len(conf["placesources"])):
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
        try:
            allikas=open(filepath,"r")
            punktid=json.load(allikas)
            allikas.close()
            #Update data source config
            conf["placesources"][entry][5]=punktid["name"] #Name
            if i[0] == 0: conf["placesources"][entry][2]=punktid["interval"] #Update interval, not to be checked on local files
            for koht in punktid["data"]:
                if koht["min"] < currentDisplay.zoomLevel:
                    andmetyyp=koht["type"] #Data type
                    if andmetyyp==0: #In case of point
                        loc=geog2polar((d2r(koht["la"]),d2r(koht["lo"])),(rlat,rlon))
                        coords=getcoords((loc[0],loc[1]),currentDisplay.zoomLevel,currentDisplay.renderCentre)
                        if coords[0] < 2000 and coords[0] > 0 and coords[1] < 2000 and coords[1] > 0: #Filter out points outside of plot
                            x,y=map(int,coords)
                            if koht["icon"] == None:
                                joonis.rectangle((x-2,y-2,x+2,y+2),fill="black")
                                joonis.rectangle((x-1,y-1,x+1,y+1),fill="white")
                                textx=x+10 #X coordinate of label if one is to be shown
                            else:
                                iconfile=laepilt("../images/icons/"+koht["icon"].lower()+".png")
                                icw,ich=iconfile.size
                                textx=x+icw/2+2
                                pilt.paste(iconfile,(int(x-icw/2),int(y-ich/2)),iconfile)
                            if koht["label"]:
                                fontsize=int(koht["size"])
                                teksty=y-int(fontsize/2) #Y coordinate of the label
                                joonis.text((textx+1,teksty+1),text=koht["txt"],fill="black",font=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",fontsize))
                                joonis.text((textx,teksty),text=koht["txt"],fill=koht["color"],font=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",fontsize))
                    elif andmetyyp==1: #More than one point in set. Therefore polygon
                        path=[]
                        for p in range(len(koht["la"])):
                            lat=koht["la"][p]
                            lon=koht["lo"][p]
                            loc=geog2polar((d2r(lat),d2r(lon)),(rlat,rlon))
                            coords=getcoords((loc[0],loc[1]),currentDisplay.zoomLevel,currentDisplay.renderCentre)
                            for p2 in coords:
                                path.append(p2)
                        if koht["conn"]: path+=path[0:2] #Connect the line to the beginning if requested
                        joonis.line(path,fill="#000000",width=int(koht["width"])+2) #Shadow
                        joonis.line(path,fill=koht["color"],width=int(koht["width"])) #The line itself
                    elif andmetyyp==2: #Label
                        loc=geog2polar((d2r(koht["la"]),d2r(koht["lo"])),(rlat,rlon))
                        coords=getcoords((loc[0],loc[1]),currentDisplay.zoomLevel,currentDisplay.renderCentre)
                        if coords[0] < 3000 and coords[0] > 0 and coords[1] < 3000 and coords[1] > 0: #Filter out points outside of plot
                            x,y=map(int,coords)
                            fontsize=int(koht["size"])
                            txtx,txty=map(lambda x:x/2,joonis.textsize(koht["txt"],font=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",fontsize))) #Determine size of the plot
                            joonis.text((x-txtx+1,y-txty+1),text=koht["txt"],fill="black",font=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",fontsize))
                            joonis.text((x-txtx,y-txty),text=koht["txt"],fill=koht["color"],font=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",fontsize))
            save_config_file() #Update config file with updated data.
        except:
            tkMessageBox.showerror(fraasid["name"],fraasid["ddp_error"]+i[5]+"\n"+str(sys.exc_info()))
    rendered2=pilt
    showrendered(pilt)
    w.itemconfig(progress,state=Tkinter.HIDDEN)
    msgtostatus(fraasid["ready"])
    currentDisplay.isCanvasBusy=False
    lopus=time.time()
    print("Time elapsed:", lopus-alguses,"seconds")
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
def checkradarposition():
    global radarposprev
    global currentDisplay
    global currentlyOpenData
    radarpos=[currentlyOpenData.headers["latitude"],currentlyOpenData.headers["longitude"]]
    if radarpos != radarposprev:
        #Reset map settings
        currentDisplay.isSameMap=False
        currentDisplay.imageCentre=canvasctr
        currentDisplay.renderCentre=[1000,1000]
        currentDisplay.zoomLevel=1
    radarposprev=radarpos
    return currentDisplay.isSameMap
def loadData(quantity,elevation=None): #Processes and insert data into cache in currentDisplay variable
    global currentDisplay
    global currentlyOpenData
    if elevation == None: elevation = currentDisplay.softElIndex
    
    currentDisplay.quantity = quantity
    currentDisplay.productTime = currentlyOpenData.headers["timestamp"]
    currentDisplay.scanTime = currentlyOpenData.times[elevation]
    currentDisplay.gain = currentlyOpenData.data[elevation][quantity]["gain"]
    currentDisplay.offset = currentlyOpenData.data[elevation][quantity]["offset"]
    currentDisplay.nodata = currentlyOpenData.data[elevation][quantity]["nodata"]
    currentDisplay.undetect = currentlyOpenData.data[elevation][quantity]["undetect"]
    if "rangefolding" in currentlyOpenData.data[elevation][quantity]:
        currentDisplay.rangefolding = currentlyOpenData.data[elevation][quantity]["rangefolding"] #We know what value represents range folding
    else:
        currentDisplay.rangefolding = None #No data 
    currentDisplay.elevation = currentlyOpenData.nominalElevations[elevation]
    currentDisplay.elevationNumber = currentlyOpenData.elevationNumbers[elevation]
    currentDisplay.softElIndex=elevation
    currentDisplay.rstart=currentlyOpenData.data[elevation][quantity]["rstart"]
    currentDisplay.rscale=currentlyOpenData.data[elevation][quantity]["rscale"]
    currentDisplay.fileType = currentlyOpenData.type
    if currentDisplay.fileType == "HDF5":
        currentDisplay.data=[[HDF5scaleValue(y, currentDisplay.gain, currentDisplay.offset, currentDisplay.nodata, currentDisplay.undetect, currentDisplay.rangefolding, currentDisplay.quantity) for y in x] for x in currentlyOpenData.data[elevation][quantity]["data"]]   #Load default data
    else:
        currentDisplay.data=[[scaleValue(y, currentDisplay.gain, currentDisplay.offset, currentDisplay.nodata, currentDisplay.undetect, currentDisplay.rangefolding) for y in x] for x in currentlyOpenData.data[elevation][quantity]["data"]]   #Load default data

def listProducts(elIndex=None): #Populates products selection menu
    global productChoice
    global currentlyOpenData
    productChoice['menu'].delete(0, 'end')
    if elIndex != None:
        for i in currentlyOpenData.quantities[elIndex]:
            productChoice['menu'].add_command(label = i, command = lambda produkt = i: changeProduct(produkt))
    else:
        allProducts=[]
        for i in range(len(currentlyOpenData.quantities)):
            for j in currentlyOpenData.quantities[i]:
                if not j in allProducts:
                    allProducts.append(j)
                    productChoice['menu'].add_command(label = j, command = lambda produkt = j: changeProduct(produkt))
        
def load(path=None):
    global clickbox
    global currenturl
    global currentfilepath
    global hcanames
    global fmt
    global currentlyOpenData
    global currentDisplay
    clickbox=None
    if path == None:
        filed=tkFileDialog.Open(None,initialdir="../data")
        path=filed.show()
        currenturl=None
    if path != "": #If a file was given
        toolsmenyy.entryconfig(fraasid["color_table"],state=Tkinter.NORMAL) #Enable ability to override colormaps since we now have something to show
        stream=file_read(path)
        currentfilepath=path
        msgtostatus(fraasid["decoding"])
        if path[-3:]== ".h5" or stream[1:4]==b"HDF":
            productChoice.config(state=Tkinter.NORMAL)
            elevationChoice.config(state=Tkinter.NORMAL)
            hcanames=fraasid["iris_hca"]
            currentlyOpenData=HDF5(path)
        elif stream[0:4] == b"AR2V" or stream[0:8] == b"ARCHIVE2":
            productChoice.config(state=Tkinter.NORMAL)
            elevationChoice.config(state=Tkinter.NORMAL)
            currentlyOpenData=NEXRADLevel2(path)
        else:
            hcanames=fraasid["hca_names"]
            currentlyOpenData=NEXRADLevel3(path)
        ## PROCESSING (former decode_file_function)
        defaultProduct=currentlyOpenData.quantities[0][0]

        #TODO: currentDisplay populeerimine viia eraldi funktsiooni. Siis vähem dubleerimist
        loadData(defaultProduct,0)
        ## Clear product and elevation menus
        ## Configuring product selectors according to the default scan shown on file open
        if not currenturl or currenturl.find("ftp://tgftp.nws.noaa.gov/SL.us008001/DF.of/DC.radar/") == -1: #Do not clear elevation and product choices when viewing current NOAA Level 3 data
            listProducts(0)
            ## Elevation menu
            elevationChoice['menu'].delete(0, 'end')
            for j in currentlyOpenData.elevationNumbers:
                elevationIndex=currentlyOpenData.elevationNumbers.index(j)
                elevationChoice['menu'].add_command(label = str(currentlyOpenData.nominalElevations[elevationIndex]), command=lambda index = elevationIndex: changeElevation(index))
            productChoice.config(state=Tkinter.ACTIVE)
            elevationChoice.config(state=Tkinter.ACTIVE)
        ## Set default values for product and menu selectors
        chosenElevation.set(str(currentlyOpenData.nominalElevations[0]))
        if currentlyOpenData.type == "NEXRAD3":
            chosenProduct.set(currentDisplay.quantity)
        elif currentlyOpenData.type == "NEXRAD2":
            chosenProduct.set("DBZH")
        else:
            chosenProduct.set(currentlyOpenData.quantities[0][0])
        drawInfo()
        
        checkradarposition() #Checking if radar position has changed
        #Checking if showing RHI
        if not currentDisplay.isRHI:
            renderRadarData()
        else:
            if len(currentlyOpenData.nominalElevations) > 1:
                getrhi(currentDisplay.rhiAzimuth)
                mkrhi()
                tozoom()
                currentDisplay.renderAgain=1
            else:
                topan()
                currentDisplay.isRHI=False
                renderRadarData()
    return 0
def reset_colortable():
    global customcolortable
    global currentDisplay
    customcolortable=None
    if currentDisplay.isRHI:
        mkrhi()
        currentDisplay.renderAgain=1
    else:
        renderRadarData()
def changeColourTable(tabel):
    global currentDisplay
    global customcolortable
    customcolortable=tabel
    if currentDisplay.isRHI:
        mkrhi()
        currentDisplay.renderAgain=1
    else:
        renderRadarData()
def changeElevation(index):
    global chosenElevation
    global chosenProduct
    global currentDisplay
    global currentlyOpenData
    listProducts(index)
    try:
        loadData(currentDisplay.quantity,index)
    except:
        firstQuantity=currentlyOpenData.quantities[index][0]
        loadData(firstQuantity,index)
        chosenProduct.set(firstQuantity)
    chosenElevation.set(currentDisplay.elevation)
    if not currentDisplay.isRHI:
        drawInfo()
        renderRadarData()
    return 0
def changeProduct(newProduct):
    global chosenProduct
    global currentDisplay
    global currentlyOpenData
    # Workarounds for NEXRAD LEVEL 2 which has products distributed over multiple scans in some elevations
    if currentDisplay.isRHI and newProduct=="DBZH" and "VRAD" in currentlyOpenData.data[currentDisplay.softElIndex] and currentDisplay.elevation < 1.6 and currentDisplay.fileType == "NEXRAD2":
        changeElevation(currentDisplay.softElIndex-1)
    if newProduct not in currentlyOpenData.data[currentDisplay.softElIndex]:
        if currentlyOpenData.type == "NEXRAD2" and currentDisplay.isRHI:
            if newProduct in ["VRAD","WRAD"]: #If doppler
                changeElevation(currentDisplay.softElIndex+1)
            elif newProduct in ["DBZH","RHOHV","PHIDP","ZDR"]: #Otherwise
                changeElevation(currentDisplay.softElIndex-1)
        else:
            tkMessageBox.showerror(fraasid["name"],fraasid["not_found_at_this_level"]) #This shouldn't really be happening but apparently it has

    loadData(newProduct)
    chosenProduct.set(newProduct)
    drawInfo()
    if not currentDisplay.isRHI:
        renderRadarData()
    else:
        currentDisplay.renderAgain = True
        getrhi(currentDisplay.rhiAzimuth)
        mkrhi()
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
    global info
    global panimg
    global currentDisplay
    zoom=0
    info=0
    rhi=0
    clearclicktext()
    setcursor()
    if currentDisplay.isRHI:
        w.coords(radaripilt,tuple(currentDisplay.imageCentre))
        taskbarbtn1.config(image=panimg)
        taskbarbtn5.config(state=Tkinter.NORMAL)
        elevationChoice.config(state=Tkinter.NORMAL)
        currentDisplay.isRHI = False
        listProducts(currentDisplay.softElIndex)
        drawInfo()
        if currentDisplay.renderAgain:
            currentDisplay.renderAgain=0
            renderRadarData()
        w.itemconfig(radaripilt,image=rendered)
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
    global canvasctr
    global currentDisplay
    if currentDisplay.isRHI:
        currentDisplay.rhiStart=0
        currentDisplay.rhiEnd=250
        mkrhi()
    else:
        currentDisplay.isSameMap=False
        clearclicktext()
        currentDisplay.renderCentre=[1000,1000]
        currentDisplay.imageCentre=canvasctr
        currentDisplay.zoomLevel=1
        if currentDisplay.quantity != 0:
            renderRadarData()
    return 0
#Drawing area events
def mouseclick(event):
    global clickcoords
    global canvasdimensions
    global canvasctr
    global currentDisplay
    if not currentDisplay.isCanvasBusy:
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
    global canvasdimensions
    global rhi
    global currentDisplay
    x=canvasdimensions[0]
    y=canvasdimensions[1]
    if currentDisplay.isCanvasBusy == False and currentDisplay.quantity != None:
        if zoom:
            if not currentDisplay.isRHI:
                dy=event.y-clickcoords[1]
                w.itemconfig(zoomrect, state=Tkinter.NORMAL)
                w.coords(zoomrect,(clickcoords[0]-dy,clickcoords[1]-dy,clickcoords[0]+dy,event.y))
            else:
                dx=event.x-clickcoords[0]
                w.itemconfig(zoomrect, state=Tkinter.NORMAL)
                w.coords(zoomrect,(clickcoords[0]-dx,-1,clickcoords[0]+dx,canvasdimensions[1]))
        else: #Not zooming
            if info: #If gathering pixel value
                drawInfobox(event.x,event.y)
            else: #Moving
                if not currentDisplay.isRHI: #And no RHI is being displayed
                    if direction==1: #If left mouse button was clicked
                        dx=event.x-clickcoords[0]
                        dy=event.y-clickcoords[1]
                        w.coords(radaripilt, (currentDisplay.imageCentre[0]+dx,currentDisplay.imageCentre[1]+dy))
    return 0
def onrelease(event):
    global clickcoords
    global canvasdimensions
    global canvasctr
    global direction
    global currentDisplay
    global sweeps
    global rendered
    global info
    if currentDisplay.isCanvasBusy == False and currentDisplay.quantity != None:
        if zoom: #If was zooming
            if not currentDisplay.isRHI:
                currentDisplay.isSameMap=False #Make sure map gets re-rendered at next render
                #Calculating zoom level
                dy=event.y-clickcoords[1] 
                if dy!=0:
                    newzoom=(float(canvasdimensions[1])/(abs(dy*2)))**direction
                else: newzoom=2**direction
                #Finding new coordinates for the centre of data
                pdx=canvasctr[0]-clickcoords[0]
                pdy=canvasctr[1]-clickcoords[1]
                currentDisplay.renderCentre[0]=1000+newzoom*(pdx+currentDisplay.renderCentre[0]-1000)
                currentDisplay.renderCentre[1]=1000+newzoom*(pdy+currentDisplay.renderCentre[1]-1000)
                currentDisplay.zoomLevel*=newzoom
                w.itemconfig(zoomrect, state=Tkinter.HIDDEN)
                if currentDisplay.quantity != None: renderRadarData()
            else: #If was zooming among the RHI
                keskpunkt=rhix(clickcoords[0])
                kauguskeskpunktist=abs(rhix(event.x)-keskpunkt)
                samm=currentDisplay.rscale
                if direction == 1:
                    currentDisplay.rhiStart=keskpunkt-kauguskeskpunktist
                    currentDisplay.rhiEnd=keskpunkt+kauguskeskpunktist
                else:
                    kauguskeskpunktist*=(currentDisplay.rhiEnd-currentDisplay.rhiStart)*2/kauguskeskpunktist
                    currentDisplay.rhiStart=keskpunkt-kauguskeskpunktist
                    currentDisplay.rhiEnd=keskpunkt+kauguskeskpunktist
                if currentDisplay.rhiStart < 0: currentDisplay.rhiStart=0
                w.itemconfig(zoomrect, state=Tkinter.HIDDEN)
                mkrhi()
        elif rhi and not currentDisplay.isRHI: ##If was choosing an azimuth for PseudoRHI
            rhiaz=round(getinfo(event.x,event.y)[1][0],1)
            getrhi(rhiaz)
            currentDisplay.rhiStart=0
            currentDisplay.rhiEnd=250
            mkrhi()
            tozoom()
        else: #If I was moving around
            if not info: #If was not gathering info
                if not currentDisplay.isRHI:
                    currentDisplay.isSameMap=False #Make sure map gets re-rendered at next render
                    if direction == 1: #On left mouseclick
                        dx_2=event.x-clickcoords[0]
                        dy_2=event.y-clickcoords[1]
                        currentDisplay.imageCentre[0]+=dx_2
                        currentDisplay.imageCentre[1]+=dy_2
                        currentDisplay.renderCentre[0]+=dx_2
                        currentDisplay.renderCentre[1]+=dy_2
                        #If going out of rendering area
                        if currentDisplay.imageCentre[0] > 1000 or currentDisplay.imageCentre[0] < -600  or currentDisplay.imageCentre[1] > 1000 or currentDisplay.imageCentre[1] < -600:
                            if currentDisplay.quantity != None: renderRadarData()
            else: #If information was queried.
                drawInfobox(event.x,event.y)
    return 0
def on_window_reconf(event):
    global sizeb4
    global canvasctr
    global clickboxloc
    global canvasdimensions
    global currentDisplay
    global rhiagain
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
        currentDisplay.imageCentre=[currentDisplay.imageCentre[0]+delta[0],currentDisplay.imageCentre[1]+delta[1]]
        canvasctr=[cdim[0]/2,cdim[1]/2]
        w.coords(radaripilt,tuple(currentDisplay.imageCentre))
        clickboxloc=[clickboxloc[0]+delta[0],clickboxloc[1]+delta[1]]
        w.coords(clicktext,(clickboxloc[0]+85,clickboxloc[1]+42))
        sizeb4=dim
        if currentDisplay.isRHI:
            if not currentDisplay.isCanvasBusy:
                mkrhi()
    return 0
def getinfo(x,y):
    global canvasdimensions
    global currentDisplay
    dimx=canvasdimensions[0]
    dimy=canvasdimensions[1]
    pointx=x-dimx/2-(currentDisplay.renderCentre[0]-1000)
    pointy=y-dimy/2-(currentDisplay.renderCentre[1]-1000)
    rlat=currentlyOpenData.headers["latitude"]
    rlon=currentlyOpenData.headers["longitude"]
    if not currentDisplay.isRHI:
        azrange=az_range(pointx,pointy,currentDisplay.zoomLevel)
        return geocoords(azrange,float(rlat),float(rlon),float(currentDisplay.zoomLevel)), azrange, getbin(azrange)
    else:
        gr=rhix(x)
        h=(canvasdimensions[1]-y-80)/((canvasdimensions[1]-120)/17.0)
        r=sqrt(gr**2+h**2)
        a=beamangle(h,r)
        return gr, h, getrhibin(h,gr,float(a))
def onmousemove(event):
    global currentDisplay
    global currentlyOpenData
    if not currentDisplay.isCanvasBusy and currentlyOpenData:
        x=event.x
        y=event.y
        info=getinfo(x,y)
        if not currentDisplay.isRHI:
            lat=info[0][0]
            latl="N" if lat >= 0 else "S"
            lon=info[0][1]
            lonl="E" if lon >= 0 else "W"
            val=info[2][0]
            infostring=u"%.3f°%s %.3f°%s; %s: %.2f°; %s: %.3f km; %s: %s" % (abs(lat),latl,abs(lon),lonl,fraasid["azimuth"],floor(info[1][0]*100)/100.0,fraasid["range"],floor(info[1][1]*1000)/1000.0,fraasid["value"],val)
            msgtostatus(infostring)
        else:
            gr,h,val=info
            msgtostatus(u"x: %.3f km; y: %.3f km; %s: %s" % (gr, h, fraasid["value"], val))
#RHI speficic functions
def chooserhi(): #Choose RHI
    global currentDisplay
    global currentlyOpenData
    global zoom
    global info
    global rhi
    global sweeps
    global radarData
    global level2fail
    if currentDisplay.data != []:
        if len(currentlyOpenData.nominalElevations) > 1:
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
    global currentDisplay
    global canvasdimensions
    return currentDisplay.rhiStart+(x-50)*((currentDisplay.rhiEnd-currentDisplay.rhiStart)/(canvasdimensions[0]-100.0))
##Vastupidised funktsioonid RHI koordinaatidele
##Reverse functions of RHI coords
def getrhi(az):
    global currentlyOpenData
    global currentDisplay
    currentDisplay.isCanvasBusy = True
    currentDisplay.rhiElevations = []
    currentDisplay.rhiData = []
    currentDisplay.isRHI = True
    currentDisplay.rhiAzimuth = az
    lastElev = currentlyOpenData.nominalElevations[0]
    for i in range(len(currentlyOpenData.nominalElevations)):
        currentElev=currentlyOpenData.nominalElevations[i]
        if currentDisplay.quantity in currentlyOpenData.data[i]:
            azimuths=currentlyOpenData.azimuths[i]
            for j in range(len(azimuths)):
                msgtostatus(fraasid["reading_elevation"]+str(currentElev)+u"°")
                w.update()
                if az >= azimuths[j-1] and az < azimuths[j]:
                    if not (currentDisplay.quantity == "DBZH" and "VRAD" in currentlyOpenData.data[i] and currentlyOpenData.type == "NEXRAD2") or currentElev-lastElev > 0.2:
                        if i == 0 or currentElev-lastElev > -1.0: #Check to filter out SAILS extra lower scans if present
                            try:
                                currentDisplay.rhiData.append([scaleValue(k, currentDisplay.gain, currentDisplay.offset, currentDisplay.nodata, currentDisplay.undetect, currentDisplay.rangefolding) for k in currentlyOpenData.data[i][currentDisplay.quantity]["data"][j]])
                                if currentlyOpenData.type == "NEXRAD2": currentDisplay.rhiElevations.append(currentlyOpenData.elevations[i][j])
                                else: currentDisplay.rhiElevations.append(currentlyOpenData.nominalElevations[i])
                                lastElev = currentElev
                            except:
                                print("Incomplete record. Processing bug in Level 2? Problematic elevation: ",currentElev)
    currentDisplay.isCanvasBusy=False
    return 0
def mkrhi():
    global currentDisplay
    global productsweeps
    global rhiout
    global rhiout2
    global ppiimg
    global canvasctr
    global pildifont
    global colortablenames
    global customcolortable
    if not currentDisplay.isCanvasBusy:
        currentDisplay.isCanvasBusy = True
        drawInfo()
        msgtostatus(fraasid["drawing_pseudorhi"])
        pikkus=int(w.cget("height"))
        laius=int(w.cget("width"))
        pilt=uuspilt("RGB", (laius,pikkus), "#000025") 
        joonis=Draw(pilt)
        samm=currentDisplay.rscale
        if customcolortable: #If color table has been overridden by user
            varvitabel=loadcolortable("../colortables/"+customcolortable) #Load a custom color table
        else:
            varvitabel=loadcolortable("../colortables/"+colortablenames[currentDisplay.quantity]+".txt") #Load a color table
        init_drawlegend(currentDisplay.quantity,varvitabel) #Redraw color table just in case it is changed in RHI mode.
        xsamm=(laius-100.0)/((currentDisplay.rhiEnd-currentDisplay.rhiStart)/samm) if currentDisplay.rhiEnd != currentDisplay.rhiStart else 0
        a=0
        a0=currentDisplay.rhiElevations[0]-0.5
        elevationsCount=len(currentDisplay.rhiElevations)
        for i in range(elevationsCount):
            r=0
            if i < elevationsCount-1:
                a=(float(currentDisplay.rhiElevations[i])+float(currentDisplay.rhiElevations[i+1]))/2
            else:
                a=float(currentDisplay.rhiElevations[i])+0.5
            x0=50
            first=1
            for j in currentDisplay.rhiData[i]:
                if currentDisplay.rhiStart-r <= samm and r < currentDisplay.rhiEnd:
                    if first:
                        x0+=(r-currentDisplay.rhiStart)*xsamm/samm
                        first=0
                    x1=x0+xsamm if currentDisplay.rhiEnd-r > samm else laius-50
                    if j != None:
                        if r-currentDisplay.rhiStart < 0:
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
        ulatus=(currentDisplay.rhiEnd-currentDisplay.rhiStart)
        teljesamm=ulatus/5.0
        teljexsamm=(laius-100)/5.0
        for l in range(5):
            joonis.line((50+teljexsamm*l,rhiypix(0,pikkus)+10,50+teljexsamm*l,rhiypix(17,pikkus)),fill="white")
            joonis.text((50+teljexsamm*l-10,rhiypix(0,pikkus)+15),text=str(round(currentDisplay.rhiStart+teljesamm*l,2)),fill="white",font=pildifont)
        joonis.line((50,rhiypix(0,pikkus),50,rhiypix(17,pikkus)),fill="white")
        joonis.text((laius/2,pikkus-50),text="r (km)",fill="white",font=pildifont) #x telje silt
        joonis.text((10,5),text="h (km)", fill="white", font=pildifont)
        rhiout2=pilt
        rhiout=PhotoImage(image=rhiout2)
        taskbarbtn1.config(image=ppiimg)
        taskbarbtn5.config(state=Tkinter.DISABLED)
        elevationChoice.config(state=Tkinter.DISABLED)
        w.coords(radaripilt,tuple(canvasctr))
        w.itemconfig(radaripilt, image=rhiout)
        msgtostatus(fraasid["ready"])
        currentDisplay.isRHI=True
        if currentDisplay.fileType == "NEXRAD2": #A workaround to get all products which otherwise are distributed over different scans on some elevations
            listProducts()
        currentDisplay.isCanvasBusy=False            
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
failimenyy.add_command(label=fraasid["batch_export"], command=batch_export)
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
toolsmenyy.add_cascade(label=fraasid["color_table"], menu=colortablemenu, underline=0, state=Tkinter.DISABLED)
toolsmenyy.add_command(label=fraasid["dyn_labels"],command=dynlabels_settings)
abimenyy.add_command(label=fraasid["key_shortcuts_menuentry"], command=keys_list)
abimenyy.add_separator()
abimenyy.add_command(label=fraasid["about_program"], command=about_program)
languagemenyy.add_command(label=fraasid["language_estonian"], command=lambda: change_language("estonian"))
languagemenyy.add_command(label=fraasid["language_english"], command=lambda: change_language("english"))
##Drawing area
w = Tkinter.Canvas(output,width=600,height=600,highlightthickness=0)
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
radaripilt=w.create_image(tuple(currentDisplay.imageCentre))
clicktext=w.create_image((300,300))
legend=w.create_image((582,300))
radardetails=w.create_image((300,580))
zoomrect=w.create_rectangle((0,0,200,200),outline="white",state=Tkinter.HIDDEN) #Ristkülik, mis joonistatakse ekraanile suurendamise ajal.
progress=w.create_rectangle((0,590,400,600),fill="#0044ff",state=Tkinter.HIDDEN)
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
chosenElevation = Tkinter.StringVar(moderaam)
elevationChoice=Tkinter.OptionMenu(moderaam, chosenElevation,None)
elevationChoice.config(bg="#44bbff",activebackground="#55ccff",highlightbackground="#55ccff",state=Tkinter.DISABLED)
elevationChoice.grid(row=0,column=6)
chosenProduct= Tkinter.StringVar(moderaam)
productChoice=Tkinter.OptionMenu(moderaam, chosenProduct,None)
productChoice.config(bg="#44bbff",activebackground="#55ccff",highlightbackground="#55ccff",state=Tkinter.DISABLED)
productChoice.grid(row=0,column=7)
status=Tkinter.Label(output, text=None, justify=Tkinter.LEFT, anchor="w")
status.grid(row=2,column=0,sticky="w")
output.mainloop()

