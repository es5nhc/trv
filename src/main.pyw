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
import translations
from translations import fixArabic
from math import floor, sqrt, radians as d2r, degrees as r2d, cos, copysign, pi
from colorconversion import *
from coordinates import *
import sys
import datetime
import shutil
if sys.version_info[0] > 2:
    import tkinter as Tkinter
    from tkinter import filedialog as tkFileDialog
    from tkinter import messagebox as tkMessageBox
    from tkinter import font as tkFont
    import urllib.request as urllibRequest
else:
    import Tkinter
    import tkFileDialog
    import tkMessageBox
    import tkFont
    import urllib2 as urllibRequest
import json
import os
import threading
import time
import platform

threadLock=threading.Lock()

configfile=open("config.json","r")
conf=json.load(configfile)
configfile.close()

fraasid=translations.phrases[conf["lang"]]
arabicOnLinux = fraasid["LANG_ID"] == "AR" and platform.system() == "Linux"

#UIFont for Linux

#Show a splash and import necessary geodata.
splash = Tkinter.Tk()
if platform.system() == "Linux":
    uiFont = tkFont.Font(family = "DejaVu Sans Condensed", size = 9) #Let's theme the Linux display
else:
    uiFont = None #Handled by OS
splash.overrideredirect(1)
splash.resizable(False, False)
splash.title("")
w = int(splash.winfo_screenwidth()/2-320)
h = int(splash.winfo_screenheight()/2-180)
splash.geometry("640x360+"+str(w)+"+"+str(h))
splashCanvas = Tkinter.Canvas(splash, width = 640, height = 360)
splashCanvas.create_rectangle((0,0,640,360), fill="#000022")
if fraasid["LANG_ID"] != "AR":
    text=splashCanvas.create_text((5,348), text="", fill="white", anchor="w", font=uiFont)
else:
    text=splashCanvas.create_text((635,348), text="", fill="white", anchor="e", font=uiFont)
versionText=splashCanvas.create_text((475,30), text=fraasid["name"][4:], fill="white", font=uiFont)
try:
    from decoderadar import *
    splashCanvas.tag_raise(text)
    try:
        from PIL.Image import open as laepilt
        from PIL.Image import new as uuspilt
        from PIL.Image import merge as yhendapilt
        from PIL.ImageDraw import Draw
        from PIL.ImageTk import PhotoImage, BitmapImage
        from PIL import ImageFont
        splashImage=laepilt("../images/splash.png")
        splashPhotoImg = PhotoImage(splashImage)
        splashCanvas.create_image((320,180), image=splashPhotoImg)
        splashCanvas.create_rectangle((0,340,640,360), fill="#000022")
        splashCanvas.tag_raise(text)
        splashCanvas.tag_raise(versionText)
        splashCanvas.pack()
    except:
        splashCanvas.pack()
        splashCanvas.itemconfig(versionText, text = fraasid["name"])
        splash.update()
        raise ImportError
    splashCanvas.itemconfig(text,text="Loading modules...")
    splash.update()
    splashCanvas.itemconfig(text,text=fraasid["loading_states"])
    splash.update()
    import states
    splashCanvas.itemconfig(text,text=fraasid["coastlines"])
    splash.update()
    import coastlines
    splashCanvas.itemconfig(text,text=fraasid["countries"])
    splash.update()
    import countries
    splashCanvas.itemconfig(text,text=fraasid["lakes"])
    splash.update()
    import lakes
    splashCanvas.itemconfig(text,text=fraasid["rivers"])
    splash.update()
    import rivers
    splashCanvas.itemconfig(text,text=fraasid["NA_roads"])
    splash.update()
    import major_NA_roads
    splash.destroy()
        
except ImportError:
    splashCanvas.update()
    splashCanvas.itemconfig(text,text=fraasid["nodependencies"])
    splashCanvas.update()
    time.sleep(5)
    splash.destroy()
    #exit(1)
    
class DownloadThread (threading.Thread):
    def __init__ (self,url,dst="../cache/urlcache"):
        threading.Thread.__init__(self)
        self.url = url
        self.dst = dst
        self.downloading = True #Initializing as true to make sure download isn't being treated as finished
        self.error = False
    def run(self):
        threadLock.acquire()
        try:
            download_file(self.url,self.dst)
        except:
            self.error = sys.exc_info()
        self.downloading=False
        threadLock.release()
class Display(): #Class for storing properties of current display
    def __init__(self):
        self.quantity=None
        self.elevationNumber=None
        self.softElIndex=None
        self.elevation=None
        self.productTime=None
        self.scanTime=None
        self.fileType=None
        self.azimuths=None
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
        
class DWDDownloadWindow(Tkinter.Toplevel):
    def __init__(self, parent, title = None):
        Tkinter.Toplevel.__init__(self,parent)
        self.title(fraasid["dwd_volume_download"])
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        label1 = Tkinter.Label(self, text = fraasid["radar_site"], font=uiFont)
        label1.grid(column = 0, row = 0, sticky = "e")
        self.selectedSite = Tkinter.StringVar()
        self.selectedSite.set("Borkum")
        siteMenu=Tkinter.OptionMenu(self, self.selectedSite, "Borkum","Boostedt","Dresden","Eisberg","Emden","Essen","Feldberg","Flechtdorf","Hannover","Isen","Memmingen","Neuhaus","Neuheilenbach","Offenthal","Prötzel","Rostock","Türkheim","Ummendorf")
        siteMenu.config(font = uiFont)
        siteMenu.grid(column = 1, row = 0, sticky = "w")

        self.scanDay = Tkinter.StringVar()
        self.scanMonth = Tkinter.StringVar()
        self.scanYear = Tkinter.StringVar()
        self.scanHour = Tkinter.StringVar()
        self.scanMinute = Tkinter.StringVar()
        self.outputFile = Tkinter.StringVar()

        #Determining latest full volume
        currentTime=datetime.datetime.utcnow()
        minutesToLastFullVolumeBeginning=(currentTime.minute % 5)+5
        scanTime=datetime.datetime.utcnow()-datetime.timedelta(minutes=minutesToLastFullVolumeBeginning)

        self.scanDay.set(str(scanTime.day).zfill(2))
        self.scanMonth.set(str(scanTime.month).zfill(2))
        self.scanYear.set(scanTime.year)
        self.scanHour.set(str(scanTime.hour).zfill(2))
        self.scanMinute.set(str(scanTime.minute).zfill(2))
        self.outputFile.set("../data/dwdexport.h5")

        dateFrame = Tkinter.Frame(self)
        dateFrame.grid(column = 2, row = 0, sticky = "e", padx = 3, pady = 3)
        Tkinter.Label(dateFrame, text = fraasid["date"]+": ", font=uiFont).grid(column = 0, row = 0)
        scanDayEntry = Tkinter.Entry(dateFrame, textvariable = self.scanDay, width = 2)
        scanDayEntry.grid(column = 1, row = 0)
        Tkinter.Label(dateFrame, text = ".", font=uiFont).grid(column = 2, row = 0)
        scanMonthEntry = Tkinter.Entry(dateFrame, textvariable = self.scanMonth, width = 2, font=uiFont)
        scanMonthEntry.grid(column = 3, row = 0)
        Tkinter.Label(dateFrame, text = ".", font=uiFont).grid(column = 4, row = 0)
        scanYearEntry = Tkinter.Entry(dateFrame, textvariable = self.scanYear, width = 4, font=uiFont)
        scanYearEntry.grid(column = 5, row = 0)
        
        timeFrame = Tkinter.Frame(self)
        timeFrame.grid(column = 3, row = 0, sticky = "w", padx = 3, pady = 3)
        Tkinter.Label(timeFrame, text = fraasid["time"]+": ", font=uiFont).grid(column = 6, row = 0)
        scanHourEntry = Tkinter.Entry(timeFrame, textvariable = self.scanHour, width = 2, font=uiFont)
        scanHourEntry.grid(column = 7, row = 0)
        Tkinter.Label(timeFrame, text = ":", font=uiFont).grid(column = 8, row = 0)
        scanMinuteEntry = Tkinter.Entry(timeFrame, textvariable = self.scanMinute, width = 2, font=uiFont)
        scanMinuteEntry.grid(column = 9, row = 0)
        Tkinter.Label(timeFrame, text = " UTC", font=uiFont).grid(column = 10, row = 0)
        
        Tkinter.Label(self, text= fraasid["output_file"], font=uiFont).grid(column = 0, row = 1, sticky = "e")
        outputFileEntry = Tkinter.Button(self, textvariable=self.outputFile, command=self.pickDestination, width=45, font=uiFont)
        outputFileEntry.grid(column = 1, row = 1, columnspan = 3)
        Tkinter.Button(self, text = fraasid["start_download"], command=self.initDownload, font=uiFont).grid(column = 1, row = 2)
        self.mainloop()
    def pickDestination(self):
        filed=tkFileDialog.SaveAs(None,initialdir="../data")
        path=filed.show()
        if len(path) > 0:
            self.outputFile.set(path)
    def initDownload(self):
        global currenturl
        #Validation
        validDate=True

        d=self.scanDay.get()
        m=self.scanMonth.get()
        y=self.scanYear.get()
        h=self.scanHour.get()
        mi=self.scanMinute.get()

        if d.isdigit() and m.isdigit() and y.isdigit() and h.isdigit() and mi.isdigit():
            try:
                scanDateTime=datetime.datetime(int(y),int(m),int(d),int(h),int(mi))
                sites={"Borkum":"asb","Boostedt":"boo","Dresden":"drs","Eisberg":"eis","Emden":"emd","Essen":"ess","Feldberg":"fbg","Flechtdorf":"fld","Hannover":"hnr","Isen":"isn","Memmingen":"mem","Neuhaus":"neu","Neuheilenbach":"nhb","Offenthal":"oft","Prötzel":"pro","Rostock":"ros","Türkheim":"tur","Ummendorf":"umm"}
                self.withdraw()
                if sys.version_info[0] > 2:
                    result=loadDWDVolume(sites[self.selectedSite.get()],scanDateTime,self.outputFile.get(),True,True)
                else:
                    result=loadDWDVolume(sites[self.selectedSite.get().encode("utf-8")],scanDateTime,self.outputFile.get(),True,True)
                if result:
                    msgtostatus(fraasid["loading_in_progress"])
                    w.update()
                    currenturl = None
                    load(self.outputFile.get())
                    self.onclose()
                else:
                    self.deiconify()
            except ValueError:
                print(sys.exc_info())
                tkMessageBox.showerror(fraasid["name"],fraasid["invalid_date"])
        else:
            tkMessageBox.showerror(fraasid["name"],fraasid["invalid_date"])
    def onclose(self):
        global dwdDownloadOpen
        dwdDownloadOpen=0
        self.destroy()
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
        label1=Tkinter.Label(frame1,text=fraasid["batch_input"], font=uiFont)
        label1.grid(column=0,row=0)
        self.btn1=Tkinter.Button(frame1,text=fraasid["batch_pick"],width=30, font=uiFont, command=lambda: self.pickdir(0))
        self.btn1.grid(column=1,row=0)
        label2=Tkinter.Label(frame1,text=fraasid["batch_output"], font=uiFont)
        label2.grid(column=0,row=1)
        self.btn2=Tkinter.Button(frame1,text=fraasid["batch_pick"],width=30, font=uiFont, command=lambda: self.pickdir(1))
        self.btn2.grid(column=1,row=1)
        frame1.grid(column=0,row=0)
        #Output format
        frame2=Tkinter.Frame(self,relief=Tkinter.SUNKEN,borderwidth=1)
        label3=Tkinter.Label(frame2,text=fraasid["batch_fmt"], font=uiFont)
        label3.grid(column=0,row=0,columnspan=2)
        radio1=Tkinter.Radiobutton(frame2,text="GIF",variable=self.outfmt,value="gif", font=uiFont)
        radio1.grid(column=0,row=1)
        radio2=Tkinter.Radiobutton(frame2,text="PNG",variable=self.outfmt,value="png", font=uiFont)
        radio2.grid(column=1,row=1)
        frame2.grid(column=1,row=0)
        #Product and sweep selection.
        frame3=Tkinter.Frame(self)
        label4=Tkinter.Label(frame3,text=fraasid["batch_quantity"], font=uiFont)
        label4.grid(column=0,row=0)
        list1=Tkinter.Entry(frame3,textvariable=self.outprod,width=7, font=uiFont)
        list1.grid(column=1,row=0)
        label5=Tkinter.Label(frame3,text=fraasid["batch_el"], font=uiFont)
        label5.grid(column=2,row=0)
        list2=Tkinter.Entry(frame3,textvariable=self.outel,width=7, font=uiFont)
        list2.grid(column=3,row=0)
        frame3.grid(column=0,row=1)
        #OK button
        okbutton=Tkinter.Button(self,text=fraasid["okbutton"],command=self.exportdir, font=uiFont)
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
                elif b"BUFR" in stream:
                    currentlyOpenData = BUFR(path)
                else:
                    hcanames = fraasid["hca_names"]
                    currentlyOpenData = NEXRADLevel3(path)
                del(stream) #Get rid of the file content stream - no longer needed
                #Getting elevation index
                for j in range(len(currentlyOpenData.nominalElevations)):
                    if abs(float(self.outel.get()) - currentlyOpenData.nominalElevations[j]) < 0.05:
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
    def onclose(self):
        global batchexportopen
        batchexportopen=0
        self.destroy()
        return 0
    
