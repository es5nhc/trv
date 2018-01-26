# -*- coding: utf-8 -*-
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

from bz2 import decompress
import translations
from bitprocessing import halfw
from bitprocessing import word
from bitprocessing import beword
from bitprocessing import floating
from coordinates import getcoords
from coordinates import parsecoords
import datetime
from math import radians as d2r, cos, pi, sqrt
import time
from h5py import File as HDF5Fail
import string
import os

from array import array
import numpy as np
from numpy import fromstring
import nexradtable

NP_UINT8 = np.uint8
NP_UINT16 = np.uint16
NP_INT16 = np.int16
NP_FLOAT = np.float32


class FileFormatError(Exception): ##Exception to throw if decoding classes fed wrong type of content
    pass

class NEXRADLevel3():
    #RELEVANT NEXRAD ICD: 2620001U
    def __init__(self, path):
        stream = file_read(path) #Load the data file
        self.type = "NEXRAD3"
        self.headers = {}
        self.data = [{}]
        self.azimuths = []
        self.headers["rstart"] = 0
        self.headers["icao"] = None
        if stream.find(b"SDUS") != -1: #If WMO headers present
            self.headers["radarId"] = stream[7:11]
            stream = stream[30:] #Get rid of the headers before decoding
        self.headers["productCode"] = convertNEXRAD3Code(halfw(stream[0:2], False)) #Product Code

        self.data[0][self.headers["productCode"]]={"data":[],"rstart":0}
        
        self.headers["timestamp"] = datetime.datetime.utcfromtimestamp((halfw(stream[2:4], False) * 86400 - 86400) + word(stream[4:8], False))
        self.headers["messageLength"] = word(stream[8:12], False) #Length of Message
        self.headers["sourceID"] = halfw(stream[12:14], False) #Source ID
        self.headers["destinationID"] = halfw(stream[14:16], False) #Destination ID
        self.headers["numberOfBlocks"] = halfw(stream[16:18], False) #Number of blocks
        self.headers["latitude"] = round(word(stream[20:24]) / 1000.0, 3) #Latitude of radar
        self.headers["longitude"] = round((word(stream[24:28])) / 1000.0, 3) #Longitude of radar
        self.headers["height"] = round(halfw(stream[28:30], False) * 0.3048, 4) #Radar height
        self.headers["operationalMode"] = halfw(stream[32:34], False) #Operational mode
        self.headers["VCP"] = halfw(stream[34:36], False) #Volume Coverage Pattern
        self.headers["sequenceNumber"] = halfw(stream[36:38], False) #Sequence number
        self.headers["volumeScanNumber"] = halfw(stream[38:40], False) #Volume Scan Number
        self.headers["volumeScanTime"] = datetime.datetime.utcfromtimestamp((halfw(stream[40:42], False) - 1) * 86400 + word(stream[42:46], False))
        self.times=[self.headers["volumeScanTime"]]
        self.headers["productGenerationTime"] = datetime.datetime.utcfromtimestamp((halfw(stream[46:48], False) - 1) * 86400 + word(stream[48:52], False))
        self.headers["antennaElevation"] = halfw(stream[58:60], False)/10.0 #Antenna elevation
        if self.headers["productCode"] in ["ZDR","RHOHV","KDP"]:
            NEXRADScale=floating(stream[60:64])
            NEXRADOffset=floating(stream[64:68])
            self.data[0][self.headers["productCode"]]["gain"] = 1/NEXRADScale
            self.data[0][self.headers["productCode"]]["offset"] = -NEXRADOffset/NEXRADScale
        elif self.headers["productCode"] == "HCLASS":
            self.data[0][self.headers["productCode"]]["gain"] = 1
            self.data[0][self.headers["productCode"]]["offset"] = 0
        else:
            self.data[0][self.headers["productCode"]]["gain"] = halfw(stream[62:64])/10 #dbz increment
            self.data[0][self.headers["productCode"]]["offset"] = halfw(stream[60:62])/10-self.data[0][self.headers["productCode"]]["gain"]*2 #Minimum data in dbz
            self.headers["amountofLevels"] = halfw(stream[64:66],False)
        self.data[0][self.headers["productCode"]]["undetect"] = None if self.headers["productCode"] != "HCLASS" else -999
        self.data[0][self.headers["productCode"]]["nodata"] = 0
        self.data[0][self.headers["productCode"]]["rangefolding"] = 1
        self.data[0][self.headers["productCode"]]["rscale"]=1 if self.headers["productCode"]=="DBZ" else 0.25

        self.nominalElevations = [self.headers["antennaElevation"]]
        self.elevationNumbers = [0]
        self.quantities = [[self.headers["productCode"]]]
        

        #DATA DECODING

        #Decompress data
        bins=decompress(stream[stream.find(b"BZ"):])[28:]
        self.headers["radialsCount"]=int(halfw(bins[0:2]))

        p=2 #pointer in "bins" - first halfword was for radials count

        self.azimuths=[[]] #Even though only 1 elevation in file, treating as full volumes so same code can be used for all filetypes

        for i in range(self.headers["radialsCount"]):
            amt=halfw(bins[p:p+2])
            az=round(halfw(bins[p+2:p+4])/10.0,1)
            self.azimuths[0].append(az)
            d_az=round(halfw(bins[p+4:p+6])/10.0,1)
            row=[]
            p+=6

            if self.headers["productCode"] == "HCLASS": #If HCA
                self.data[0][self.headers["productCode"]]["nodata"]=-999
                #Override usual decoding system and plot them as numbers
                for j in range(p,p+amt):
                    val=bins[j]
                    if val == 0: row.append(-999)
                    elif val > 0 and val < 140: row.append(int(val/10-1))
                    elif val >= 140: row.append(int(val/10-4))
            else:
                for j in range(p,p+amt):
                    val=bins[j]
                    row.append(val)
            self.data[0][self.headers["productCode"]]["data"].append(row)
            p+=amt
        
        del(stream) #Garbage collection
        
