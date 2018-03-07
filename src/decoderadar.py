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

from __future__ import division
from bz2 import decompress
import translations
from bitprocessing import *
from coordinates import getcoords
from coordinates import parsecoords
from translations import fixArabic
import datetime
from math import radians as d2r, cos, pi, sqrt, copysign
import time
from h5py import File as HDF5Fail
import string
import os
import sys
from copy import deepcopy

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

class BUFR(): #BUFR radar data issued by Deutscher Wetterdienst through their open data output
    def __init__(self,path):
        
        python2 = True if sys.version_info[0] == 2 else False #Check for Python 2 in use
        andmed = file_read(path)
        if andmed[0:2] == b"BZ":
            andmed=decompress(andmed)
        andmed = andmed[andmed.find(b"BUFR"):] #Start decoding from START Marker
        if not python2:
            self.messageLength = (andmed[4] << 16) + (andmed[5] << 8) + (andmed[6])
        else:
            self.messageLength = (ord(andmed[4]) << 16) + (ord(andmed[5]) << 8) + (ord(andmed[6]))
        self.bufrVersion = andmed[7]
        self.isModified = False #Here and further - means the dataset has been processed at runtime.
        #IDENT SECTION (index 8-...)
        self.identSection={}
        self.vMax=[]
        self.rMax=[]
        self.identSection["originatingCentre"] = halfw(andmed[12:14], False)
        if not python2:
            self.identSection["length"] = (andmed[8] << 16) + (andmed[9] << 8) + andmed[10]
            self.identSection["masterTable"] = andmed[11]
            self.identSection["updateSequenceNumber"] = andmed[14]
            self.identSection["optionalSelection"] = andmed[15]
            self.identSection["dataCategory"] = andmed[16] #Returns 6 if radar data!
            self.identSection["dataCategorySubtype"] = andmed[17]
            self.identSection["versionNumberOfMasterTables"] = andmed[18]
            self.identSection["versionNumberOfLocalTables"] = andmed[19]
            self.identSection["year"] = andmed[20]
            self.identSection["month"] = andmed[21]
            self.identSection["day"] = andmed[22]
            self.identSection["hour"] = andmed[23]
            self.identSection["minute"] = andmed[24]
        else:
            self.identSection["length"] = (ord(andmed[8]) << 16) + (ord(andmed[9]) << 8) + ord(andmed[10])
            self.identSection["masterTable"] = ord(andmed[11])
            self.identSection["updateSequenceNumber"] = ord(andmed[14])
            self.identSection["optionalSelection"] = ord(andmed[15])
            self.identSection["dataCategory"] = ord(andmed[16])
            self.identSection["dataCategorySubtype"] = ord(andmed[17])
            self.identSection["versionNumberOfMasterTables"] = ord(andmed[18])
            self.identSection["versionNumberOfLocalTables"] = ord(andmed[19])
            self.identSection["year"] = ord(andmed[20])
            self.identSection["month"] = ord(andmed[21])
            self.identSection["day"] = ord(andmed[22])
            self.identSection["hour"] = ord(andmed[23])
            self.identSection["minute"] = ord(andmed[24])
        #Let's get rid of the first two sections
        andmed=andmed[8+self.identSection["length"]:]
        if self.identSection["optionalSelection"] != 0: #If Section two present
            if not python2:
                sectionTwoLength=(andmed[0] << 16) + (andmed[1] << 8) + andmed[2]
            else:
                sectionTwoLength=(ord(andmed[0]) << 16) + (ord(andmed[1]) << 8) + ord(andmed[2])
            andmed=andmed[sectionTwoLength:] #skip over
        #Section 3
        self.dataDescriptionSection={}
        if not python2:
            sectionThreeLength=(andmed[0] << 16) + (andmed[1] << 8) + andmed[2]
            self.dataDescriptionSection["numberofDataSubsets"]=halfw(andmed[4:6])
            bits=andmed[6]
        else:
            sectionThreeLength=(ord(andmed[0]) << 16) + (ord(andmed[1]) << 8) + ord(andmed[2])
            self.dataDescriptionSection["numberofDataSubsets"]=halfw(andmed[4:6])
            bits=ord(andmed[6])
        self.dataDescriptionSection["descriptors"]=[]

        for i in range(7,sectionThreeLength,2): self.dataDescriptionSection["descriptors"].append(BUFRDescriptor(andmed[i:i+2])) #Save all descriptors into list

        andmed=andmed[sectionThreeLength:] #Off to section 4 - data

        #DATA
        if not python2:
            self.dataSectionLength=(andmed[0] << 16) + (andmed[1] << 8) + andmed[2]
        self.rawData=andmed

        dataStream=BitStream(andmed[4:])

        scaleOverride=1
        bitWidthOverride=0

        quantityInFile=None

        descriptorPointer=0

        while descriptorPointer < len(self.dataDescriptionSection["descriptors"]):
            currentDescriptor=self.dataDescriptionSection["descriptors"][descriptorPointer]
            if currentDescriptor == (0, 1, 230):
                self.dataDescriptionSection["uniqueProductDescription"] = dataStream.getBytes(256).rstrip(b"\x00")
            elif currentDescriptor == (0, 30, 196):
                self.dataDescriptionSection["typeOfProduct"] = dataStream.getBits(16)
                quantityInFile = "DBZH" if self.dataDescriptionSection["typeOfProduct"] == 7 else "VRADH"
            elif currentDescriptor == (0, 1, 18):
                self.dataDescriptionSection["shortStationName"] = dataStream.getBytes(5).rstrip(b"\x00")
            elif currentDescriptor == (0, 1, 1):
                self.dataDescriptionSection["wmoBlockNumber"] = dataStream.getBits(7)
            elif currentDescriptor == (0, 1, 2):
                self.dataDescriptionSection["wmoStationNumber"] = dataStream.getBits(10)
            elif currentDescriptor == (0, 8, 21):
                self.dataDescriptionSection["timeSignificance"] = dataStream.getBits(5)
            elif currentDescriptor == (3, 1, 11):
                if "year" not in self.dataDescriptionSection:
                    self.dataDescriptionSection["year"] = dataStream.getBits(12)
                    self.dataDescriptionSection["month"] = dataStream.getBits(4)
                    self.dataDescriptionSection["day"] = dataStream.getBits(6)
                else:
                    self.dataDescriptionSection["sweepYear"] = dataStream.getBits(12)
                    self.dataDescriptionSection["sweepMonth"] = dataStream.getBits(4)
                    self.dataDescriptionSection["sweepDay"] = dataStream.getBits(6)
            elif currentDescriptor == (3, 1, 12):
                if "hour" not in self.dataDescriptionSection:
                    self.dataDescriptionSection["hour"] = dataStream.getBits(5)
                    self.dataDescriptionSection["minute"] = dataStream.getBits(6)
                else:
                    self.dataDescriptionSection["sweepHour"] = dataStream.getBits(5)
                    self.dataDescriptionSection["sweepMinute"] = dataStream.getBits(6)
            elif currentDescriptor[0:2] == (2, 2) and currentDescriptor[2] != 0:
                scaleOverride=10**(-(currentDescriptor[2]-128))
            elif currentDescriptor == (0, 4, 7):
                if "second" not in self.dataDescriptionSection:
                    self.dataDescriptionSection["second"] = round(dataStream.getBits(26) * 0.000001 * scaleOverride, 6)
                else:
                    self.dataDescriptionSection["sweepSecond"] = round(dataStream.getBits(26) * 0.000001 * scaleOverride, 6)
            elif currentDescriptor == (0, 8, 21):
                self.dataDescriptionSection["timeSignificance2"] = dataStream.getBits(5) * scale
            elif currentDescriptor == (2, 2, 0):
                scaleOverride=1
            elif currentDescriptor == (3, 1, 22):
                self.dataDescriptionSection["latitude"] = round((-9000000 + dataStream.getBits(25)) * 0.00001 ,6)
                self.dataDescriptionSection["longitude"] = round((-18000000 + dataStream.getBits(26)) * 0.00001 , 6)
                self.dataDescriptionSection["heightofStation"] = -400 + dataStream.getBits(15)
            elif currentDescriptor == (0, 1, 32):
                self.dataDescriptionSection["generatingApplication"] = dataStream.getBits(8)
            elif currentDescriptor == (0, 5, 230):
                self.dataDescriptionSection["nbins"] = dataStream.getBits(12)
            elif currentDescriptor == (0, 6, 230):
                self.dataDescriptionSection["maximumSizeOfYDimension"] = dataStream.getBits(12)
            elif currentDescriptor == (0, 7, 230):
                self.dataDescriptionSection["elevationsCount"] = dataStream.getBits(12)
            elif currentDescriptor == (0, 21, 203):
                self.dataDescriptionSection["rstart"] = dataStream.getBits(14)*10/1000 #Scale = -1 ?
            elif currentDescriptor == (0, 21, 204):
                self.dataDescriptionSection["azimuthOffset"] = dataStream.getBits(12)/10
            elif currentDescriptor == (0, 2, 135):
                self.dataDescriptionSection["antennaElevation"] = round((dataStream.getBits(15)-9000)*0.01,3)
            elif currentDescriptor == (0, 7, 231):
                self.dataDescriptionSection["elNumber"] = dataStream.getBits(16)
            elif currentDescriptor == (0, 2, 134):
                self.dataDescriptionSection["a1gate"] = dataStream.getBits(16)*0.01
            elif currentDescriptor == (0, 21, 236):
                self.dataDescriptionSection["extendedNyquistVelocity"] = dataStream.getBits(8)
            elif currentDescriptor == (0, 21, 237):
                self.dataDescriptionSection["highNyquistVelocity"] = dataStream.getBits(8)
            elif currentDescriptor == (0, 2, 194):
                self.dataDescriptionSection["dualPRFRatio"] = dataStream.getBits(4)
            elif currentDescriptor[0:2] == (2, 1) and currentDescriptor[2] != 0:
                bitWidthOverride = currentDescriptor[2]-128
            elif currentDescriptor == (0, 25, 1):
                self.dataDescriptionSection["rangeGateLength"] = dataStream.getBits(6 + bitWidthOverride)
            elif currentDescriptor == (2, 1, 0):
                bitWidthOverride = 0
            elif currentDescriptor == (0, 25, 2):
                self.dataDescriptionSection["numberOfGatesAveraged"] = dataStream.getBits(4 + bitWidthOverride)
            elif currentDescriptor == (0, 25, 3):
                self.dataDescriptionSection["numberOfIntegratedPulses"] = dataStream.getBits(8)
            elif currentDescriptor == (0, 25, 4):
                self.dataDescriptionSection["echoProcessing"] = dataStream.getBits(2)
            elif currentDescriptor == (0, 21, 201):
                self.dataDescriptionSection["rscale"] = dataStream.getBits(14)*0.001 #Converting to km! BUFR has in meters
            elif currentDescriptor == (0, 21, 202):
                self.dataDescriptionSection["azimuthalResolution"] = dataStream.getBits(8)*0.1
            elif currentDescriptor == (0, 2, 193):
                self.dataDescriptionSection["antennaRotationDirection"] = dataStream.getBits(2)
            elif currentDescriptor == (0, 29, 1):
                self.dataDescriptionSection["projectionType"] = dataStream.getBits(3)
            elif currentDescriptor == (0, 29, 2):
                self.dataDescriptionSection["coordinateGridType"] = dataStream.getBits(3)
            elif currentDescriptor == (0, 30, 194):
                self.dataDescriptionSection["nBinsAlongRadial"] = dataStream.getBits(12)
            elif currentDescriptor == (0, 30, 195):
                self.dataDescriptionSection["nrays"] = dataStream.getBits(11)
            elif currentDescriptor == (1, 18, 0) or (1, 10, 0):
                azimuthsInData=dataStream.getBits(16)
                self.azimuths=[[]]
                self.type="BUFR"
                self.elevations=[[]]
                self.nominalElevations=[self.dataDescriptionSection["antennaElevation"]]
                self.quantities=[[quantityInFile]]
                startTime=datetime.datetime(self.dataDescriptionSection["sweepYear"],self.dataDescriptionSection["sweepMonth"],self.dataDescriptionSection["sweepDay"],self.dataDescriptionSection["sweepHour"],self.dataDescriptionSection["sweepMinute"],int(self.dataDescriptionSection["sweepSecond"]),int((self.dataDescriptionSection["sweepSecond"]%1)*1000000))
                self.times=[[startTime]]
                self.elevationNumbers=[self.dataDescriptionSection["elNumber"]]
                self.headers={"timestamp":datetime.datetime(self.dataDescriptionSection["year"],self.dataDescriptionSection["month"],self.dataDescriptionSection["day"],self.dataDescriptionSection["hour"],self.dataDescriptionSection["minute"],int(self.dataDescriptionSection["second"]),int((self.dataDescriptionSection["second"]%1)*1000000)),
                              "latitude": self.dataDescriptionSection["latitude"],
                              "longitude": self.dataDescriptionSection["longitude"],
                              "height":self.dataDescriptionSection["heightofStation"]}

                #Guessing PRF based on DWD documentation and elevation number
                highprfs=[800,800,800,800,800,800,1200,2410,2410,2410]
                lowprfs=[600,600,600,600,600,600,800,2410,2410,2410]#
                if self.dataDescriptionSection["extendedNyquistVelocity"] < 20: #If extended Nyquist velocity is very low, assume Single PRF scan
                    highprf=600
                    lowprf=600
                else:
                    highprf=highprfs[self.dataDescriptionSection["elNumber"]]
                    lowprf=lowprfs[self.dataDescriptionSection["elNumber"]]
                    
                vMaxMult=((highprf/lowprf)%1)**-1 if not highprf == lowprf else 1
                self.rMax.append(299792.458/highprf/2)
                self.wavelength=0.053154691134751776 #Based on frequency of 5640 declared in OPERA database, using c = 299792458 m/s
                NI=highprf*self.wavelength/4
                self.vMax.append(NI)

                    
                self.data=[{quantityInFile:{"data":[],"highprf":highprf,"lowprf":lowprf,"gain":0.1,"offset":-32.0 if quantityInFile == "DBZH" else -409.6, "undetect":8191, "nodata":0, "rangefolding":1,"rscale":self.dataDescriptionSection["rscale"],"rstart":self.dataDescriptionSection["rstart"]}}]
                for i in range(azimuthsInData):
                    timePeriodOrDisplacement = dataStream.getBits(16)*0.001
                    self.times[-1].append(startTime+datetime.timedelta(seconds=timePeriodOrDisplacement))
                    az = dataStream.getBits(16)*0.01
                    self.azimuths[0].append(az)
                    el = (dataStream.getBits(15)-9000)*0.01
                    self.elevations[0].append(el)
                    if quantityInFile == "DBZH":
                        reference = convertToSigned(dataStream.getBits(10),10)*0.1
                    dataRow = []
                    rangeBins = int(dataStream.getBits(16))
                    for j in range(rangeBins):
                        if quantityInFile == "DBZH":
                            addition = int((reference+32)*10) #In the event default offset is differnet from -32
                            dataRow.append(dataStream.getBits(11) + addition)
                        else: #We're dealing with velocity data
                            dataRow.append(dataStream.getBits(13))
                    self.data[0][quantityInFile]["data"].append(dataRow)
                break
            descriptorPointer+=1
        return None
    def prf(self,elNumber):
        
        return [highprfs[elNumber],lowprfs[elNumber]]