class NEXRADChooser(Tkinter.Toplevel): #Choice of NEXRAD station
    def __init__(self, parent, title = None):
        global conf
        Tkinter.Toplevel.__init__(self,parent)
        self.title(fraasid["nexrad_choice"])
        self.protocol("WM_DELETE_WINDOW",self.onclose)
        jaamatiitel=Tkinter.Label(self,text=fraasid["choose_station"], font=uiFont)
        jaamatiitel.pack()
        jaamavalik=Tkinter.Frame(self)
        kerimisriba=Tkinter.Scrollbar(jaamavalik)
        kerimisriba.pack(side=Tkinter.RIGHT, fill=Tkinter.Y)
        self.jaamaentry=Tkinter.Listbox(jaamavalik,width=30,yscrollcommand=kerimisriba.set, font=uiFont)
        self.jaamaentry.pack(side=Tkinter.LEFT, fill=Tkinter.BOTH)
        kerimisriba.config(command=self.jaamaentry.yview)
        jaamavalik.pack()
        jaamad=file_read("nexradstns.txt").decode("utf-8").split("\n")
        for i in jaamad:
            rida=i.split("|")
            self.jaamaentry.insert(Tkinter.END, rida[0]+" - "+rida[1]+", "+rida[2])
        okbutton=Tkinter.Button(self,text=fraasid["okbutton"],command=self.newstn, font=uiFont)
        okbutton.pack()
        self.mainloop()
    def newstn(self):
        global conf
        selection=self.jaamaentry.curselection()
        if selection != ():
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
        okbutton=Tkinter.Button(self,text=fraasid["okbutton"],command=lambda: self.submit_source(parent))
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
        urltitle=Tkinter.Label(self,text="URL:",font=uiFont)
        urltitle.grid(column=0,row=0)
        self.url=Tkinter.StringVar()
        self.url.set("")
        urlentry=Tkinter.Entry(self,textvariable=self.url,width=70,font=uiFont)
        urlentry.grid(column=1,row=0)
        downloadbutton=Tkinter.Button(self,text=fraasid["open"],command=self.laealla,font=uiFont)
        downloadbutton.grid(column=0,row=1,sticky="w")
        self.mainloop()
    def laealla(self):
        global currentfilepath
        global currenturl
        currenturl=self.url.get()
        try:
            self.onclose()
            downloadResult=multithreadedDownload(currenturl)
            if downloadResult:
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
pildifont3=ImageFont.truetype("../fonts/DejaVuSansCondensed.ttf",8)
currenturl=None
nexradstn=conf["nexradstn"] #Chosen NEXRAD station
urlwindowopen=0 #1 if dialog to open an URL is open
nexradchooseopen=0 #1 if dialog to choose a nexrad station is open
addingRmax=0 #1 if configuration window to add Rmax to chunk of data is open.
dynlabelsopen=0 #same rule as above for selection of dynamic labels
batchexportopen=0 #same as when batch export window is open.
dwdDownloadOpen=0 #same as when dwd volume download window is open.
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
       "PHIDP": u"°",
       "VE": "m/s",
       "VF": "m/s",
       "VC": "m/s",
       "DM": "dB",
       "DZ": "dBZ",
       "ZD": "dBZ",
       "RH": "",
       "PH": u"°",
       "SH": "dB",
       "SV": "dB",
       "AH": "dB",
       "AD": "dB",
       "WV": "m/s",
       "SW": "m/s",
       "DCC": "dBZ",
       "DCZ": "dBZ",
       "ZH": "dBZ"}
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
                 "CLASS": "hclass",
                 "PHIDP": "phi",
                 "WRAD": "sw",
                 "WRADH": "sw",
                 "WRADV": "sw",
                 "SW": "sw",
                 "WV": "sw",
                 "ZH": "dbz",
                 "VE": "v",
                 "VC": "v",
                 "VF": "v",
                 "ZD": "zdr",
                 "RH": "rhohv",
                 "PH": "phidp",
                 "DZ": "dbz", 
                 "SH": "dbz", #fixme
                 "SV": "dbz", #fixme
                 "AH": "dbz", #fixme
                 "AD": "dbz", #fixme
                 "DM": "dm", #fixme
                 "NCP": "sqi",
                 "DCC": "dbz",
                 "DCZ": "dbz",
                 } #Names for color tables according to product
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
def toAddingRmax():
    global addingRmax
    global pan
    global zoom
    global rhi
    addingRmax = 1
    pan = 0
    zoom = 0
    rhi = 0
    clearclicktext()
    setcursor()
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
        multithreadedDownload(currenturl,"../cache/nexradcache/"+product)
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
    ids={"p94":"DBZH",
         "p99":"VRADDH", #[sic!] - Level 3 product 99 is dealiased radial velocity
         "159":"ZDR",
         "161":"RHOHV",
         "163":"KDP",
         "165":"HCLASS"}
    elevationChoice["menu"].delete(0, 'end')
    for i in range(4):
        productcode=product[:-1]+str(i)
        elevationChoice["menu"].add_command(label=fraasid["level3_slice"].replace("/NR/",str(i+1)),command=lambda x=productcode: fetchnexrad(x), font = uiFont)
    index=product[-1]
    #chosenElevation.set(fraasid["level3_slice"].replace("/NR/",str(int(product[-1])+1)))
    chosenProduct.set(ids[product[0:3]])
    productChoice["menu"].delete(0, 'end')
    productChoice["menu"].add_command(label="DBZH",command=lambda x=index: fetchnexrad("p94r"+index), font = uiFont)
    productChoice["menu"].add_command(label="VRADDH",command=lambda x=index: fetchnexrad("p99v"+index), font = uiFont)
    productChoice["menu"].add_command(label="ZDR",command=lambda x=index: fetchnexrad("159x"+index), font = uiFont)
    productChoice["menu"].add_command(label="RHOHV",command=lambda x=index: fetchnexrad("161c"+index), font = uiFont)
    productChoice["menu"].add_command(label="KDP",command=lambda x=index: fetchnexrad("163k"+index), font = uiFont)
    productChoice["menu"].add_command(label="HCLASS",command=lambda x=index: fetchnexrad("165h"+index), font = uiFont)
    return 0
def saveHDF5(path=None):
    global currentlyOpenData
    global currentfilepath
    if not path:
        filed=tkFileDialog.SaveAs(None,initialdir="../data")
        path=filed.show()
    if path != "":
        if currentlyOpenData.type != "HDF5" or (currentlyOpenData.type == "HDF5" and currentlyOpenData.isODIM == False) or (currentlyOpenData.type == "HDF5" and currentlyOpenData.isModified == True):
            try:
                msgtostatus("Exporting...")
                w.update()
                dumpVolume(currentlyOpenData,path)
                msgtostatus(fraasid["ready"])
                tkMessageBox.showinfo(fraasid["name"], "Export successful")
            except:
                print(sys.exc_info())
                tkMessageBox.showerror(fraasid["name"],"Export failed")
        else:
            try:
                shutil.copyfile(currentfilepath,path)
                tkMessageBox.showinfo(fraasid["name"],"Successfully saved another version.")
            except:
                tkMessageBox.showerror(fraasid["name"],"Error occurred while saving.")
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
        if clickbox:
            cbh = clickbox.height()
        else:
            cbh = None
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
                if rlegend != None: outimage.paste(rlegend2,(x-35,halfy-228,x,halfy+227))
                if infotekst != None: outimage.paste(infotekst2,(halfx-265,y-30,halfx+265,y-10))
                outimage.save(path)
                if GUI: tkMessageBox.showinfo(fraasid["name"],fraasid["export_success"])
            except:
                tkMessageBox.showerror(fraasid["name"],fraasid["export_format_fail"])
        return 0
    else:
        tkMessageBox.showerror(fraasid["name"],fraasid["no_data_loaded"])