class NEXRADLevel2():
    ##RELEVANT NEXRAD ICD'S: 2620002P, 2620010E
    def __init__(self,path):
        sisu=file_read(path)
        if sisu[0:4] == b"AR2V" and sisu[0:8] != b"AR2V0001":
            self.type="NEXRAD2"
            self.headers={}
            self.elevations=[]
            self.nominalElevations=[]
            self.elevationNumbers=[]
            self.azimuths=[]
            azimuthCentres=[]
            self.times=[]
            self.quantities=[]
            self.data=[]
            self.rMax=[]
            self.vMax=[]
            self.headers["timestamp"]=datetime.datetime.utcfromtimestamp((word(sisu[12:16])-1)*86400+word(sisu[16:20])/1000)
            self.headers["icao"]=sisu[20:24]
            ptr=24
            messageType=None
            while ptr < len(sisu):
                compressionControlWord=abs(word(sisu[ptr:ptr+4]))
                if compressionControlWord:
                    fullmsg=decompress(sisu[ptr+4:ptr+compressionControlWord+4])[12:]
                    messageSize=halfw(fullmsg[0:2],False)
                    ptr+=compressionControlWord+4
                    y=0
                else:
                    messageSize=halfw(sisu[ptr+12:ptr+14],False)
                    fullmsg=sisu[ptr+12:ptr+messageSize*2]
                    messageType=sisu[ptr+15]
                    if messageSize != 0 and messageSize > 0:
                        if messageType != 31:
                            ptr+=2432
                        else:
                            ptr+=messageSize*2+12
                    else:
                        while sisu[ptr+12] == 0: ptr+=2432
                msgptr=0 #Pointer within a message
                while msgptr < len(fullmsg):
                    msg=fullmsg[msgptr:msgptr+messageSize*2+12]
                    if compressionControlWord:
                        messageType=msg[3]
                    if messageType == 31:
                        #azNumber=halfw(msg[26:28])
                        azAngle=floating(msg[28:32])
                        #azimuthResolutionSpacing=msg[36]*0.5
                        #radialStatus=msg[37]
                        elevationNumber=msg[38]
                        elIndex=elevationNumber-1
                        elevationAngle=floating(msg[40:44])
                        if elevationNumber not in self.elevationNumbers:
                            self.elevationNumbers.append(elevationNumber)
                            self.data.append({})
                            azimuthCentres.append([])
                            self.elevations.append([])
                            self.quantities.append([])
                            self.times.append(datetime.datetime.utcfromtimestamp((halfw(msg[24:26],False)-1)*86400+word(msg[20:24])/1000.0))

                            rdcPointer=word(msg[56:60])+16
                            rdcSize=msg[rdcPointer+4:rdcPointer+6]
                            self.rMax.append(halfw(msg[rdcPointer+6:rdcPointer+8])*0.1)
                            self.vMax.append(halfw(msg[rdcPointer+16:rdcPointer+18])*0.01)
                        
                        self.elevations[elIndex].append(elevationAngle)
                        azimuthCentres[elIndex].append(azAngle)
                        #Latitude and longitude data
                        if "latitude" not in self.headers.keys():
                            #We don't have all the data in the headers yet. Going also through Volume Data Constant and Radial Data Constant blocks
                            #We skip them once populated to save on CPU time, assuming they are constant.
                            #Get the pointers
                            vdcPointer=word(msg[48:52])+16

                            vdcSize=msg[vdcPointer+4:vdcPointer+6]

                            self.headers["latitude"]=floating(msg[vdcPointer+8:vdcPointer+12])
                            self.headers["longitude"]=floating(msg[vdcPointer+12:vdcPointer+16])
                            self.headers["siteHeightASL"]=halfw(msg[vdcPointer+16:vdcPointer+18])
                            self.headers["feedhornHeight"]=halfw(msg[vdcPointer+18:vdcPointer+20])
                        #Grabbing unscaled data. Scaling will be done real-time when the particular sweep gets displayed.
                        for adds in range(60,84,4):
                            quantityPointer=word(msg[adds:adds+4],False)
                            if quantityPointer:
                                x=quantityPointer+16
                                quantityType=msg[x]
                                quantityName=convertNEXRAD2Code(msg[x+1:x+4].decode("utf-8"))
                                dataQuantityGatesNr=halfw(msg[x+8:x+10])
                                dataWordSize=msg[x+19]
                                dataGain=1/floating(msg[x+20:x+24]) #Converting to Gain/Offset values as known in HDF5 files.
                                dataOffset=-floating(msg[x+24:x+28])*dataGain
                                if quantityName not in self.data[-1]:
                                    rscale=halfw(msg[x+12:x+14])/1000
                                    self.data[elIndex][quantityName]={"data":[],"gain":dataGain,"offset":dataOffset,"undetect":0,"rangefolding":1,"nodata":2**dataWordSize,"rscale":rscale,"rstart":halfw(msg[x+10:x+12])/1000-rscale/2}
                                    self.quantities[elIndex].append(quantityName)

                                if dataWordSize == 8:
                                    dataRow=array("B",msg[x+28:x+28+dataQuantityGatesNr])
                                elif dataWordSize == 16:
                                    dataRow=array("H",msg[x+28:x+28+dataQuantityGatesNr*2])
                                    dataRow.byteswap() #CAVEAT: byteswap modifies the variable in place and returns None!
                                self.data[elIndex][quantityName]["data"].append(dataRow)
                    msgptr+=messageSize*2+12
            #Final processing: Trying to guess nominal elevation angle
            for e in self.elevations:
                self.nominalElevations.append(round(sum(e)/len(e),2))
            #Final processing: The azimuths. The final azimuths list does not contain the direction of the beam center, but rather the boundaries between two adjacent bins. 
            self.azimuths=[]
            for i in range(len(azimuthCentres)):
                self.azimuths.append([])
                x=azimuthCentres[i]
                eelmine_az=x[0]
                #self.azimuths.append([azimuthCentres[i][-1]]+azimuthCentres[i][:-1])
                for j in range(len(x)):
                    if x[j] < eelmine_az and eelmine_az-x[j] > 350: #If crossing North
                        eelmine_az-=360
                    az_begin=(x[j]+eelmine_az)/2
                    eelmine_az=x[j]
                    self.azimuths[-1].append(az_begin)
        elif sisu[0:8] in [b"ARCHIVE2",b"AR2V0001"]:
            self.type="NEXRAD2"
            self.headers={}
            self.elevations=[]
            self.nominalElevations=[]
            self.elevationNumbers=[]
            self.azimuths=[]
            azimuthCentres=[]
            self.times=[]
            self.quantities=[]
            self.data=[]
            self.rMax=[]
            self.vMax=[]
            ##FAILIS ISE METAANDMEID EI OLE! Vähemalt asukoha osas.
            fileName=os.path.basename(path)
            icao=fileName[0:4]
            fileCreated=datetime.datetime.utcfromtimestamp((word(sisu[12:16])-1)*86400+word(sisu[16:20])/1000)
            self.headers["latitude"],self.headers["longitude"]=nexradtable.table[icao]
            self.headers["timestamp"]=fileCreated
            self.headers["icao"]=icao
            ptr=24
            fileSize=len(sisu)
            while ptr < fileSize:
                messageSize=halfw(sisu[ptr+12:ptr+14],False)
                fullmsg=sisu[ptr+12:ptr+2432]
                messageType=sisu[ptr+15]
                if messageType == 1:
                    #rmax=halfw(fullmsg[22:24])/10
                    azAngle=(halfw(fullmsg[24:26])/8)*(180/4096) % 360
                    elAngle=(halfw(fullmsg[30:32])/8)*(180/4096)
                    elNumber=halfw(fullmsg[32:34])
                    elIndex=elNumber-1
                    collectionTime=datetime.datetime.utcfromtimestamp((halfw(fullmsg[20:22])-1)*86400+word(fullmsg[16:20])/1000)
                    if elNumber not in self.elevationNumbers:
                            self.elevationNumbers.append(elNumber)
                            self.data.append({})
                            self.times.append(collectionTime)
                            azimuthCentres.append([])
                            self.elevations.append([])
                            self.quantities.append([])
                    self.elevations[elIndex].append(elAngle)
                    azimuthCentres[elIndex].append(azAngle)
                    rstartDBZ=halfw(fullmsg[34:36])/1000
                    rstartVRAD=halfw(fullmsg[36:38])/1000
                    rscaleDBZ=halfw(fullmsg[38:40])/1000
                    rscaleVRAD=halfw(fullmsg[40:42])/1000
                    refGates=halfw(fullmsg[42:44])
                    velGates=halfw(fullmsg[44:46])
                    dbzPointer=halfw(fullmsg[52:54])
                    vradPointer=halfw(fullmsg[54:56])
                    wradPointer=halfw(fullmsg[56:58])

                    pointers=[halfw(fullmsg[52:54]), halfw(fullmsg[54:56]), halfw(fullmsg[56:58])]

                    if pointers[0] and pointers[1] and elAngle < 1.6:
                        pointers[0]=0 #Workaround for files like OKC on May 3 1999. Assuming no actual reflectivity data when doppler data is present.
                    
                    quantityCodes=["DBZH","VRAD","WRAD"]
                    dopplerResolution=halfw(fullmsg[58:60])
                    dopplerOffset=-64.5 if  dopplerResolution == 2 else -129
                    dopplerGain=0.5 if dopplerResolution == 2 else 1

                    for m in range(3):
                        quantity=quantityCodes[m]
                        gain=0.5 if m == 0 else dopplerGain
                        offset=-33 if m == 0 else dopplerOffset
                        rstart=rstartDBZ if m == 0 else rstartVRAD
                        rscale=rscaleDBZ if m == 0 else rscaleVRAD
                        gatesNumber=refGates if m == 0 else velGates
                        if pointers[m]:
                            if quantity not in self.data[elIndex]:
                                self.data[elIndex][quantity]={"data":[],"gain":gain,"offset":offset,"undetect":0,"rangefolding":1,"nodata":None,"rscale":rscale,"rstart":rstart-rscale/2}
                                self.quantities[elIndex].append(quantity)
                            quantityStart=16+pointers[m]
                            dataRow=array("B",fullmsg[quantityStart:quantityStart+gatesNumber])
                            self.data[elIndex][quantity]["data"].append(dataRow)
                ptr+=2432
            #print("Vara veel")
            #Final processing: Trying to guess nominal elevation angle
            for e in self.elevations:
                self.nominalElevations.append(round(sum(e)/len(e),2))
            #Final processing: The azimuths. The final azimuths list does not contain the direction of the beam center, but rather the boundaries between two adjacent bins. 
            self.azimuths=[]
            for i in range(len(azimuthCentres)):
                self.azimuths.append([])
                x=azimuthCentres[i]
                eelmine_az=x[0]
                #self.azimuths.append([azimuthCentres[i][-1]]+azimuthCentres[i][:-1])
                for j in range(len(x)):
                    if x[j] < eelmine_az and eelmine_az-x[j] > 350: #If crossing North
                        eelmine_az-=360
                    az_begin=(x[j]+eelmine_az)/2
                    eelmine_az=x[j]
                    self.azimuths[-1].append(az_begin)
        else:
            raise FileFormatError("Not a NEXRAD Level 2 file. Did you decompress it first?")
                