class NEXRADLevel3():
    #RELEVANT NEXRAD ICD: 2620001U
    def __init__(self, path):
        python2 = True if sys.version_info[0] == 2 else False #Check for Python 2 in use
        stream = file_read(path) #Load the data file
        self.type = "NEXRAD3"
        self.headers = {}
        self.data = [{}]
        self.isModified = False
        self.azimuths = []
        self.headers["rstart"] = 0
        self.headers["icao"] = None
        if stream.find(b"SDUS") != -1: #If WMO headers present
            self.headers["icao"] = stream[7:11]
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
        self.times=[[self.headers["volumeScanTime"]]]
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
        self.data[0][self.headers["productCode"]]["undetect"] = 0 if self.headers["productCode"] != "HCLASS" else -999
        self.data[0][self.headers["productCode"]]["nodata"] = 0 
        self.data[0][self.headers["productCode"]]["rangefolding"] = 1
        self.data[0][self.headers["productCode"]]["rscale"]=1 if self.headers["productCode"]=="DBZH" else 0.25

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
                    val=bins[j] if not python2 else ord(bins[j])
                    if val == 0: row.append(-999)
                    elif val > 0 and val < 140: row.append(int(val/10-1))
                    elif val >= 140: row.append(int(val/10-4))
            else:
                for j in range(p,p+amt):
                    val=bins[j] if not python2 else ord(bins[j])
                    row.append(val)
            self.data[0][self.headers["productCode"]]["data"].append(row)
            p+=amt
        
        del(stream) #Garbage collection
        