def getrhibin(h,gr,a):
    global currentDisplay
    lowestBeamStart = min(currentDisplay.rhiElevations) - 0.5 #Assuming beamwidth of 1°
    highestBeamEnd = max(currentDisplay.rhiElevations) + 0.5
    if a < lowestBeamStart: return fraasid["no_data"]
    if a >= highestBeamEnd: return fraasid["no_data"]
    elevationsCount=len(currentDisplay.rhiElevations)
    for i in range(elevationsCount):
        rstart = currentDisplay.rhiBinProperties[i]["rstart"]
        condition1 = lowestBeamStart if i == 0 else (currentDisplay.rhiElevations[i-1]+currentDisplay.rhiElevations[i])/2
        condition2 = (currentDisplay.rhiElevations[i]+currentDisplay.rhiElevations[i+1])/2 if i < elevationsCount-1 else highestBeamEnd
        if a >= condition1 and a < condition2:
            kordaja = currentDisplay.rhiBinProperties[i]["rscale"]**-1
            indeks = int((gr-rstart)*kordaja)
            if len(currentDisplay.rhiData[i]) <= indeks:
                val=None
            elif gr < rstart:
                val = None
            else:
                val=currentDisplay.rhiData[i][indeks]
            if val != None and (currentDisplay.quantity == "HCLASS"):
                val=hcanames[int(val)]
            elif val == None:
                val=fraasid["no_data"]
            if type(val) is float:
                val=round(val,8)
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
            previous=currentDisplay.azimuths[i-1]
            current=currentDisplay.azimuths[i]
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
            val=fraasid["no_data"]
        delta=None
        if (val != None and val != currentDisplay.rangefolding) and ("VRAD" in currentDisplay.quantity):
            valprev=currentDisplay.data[int(azi)-1][int((kaugus-mindistance)*kordaja)]
            delta=abs(float(val)-valprev) if (valprev != None and valprev != "RF") else None
        elif val != None and currentDisplay.quantity == "HCLASS":
            val=hcanames[int(val)]
        elif val == currentDisplay.nodata or val == None:
            val=fraasid["no_data"]
    except:
        val = fraasid["no_data"]
    if type(val) is float: val = round(val, 8)
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
    global currentlyOpenData
    andmed=getinfo(x,y)
    azrange=andmed[1]
    data=andmed[2]
    vaartus=data[0] if not currentDisplay.isRHI else data

    ### PREPARING TEXT DISPLAY ON INFOBOX
    if vaartus == "RF":
        row0="RF"
    elif vaartus == fraasid["no_data"]:
        if fraasid["LANG_ID"] != "AR" or arabicOnLinux:
            row0=fraasid["no_data"]
        else:
            row0=fixArabic(fraasid["no_data"])
    else:
        if fraasid["LANG_ID"] != "AR":
            row0=u"%s %s" % (vaartus, units[currentDisplay.quantity])
        else:
            if arabicOnLinux:
                row0=u"%s %s" % (units[currentDisplay.quantity], vaartus)
            else:
                row0=fixArabic(u"%s %s" % (units[currentDisplay.quantity], vaartus))
    if not currentDisplay.isRHI:        
        coords=andmed[0]
        latletter="N" if coords[0] > 0 else "S"
        lonletter="E" if coords[1] > 0 else "W"
        if fraasid["LANG_ID"] != "AR":
            row1=u"%.5f°%s %.5f°%s" % (abs(coords[0]),latletter,abs(coords[1]),lonletter)
            row2=u"%s: %.1f°" % (fraasid["azimuth"],azrange[0])
            row3=u"%s: %.3f km" % (fraasid["range"],azrange[1])
            row4=u"%s: ~%.1f km" % (fraasid["beam_height"],data[2])
            row5=None if (data[1] == None or data[1] == "RF") else fraasid["g2g_shear"]+": %.1f m/s" % (data[1])
        else:
            if not arabicOnLinux:
                row1=u"%.5f°%s %.5f°%s" % (abs(coords[1]),lonletter,abs(coords[0]),latletter)
                row2=u"°%.1f :%s" % (azrange[0],fixArabic(fraasid["azimuth"]))
                row3=u"km %.3f :%s" % (azrange[1], fixArabic(fraasid["range"]))
                row4=u"km %.1f~ :%s" % (data[2], fixArabic(fraasid["beam_height"]))
                row5=None if (data[1] == None or data[1] == "RF") else "m/s %.1f :%s" % (data[1], fixArabic(fraasid["g2g_shear"]))
            else:
                row1=u"%.5f°%s %.5f°%s" % (abs(coords[1]),lonletter,abs(coords[0]),latletter)
                row2=u"°%.1f :%s" % (azrange[0], fraasid["azimuth"])
                row3=u"km %.3f :%s" % (azrange[1], fraasid["range"])
                row4=u"km %.1f~ :%s" % (data[2], fraasid["beam_height"])
                row5=None if (data[1] == None or data[1] == "RF") else "m/s %.1f :%s" % (data[1], fraasid["g2g_shear"])
    else:
        if fraasid["LANG_ID"] != "AR":
            row1=u"%s: %.3f km" % (fraasid["range"],andmed[0])
            row2=u"%s: %.3f km" % (fraasid["height"],andmed[1])
        else:
            if not arabicOnLinux:
                row1=u"km %.3f :%s" % (andmed[0], fixArabic(fraasid["range"]))
                row2=u"km %.3f :%s" % (andmed[1], fixArabic(fraasid["height"]))
            else:
                row1=u"km %.3f :%s" % (andmed[0], fraasid["range"])
                row2=u"km %.3f :%s" % (andmed[1], fraasid["height"])

    ## DOPPLER SCALE feature
    canDrawDopplerScale="VRAD" in currentDisplay.quantity and "highprf" in currentlyOpenData.data[currentDisplay.softElIndex][currentDisplay.quantity]
    if canDrawDopplerScale:
        highPRF=currentlyOpenData.data[currentDisplay.softElIndex][currentDisplay.quantity]["highprf"]
        lowPRF=currentlyOpenData.data[currentDisplay.softElIndex][currentDisplay.quantity]["lowprf"]
        kastikorgus=170 if not currentDisplay.isRHI else 45
    else:
        kastikorgus=84 if not currentDisplay.isRHI else 45
        
    kast=uuspilt("RGB",(170,kastikorgus),"#44ccff") #Create the image for the infobox
    kastdraw=Draw(kast)

    if sys.version_info[0] > 2:
        validValue=type(vaartus) is not str
    else:
        validValue=type(vaartus) is not str and type(vaartus) is not unicode
        
    if canDrawDopplerScale: #Doppler scale
        
        kastdraw.rectangle((0,85,170,170), fill="#ffffff")
        kastdraw.line((5,128,165,128), fill="#000000")
        kastdraw.line((85,123,85,133), fill="#000000")
        
        unitlabelsize=kastdraw.textsize("m/s", font=pildifont3)[0]
        kastdraw.text((85-unitlabelsize/2,90), text="m/s", fill="#000000", font=pildifont3)

        NI1=highPRF*0.5*currentlyOpenData.wavelength #Getting the length of whole interval, so vMax*2
        

        if highPRF == lowPRF: #If using DualPRF, we'll set the scale along multiple highPRF velocity intervals
            if "VRADD" in currentDisplay.quantity:
                dopplerRange = 2
            else:
                dopplerRange = 1
            NI2 = NI1
            NI2IntervalRange=dopplerRange
        else:
            dopplerRange = 2
            NI2 = lowPRF*0.5*currentlyOpenData.wavelength
            NI2IntervalRange=int(round((NI1*(dopplerRange-0.5)*highPRF/lowPRF)))

        xgain=80/(NI1*(dopplerRange-0.5))
        if fraasid["LANG_ID"] == "AR": xgain *= -1

        for interval in range(-dopplerRange,dopplerRange):
            v1=NI1/2+NI1*interval
            v1x=85+xgain*v1
            if v1x >= 5 and v1x <= 165:
                kastdraw.line((v1x,100,v1x,128 if highPRF != lowPRF else 155), fill="#000000")
                textwidth=kastdraw.textsize(str(round(v1,1)), font=pildifont3)[0]
                if interval == -dopplerRange:
                    kastdraw.text((v1x if fraasid["LANG_ID"] != "AR" else v1x-textwidth, 90), text = str(round(v1,1)), fill="#000000", font=pildifont3)
                elif interval == dopplerRange -1:
                    kastdraw.text((v1x-textwidth if fraasid["LANG_ID"] != "AR" else v1x, 90), text = str(round(v1,1)), fill="#000000", font=pildifont3)
                else:
                    kastdraw.text((v1x-textwidth/2, 90), text = str(round(v1,1)), fill="#000000", font=pildifont3)
        if highPRF != lowPRF:
            for interval2 in range(-NI2IntervalRange,NI2IntervalRange):
                v2=NI2/2+NI2*interval2
                v2x=85+xgain*v2
                if v2x >= 5 and v2x <= 165:
                    kastdraw.line((v2x,128,v2x,155), fill="#000000")
                    textwidth=kastdraw.textsize(str(round(v2,1)), font=pildifont3)[0]
                    if interval2 == -NI2IntervalRange:
                        kastdraw.text((v2x if fraasid["LANG_ID"] != "AR" else v2x-textwidth, 155), text = str(round(v2,1)), fill="#000000", font=pildifont3)
                    elif interval2 == NI2IntervalRange-1:
                        kastdraw.text((v2x-textwidth if fraasid["LANG_ID"] != "AR" else v2x, 155), text = str(round(v2,1)), fill="#000000", font=pildifont3)
                    else:
                        kastdraw.text((v2x-textwidth/2, 155), text = str(round(v2,1)), fill="#000000", font=pildifont3)
        
        #Lets draw the NI gates.
        
        if validValue:
            scalePointerX=85+xgain*vaartus
            v1aliased=((vaartus+NI1/2)%NI1)-(NI1/2)
            v2aliased=((vaartus+NI2/2)%NI2)-(NI2/2)

            #Reusing the same drawing code from above for now, probably possible to move into separate function
            if dopplerRange > 1:
                for interval in range(-dopplerRange,dopplerRange):
                    v1=v1aliased+NI1*interval
                    v1x=85+xgain*v1
                    if v1x >= 5 and v1x <= 165:
                        kastdraw.line((v1x,100,v1x,128), fill="#aaaaaa")
                for interval2 in range(-NI2IntervalRange,NI2IntervalRange):
                    v2=v2aliased+NI2*interval2
                    v2x=85+xgain*v2
                    if v2x >= 5 and v2x <= 165:
                        kastdraw.line((v2x,128,v2x,155), fill="#aaaaaa")
            ##
            kastdraw.polygon((scalePointerX-5,90,scalePointerX+5,90,scalePointerX,95), fill="#ff0000")
            kastdraw.polygon((scalePointerX-5,165,scalePointerX+5,165,scalePointerX,160), fill="#ff0000")
                
            kastdraw.line((scalePointerX,90,scalePointerX,165), fill="#ff0000")
    #END OF DOPPLER SCALE        
    kastdraw.rectangle((0,0,170,16),fill="#0033ee")
    kastdraw.polygon((0,0,10,0,0,10,0,0),fill="#FFFFFF")
    if fraasid["LANG_ID"] != "AR":
        kastdraw.text((9,1),text=row0, font=pildifont2)
        kastdraw.text((5,17),text=row1, fill="#000000", font=pildifont)
        kastdraw.text((5,30),text=row2, fill="#000000", font=pildifont)
        if not currentDisplay.isRHI:
            kastdraw.text((5,43),text=row3, fill="#000000", font=pildifont)
            kastdraw.text((5,56),text=row4, fill="#000000", font=pildifont)
            if row5 != None: kastdraw.text((5,69),text=row5, fill="#000000", font=pildifont)
    else:
        kastdraw.text((160-kastdraw.textsize(row0,pildifont)[0],1),text=row0, font=pildifont2)
        kastdraw.text((163-kastdraw.textsize(row1,pildifont)[0],17),text=row1, fill="#000000", font=pildifont)
        kastdraw.text((165-kastdraw.textsize(row2,pildifont)[0],30),text=row2, fill="#000000", font=pildifont)
        if not currentDisplay.isRHI:
            kastdraw.text((165-kastdraw.textsize(row3,pildifont)[0],43),text=row3, fill="#000000", font=pildifont)
            kastdraw.text((165-kastdraw.textsize(row4,pildifont)[0],56),text=row4, fill="#000000", font=pildifont)
            if row5 != None: kastdraw.text((165-kastdraw.textsize(row5,pildifont)[0],69),text=row5, fill="#000000", font=pildifont)
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
    textimg=uuspilt("RGB",(530,20), "#0033ee")
    textdraw=Draw(textimg)
    if fraasid["LANG_ID"] != "AR":
        textdraw.text((5,3),text=tekst, font=pildifont)
    else:
        textwidth=textdraw.textsize(tekst, font=pildifont)[0]
        textdraw.text((525-textwidth,3),text=tekst, font=pildifont)
    infotekst2=textimg
    infotekst=PhotoImage(image=textimg)
    w.itemconfig(radardetails,image=infotekst)
    return 0