class HDF5():
    def __init__(self,path):
        self.type="HDF5"
        self.headers={}
        self.nominalElevations=[]
        self.azimuths=[]
        self.data=[]
        self.times=[]
        self.quantities=[]

        andmed=HDF5Fail(path,"r") #Load the data file
        self.orig=andmed

        mainwhatattrs=andmed["/what"].attrs
        mainwhereattrs=andmed["/where"].attrs

        self.headers["version"]=mainwhatattrs.get("version")
        if type(mainwhatattrs.get("date")) is np.ndarray:
            ajastring=mainwhatattrs.get("date")[0]+mainwhatattrs.get("time")[0]
        else:
            ajastring=mainwhatattrs.get("date")+mainwhatattrs.get("time")
        self.headers["timestamp"]=datetime.datetime.strptime(ajastring.decode("utf-8"),"%Y%m%d%H%M%S")
        self.headers["latitude"]=float(mainwhereattrs.get(u"lat"))
        self.headers["longitude"]=float(mainwhereattrs.get(u"lon"))

        if self.headers["version"] == b"H5rad 1.2":
            name="scan"
            datasetamt=len(list(filter(lambda x:x[0:4]=="scan",andmed.keys())))
            for i in range(1,datasetamt+1):
                elevation=andmed[name+str(i)+"/where"].attrs.get("angle")
                whatattrs=andmed[name+str(i)+"/what"].attrs
                if elevation not in self.nominalElevations:
                    if type(whatattrs.get("startdate")) is np.ndarray: #Grr. See post-nrays-get if.
                        starttimestring=whatattrs.get("startdate")[0]+whatattrs.get("starttime")[0]
                    else:
                        starttimestring=whatattrs.get("startdate")+whatattrs.get("starttime")
                    starttime=datetime.datetime.strptime(starttimestring.decode("utf-8"),"%Y%m%d%H%M%S")
                    self.times.append(starttime)
                    
                    self.nominalElevations.append(elevation)
                    self.azimuths.append(range(0,len(andmed[name+str(i)+"/data"])))
                    self.data.append({})
                    self.quantities.append([])
                elIndex=self.nominalElevations.index(elevation)
                quantity=whatattrs.get("quantity").decode("utf-8")
                if quantity not in self.quantities[elIndex]:
                    self.quantities[elIndex].append(quantity)
                    
                try: #Get Dual-PRF values. Report none if /how not found.
                    mainhowattrs=andmed["/how"].attrs
                    highprf=float(mainhowattrs.get("highprf"))
                    lowprf=float(mainhowattrs.get("lowprf"))
                except:
                    highprf=None
                    lowprf=None
                    
                self.data[elIndex][quantity]={
                    "data":andmed[name+str(i)+"/data"],
                    "rscale":float(mainwhereattrs.get("xscale"))/1000,
                    "rstart":0,
                    "highprf":highprf,
                    "lowprf":lowprf,
                    "offset":float(whatattrs.get("offset")),
                    "gain":float(whatattrs.get("gain")),
                    "nodata":float(whatattrs.get("nodata")),
                    "undetect":float(whatattrs.get("undetect")),
                    }
        else:
            datasetamt=len(list(filter(lambda x:x[0:7]=="dataset",andmed.keys())))
            for i in range(1,datasetamt+1):
                datasetpath="dataset"+str(i)
                datacount=len(list(filter(lambda x:x[0:4] == "data",andmed[datasetpath].keys())))
                datasetwhat=andmed[datasetpath+"/what"].attrs
                datasetwhere=andmed[datasetpath+"/where"].attrs
                elevation=datasetwhere.get("elangle")
                if type(elevation) is np.ndarray: elevation=elevation[0]
                elevation=round(elevation,2) #Round just in case there are floating point inaccuracies in the original data.
                nrays=datasetwhere.get("nrays")
                if nrays == None: nrays = 360 #If no nrays defined assume 360. Workaround for personal stopgap HDF5 creations from the past)
                if type(nrays) is np.ndarray: nrays=nrays[0] #Oh brother. Value saved as array again.
                
                if elevation not in self.nominalElevations:
                    #STARTTIME
                    noStartTime=False #True if no start time defined in data(e.g my internal stopgap HDF5 creations)
                    if type(datasetwhat.get("startdate")) is np.ndarray: #Grr. See post-nrays-get if.
                        starttimestring=datasetwhat.get("startdate")[0]+datasetwhat.get("starttime")[0]
                    else:
                        starttimedate=datasetwhat.get("startdate")
                        starttimetime=datasetwhat.get("starttime")
                        if not starttimedate and not starttimetime: ## Workaround for my internally generated HDF5s derived from GeoTIFF images
                            noStartTime=True
                        else:
                            starttimestring=datasetwhat.get("startdate")+datasetwhat.get("starttime")
                    if not noStartTime:
                        starttime=datetime.datetime.strptime(starttimestring.decode("utf-8"),"%Y%m%d%H%M%S")
                    else:
                        starttime=None
                    self.times.append(starttime)
                    self.nominalElevations.append(elevation)
                    self.azimuths.append(list(map(lambda x,y=nrays:360*x/y,range(nrays))))
                    self.data.append({})
                    self.quantities.append([])
                    for da in range(datacount):
                        d="data"+str(da+1)
                        datawhat=andmed[datasetpath+"/"+d+"/what"].attrs
                        quantity=datawhat.get("quantity")
                        if type(quantity) is np.ndarray: quantity=quantity[0]
                        quantity=quantity.decode("utf-8")
                        if quantity not in self.quantities[-1]:
                            self.quantities[-1].append(quantity)
                            
                        try:
                            datasethow=andmed[datasetpath+"/how"].attrs
                            highprf=float(datasethow.get("highprf"))
                            lowprf=float(datasethow.get("lowprf"))
                        except:
                            highprf=None
                            lowprf=None

                        rstart=datasetwhere.get("rstart")
                        if rstart == None: rstart=0 #Workaround for... see above!
                        self.data[-1][quantity]={
                            "data":andmed[datasetpath+"/"+d+"/data"],
                            "rscale":float(datasetwhere.get("rscale"))/1000,
                            "rstart":float(rstart),
                            "highprf":highprf,
                            "lowprf":lowprf,
                            "offset":float(datawhat.get("offset")),
                            "gain":float(datawhat.get("gain")),
                            "nodata":float(datawhat.get("nodata")),
                            "undetect":float(datawhat.get("undetect"))
                            }
        self.elevationNumbers=list(range(len(self.nominalElevations)))  

            