class NEXRADLevel2():
    ##RELEVANT NEXRAD ICD'S: 2620002P, 2620010E
    def __init__(self,path):
        python2 = True if sys.version_info[0] == 2 else False #Check whether we are on Python 2
        sisu=file_read(path)
        self.isModified = False
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
            self.wavelength=None
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
                    messageType=ord(sisu[ptr+15]) if python2 else sisu[ptr+15]
                    if messageSize != 0 and messageSize > 0:
                        if messageType != 31:
                            ptr+=2432
                        else:
                            ptr+=messageSize*2+12
                    else:
                        while sisu[ptr+12] in [0,"\0"]: ptr+=2432
                msgptr=0 #Pointer within a message
                while msgptr < len(fullmsg):
                    msg=fullmsg[msgptr:msgptr+messageSize*2+12]
                    if compressionControlWord:
                        messageType=ord(msg[3]) if python2 else msg[3]
                    if messageType == 31:
                        #azNumber=halfw(msg[26:28])
                        collectionTime=datetime.datetime.utcfromtimestamp((halfw(msg[24:26],False)-1)*86400+word(msg[20:24])/1000.0)
                        azAngle=floating(msg[28:32])
                        #azimuthResolutionSpacing=msg[36]*0.5
                        #radialStatus=msg[37]
                        elevationNumber=ord(msg[38]) if python2 else msg[38]
                        elIndex=elevationNumber-1
                        elevationAngle=floating(msg[40:44])
                        if elevationNumber not in self.elevationNumbers:
                            self.elevationNumbers.append(elevationNumber)
                            self.data.append({})
                            azimuthCentres.append([])
                            self.elevations.append([])
                            self.quantities.append([])
                            self.times.append([])

                            rdcPointer=word(msg[56:60])+16
                            rdcSize=msg[rdcPointer+4:rdcPointer+6]
                            rMax=halfw(msg[rdcPointer+6:rdcPointer+8])*0.1
                            vMax=halfw(msg[rdcPointer+16:rdcPointer+18])*0.01
                            PRF=round(150000/rMax)
                            if not self.wavelength:
                                self.wavelength=vMax*4/PRF
                            self.rMax.append(rMax)
                            self.vMax.append(vMax)
                            
                        self.times[-1].append(collectionTime)
                        
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
                            self.headers["height"]=halfw(msg[vdcPointer+16:vdcPointer+18])
                            self.headers["feedhornHeight"]=halfw(msg[vdcPointer+18:vdcPointer+20])
                        #Grabbing unscaled data. Scaling will be done real-time when the particular sweep gets displayed.
                        for adds in range(60,84,4):
                            quantityPointer=word(msg[adds:adds+4],False)
                            if quantityPointer:
                                x=quantityPointer+16
                                quantityType=msg[x]
                                quantityName=convertNEXRAD2Code(msg[x+1:x+4].decode("utf-8"))
                                dataQuantityGatesNr=halfw(msg[x+8:x+10])
                                dataWordSize=ord(msg[x+19]) if python2 else msg[x+19]
                                dataGain=1/floating(msg[x+20:x+24]) #Converting to Gain/Offset values as known in HDF5 files.
                                dataOffset=-floating(msg[x+24:x+28])*dataGain
                                if quantityName not in self.data[-1]:
                                    rscale=halfw(msg[x+12:x+14])/1000
                                    self.data[elIndex][quantityName]={"data":[],"gain":dataGain,"offset":dataOffset,"undetect":0,"rangefolding":1,"nodata":2**dataWordSize,"rscale":rscale,"rstart":halfw(msg[x+10:x+12])/1000-rscale/2,"highprf":PRF,"lowprf":PRF}
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
            self.headers["latitude"],self.headers["longitude"],self.headers["height"]=nexradtable.table[icao]
            self.headers["timestamp"]=fileCreated
            self.headers["icao"]=icao.encode("utf-8")
            self.wavelength=None
            ptr=24
            fileSize=len(sisu)
            while ptr < fileSize:
                messageSize=halfw(sisu[ptr+12:ptr+14],False)
                fullmsg=sisu[ptr+12:ptr+2432]
                messageType=ord(sisu[ptr+15]) if python2 else sisu[ptr+15]
                if messageType == 1:
                    rMax=halfw(fullmsg[22:24])/10
                    PRF=round(150000/rMax)
                    azAngle=(halfw(fullmsg[24:26])/8)*(180/4096) % 360
                    elAngle=(halfw(fullmsg[30:32])/8)*(180/4096)
                    elNumber=halfw(fullmsg[32:34])
                    elIndex=elNumber-1
                    collectionTime=datetime.datetime.utcfromtimestamp((halfw(fullmsg[20:22])-1)*86400+word(fullmsg[16:20])/1000)
                    if elNumber not in self.elevationNumbers:
                            self.elevationNumbers.append(elNumber)
                            vMax=halfw(fullmsg[76:78])/100.0
                            if not self.wavelength:
                                self.wavelength=(8000*rMax*vMax)/300000000
                            self.rMax.append(rMax)
                            self.vMax.append(vMax)
                            self.data.append({})
                            self.times.append([])
                            azimuthCentres.append([])
                            self.elevations.append([])
                            self.quantities.append([])
                    self.times[-1].append(collectionTime)
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
                                self.data[elIndex][quantity]={"data":[],"gain":gain,"offset":offset,"undetect":0,"rangefolding":1,"nodata":0,"rscale":rscale,"rstart":rstart-rscale/2,"highprf":PRF, "lowprf": PRF}
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
        del(sisu) #Garbage collecting - this file can be bigly!
                