def listcolortables():
    global colortablemenu
    failid=os.listdir("../colortables")
    for i in failid:
        colortablemenu.add_command(label=i, command=lambda x=i:changeColourTable(x), font = uiFont)
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
    if product == 165 or product == "HCLASS" or product == "CLASS":
        tosmooth=0
    increment=(maximum-minimum)/430.0
    legendimg=uuspilt("RGB",(35,455),"#0033ee")
    legenddraw=Draw(legendimg)
    for i in range(430):
        val=minimum+increment*i
        legenddraw.rectangle((25,454-i,35,454-i),fill=getcolor(tabel,val,tosmooth))
    step=1.0/increment
    majorstep=10
    if customcolortable == "hurricane.txt": majorstep=20
    if product == "PHIDP":
        majorstep=45
    if product in [159, 163, 165, "HCLASS", "CLASS"]:
        majorstep=1
    if product in [161, "SQI"]:
        majorstep=0.1
    firstten=majorstep+minimum-minimum%majorstep
    if firstten == majorstep+minimum: firstten = minimum
    ystart=454-(firstten-minimum)*step
    lastten=maximum-maximum%majorstep
    hulk=int((lastten-firstten)/majorstep)
    yend=ystart-majorstep*step*hulk #If the next full step is too close to the edge.
    if yend < 30: hulk-=1 #Let's not list this last point on legend
    legenddraw.text((5,0),text=unit, font=pildifont)
    for j in range(hulk+1):
        y=ystart-majorstep*step*j
        if product in ["CLASS", "HCLASS"] and currentDisplay.fileType=="NEXRAD3": #Other products have a numeric value
            legendlist=["BI","AP","IC","DS","WS","RA","+RA","BDR","GR","HA","UNK","RF"]; #List of classifications
            legendtext=legendlist[int(firstten+j*majorstep)]
        elif product in ["CLASS", "HCLASS"] and currentDisplay.fileType in ["HDF5", "IRIS"]:
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
    if product in [99, "VRAD", "VRADH", "VRADV", "VRADDH", "VRADDV", "VE", "VC", "VF"]:
        drawlegend(99,-80,80,tabel)
    elif product in [159, "ZDR", "LZDR"]:
        drawlegend(159,-6,6,tabel)
    elif product in [161, "RHOHV", product == "RHO"]:
        drawlegend(161,0.2,1.05,tabel)
    elif product in [163, "KDP"]:
        drawlegend(163,-2,7,tabel)
    elif product in ["CLASS", "HCLASS"] and currentDisplay.fileType=="NEXRAD3":
        drawlegend("HCLASS",0,12,tabel)
    elif product in ["CLASS", "HCLASS"] and currentDisplay.fileType in ["HDF5", "IRIS"]:
        drawlegend("HCLASS",1,7,tabel)
    elif product in ["DBZ", "TH", "TV", "DBZH", "DBZV"]:
        drawlegend(94,-25,75,tabel)
    elif product in ["WRAD","WRADH","WRADV","SW","VW"]:
        drawlegend("SW",0,30,tabel)
    elif product == "PHIDP":
        drawlegend("PHIDP",0,180,tabel)
    elif product == "DM":
        drawlegend("DM",-115,-30,tabel)
    elif product in ["SQI","QIDX","SQIH","SQIV","NCP"]:
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
    if arabicOnLinux:
        msgtostatus(fraasid["radar_image"]+" "+fraasid["drawing"])
    else:
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
    azimuths=[x for x in map(d2r,currentDisplay.azimuths)]
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
        if arabicOnLinux:
            msgtostatus(fraasid["coastlines"]+" "+fraasid["drawing"])
        else:
            msgtostatus(fraasid["drawing"]+" "+fraasid["coastlines"].lower())
        drawmap(coastlines.points,(rlat,rlon),(17,255,17,255))
        if arabicOnLinux:
            msgtostatus(fraasid["lakes"]+" "+fraasid["drawing"])
        else:
            msgtostatus(fraasid["drawing"]+" "+fraasid["lakes"].lower())
        drawmap(lakes.points,(rlat,rlon),(0,255,255,255),1)
        if rlon < 0:
            if arabicOnLinux:
                msgtostatus(fraasid["NA_roads"]+" "+fraasid["drawing"])
            else:
                msgtostatus(fraasid["drawing"]+" "+fraasid["NA_roads"])
            drawmap(major_NA_roads.points,(rlat,rlon),(125,0,0,255),2)
        if arabicOnLinux:
            msgtostatus(fraasid["rivers"]+" "+fraasid["drawing"])
        else:
            msgtostatus(fraasid["drawing"]+" "+fraasid["rivers"].lower())
        drawmap(rivers.points,(rlat,rlon),(0,255,255,255),1)
        if arabicOnLinux:
            msgtostatus(fraasid["states_counties"]+" "+fraasid["drawing"])
        else:
            msgtostatus(fraasid["drawing"]+" "+fraasid["states_counties"])
        drawmap(states.points,(rlat,rlon),(255,255,255,255),1)
        if arabicOnLinux:
            msgtostatus(fraasid["country_boundaries"]+" "+fraasid["drawing"])
        else:
            msgtostatus(fraasid["drawing"]+" "+fraasid["country_boundaries"])
        drawmap(countries.points,(rlat,rlon),(255,0,0,255),2)
    image_alpha(pilt,kaart)
    currentDisplay.isSameMap=True #Don't render the map contours again unless the view has changed(pan, zoom)
    #Dynamic information
    for entry in range(len(conf["placesources"])):
        i=conf["placesources"][entry]
        if i[4] != 1: continue #If the data source has been disabled, skip.
        if arabicOnLinux:
            msgtostatus(fraasid["drawing"]+" "+fraasid["placenames"]+" - "+i[1])
        else:
            msgtostatus(i[1]+" - "+fraasid["placenames"]+" "+fraasid["drawing"])
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
                print(sys.exc_info())
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
def openDWDDialog():
    global dwdDownloadOpen
    if dwdDownloadOpen == 0:
        dwdDownloadOpen = 1
        DWDDownloadWindow(output)
def loadurl():
    global urlwindowopen
    if urlwindowopen == 0:
        urlwindowopen = 1
        URLAken(output)
    return 0
def reloadfile():
    global currentfilepath
    global currenturl
    if currenturl:
        if "opendata.dwd.de" in currenturl:
            siteId = currenturl.split("/")[7]
            loadDWDFile(siteId, currentDisplay.elIndex)
        if "knmi.nl" in currenturl:
            if "radar_volume_denhelder" in currenturl:
                loadKNMI(0)
            elif "radar_volume_full_herwijnen" in currenturl:
                loadKNMI(1)
        else:
            download_file(currenturl, currentfilepath)
            load(currentfilepath)
    elif currentfilepath != "":
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
    if currentlyOpenData.times[elevation][0] != None:
        currentDisplay.scanTime = min(currentlyOpenData.times[elevation])
    else:
        currentDisplay.scanTime = None
    currentDisplay.azimuths = currentlyOpenData.azimuths[elevation]
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
    if currentDisplay.fileType == "HDF5" or currentDisplay.fileType == "IRIS":
        variableType=currentlyOpenData.data[elevation][quantity]["dataType"]
        isDataRowTypeAlreadyList=isinstance(currentlyOpenData.data[elevation][quantity]["data"][0],list)
        
        if not isDataRowTypeAlreadyList:
            currentDisplay.data=[[HDF5scaleValue(y, currentDisplay.gain, currentDisplay.offset, currentDisplay.nodata, currentDisplay.undetect, currentDisplay.rangefolding, currentDisplay.quantity, variableType, currentlyOpenData.wavelength) for y in x.tolist()] for x in currentlyOpenData.data[elevation][quantity]["data"]]   #Load default data
        else:
            currentDisplay.data=[[HDF5scaleValue(y, currentDisplay.gain, currentDisplay.offset, currentDisplay.nodata, currentDisplay.undetect, currentDisplay.rangefolding, currentDisplay.quantity, variableType, currentlyOpenData.wavelength) for y in x] for x in currentlyOpenData.data[elevation][quantity]["data"]]   #Load default data
    else:
        currentDisplay.data=[[scaleValue(y, currentDisplay.gain, currentDisplay.offset, currentDisplay.nodata, currentDisplay.undetect, currentDisplay.rangefolding) for y in x] for x in currentlyOpenData.data[elevation][quantity]["data"]]   #Load default data
    if "VRAD" in quantity:
        toolsmenyy.entryconfig(fraasid["dealiasing"], state = Tkinter.NORMAL)
    else:
        toolsmenyy.entryconfig(fraasid["dealiasing"], state = Tkinter.DISABLED)