def IrisMETEO(x):
    x=int(x)
    if x > 6:
        return x-((x >> 3) << 3)
    else:
        return x

def file_read(path):
    andmefail=open(path,"rb")
    sisu=andmefail.read()
    andmefail.close()
    return sisu

def convertNEXRAD2Code(quantity):
    ''' Converts NEXRAD product codes to ODIM H5 nomenclature which is now used by default '''
    convertDict = {
        "REF":"DBZH",
        "VEL":"VRAD",
        "PHI":"PHIDP",
        "RHO":"RHOHV",
        "KDP":"KDP",
        "SW ":"WRAD",
    }
    return convertDict[quantity] if quantity in convertDict else quantity
def convertNEXRAD3Code(productCode):
    ''' Converts NEXRAD product codes to ODIM H5 nomenclature which is now used by default '''
    convertDict={
        94:"DBZ",
        99:"VRADDH",
        159:"ZDR",
        161:"RHOHV",
        163:"KDP",
        165:"HCLASS"
    }
    return convertDict[productCode]
def productname(quantity,fraasid):
    products={94:fraasid["product_reflectivity"],
              99:fraasid["product_radialvelocity"],
              159:fraasid["product_zdr"],
              161:fraasid["product_rhohv"],
              163:fraasid["product_kdp"],
              165:fraasid["product_hclass"],
              "TH":fraasid["th"],
              "TV":fraasid["tv"],
              "DBZ":fraasid["product_reflectivity"],
              "DBZH":fraasid["dbzh"],
              "DBZV":fraasid["dbzv"],
              "REF":fraasid["product_reflectivity"],
              "ZDR":fraasid["product_zdr"],
              "LZDR":fraasid["product_zdr"],
              "RHOHV":fraasid["product_rhohv"],
              "RHO":fraasid["product_rhohv"],
              "KDP":fraasid["product_kdp"],
              "HCLASS":fraasid["product_hclass"],
              "V":fraasid["product_radialvelocity"],
              "VEL":fraasid["product_radialvelocity"],
              "VRAD":fraasid["product_radialvelocity"],
              "VRADH":fraasid["vradh"],
              "VRADV":fraasid["vradv"],
              "VRADDH":fraasid["vraddh"],
              "VRADDV":fraasid["vraddv"],
              "PHI":fraasid["product_phi"],
              "SQI":fraasid["sqi"],
              "QIDX":fraasid["qidx"],
              "PHIDP":fraasid["product_phi"],
              "SW":fraasid["product_sw"],
              "WRAD":fraasid["product_sw"],
              "WRADH":fraasid["wradh"],
              "WRADV":fraasid["wradv"],
              }
    return products[quantity]