class HDF5():
    def __init__(self,path):
        self.type="HDF5"
        self.headers={}
        self.nominalElevations=[]
        self.azimuths=[]
        self.data=[]
        self.times=[]
        self.elevations=[]
        self.quantities=[]
        self.isModified = False

        andmed=HDF5Fail(path,"r") #Load the data file

        if "what" in andmed:
            self.isODIM=True
            mainwhatattrs=andmed["/what"].attrs
            mainwhereattrs=andmed["/where"].attrs

            self.headers["version"]=mainwhatattrs.get("version")
            if type(mainwhatattrs.get("date")) is np.ndarray:
                ajastring=mainwhatattrs.get("date")[0]+mainwhatattrs.get("time")[0]
            else:
                ajastring=mainwhatattrs.get("date")+mainwhatattrs.get("time")
            self.source = mainwhatattrs.get("source")
            self.headers["timestamp"]=datetime.datetime.strptime(ajastring.decode("utf-8"),"%Y%m%d%H%M%S")
            self.headers["latitude"]=float(mainwhereattrs.get(u"lat"))
            self.headers["longitude"]=float(mainwhereattrs.get(u"lon"))
            self.headers["height"]=mainwhereattrs.get(u"height")
            self.wavelength=andmed["how"].attrs.get("wavelength")
            if self.wavelength: self.wavelength /= 100.0
            
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
                        if type(whatattrs.get("enddate")) is np.ndarray: #Grr. See post-nrays-get if.
                            endtimestring=whatattrs.get("enddate")[0]+whatattrs.get("endtime")[0]
                        else:
                            endtimestring=whatattrs.get("enddate")+whatattrs.get("endtime")
                                
                        starttime=datetime.datetime.strptime(starttimestring.decode("utf-8"),"%Y%m%d%H%M%S")
                        endtime=datetime.datetime.strptime(endtimestring.decode("utf-8"),"%Y%m%d%H%M%S")
                        self.times.append([starttime,endtime])
                        
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
                        "data": np.array(andmed[name+str(i)+"/data"]),
                        "dataType": type(andmed[name+str(i)+"/data"][0]),
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
                    datasethow=andmed[datasetpath+"/how"].attrs if "how" in andmed[datasetpath] else None
                    elevation=datasetwhere.get("elangle")
                    if type(elevation) is np.ndarray: elevation=elevation[0]
                    elevation=round(elevation,2) #Round just in case there are floating point inaccuracies in the original data.
                    nrays=datasetwhere.get("nrays")
                    if nrays is None: nrays = 360 #If no nrays defined assume 360. Workaround for personal stopgap HDF5 creations from the past)
                    if type(nrays) is np.ndarray: nrays=nrays[0] #Oh brother. Value saved as array again.
                    
                    #if elevation not in self.nominalElevations: ##DO I REALLY NEED THIS?
                    noStartTime=False #True if no start time defined in data(e.g my internal stopgap HDF5 creations)
                    if type(datasetwhat.get("startdate")) is np.ndarray: #Grr. See post-nrays-get if.
                        starttimestring=datasetwhat.get("startdate")[0]+datasetwhat.get("starttime")[0]
                        starttimestring=datasetwhat.get("enddate")[0]+datasetwhat.get("endtime")[0] #Well, this is probably in the same condition
                    else:
                        starttimedate=datasetwhat.get("startdate")
                        starttimetime=datasetwhat.get("starttime")
                        if not starttimedate and not starttimetime: ## Workaround for my internally generated HDF5s derived from GeoTIFF images
                            noStartTime=True
                        else:
                            starttimestring=datasetwhat.get("startdate")+datasetwhat.get("starttime")
                            endtimestring=datasetwhat.get("enddate")+datasetwhat.get("endtime")
                    if not noStartTime:
                        starttime=datetime.datetime.strptime(starttimestring.decode("utf-8"),"%Y%m%d%H%M%S")
                        endtime=datetime.datetime.strptime(endtimestring.decode("utf-8"),"%Y%m%d%H%M%S")
                    else:
                        starttime=None
                        endtime=None
                    self.times.append([starttime,endtime])
                    self.nominalElevations.append(elevation)
                    if datasethow:
                        if "startazA" in datasethow:
                            self.azimuths.append(datasethow.get("startazA"))
                            self.elevations.append(datasethow.get("elangles"))
                        else:
                            self.azimuths.append(list(map(lambda x,y=nrays:360*x/y,range(nrays))))
                    self.data.append({})
                    self.quantities.append([])
                    for da in range(datacount):
                        d="data"+str(da+1)
                        datawhat=andmed[datasetpath+"/"+d+"/what"].attrs
                        datahow=andmed[datasetpath+"/"+d+"/how"].attrs if "how" in andmed[datasetpath+"/"+d] else None
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

                        rstart = datasetwhere.get("rstart")
                        if rstart == None: rstart=0 #Workaround for... see above!

                        rscale=datasetwhere.get("rscale")
                        if rscale == None: #Workaround for stuff like old NEXRAD!
                            rscale=andmed[datasetpath+"/"+d+"/where"].attrs.get("rscale")
                            
                        self.data[-1][quantity]={
                            "data":np.array(andmed[datasetpath+"/"+d+"/data"]),
                            "dataType": type(andmed[datasetpath+"/"+d+"/data"][0][0]),
                            "rscale":float(rscale)/1000.0,
                            "rstart":float(rstart),
                            "highprf":highprf,
                            "lowprf":lowprf,
                            "offset":float(datawhat.get("offset")),
                            "gain":float(datawhat.get("gain")),
                            "nodata":float(datawhat.get("nodata")),
                            "undetect":float(datawhat.get("undetect"))
                            }
                        if datahow:
                            if "rangefolding" in datahow:
                                self.data[-1][quantity]["rangefolding"]=datahow.get("rangefolding")
            self.elevationNumbers=list(range(len(self.nominalElevations)))
        else: #Uh oh! Looks like this is not ODIM! KNMI?
            self.isODIM=False
            self.elevationNumbers=[]
            if "overview" in andmed: #Starts to look like KNMI data.
                
                if "product_group_name" in andmed["overview"].attrs: #It is KNMI data.
                    self.headers["timestamp"]=knmiDateTime(andmed["overview"].attrs.get("product_datetime_start"))
                    self.headers["longitude"],self.headers["latitude"]=andmed["radar1"].attrs.get("radar_location")
                    radarSiteName=andmed["radar1"].attrs.get("radar_name")
                    if radarSiteName == b"Herwijnen":
                        self.wavelength = 0.05322074525
                        self.headers["height"] = 27.7
                        self.source = b"NOD:nlhrw"
                    elif radarSiteName == b"DenHelder":
                        self.wavelength = 0.05329643697
                        self.headers["height"] = 51
                        self.source = b"NOD:nldhl"
                    elif radarSiteName == b"DeBilt":
                        self.wavelength = 0.05308880077
                        self.headers["height"] = 44
                        self.source = b"NOD:ndlbl"
                    
                    scanGroupsAmount=andmed["overview"].attrs.get("number_scan_groups")[0]
                    for i in range(scanGroupsAmount): #Radar sweeps seem to be in opposite order
                        scanname="scan%i" %(i+1)
                        scanattrs=andmed[scanname].attrs
                        self.times.append([knmiDateTime(scanattrs.get("scan_datetime"))])
                        self.elevationNumbers.append(i)
                        self.nominalElevations.append(round(scanattrs.get("scan_elevation")[0],2))
                        
                        highPRF=scanattrs.get("scan_high_PRF")[0]
                        lowPRF=scanattrs.get("scan_low_PRF")[0]
                        if lowPRF == 0: lowPRF = highPRF #Just to make it similar to what I have seen in ODIM files
                        rscale=scanattrs.get("scan_range_bin")[0]

                        azimuthslist=list(map(lambda x,y=scanattrs.get("scan_azim_bin")[0]:x*y,range(scanattrs.get("scan_number_azim")[0])))
                        
                        KNMIQtys=["Z","Zv","V","Vv","W","Wv","uZ","uZv","KDP","PhiDP","RhoHV","SQI","SQIv"]
                        ODIMQtys=["DBZH","DBZV","VRADH","VRADV","WRAD","WRADV","TH","TV","KDP","PHIDP","RHOHV","SQI","SQIV"] #very rough guess
                        nodata=andmed[scanname]["calibration"].attrs.get("calibration_missing_data")

                        scandata={}
                        for j in range(len(KNMIQtys)):
                            gainoffset=andmed[scanname]["calibration"].attrs.get("calibration_"+KNMIQtys[j]+"_formulas")
                            gain=float(gainoffset[gainoffset.find(b"GEO")+4:gainoffset.find(b"*PV")])
                            offset=float(gainoffset[gainoffset.find(b"+")+1:])
                            scandata[ODIMQtys[j]]={"undetect":0,
                                                   "nodata":0,
                                                   "rstart":0,
                                                   "rscale":rscale,
                                                   "highprf":highPRF,
                                                   "lowprf":lowPRF,
                                                   "rangefolding": -999999,
                                                   "gain":gain,
                                                   "offset":offset,
                                                   "data":np.array(andmed[scanname]["scan_"+KNMIQtys[j]+"_data"])}
                        self.data.append(scandata)
                        self.azimuths.append(azimuthslist)
                        self.quantities.append(ODIMQtys)
                else:
                    raise FileFormatError("This is not an ODIM H5 file and neither looks it like KNMI's")
                    
        andmed.close()