def listProducts(elIndex=None): #Populates products selection menu
    global productChoice
    global currentlyOpenData
    productChoice['menu'].delete(0, 'end')
    if elIndex != None:
        for i in currentlyOpenData.quantities[elIndex]:
            productChoice['menu'].add_command(label = i, command = lambda produkt = i: changeProduct(produkt), font = uiFont)
    else:
        allProducts=[]
        for i in range(len(currentlyOpenData.quantities)):
            for j in currentlyOpenData.quantities[i]:
                if not j in allProducts:
                    allProducts.append(j)
                    productChoice['menu'].add_command(label = j, command = lambda produkt = j: changeProduct(produkt), font = uiFont)
        
def load(path=None,defaultElevation=0):
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
    if len(path) > 0: #If a file was given
        toolsmenyy.entryconfig(fraasid["linear_interp"], state = Tkinter.NORMAL)
        toolsmenyy.entryconfig(fraasid["color_table"], state = Tkinter.NORMAL) #Enable ability to override colormaps since we now have something to show
        stream=file_read(path)
        currentfilepath=path
        msgtostatus(fraasid["decoding"])
        if stream[0:2] == b"BZ":
            stream=bz2.decompress(stream)
        if path[-3:]== ".h5" or stream[1:4]==b"HDF":
            productChoice.config(state=Tkinter.NORMAL)
            elevationChoice.config(state=Tkinter.NORMAL)
            hcanames=fraasid["iris_hca"]
            currentlyOpenData=HDF5(path)
        elif path[-4:].lower() == ".raw":
            productChoice.config(state=Tkinter.NORMAL)
            elevationChoice.config(state=Tkinter.NORMAL)
            hcanames=fraasid["iris_hca"]
            currentlyOpenData=IRIS(path)
        elif stream[0:4] == b"AR2V" or stream[0:8] == b"ARCHIVE2":
            productChoice.config(state=Tkinter.NORMAL)
            elevationChoice.config(state=Tkinter.NORMAL)
            currentlyOpenData=NEXRADLevel2(path)
        elif b"BUFR" in stream:
            currentlyOpenData=BUFR(path)
        elif b"SSWB" in stream and b"VOLD" in stream: #Probably DORADE
            currentlyOpenData=DORADE(path)
        else:
            hcanames=fraasid["hca_names"]
            currentlyOpenData=NEXRADLevel3(path)
        ## PROCESSING (former decode_file_function)
        defaultProduct=currentlyOpenData.quantities[0][0]
        if "highprf" in currentlyOpenData.data[0][defaultProduct]:
            taskbarbtn6.config(state = Tkinter.NORMAL)
        else:
            taskbarbtn6.config(state = Tkinter.DISABLED)

        #TODO: currentDisplay populeerimine viia eraldi funktsiooni. Siis vähem dubleerimist
        loadData(defaultProduct,defaultElevation)
        ## Clear product and elevation menus
        ## Configuring product selectors according to the default scan shown on file open
        if not currenturl or (currenturl.find("ftp://tgftp.nws.noaa.gov/SL.us008001/DF.of/DC.radar/") == -1 and currenturl.find("http://opendata.dwd.de/weather/radar/") == -1): #Do not clear elevation and product choices when viewing current NOAA Level 3 data
            listProducts(defaultElevation)
            ## Elevation menu
            elevationChoice['menu'].delete(0, 'end')
            for j in currentlyOpenData.elevationNumbers:
                elevationIndex=currentlyOpenData.elevationNumbers.index(j)
                elevationChoice['menu'].add_command(label = str(currentlyOpenData.nominalElevations[elevationIndex]), command=lambda index = elevationIndex: changeElevation(index), font = uiFont)
            productChoice.config(state=Tkinter.ACTIVE)
            elevationChoice.config(state=Tkinter.ACTIVE)
        ## Set default values for product and menu selectors
        chosenElevation.set(str(currentlyOpenData.nominalElevations[defaultElevation]))
        if currentlyOpenData.type == "NEXRAD3":
            chosenProduct.set(currentDisplay.quantity)
        elif currentlyOpenData.type == "NEXRAD2":
            chosenProduct.set("DBZH")
        else:
            chosenProduct.set(currentlyOpenData.quantities[defaultElevation][0])
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
    if zoom or info or rhi or addingRmax:
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
    global addingRmax
    zoom=1
    info=0
    addingRmax=0
    rhi=0
    clearclicktext()
    setcursor()
    return 0
def topan(event=None):
    global zoom
    global info
    global rhi
    global addingRmax
    global panimg
    global currentDisplay
    global arabicOnLinux
    zoom=0
    info=0
    rhi=0
    addingRmax=0
    
    clearclicktext()
    setcursor()
    if currentDisplay.isRHI:
        w.coords(radaripilt,tuple(currentDisplay.imageCentre))
        taskbarbtn1.config(image=panimg)
        taskbarbtn5.config(state=Tkinter.NORMAL)
        elevationChoice.config(state=Tkinter.NORMAL)
        currentDisplay.isRHI = False
        toolsmenyy.entryconfig(fraasid["linear_interp"], state = Tkinter.NORMAL)
        taskbarbtn6.config(state = Tkinter.NORMAL)
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
    global addingRmax
    zoom = 0
    info = 1
    rhi = 0
    addingRmax = 0
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
    global addingRmax
    global currentDisplay
    global rMaxAddSelectorShape
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
        elif addingRmax:
            cx, cy = clickcoords
            ax, ay = canvasToImageCoords(cx,cy) #Initial coordinates
            bx, by = canvasToImageCoords(event.x, event.y) # Final coordinates

            initialAz,initialRange = az_range(ax, ay, 1)
            currentAz,currentRange = az_range(bx, by, 1)
                    
            arcExtent =  (((initialAz - currentAz) + 180) % 360) - 180

            ctrx,ctry = imageToCanvasCoords(0, 0)

            x1,y1=getcoords((initialRange, d2r(initialAz)), 1, [ctrx,ctry])
            x2,y2=getcoords((currentRange, d2r(initialAz)), 1, [ctrx,ctry])
            x3,y3=getcoords((initialRange, d2r(currentAz)), 1, [ctrx,ctry])
            x4,y4=getcoords((currentRange, d2r(currentAz)), 1, [ctrx,ctry])
            
            w.coords(rMaxAddSelectorShape[0], (ctrx-initialRange,ctry-initialRange,ctrx+initialRange,ctry+initialRange))
            w.itemconfig(rMaxAddSelectorShape[0], state = Tkinter.NORMAL, start=450-initialAz, extent=arcExtent)
            w.coords(rMaxAddSelectorShape[1], (x1,y1,x2,y2))
            w.itemconfig(rMaxAddSelectorShape[1], state = Tkinter.NORMAL)
            w.coords(rMaxAddSelectorShape[2], (x3,y3,x4,y4))
            w.itemconfig(rMaxAddSelectorShape[2], state = Tkinter.NORMAL)
            w.coords(rMaxAddSelectorShape[3], (ctrx-currentRange,ctry-currentRange,ctrx+currentRange,ctry+currentRange))
            w.itemconfig(rMaxAddSelectorShape[3], state = Tkinter.NORMAL, start=450-initialAz, extent=arcExtent)

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
    global addingRmax
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
        elif addingRmax:
            for i in range(len(rMaxAddSelectorShape)): w.itemconfig(rMaxAddSelectorShape[i], state=Tkinter.HIDDEN) #Hide the selector shape            
            ax,ay=canvasToImageCoords(clickcoords[0],clickcoords[1])
            bx,by=canvasToImageCoords(event.x,event.y)
            az1,r1=az_range(ax,ay,currentDisplay.zoomLevel)
            az2,r2=az_range(bx,by,currentDisplay.zoomLevel)
            minrange = r1 if r1 < r2 else r2
            maxrange = r1 if r1 > r2 else r2
            minaz = az1 if az1 < az2 else az2
            maxaz = az1 if az1 > az2 else az2
            cx,cy=imageToCanvasCoords(ax,ay)
            addRmax(currentlyOpenData,currentDisplay.softElIndex,minaz,maxaz,minrange,maxrange)
            currentlyOpenData.isModified = True
            loadData(currentDisplay.quantity, currentDisplay.softElIndex)
            renderRadarData()
            
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

def canvasToImageCoords(x,y):
    ''' Converts canvas coordinates to image coordinates '''
    dimx = canvasdimensions[0]
    dimy = canvasdimensions[1]
    pointx = x - dimx/2 - (currentDisplay.renderCentre[0] - 1000)
    pointy = y - dimy/2 - (currentDisplay.renderCentre[1] - 1000)
    return (pointx,pointy)
def imageToCanvasCoords(pointx,pointy):
    ''' Converts image coordinates to canvas coordinates '''
    dimx=canvasdimensions[0]
    dimy=canvasdimensions[1]
    x = pointx + (currentDisplay.renderCentre[0] - 1000) + dimx/2
    y = pointy + (currentDisplay.renderCentre[1] - 1000) + dimy/2
    return (int(x),int(y))
    