def rhiheadersdecoded(display,fraasid):
    msg=productname(display.quantity,fraasid).capitalize()+" | "+fraasid["azimuth"]+": "+str(display.rhiAzimuth)+u"° | "+str(display.productTime)+" UTC"
    return msg
def headersdecoded(display,fraasid):
    msg=str(float(display.elevation))+u"° "+productname(display.quantity,fraasid)+" | "+str(display.productTime)+" UTC"
    if display.scanTime: #Kui on Level 2 fail.
        msg+=" ("+str(display.scanTime)+")"
    return msg


def leiasuund(rad,rad2,y,currentDisplay,zoom=1,center=[1000,1000],samm=1):
    '''makepath(algasimuut, (asimuudi) samm, kaugus radarist, suurendusaste, renderduse keskpunkti asukoht), kauguse samm'''
    koosinus=1 if not currentDisplay.fileType == "NEXRAD3" else cos(d2r(currentDisplay.elevation)) #Kui on NEXRADi produktid, arvesta nurga muutusega!
    r=y*koosinus
    r_new=r+samm*koosinus
    coords1=getcoords((r_new,rad),zoom,center)
    coords2=getcoords((r_new,rad+rad2),zoom,center)
    coords3=getcoords((r,rad),zoom,center)
    coords4=getcoords((r,rad+rad2),zoom,center)
    startx1,starty1=coords3
    startx2,starty2=coords4
    endx1,endy1=coords1
    endx2,endy2=coords2
    dx1=endx1-startx1
    dx2=endx2-startx2
    dy1=endy1-starty1
    dy2=endy2-starty2
    return startx1,startx2,starty1,starty2,dx1,dx2,dy1,dy2

def scaleValue(value,gain,offset,nodata,undetect,rangefolding):
    if value != nodata and value != undetect and value != rangefolding:
        return value*gain+offset
    else:
        if value == rangefolding:
            return "RF"
        else:
            return None

def HDF5scaleValue(value,gain,offset,nodata,undetect,rangefolding,quantity):
    if value != nodata and value != undetect and value != rangefolding:
        if type(value) is NP_INT16:
            value=NP_UINT16(value)
        if quantity == "ZDR" and offset == 8.0: offset = -8 #A fix to bad offsets in some HDF5 files
        if (quantity == "RHOHV" or quantity == "QIDX") and type(value) is NP_UINT8: #To get around IRIS's non-linear 8 bit variables for these quantities.
            if value > 0:
                return sqrt((value-1)/253)
            else:
                return None
        if quantity == "HCLASS":
            return IrisMETEO(value)
        else:
            return value*gain+offset
    else:
        if value == rangefolding:
            return "RF"
        else:
            return None