def padData(data,fillValue=0):
    highestAmount=0
    needFilling=False
    for i in data:
        if len(i) != highestAmount:
            needFilling=True
        if len(i) > highestAmount:
            if highestAmount > 0: needFilling=True
            highestAmount=len(i)
    if needFilling:
        for j in range(len(data)):
            if len(data[j]) < highestAmount:
                for k in range(highestAmount-len(data[j])):
                    data[j].append(fillValue)
    return data

def addRmax(dataObject,elIndex,az0,az1,r0,r1):
    for quantity in dataObject.quantities[elIndex]:
        prf=dataObject.data[elIndex][quantity]["highprf"]

        rstart = dataObject.data[elIndex][quantity]["rstart"]
        rscale = dataObject.data[elIndex][quantity]["rscale"]
        nodata = dataObject.data[elIndex][quantity]["nodata"]
        
        rmax=299792.458/prf/2
        r0new=r0+rmax
        r1new=r1+rmax

        data = dataObject.data[elIndex][quantity]["data"]
        dataisndarray = False #We'll make it back to an array later since 8 bit products generated with IRIS are not necessarily linear and checks for that require type check
        if type(data) is np.ndarray and dataObject.type == "HDF5":
            data=data.tolist()
            dataisndarray = True
        azimuths = dataObject.azimuths[elIndex]
        
        for i in range(len(data)):
            r=data[i]
            if type(r) is not list:
                r = r.tolist()
            curaz=azimuths[i]
            firstBinOffset=int((rstart/rscale)) #Correct range to a particular bin!
            slicestart=int(r0/rscale)-firstBinOffset
            sliceend=int(r1/rscale)-firstBinOffset
            if slicestart < 0: slicestart=0
            if sliceend < 0: sliceend=0 #Seems like overkill but these days always pays to check everything that is related to user input
            rmaxbins=int(round(rmax/rscale)) #Amount of bins that coorespond to Rmax
            paddingamt=int(round(r1new/rscale)-firstBinOffset)-len(r)
            
            if az1-az0 <= 180:
                processingCondition = curaz >= az0 and curaz < az1
            else:
                processingCondition = curaz < az0 or curaz >= az1
            if processingCondition:
                for j in range(paddingamt):
                    data[i].append(nodata)
                for k in range(slicestart,sliceend,1):
                    if data[i][k+rmaxbins] == nodata: #Let's not copy empty areas to Rmax
                        data[i][k+rmaxbins]=data[i][k]
                        data[i][k]=nodata
        dataObject.data[elIndex][quantity]["data"] = padData(data, nodata)
        
    return dataObject