def getinfo(x,y):
    pointx,pointy = canvasToImageCoords(x,y)
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
def moveMinus(nr): #For Arabic compatibility on Windows.
    if not type(nr) is str:
        try:
            if nr < 0:
                onr=str(nr)[1:]+u"-"
            else:
                onr=str(nr)
            return onr
        except:
            return nr
    else:
        return nr
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
            if fraasid["LANG_ID"] == "AR":
                if arabicOnLinux:
                    infostring=u"%.3f°%s %.3f°%s ؛°%.2f :%s ؛km %.3f :%s ؛%s :%s" % (abs(lon),lonl,abs(lat),latl,floor(info[1][0]*100)/100.0,fraasid["azimuth"],floor(info[1][1]*1000)/1000.0,fraasid["range"],val,fraasid["value"])
                else:
                    infostring=u"%.3f°%s %.3f°%s %s: °%.2f؛ %s: %.3f ؛%s: %s؛ " % (abs(lon),lonl,abs(lat),latl,fraasid["azimuth"],floor(info[1][0]*100)/100.0,fraasid["range"],floor(info[1][1]*1000)/1000.0,fraasid["value"],moveMinus(val))
            else:
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
    global addingRmax
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
            addingRmax=0
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
    global arabicOnLinux
    currentDisplay.isCanvasBusy = True
    currentDisplay.rhiElevations = []
    currentDisplay.rhiData = []
    currentDisplay.rhiBinProperties=[]
    currentDisplay.isRHI = True
    toolsmenyy.entryconfig(fraasid["linear_interp"], state = Tkinter.DISABLED)
    taskbarbtn6.config(state = Tkinter.DISABLED)
    currentDisplay.rhiAzimuth = az


    if not currentlyOpenData.type == "NEXRAD2":    
        finalElevIndexes=[]
        finalElevations=[]
        rawElevationList=[x for x in currentlyOpenData.nominalElevations] #To make sure we make a clean copy! Don't want to affect the property!
        rawElevationIndexes=list(range(len(rawElevationList)))
        
        for i in range(len(rawElevationList)):
            #Ignore the 90° scan for this purpose! Present for example in KNMI data.
            lowestValIndex=rawElevationList.index(min(rawElevationList))
            if currentlyOpenData.nominalElevations[rawElevationIndexes[lowestValIndex]] != 90 and rawElevationList[lowestValIndex] not in finalElevations:
                finalElevIndexes.append(rawElevationIndexes[lowestValIndex])
                finalElevations.append(rawElevationList[lowestValIndex])
            rawElevationList.pop(lowestValIndex)
            rawElevationIndexes.pop(lowestValIndex)
    else:
        finalElevIndexes = list(range(len(currentlyOpenData.nominalElevations)))
        
    #Processing
    lastElev = currentlyOpenData.nominalElevations[finalElevIndexes[0]]
    for i in finalElevIndexes:
        currentElev=currentlyOpenData.nominalElevations[i]
        if currentDisplay.quantity in currentlyOpenData.data[i]:
            azimuths=currentlyOpenData.azimuths[i]
            for j in range(len(azimuths)):
                msgtostatus(fraasid["reading_elevation"]+str(currentElev)+u"°")
                w.update()
                if az >= azimuths[j-1] and az < azimuths[j]:
                    if not (currentDisplay.quantity == "DBZH" and "VRAD" in currentlyOpenData.data[i] and currentlyOpenData.type == "NEXRAD2") or currentElev-lastElev > 0.2 or (currentElev not in currentDisplay.rhiElevations and currentlyOpenData.type != "NEXRAD2"):
                        if i == 0 or currentElev-lastElev > -1.0: #Check to filter out SAILS extra lower scans if present
                            try:
                                if currentDisplay.fileType in ["HDF5", "IRIS"]:
                                    currentDisplay.rhiData.append([HDF5scaleValue(k, currentDisplay.gain, currentDisplay.offset, currentDisplay.nodata, currentDisplay.undetect, currentDisplay.rangefolding, currentDisplay.quantity, currentlyOpenData.data[i][currentDisplay.quantity]["dataType"], currentlyOpenData.wavelength) for k in currentlyOpenData.data[i][currentDisplay.quantity]["data"][j]])
                                else:
                                    currentDisplay.rhiData.append([scaleValue(k, currentDisplay.gain, currentDisplay.offset, currentDisplay.nodata, currentDisplay.undetect, currentDisplay.rangefolding) for k in currentlyOpenData.data[i][currentDisplay.quantity]["data"][j]])
                                currentDisplay.rhiBinProperties.append({"rscale": currentlyOpenData.data[i][currentDisplay.quantity]["rscale"],"rstart": currentlyOpenData.data[i][currentDisplay.quantity]["rstart"]})
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
        if customcolortable: #If color table has been overridden by user
            varvitabel=loadcolortable("../colortables/"+customcolortable) #Load a custom color table
        else:
            varvitabel=loadcolortable("../colortables/"+colortablenames[currentDisplay.quantity]+".txt") #Load a color table
        init_drawlegend(currentDisplay.quantity,varvitabel) #Redraw color table just in case it is changed in RHI mode.
        a=0
        a0=currentDisplay.rhiElevations[0]-0.5
        elevationsCount=len(currentDisplay.rhiElevations)
        for i in range(elevationsCount):
            r=currentDisplay.rhiBinProperties[i]["rstart"]
            samm=currentDisplay.rhiBinProperties[i]["rscale"]
            xsamm=(laius-100.0)/((currentDisplay.rhiEnd-currentDisplay.rhiStart)/samm) if currentDisplay.rhiEnd != currentDisplay.rhiStart else 0
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
def interpolateData():
    global currentDisplay
    if not currentDisplay.isRHI:
        azimuths=[]
        oldData=currentDisplay.data
        newData=[]
        previous=currentDisplay.azimuths[-1]
        for i in currentDisplay.azimuths:
            if previous > 350 and i < 10: #When crossing North
                previous -= 360
            azimuths.append(((i+previous) / 2) % 360)
            azimuths.append(i % 360)
            previous=i
        for j in range(len(oldData)):
            dataRow1=[None]
            dataRow2=[None]
            previousData1=oldData[j-1][0]
            previousData2=oldData[j][0]

            previousInterpolatedAz=None if (previousData1 in [None, "RF"] or previousData2 in [None, "RF"]) else (previousData1+previousData2)/2
            for k in range(1,len(oldData[j])):
                currentData1raw=oldData[j-1][k]
                currentData2raw=oldData[j][k]

                currentData1 = currentData1raw
                currentData2 = currentData2raw

                showingReflectivity=currentDisplay.quantity in ["DBZ","DBZH","DBZV","TH"]
                if showingReflectivity:
                    if currentData1 == None: currentData1 = -32
                    if currentData2 == None: currentData2 = -32
                    if previousData1 == None: previousData1 = -32
                    if previousData2 == None: previousData2 = -32
                
                currentInterpolatedAz=None if (currentData1 in [None, "RF"] or currentData2 in [None, "RF"]) else (currentData1+currentData2)/2
                currentInterpolatedR1=None if (currentInterpolatedAz in [None, "RF"] or previousInterpolatedAz in [None, "RF"]) else (previousInterpolatedAz+currentInterpolatedAz)/2
                currentInterpolatedR2=None if (currentData2 in [None, "RF"] or previousData2 in [None, "RF"]) else (currentData2+previousData2)/2

                if showingReflectivity:
                    currentInterpolatedAz=currentInterpolatedAz if not currentInterpolatedAz == -32 else None
                    currentInterpolatedR1=currentInterpolatedR1 if not currentInterpolatedR1 == -32 else None
                    currentInterpolatedR2=currentInterpolatedR2 if not currentInterpolatedR2 == -32 else None
                    currentData2=currentData2 if not currentData2 == -32 else None
                    currentData1=currentData1 if not currentData1 == -32 else None
                    

                if currentDisplay.rscale >= 0.1: #If range bin spacing is less than 250 meters, only interpolate azimuth wise
                    dataRow1.append(currentInterpolatedR1)
                    dataRow2.append(currentInterpolatedR2)
                dataRow1.append(currentInterpolatedAz)
                dataRow2.append(currentData2)
                
                previousInterpolatedAz=currentInterpolatedAz
                previousData1=currentData1
                previousData2=currentData2
            newData.append(dataRow1)
            newData.append(dataRow2)
        currentDisplay.data=newData
        if currentDisplay.rscale >= 0.1: currentDisplay.rscale/=2
        currentDisplay.azimuths=azimuths
        renderRadarData()
def loadDWDVolume(site="fld",volumeTime=datetime.datetime(2018,2,15,11,30,0),output="../data/dwd_volume.h5",downloadOnly=False,gui=False):
    dataObject = None
    incomplete = False
    for quantity in ["z","v"]:
        fileListingURL="http://opendata.dwd.de/weather/radar/sites/sweep_vol_"+quantity+"/"+site+"/"
        download_file(fileListingURL,"../cache/dwdcache/dir_list_"+quantity)
        listRaw=file_read("../cache/dwdcache/dir_list_"+quantity)
        listContent=listRaw.split(b"<a")[1:]
        sweepTimes={}
        for i in listContent: #Let's get available files
            fileName=i[i.find(b">")+1:i.find(b"</a>")]
            if b"buf" in fileName:
                fileInfo=fileName.split(b"_")
                elevNumber,timeStamp=fileInfo[3].split(b"-")
                fileWMO=int(fileInfo[4][:fileInfo[4].find(b"-")])
                if not timeStamp==b"latest":
                    year=int(timeStamp[0:4])
                    month=int(timeStamp[4:6])
                    day=int(timeStamp[6:8])
                    hour=int(timeStamp[8:10])
                    minute=int(timeStamp[10:12])
                    second=int(timeStamp[12:14])
                    scanTime=datetime.datetime(year,month,day,hour,minute,second)
                    timeFromVolumeStart=(scanTime-volumeTime)
                    secondsFromVolumeStart=timeFromVolumeStart.seconds
                    daysFromVolumeStart=timeFromVolumeStart.days
                    if secondsFromVolumeStart < 300 and daysFromVolumeStart == 0:
                        sweepTimes[int(elevNumber)]=timeStamp.decode("utf-8")
        if len(sweepTimes) < 10 and len(sweepTimes) > 0:
            if not incomplete:
                if gui:
                    tkMessageBox.showwarning(fraasid["name"],fraasid["volume_incomplete"])
                else:
                    print("This volume is incomplete. Perhaps its scan is still in progress.")
                incomplete = True
        elif len(sweepTimes) == 0:
            if gui:
                tkMessageBox.showerror(fraasid["name"],fraasid["volume_not_found"])
            else:
                print("Volume not found")
            return False
        DWDElevs=[5, 4, 3, 2, 1, 0, 6, 7, 8, 9]
        for j in range(len(DWDElevs)): #Single elevations
            quantityCode = "DBZH" if quantity == "z" else "VRADH"
            if DWDElevs.index(j) in sweepTimes:
                cachefile = loadDWDFile(site,j,quantityCode,sweepTimes[DWDElevs.index(j)],downloadOnly,False,gui)
                loadedData = BUFR(cachefile)
                if dataObject == None:
                    dataObject = loadedData
                else:
                    if len(dataObject.azimuths) < j+1:
                        dataObject.azimuths+=loadedData.azimuths
                        dataObject.times+=loadedData.times
                        dataObject.data+=loadedData.data
                        dataObject.vMax+=loadedData.vMax
                        dataObject.rMax+=loadedData.rMax
                        dataObject.nominalElevations+=loadedData.nominalElevations
                        dataObject.elevationNumbers+=loadedData.elevationNumbers
                        dataObject.elevations+=loadedData.elevations
                        dataObject.quantities+=loadedData.quantities
                    else:
                        if quantityCode not in dataObject.quantities[j][0]:
                            dataObject.quantities[j].append(quantityCode)
                            dataObject.data[j][quantityCode]=loadedData.data[0][quantityCode]
    if gui:
        msgtostatus(fraasid["saving_as_HDF5"])
        w.update()
    dumpVolume(dataObject, output)
    return True
    