def dealiasVelocities(dataObject,quantity,index, passesList=[1,2,3,2,1]):
    wavelength = dataObject.wavelength
    highprf = dataObject.data[index][quantity]["highprf"]
    lowprf = dataObject.data[index][quantity]["lowprf"]
    gain = dataObject.data[index][quantity]["gain"]
    zeroValue = (dataObject.data[index][quantity]["offset"]/gain)*-1
    nodata = dataObject.data[index][quantity]["nodata"]
    undetect = dataObject.data[index][quantity]["undetect"]
    dualPRF = False if highprf == lowprf else True
    threshold = 0.5 if not dualPRF else 0.6
    maxGapSize = 0 if dualPRF else 5000 #Maximum gap at which to still trust the previous valid measurement
    
    rangefolding = None if not "rangefolding" in dataObject.data[index][quantity] else dataObject.data[index][quantity]["rangefolding"]
    vMaxIntervalHigh = round(wavelength*highprf*0.5/gain) #Converting to data values steps
    vMaxIntervalLow = round(wavelength*lowprf*0.5/gain)
    if not isinstance(dataObject.data[index][quantity]["data"][0],list):
        newData = [x.tolist() for x in dataObject.data[index][quantity]["data"]]
    else:
        newData = [x for x in dataObject.data[index][quantity]["data"]]
    numberOfRays = len(dataObject.data[index][quantity]["data"])
    numberOfBins = len(dataObject.data[index][quantity]["data"][0])
    iRanges = [range(numberOfRays), range(numberOfBins), range(numberOfRays), range(numberOfBins)]
    jRanges = [numberOfBins, numberOfRays, numberOfBins, numberOfRays]
    
    for passnr in passesList:
        algusaeg=time.time()
        iRange = iRanges[passnr]
        jRange = jRanges[passnr]
        print("Dealiasing pass - type", passnr+1)
        if passnr == 3: #If doing an along-an-azimuth dealias counter clockwise  - thus reverse the list
            newData.reverse()
        for i in iRange:
        #    azPraegu = dataObject.azimuths[index][i % numberOfRays]
        #    if azPraegu > 265.5 or azPraegu < 265: continue
      #      print("--------------------------",azPraegu)
            prev = None
            gapSize = 0 #Size of gap between current and previous bin
            j = 0
            #If azimuthal check:
            #First do a survey trying to find a region where the wind is perpendicular to the radar beam.
            if passnr in [1, 3]:
                for az1 in range(0, -numberOfRays, -1):
                    if abs(newData[az1][i]-zeroValue) < 3/gain:
                        j += az1
                        jRange = jRanges[passnr] + az1
                        break
            if passnr == 2:
                newData[i].reverse() #Reverse values in bin
                newData[i-1].reverse()
            while j < jRange:
                if passnr not in [1, 3]:
                    current=newData[i][j]
                else:
                    current=newData[j][i]
                if current != nodata and current != undetect and current != rangefolding:# and j > 5:
                    if prev != None:
                        diffFromPrev=current-prev

                        if gapSize > maxGapSize:
                            nearby = newData[i][(j+2) % numberOfBins] if passnr not in [1, 3] else newData[(j + 1) % numberOfRays][i-1]
                            if nearby != nodata and nearby != undetect and nearby != rangefolding: 
                                diffFromNextTo=current-nearby
                                if abs(diffFromNextTo) < abs(diffFromPrev):
                                    diffFromPrev=diffFromNextTo
                        else:
                            nearby = (newData[i-1][j-1]) if passnr not in [1, 3] else newData[j-1][i-1]
                            if nearby != nodata and nearby != undetect and nearby != rangefolding: 
                                diffFromNextTo=current-nearby
                                if abs(diffFromNextTo) < abs(diffFromPrev):
                                    diffFromPrev=diffFromNextTo
                        if diffFromPrev > vMaxIntervalLow*threshold or diffFromPrev < -vMaxIntervalLow*threshold:
                            ratio1=diffFromPrev/vMaxIntervalHigh
                            ratioweight1 = abs(((ratio1*2) % 1) - 0.5)
                            if dualPRF:
                                ratio2=diffFromPrev/vMaxIntervalLow
                                ratioweight2 = abs(((ratio2*2) % 1) - 0.5)
                            else:
                                ratioweight2 = ratioweight1

                            if ratioweight1 >= ratioweight2:
                                multiplier = round(ratio1)
                                if multiplier == 0: multiplier = copysign(2, ratio1)
                                current -= int(vMaxIntervalHigh * multiplier)
                            else:
                                multiplier = round(ratio2)
                                if multiplier == 0: multiplier = copysign(2, ratio1)
                                current -= int(vMaxIntervalLow * multiplier)
                                
                            if passnr not in [1, 3]:
                                newData[i][j]=current
                            else:
                                newData[j][i]=current
                    
                    prev = current

                    gapSize = 0
                else:
                    gapSize += 1
                j += 1
            if passnr == 2:
                newData[i].reverse() #Reverse back
                newData[i-1].reverse() #Reverse back
        if passnr == 3: #Reverse back
            newData.reverse()
        print("Pass duration: %f seconds" %(time.time()-algusaeg))
    firstTry = False
    if quantity == "VRAD":  #Assuming horizontal polarisation by default
        newQuantity = "VRADDH"
        firstTry = True
    elif not "VRADD" in quantity and quantity != "VRAD":
        newQuantity = quantity.replace("VRAD","VRADD")
        firstTry = True
    else:
        newQuantity = quantity
    if firstTry:
        if newQuantity not in dataObject.quantities[index]: dataObject.quantities[index].append(newQuantity)
        dataObject.data[index][newQuantity] = deepcopy(dataObject.data[index][quantity])
    dataObject.data[index][newQuantity]["data"] = newData


    return dataObject, newQuantity