def loadDWDFile(site, elevationNumber, quantity="DBZH", timestamp="latest", downloadOnly=False, realTime=True, gui=False):
    global currenturl
    global currentDisplay
    elevationNumbers=[5, 4, 3, 2, 1, 0, 6, 7, 8, 9]
    if elevationNumber != -1:
        elevationNumber=elevationNumbers[elevationNumber] #Convert over to DWD's numbering from relative numbering used in software for display purposes
    wmoCodes={"asb":10103,
           "boo":10132,
           "drs":10488,
           "eis":10780,
           "emd":10204,
           "ess":10410,
           "fbg":10908,
           "fld":10440,
           "hnr":10339,
           "neu":10557,
           "nhb":10605,
           "oft":10629,
           "pro":10392,
           "mem":10950,
           "ros":10169,
           "isn":10873,
           "tur":10832,
           "umm":10356
           }
    if elevationNumber == -1:
        scan="sweep_pcp"
    else:
        scan="sweep_vol"
    quantityMarker="z" if quantity == "DBZH" else "v"
    currentDWDFileName=scan+"_"+quantityMarker+"_"+str(elevationNumber if elevationNumber != -1 else 0)+"-"+timestamp+"_"+str(wmoCodes[site])+"--buf.bz2"
    downloadurl="http://opendata.dwd.de/weather/radar/sites/"+scan+"_"+quantityMarker+"/"+site+"/"+currentDWDFileName
    if not downloadOnly: currenturl=downloadurl
    try:
        cachefilename="../cache/dwdcache/"+site+scan+quantityMarker+str(elevationNumber)+timestamp
        if os.path.isfile(cachefilename):
            cachedFileTime=BUFR(cachefilename).times[0][0]
            if (datetime.datetime.utcnow()-cachedFileTime).seconds > 330 and realTime:
                downloadAgain=True
            else:
                downloadAgain=False
             #   print("Already have it. Loading from cache.")
        else:
            downloadAgain=True
            
        if downloadAgain:
            download_file(downloadurl,cachefilename)
            if gui:
                if fraasid["LANG_ID"] != "AR":
                    msgtostatus(fraasid["downloading_file"]+" "+currentDWDFileName)
                else:
                    msgtostatus(currentDWDFileName+u" "+fraasid["downloading_file"])
                w.update()
        else:
            if gui:
                if fraasid["LANG_ID"] != "AR":
                    msgtostatus(fraasid["loading_from_cache"]+" "+cachefilename)
                else:
                    msgtostatus(cachefilename+u" "+fraasid["loading_from_cache"])
                w.update()
            #print("Downloading from the server")
            
        if not downloadOnly:
            currentfilepath=cachefilename
            load(currentfilepath)
            currentDisplay.softElIndex=0
            if elevationNumber != -1:
                currentDisplay.elIndex=elevationNumbers.index(elevationNumber)
            else:
                currentDisplay.elIndex=-1
            populateDWDMenus()
        return cachefilename
    except:
        print(sys.exc_info())
        if gui:
            tkMessageBox.showerror(fraasid["name"],fraasid["download_failed"])
        return -1

def multithreadedDownload(src,dst="../cache/urlcache"):
    global currentDisplay
    try:
        dl = DownloadThread(src,dst)
        dl.start()
        dlpoints = ""

        currentDisplay.isCanvasBusy = True

        while dl.downloading:
            if fraasid["LANG_ID"] != "AR":
                msgtostatus(fraasid["downloading..."] + dlpoints)
                w.update()
                dlpoints += "."
            else:
                msgtostatus(dlpoints + fraasid["downloading..."])
                w.update()
                dlpoints += u"."
            time.sleep(0.5)

        currentDisplay.isCanvasBusy = False
        if dl.error:
            raise Exception(dl.error[1].reason)
        return True
            
    except:
        print(sys.exc_info())
        tkMessageBox.showerror(fraasid["name"],fraasid["download_failed"])
        return False
def loadKNMI(index,downloadOnly=False,scanTime=False):
    global currentlyOpenData
    global currentDisplay
    global currenturl
    folders = ["ftp://data.knmi.nl/download/radar_volume_denhelder/2.0/noversion/","ftp://data.knmi.nl/download/radar_volume_full_herwijnen/1.0/noversion/"]
    fileNamePrefixes = ["RAD_NL61_VOL_NA_","RAD_NL62_VOL_NA_"]

    #Guess the latest available scan time
    if not scanTime: #If we are not looking for an earlier scan...
        currentTime = datetime.datetime.utcnow() - datetime.timedelta(minutes = 6)
        secondsFromScan = (currentTime.minute % 5) * 60 + currentTime.second + currentTime.microsecond / 1000000
        scanTime = currentTime - datetime.timedelta(seconds = secondsFromScan)

    downloadurl = folders[index] + scanTime.strftime("%Y/%m/%d/") + fileNamePrefixes[index] + scanTime.strftime("%H%M") + ".h5"

    #Checking cache first
    cachePath = "../cache/knmicache/" + fileNamePrefixes[index] + "cache"
    if os.path.isfile(cachePath):
        if not downloadOnly:
            msgtostatus(fraasid["checkingKNMI"])
            w.update()
        try:
            cachedTime=HDF5(cachePath).headers["timestamp"]
            print(currentTime, cachePath, cachedTime, datetime.datetime.utcnow(), scanTime)
            if (currentTime-cachedTime).seconds < 300:
                download = False
            else:
                download = True
        except OSError: #The cached version is not readable. Most likely the download was cut short. Getting rid of it.
            os.unlink(cachePath)
            download = True
    else:
        download = True
        
    if download:
        if not downloadOnly:
            currenturl = downloadurl
            downloadSuccess=multithreadedDownload(downloadurl,cachePath)
        else:
            download_file(downloadurl,cachePath)
            downloadSuccess = True
    else:
        if not downloadOnly:
            msgtostatus(fraasid["loading_from_cache"]+"...")
            w.update()
        else:
            print("No need for downloading!")
    if (not downloadOnly) and downloadSuccess: load(cachePath,-1)
    
def populateDWDMenus():
    global currentDisplay
    elevationChoice["menu"].delete(0, 'end')
    if currentDisplay.DWDSite != "asb":
        elevations=[0.5, 0.8, 1.5, 2.5, 3.5, 4.5, 5.5, 8.0, 12.0, 17.0, 25.0]
    else:
        elevations=[0.8, 1.3, 1.5, 2.5, 3.5, 4.5, 5.5, 8.0, 12.0, 17.0, 25.0]
    elevationNumbers=[0, -1, 1, 2, 3, 4, 5, 6, 7, 8, 9] #-1: sweep_pcp 0. Others sweep_vols
    for i in range(len(elevations)):
        elevationChoice["menu"].add_command(label=str(elevations[i]), command=lambda x=elevationNumbers[i],y=currentDisplay.DWDSite,z=currentDisplay.quantity:loadDWDFile(y,x,z), font = uiFont)
    productChoice["menu"].delete(0, 'end')
    productChoice["menu"].add_command(label="DBZH",command=lambda x=currentDisplay.elIndex, y=currentDisplay.DWDSite: loadDWDFile(y,x,"DBZH"), font = uiFont)
    productChoice["menu"].add_command(label="VRADH",command=lambda x=currentDisplay.elIndex, y=currentDisplay.DWDSite: loadDWDFile(y,x,"VRADH"), font = uiFont)
def loadDWDSite(site):
    global currentDisplay
    productChoice.config(state=Tkinter.NORMAL)
    elevationChoice.config(state=Tkinter.NORMAL)
    currentDisplay.DWDSite=site
    currentDisplay.softElIndex = 0
    currentDisplay.elIndex = 5
    loadDWDFile(site,0)
def dealiasVelocitiesStart(onePass = False):
    global currentlyOpenData
    global currentDisplay
    global currenturl
    if "VRAD" in currentDisplay.quantity:
        currentlyOpenData,currentDisplay.quantity=dealiasVelocities(currentlyOpenData,currentDisplay.quantity,currentDisplay.softElIndex, onePass)
        if not (currenturl and "opendata.dwd.de" in currenturl):
            listProducts(currentDisplay.softElIndex)
        changeProduct(currentDisplay.quantity)
        currentlyOpenData.isModified = True
def clearCache():
    directories=["../cache/nexradcache","../cache/dwdcache","../cache/knmicache"]
    for directory in directories:
        files=os.listdir(directory)
        for file in files:
            fullPath=directory+"/"+file
            if file != "README":
                os.unlink(fullPath)
    tkMessageBox.showinfo(fraasid["name"],fraasid["delete_cache_complete"])
def change_language(lang):
    global conf
    conf["lang"]=lang
    save_config_file()
    tkMessageBox.showinfo(fraasid["name"],translations.phrases[lang]["conf_restart_required"])
clickcoords=[]
output=Tkinter.Tk()

if platform.system() == "Linux":
    uiFont = tkFont.Font(family = "DejaVu Sans Condensed", size = 9) #Let's theme the Linux display
    output.option_add("*Dialog.msg.font", "DejaVuSansCondensed 9")
else:
    uiFont = None #Handled by OS
    
output.title(fraasid["name"])
if os.name in ["posix", "nt"]:
    output.geometry("600x656")
else:
    output.geometry("600x660")
output.bind("<Configure>",on_window_reconf)
##Drawing the menu
menyy = Tkinter.Menu(output)

output.config(menu=menyy)
failimenyy = Tkinter.Menu(menyy, tearoff = 0)
radarmenyy = Tkinter.Menu(menyy, tearoff = 0)
dwdmenyy = Tkinter.Menu(menyy, tearoff = 0)
knmimenyy = Tkinter.Menu(menyy, tearoff = 0)
toolsmenyy = Tkinter.Menu(menyy,tearoff = 0)
abimenyy = Tkinter.Menu(menyy, tearoff = 0)
languagemenyy=Tkinter.Menu(menyy,tearoff=0)
menyy.add_cascade(label = fraasid["file"], menu = failimenyy, font = uiFont)
menyy.add_cascade(label = fraasid["nexrad"], menu = radarmenyy, font = uiFont)
menyy.add_cascade(label = "DWD", menu = dwdmenyy, font = uiFont)
menyy.add_cascade(label = "KNMI", menu = knmimenyy, font = uiFont)
menyy.add_cascade(label = fraasid["tools"], menu = toolsmenyy, font = uiFont)
menyy.add_cascade(label = fraasid["current_language"], menu = languagemenyy, font = uiFont)
menyy.add_cascade(label = fraasid["help"], menu = abimenyy, font = uiFont)
failimenyy.add_command(label = fraasid["open_datafile"], command = load, font = uiFont)
failimenyy.add_command(label = fraasid["open_url"], command = loadurl, font = uiFont)
failimenyy.add_separator()
failimenyy.add_command(label = fraasid["export_odim_h5"], command = saveHDF5, font = uiFont)
failimenyy.add_command(label = fraasid["export_img"], command = exportimg, font = uiFont)
failimenyy.add_command(label = fraasid["batch_export"], command = batch_export, font = uiFont)
failimenyy.add_separator()
failimenyy.add_command(label = fraasid["delete_cache"], command = clearCache, font = uiFont)
failimenyy.add_separator()
failimenyy.add_command(label = fraasid["quit"], command = output.destroy, font = uiFont)
radarmenyy.add_command(label = fraasid["current_data"], command = activatecurrentnexrad, font = uiFont)
radarmenyy.add_separator()
radarmenyy.add_command(label = fraasid["level3_station_selection"], command = choosenexrad, font = uiFont)
dwdmenyy.add_command(label = fraasid["dwd_credit"], state = Tkinter.DISABLED, font = uiFont)
dwdmenyy.add_separator()
dwdmenyy.add_command(label = "Borkum", command = lambda: loadDWDSite("asb"), font = uiFont)
dwdmenyy.add_command(label = "Boostedt", command = lambda: loadDWDSite("boo"), font = uiFont)
dwdmenyy.add_command(label = "Dresden", command = lambda: loadDWDSite("drs"), font = uiFont)
dwdmenyy.add_command(label = "Eisberg", command = lambda: loadDWDSite("eis"), font = uiFont)
dwdmenyy.add_command(label = "Emden", command = lambda: loadDWDSite("emd"), font = uiFont)
dwdmenyy.add_command(label = "Essen", command = lambda: loadDWDSite("ess"), font = uiFont)
dwdmenyy.add_command(label = "Feldberg", command = lambda: loadDWDSite("fbg"), font = uiFont)
dwdmenyy.add_command(label = "Flechtdorf", command = lambda: loadDWDSite("fld"), font = uiFont)
dwdmenyy.add_command(label = "Hannover", command = lambda: loadDWDSite("hnr"), font = uiFont)
dwdmenyy.add_command(label = "Isen", command = lambda: loadDWDSite("isn"), font = uiFont)
dwdmenyy.add_command(label = "Memmingen", command = lambda: loadDWDSite("mem"), font = uiFont)
dwdmenyy.add_command(label = "Neuhaus", command = lambda: loadDWDSite("neu"), font = uiFont)
dwdmenyy.add_command(label = "Neuheilenbach", command = lambda: loadDWDSite("nhb"), font = uiFont)
dwdmenyy.add_command(label = "Offenthal", command = lambda: loadDWDSite("oft"), font = uiFont)
dwdmenyy.add_command(label = "Prötzel", command = lambda: loadDWDSite("pro"), font = uiFont)
dwdmenyy.add_command(label = "Rostock", command = lambda: loadDWDSite("ros"), font = uiFont)
dwdmenyy.add_command(label = "Türkheim", command = lambda: loadDWDSite("tur"), font = uiFont)
dwdmenyy.add_command(label = "Ummendorf", command = lambda: loadDWDSite("umm"), font = uiFont)
dwdmenyy.add_separator()
dwdmenyy.add_command(label = fraasid["download_entire_volume"], command = openDWDDialog, font = uiFont)
knmimenyy.add_command(label = "Den Helder", command = lambda: loadKNMI(0), font = uiFont)
knmimenyy.add_command(label = "Herwijnen", command = lambda: loadKNMI(1), font = uiFont)

dealiasingMenu = Tkinter.Menu(toolsmenyy, tearoff = 0)
dealiasingMenu.add_command(label=fraasid["dealiassequence1"], command = lambda: dealiasVelocitiesStart([0,1,2,1,0]), font = uiFont)
dealiasingMenu.add_command(label=fraasid["dealiassequence2"], command = lambda: dealiasVelocitiesStart([1,0,3,2,0]), font = uiFont)
dealiasingMenu.add_separator()
dealiasingMenu.add_command(label = fraasid["dealias1"], command = lambda: dealiasVelocitiesStart([0]), font = uiFont)
dealiasingMenu.add_command(label = fraasid["dealias2"], command = lambda: dealiasVelocitiesStart([1]), font = uiFont)
dealiasingMenu.add_command(label = fraasid["dealias3"], command = lambda: dealiasVelocitiesStart([2]), font = uiFont)
dealiasingMenu.add_command(label = fraasid["dealias4"], command = lambda: dealiasVelocitiesStart([3]), font = uiFont)

toolsmenyy.add_command(label = fraasid["linear_interp"], command = interpolateData, state = Tkinter.DISABLED, font = uiFont)
toolsmenyy.add_cascade(label = fraasid["dealiasing"], menu=dealiasingMenu, state = Tkinter.DISABLED, font = uiFont)
colortablemenu=Tkinter.Menu(toolsmenyy, tearoff = 0) #Custom color tables menu
listcolortables() #Adds all available color tables to the menu
colortablemenu.add_separator()
colortablemenu.add_command(label = fraasid["default_colors"], command = reset_colortable, font = uiFont)
toolsmenyy.add_cascade(label = fraasid["color_table"], menu = colortablemenu, underline = 0, state = Tkinter.DISABLED, font = uiFont)
if arabicOnLinux:
    toolsmenyy.add_command(label = fixArabic(fraasid["dyn_labels"]), command = dynlabels_settings, font = uiFont)
else:
    toolsmenyy.add_command(label = fraasid["dyn_labels"], command = dynlabels_settings, font = uiFont)
abimenyy.add_command(label = fraasid["key_shortcuts_menuentry"], command = keys_list, font = uiFont)
abimenyy.add_separator()
abimenyy.add_command(label = fraasid["about_program"], command = about_program, font = uiFont)
languagemenyy.add_command(label = fraasid["language_estonian"], command = lambda: change_language("estonian"), font = uiFont)
languagemenyy.add_command(label = fraasid["language_english"], command = lambda: change_language("english"), font = uiFont)
languagemenyy.add_command(label = fraasid["language_arabic"], command = lambda: change_language("arabic"), font = uiFont)
##Drawing area
w = Tkinter.Canvas(output, width = 600, height = 600, highlightthickness = 0)
w.bind("<Button-1>", leftclick)
w.bind("<Button-3>", rightclick)
w.bind("<B1-Motion>", onmotion)
w.bind("<B3-Motion>", onmotion)
w.bind("<ButtonRelease-1>", onrelease)
w.bind("<ButtonRelease-3>", onrelease)
w.bind("<Motion>", onmousemove)
w.config(background = "#000025")
w.config(cursor = "crosshair")
w.grid(row = 0, column = 0)
radaripilt = w.create_image(tuple(currentDisplay.imageCentre))
clicktext = w.create_image((300, 300))
legend = w.create_image((582, 300))
radardetails = w.create_image((300, 580))
zoomrect = w.create_rectangle((0, 0, 200, 200), outline = "white", state = Tkinter.HIDDEN) #Ristkülik, mis joonistatakse ekraanile suurendamise ajal.
rMaxAddSelectorShape = [w.create_arc((0,0,0,0), outline = "white", style = Tkinter.ARC, state = Tkinter.HIDDEN),
                        w.create_line((0,0,0,0), fill = "white", state = Tkinter.HIDDEN),
                        w.create_line((0,0,0,0), fill = "white", state = Tkinter.HIDDEN),
                        w.create_arc((0,0,0,0), outline = "white", style = Tkinter.ARC, state = Tkinter.HIDDEN)]
progress = w.create_rectangle((0, 590, 400, 600), fill = "#0044ff", state = Tkinter.HIDDEN)
#Key bindings
output.bind("r", resetzoom)
output.bind("i", toinfo)
output.bind("p", topan)
output.bind("z", tozoom)
output.bind("h", chooserhi)
moderaam = Tkinter.Frame(output)
moderaam.grid(row = 1, column = 0, sticky = "we")
moderaam.config(bg = "#0099ff")
panimg = PhotoImage(file = "../images/pan.png")
zoomimg = PhotoImage(file = "../images/zoom.png")
resetzoomimg = PhotoImage(file = "../images/resetzoom.png")
infoimg = PhotoImage(file = "../images/info.png")
rhiimg = PhotoImage(file = "../images/rhi.png")
ppiimg = PhotoImage(file = "../images/ppi.png")
rmaximg = PhotoImage(file = "../images/rmax.png")
reloadimg = PhotoImage(file = "../images/reload.png")
taskbarbtn1 = Tkinter.Button(moderaam, bg = "#0099ff", activebackground = "#0044ff", highlightbackground = "#0044ff", image = panimg, command = topan)
taskbarbtn1.grid(row = 0, column = 0)
taskbarbtn2=Tkinter.Button(moderaam, bg = "#0099ff", activebackground = "#0044ff", highlightbackground = "#0044ff", image = zoomimg, command = tozoom)
taskbarbtn2.grid(row = 0, column = 1)
taskbarbtn3 = Tkinter.Button(moderaam, bg = "#0099ff", activebackground = "#0044ff", highlightbackground = "#0044ff", image = resetzoomimg, command = resetzoom)
taskbarbtn3.grid(row = 0, column = 2)
taskbarbtn4 = Tkinter.Button(moderaam, bg = "#0099ff", activebackground = "#0044ff", highlightbackground = "#0044ff", image = infoimg, command = toinfo)
taskbarbtn4.grid(row = 0, column = 3)
taskbarbtn5 = Tkinter.Button(moderaam, bg = "#0099ff", activebackground = "#0044ff", highlightbackground = "#0044ff", image = rhiimg, command = chooserhi)
taskbarbtn5.grid(row = 0, column = 4)
taskbarbtn6 = Tkinter.Button(moderaam, bg = "#0099ff", activebackground = "#0044ff", highlightbackground = "#0044ff", image = rmaximg, command = toAddingRmax, state = Tkinter.DISABLED) #add rmax button
taskbarbtn6.grid(row = 0, column = 5)
taskbarbtn7 = Tkinter.Button(moderaam, bg = "#0099ff", activebackground = "#0044ff", highlightbackground = "#0044ff", image = reloadimg, command = reloadfile)
taskbarbtn7.grid(row = 0, column = 6)
chosenElevation = Tkinter.StringVar(moderaam)
elevationChoice = Tkinter.OptionMenu(moderaam, chosenElevation, None)
elevationChoice.config(bg = "#44bbff", activebackground = "#55ccff", highlightbackground = "#55ccff", state = Tkinter.DISABLED, font = uiFont)
elevationChoice.grid(row = 0, column = 7, ipadx = 10, sticky="ew")
chosenProduct = Tkinter.StringVar(moderaam)
productChoice = Tkinter.OptionMenu(moderaam, chosenProduct, None)
productChoice.config(bg = "#44bbff", activebackground = "#55ccff", highlightbackground = "#55ccff", state = Tkinter.DISABLED, font = uiFont)
productChoice.grid(row = 0, column = 8, ipadx = 10, sticky="ew")
if fraasid["LANG_ID"] != "AR":
    status = Tkinter.Label(output, text = None, justify = Tkinter.LEFT, anchor = "w", font = uiFont)
    status.grid(row = 2, column = 0, sticky = "w")
else:
    status = Tkinter.Label(output, text = None, justify = Tkinter.RIGHT, anchor = "e", font = uiFont)
    status.grid(row = 2, column = 0, sticky = "e")
output.mainloop()