def dumpVolume(dataObject=None,outputFile=None):
    '''Dumps NEXRAD of BUFR data object to disk in ODIM H5 format'''
    if dataObject and outputFile:
        file=HDF5Fail(outputFile,"w")
        file.attrs.create("Conventions",b"ODIM_H5/V2_2")
        #Top level what
        file.create_group("what")
        file["what"].attrs.create("object",b"PVOL" if len(dataObject.nominalElevations) > 1 else b"SCAN")
        file["what"].attrs.create("version",b"H5rad 2.2")
        file["what"].attrs.create("date",dataObject.headers["timestamp"].strftime("%Y%m%d").encode("utf-8"))
        file["what"].attrs.create("time",dataObject.headers["timestamp"].strftime("%H%M%S").encode("utf-8"))
        if dataObject.type == "NEXRAD2" or dataObject.type == "NEXRAD3":
            file["what"].attrs.create("source",b"NOD:us"+dataObject.headers["icao"][1:].lower())
        elif dataObject.type == "BUFR":
            file["what"].attrs.create("source",b"WMO:"+str(dataObject.dataDescriptionSection["wmoBlockNumber"]).zfill(2).encode("utf-8")+str(dataObject.dataDescriptionSection["wmoStationNumber"]).zfill(3).encode("utf-8"))
        elif dataObject.type == "HDF5":
            file["what"].attrs.create("source",dataObject.source)
        #Top level where
        file.create_group("where")
        file["where"].attrs.create("lat",dataObject.headers["latitude"])
        file["where"].attrs.create("lon",dataObject.headers["longitude"])
        file["where"].attrs.create("height",dataObject.headers["height"])
        file.create_group("how")
        file["how"].attrs.create("software",b"TRV")
        if not dataObject.type=="NEXRAD3":
            file["how"].attrs.create("wavelength",dataObject.wavelength*100)

        datasetCounter=1
        for i in range(len(dataObject.nominalElevations)):
            datasetName = "dataset%i" % (datasetCounter)
            file.create_group(datasetName)

            file[datasetName].create_group("what")
            file[datasetName].create_group("where")
            file[datasetName].create_group("how")

            file[datasetName]["what"].attrs.create("product",b"SCAN")
            file[datasetName]["what"].attrs.create("startdate",dataObject.times[i][0].strftime("%Y%m%d").encode("utf-8"))
            file[datasetName]["what"].attrs.create("starttime",dataObject.times[i][0].strftime("%H%M%S").encode("utf-8"))
            file[datasetName]["what"].attrs.create("enddate",dataObject.times[i][-1].strftime("%Y%m%d").encode("utf-8"))
            file[datasetName]["what"].attrs.create("endtime",dataObject.times[i][-1].strftime("%H%M%S").encode("utf-8"))
            
            file[datasetName]["where"].attrs.create("elangle", dataObject.nominalElevations[i])
            firstMomentInElevation=dataObject.quantities[i][0] #First moment in this elevation, we'll use this for grabbing some metadata

            file[datasetName]["where"].attrs.create("a1gate", 0)

            if not dataObject.type == "NEXRAD3" and len(dataObject.elevations) > 0:
                file[datasetName]["how"].attrs.create("elangles", dataObject.elevations[i])
                
            file[datasetName]["how"].attrs.create("startazA", dataObject.azimuths[i])
            file[datasetName]["how"].attrs.create("stopazA", dataObject.azimuths[i][1:]+[dataObject.azimuths[i][0]])
            if dataObject.type == "NEXRAD2" or dataObject.type == "BUFR":
                file[datasetName]["how"].attrs.create("highprf",dataObject.data[i][firstMomentInElevation]["highprf"])
                file[datasetName]["how"].attrs.create("lowprf",dataObject.data[i][firstMomentInElevation]["lowprf"])
                file[datasetName]["how"].attrs.create("NI",dataObject.data[i][firstMomentInElevation]["highprf"]*dataObject.wavelength/4)
            dataCounter=1

            nraysList=[]
            nbinsList=[]
            rscaleList=[]
            rstartList=[]

            
            for j in dataObject.quantities[i]:
                dataName = "data%i" % dataCounter
                file[datasetName].create_group(dataName)
                file[datasetName][dataName].create_group("what")
                file[datasetName][dataName].create_group("how")
                file[datasetName][dataName].create_group("where")

                padData(dataObject.data[i][j]["data"]) #Ensure we are in uniform shape
                nbins = len(dataObject.data[i][j]["data"][0])

                rstartList.append(dataObject.data[i][j]["rstart"])
                rscaleList.append(dataObject.data[i][j]["rscale"]*1000)
                nrays = len(dataObject.data[i][j]["data"])
                nraysList.append(nrays)
                nbins = len(dataObject.data[i][j]["data"][0])
                nbinsList.append(nbins)
                
                file[datasetName][dataName]["what"].attrs.create("gain",dataObject.data[i][j]["gain"])
                file[datasetName][dataName]["what"].attrs.create("offset",dataObject.data[i][j]["offset"])
                file[datasetName][dataName]["what"].attrs.create("undetect",dataObject.data[i][j]["undetect"])
                file[datasetName][dataName]["what"].attrs.create("nodata",dataObject.data[i][j]["nodata"])
                file[datasetName][dataName]["what"].attrs.create("quantity",j.encode("utf-8"))
                if "rangefolding" in dataObject.data[i][j]: file[datasetName][dataName]["how"].attrs.create("rangefolding",dataObject.data[i][j]["rangefolding"])
                file[datasetName][dataName].create_dataset("data", (nrays,nbins), data=padData(dataObject.data[i][j]["data"]), compression="gzip")
                
                dataCounter+=1

            #Here's workaround for datasets where shape and rscale etc can vary even between different quantities, yes - I mean NEXRAD Level 2!
            if max(nraysList) == min(nraysList):
                file[datasetName]["where"].attrs.create("nrays", nraysList[0])
                nraysOkay = True
            else:
                nraysOkay = False

            if max(nbinsList) == min(nbinsList):
                file[datasetName]["where"].attrs.create("nbins", nbinsList[0])
                nbinsOkay = True
            else:
                nbinsOkay = False

            if max(rscaleList) == min(rscaleList):
                file[datasetName]["where"].attrs.create("rscale", rscaleList[0])
                rscaleOkay = True
            else:
                rscaleOkay = False

            if max(rstartList) == min(rstartList):
                file[datasetName]["where"].attrs.create("rstart", rstartList[0])
                rstartOkay = True
            else:
                rstartOkay = False

            for k in range(len(nraysList)):
                dataName = "data%i" % (k+1)
                if not nraysOkay:
                    file[datasetName][dataName]["where"].attrs.create("nrays", nraysList[k])
                if not nbinsOkay:
                    file[datasetName][dataName]["where"].attrs.create("nbins", nbinsList[k])
                if not rscaleOkay:
                    file[datasetName][dataName]["where"].attrs.create("rscale", rscaleList[k])
                if not rstartOkay:
                    file[datasetName][dataName]["where"].attrs.create("rstart", rstartList[k])
            
            datasetCounter+=1

        file.close()

def BUFRDescriptor(baidid): #Convert bytes into BUFR descriptors. E.g. b'\x01\xe6' => 0-01-230
    if sys.version_info[0] == 2: baidid = map(ord, baidid)
    f = baidid[0] >> 6
    x = baidid[0] & 0b00111111
    y = baidid[1]
    return (f, x, y)

def knmiDateTime(timestamp):
    months={b"JAN":1, b"FEB":2, b"MAR":3, b"APR":4, b"MAY":5, b"JUN":6, b"JUL":7, b"AUG":8, b"SEP":9, b"OCT":10, b"NOV":11, b"DEC":12}
    date,time=timestamp.split(b";")
    day,mon,year=date.split(b"-")
    h,m,s=time.split(b":")
    s,ms=s.split(b".")
    return datetime.datetime(int(year),months[mon],int(day),int(h),int(m),int(s),int(ms)*100)

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
        94:"DBZH",
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
              "VRADD":fraasid["vraddh"],
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
    if fraasid["LANG_ID"] != "AR":
        msg=productname(display.quantity,fraasid).capitalize()+" | "+fraasid["azimuth"]+": "+str(display.rhiAzimuth)+u"° | "+str(display.productTime)+" UTC"
    else:
        if os.name == "nt":
            msg=fixArabic(productname(display.quantity,fraasid).capitalize())+u" | °"+str(display.rhiAzimuth)+u" :"+fixArabic(fraasid["azimuth"])+" | UTC "+str(display.productTime)
        else:
            msg=productname(display.quantity,fraasid).capitalize()+u" | °"+str(display.rhiAzimuth)+u" :"+fraasid["azimuth"]+" | UTC "+str(display.productTime)
    return msg
def headersdecoded(display,fraasid):
    if fraasid["LANG_ID"] != "AR":
        msg=str(round(float(display.elevation),3))+u"° "+productname(display.quantity,fraasid)+" | "+str(display.productTime)+" UTC"
    else:
        if os.name == "nt":
            msg=fixArabic(productname(display.quantity,fraasid))+" "+u"°"+str(round(float(display.elevation),3))+" |  UTC "+str(display.productTime)
        else:
            msg=productname(display.quantity,fraasid)+" "+u"°"+str(round(float(display.elevation),3))+" |  UTC "+str(display.productTime)
    if display.scanTime: #Kui on has scan time
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
        return round(value*gain+offset,6)
    else:
        if value == rangefolding:
            return "RF"
        else:
            return None

def HDF5scaleValue(value,gain,offset,nodata,undetect,rangefolding,quantity,variabletype):
    if value != nodata and value != undetect and value != rangefolding:
        if variabletype is NP_INT16:
            value=NP_UINT16(value)
        if quantity == "ZDR" and offset == 8.0: offset = -8 #A fix to bad offsets in some HDF5 files
        if (quantity == "RHOHV" or quantity == "QIDX") and variabletype is NP_UINT8: #To get around IRIS's non-linear 8 bit variables for these quantities.
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
