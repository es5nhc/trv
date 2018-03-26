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
import platform
from copy import deepcopy

from array import array
import numpy as np
from numpy import fromstring
import nexradtable

NP_UINT8 = np.uint8
NP_UINT16 = np.uint16
NP_INT8 = np.int8
NP_INT16 = np.int16
NP_INT32 = np.int32
NP_FLOAT = np.float32


class FileFormatError(Exception): ##Exception to throw if decoding classes fed wrong type of content
    pass

class IRIS(): #IRIS RAW
    def __init__(self,path):
        self.type = "IRIS"
        self.elevationNumbers = []
        self.elevations = []
        self.times = []
        self.azimuths = []
        self.nominalElevations = []
        self.quantities = []
        self.data=[]
        self.headers={}
        oneByteProducts=[1,2,3,4,5,7,14,16,17,18,19,25,27,32,35,38,39,46,48,50,52,55,57,75,77,79,81,83,85,87]
        signedProducts=[36, 40, 41, 42, 43, 44]
        
        python2 = True if sys.version_info[0] == 2 else False #Check for Python 2 in use
        productTypes={1: "PPI",
                      2: "RHI",
                      3: "CAPPI",
                      4: "CROSS",
                      5: "TOPS",
                      6: "TRACK",
                      7: "RAIN1",
                      8: "RAINN",
                      9: "VVP",
                      10: "VIL",
                      11: "SHEAR",
                      12: "WARN",
                      13: "CATCH",
                      14: "RTI",
                      15: "RAW",
                      16: "MAX",
                      17: "USER",
                      18: "USERV",
                      19: "OTHER",
                      20: "STATUS",
                      21: "SLINE",
                      22: "WIND",
                      23: "BEAM",
                      24: "TEXT",
                      25: "FCAST",
                      26: "NDOP",
                      27: "IMAGE",
                      28: "COMP",
                      29: "TWDR",
                      30: "GAGE",
                      31: "DWELL",
                      32: "SRI",
                      33: "BASE",
                      34: "HMAX",
                      35: "VAD",
                      36: "THICK",
                      37: "SATELLITE",
                      38: "LAYER",
                      39: "SWS",
                      40: "MLGHT"}
        ##
        rawdata = file_read(path)
        self.rawdata = rawdata
        #product_hdr
        #structure_header
        ptr = 0
        self.product_hdr={}
        self.product_hdr["structure_header"] = {"structureIdentifier": halfw(rawdata[ptr:ptr+2], True, False),
                                                "formatVersionNumber": halfw(rawdata[ptr+2:ptr+4], True, False),
                                                "numberOfBytes": word(rawdata[ptr+4:ptr+8], True, False),
                                                "reserved": halfw(rawdata[ptr+8:ptr+10], True, False),
                                                "flags": halfw(rawdata[ptr+10:ptr+12], True, False)}
        ptr+=12
        self.product_hdr["product_configuration"] = {"productType": productTypes[halfw(rawdata[ptr+12:ptr+14], False, False)],
                                                     "schedulingCode": halfw(rawdata[ptr+14:ptr+16], False, False),
                                                     "secondsToSkipBetweenRuns": word(rawdata[ptr+16:ptr+20], True, False),
                                                     "timeProductGenerated": ymds_time(rawdata[ptr+20:ptr+32], False),
                                                     "timeOfInputIngestSweep": ymds_time(rawdata[ptr+32:ptr+44], False),
                                                     "timeOfInputIngestFile": ymds_time(rawdata[ptr+44:ptr+56], False),
                                                     "nameOfConfigFile": rawdata[ptr+62:ptr+74].rstrip(b"\x00").rstrip(),
                                                     "taskName": rawdata[ptr+74:ptr+86].rstrip(b"\x00").rstrip(),
                                                     "flagWord": rawdata[ptr+86:ptr+88],
                                                     "xScale": word(rawdata[ptr+88:ptr+92], True, False), #cm/pixel
                                                     "yScale": word(rawdata[ptr+92:ptr+96], True, False),
                                                     "zScale": word(rawdata[ptr+96:ptr+100], True, False),
                                                     "xDirection": word(rawdata[ptr+100:ptr+104], True, False),
                                                     "yDirection": word(rawdata[ptr+104:ptr+108], True, False),
                                                     "zDirection": word(rawdata[ptr+108:ptr+112], True, False),
                                                     "xLocation": word(rawdata[ptr+112:ptr+116], True, False)/1000,
                                                     "yLocation": word(rawdata[ptr+116:ptr+120], True, False)/1000,
                                                     "zLocation": word(rawdata[ptr+120:ptr+124], True, False)/1000,
                                                     "maximumRange": word(rawdata[ptr+124:ptr+128], True, False),
                                                     "dataTypeGenerated": halfw(rawdata[ptr+130:ptr+13], False, False),
                                                     "projectionName": rawdata[132:144].rstrip(b"\x00").rstrip(),
                                                     "dataTypeUsedAsInput": halfw(rawdata[ptr+144:ptr+146], False, False),
                                                     "projectionType": ord(rawdata[ptr+147]) if python2 else rawdata[ptr+147],
                                                     "radialSmoother": halfw(rawdata[ptr+148:ptr+150], True, False)/100, #km
                                                     "numberOfTimesConfigHasRun": halfw(rawdata[ptr+150:ptr+152]),
                                                     "ZRRelationshipConstant": word(rawdata[ptr+152:ptr+156], True, False)/1000,
                                                     "ZRRelationshipExponent": word(rawdata[ptr+156:ptr+160], True, False)/1000,
                                                     "XdirectionSmoother": halfw(rawdata[ptr+160:ptr+162], True, False)/100,
                                                     "YdirectionSmoother": halfw(rawdata[ptr+162:ptr+164], True, False)/100
                                                     }
        ptr+=320
        self.product_hdr["product_end"] = {"siteName": rawdata[ptr:ptr+16].rstrip(),
                                           "IRISVersion": rawdata[ptr+16:ptr+24].rstrip(b"\x00").rstrip(),
                                           "IRISVersionIngestData": rawdata[ptr+24:ptr+32].rstrip(b"\x00").rstrip(),
                                           "timeOfOldestInputIngestFile": ymds_time(rawdata[ptr+32:ptr+44], False),
                                           "LTMinutesWestOfUTC": halfw(rawdata[ptr+72:ptr+74], True, False),
                                           "hardWareNameOfIngestDataSrc": rawdata[ptr+74:ptr+90].rstrip(),
                                           "siteNameOfIngestDataSrc": rawdata[ptr+90:ptr+106].rstrip(),
                                           "recordedLTMinsWestOfUTC": halfw(rawdata[ptr+106:ptr+108], True, False),
                                           "latitudeOfCentre": binaryAngle(word(rawdata[ptr+108:ptr+112], False, False), 32),
                                           "longitudeOfCentre": binaryAngle(word(rawdata[ptr+112:ptr+116], False, False), 32),
                                           "groundHeightMSL": halfw(rawdata[ptr+116:ptr+118], True, False),
                                           "radarHeightAGL": halfw(rawdata[ptr+118:ptr+120], True, False),
                                           "PRF": word(rawdata[ptr+120:ptr+124], True, False),
                                           "pulseWidth": word(rawdata[ptr+124:ptr+128], True, False)/100, #microseconds
                                           "typeOfSignalProcessor": halfw(rawdata[ptr+128:ptr+130], False, False),
                                           "triggerRateScheme": halfw(rawdata[ptr+130:ptr+132], False, False),
                                           "nrSamplesUsed": halfw(rawdata[ptr+132:ptr+134], True, False),
                                           "clutterFileName": rawdata[ptr+134:ptr+146].rstrip(b"\x00").rstrip(),
                                           "numberOfLinearBasedFilterFOrFirstBin": halfw(rawdata[ptr+146:ptr+148], False, False),
                                           "wavelength": word(rawdata[ptr+148:ptr+152], True, False) / 10000, #converted to meters
                                           "truncationHeight": word(rawdata[ptr+152:ptr+156], True, False), # in cm
                                           "firstBinRange": word(rawdata[ptr+156:ptr+160], True, False) / 100000, #converted to km
                                           "lastbinRange": word(rawdata[ptr+160:ptr+164], True, False) / 100000, #Same as above
                                           "numberOfOutputBins": word(rawdata[ptr+164:ptr+168], True, False),
                                           "flagWord": halfw(rawdata[ptr+168:ptr+170], False, False),
                                           "NumberOfIngestOrProductFilesUsed": halfw(rawdata[ptr+170:ptr+172], False, False),
                                           "typeOfPolarisationUsed": halfw(rawdata[ptr+172:ptr+174], False, False),
                                           "IOCalValueH": halfw(rawdata[ptr+174:ptr+176], True, False) / 100, #in dBm
                                           "NoiseAtCalibrationH": halfw(rawdata[ptr+176:ptr+178], True, False) / 100, #dBm
                                           "RadarConstant": halfw(rawdata[ptr+178:ptr+180], True, False) / 100, #dBm
                                           "RXBandwidth": halfw(rawdata[ptr+180:ptr+182], False, False), #kHz
                                           "currentNoiseLevelH": halfw(rawdata[ptr+182:ptr+184], True, False) / 100, #dBm
                                           "currentNoiseLevelV": halfw(rawdata[ptr+184:ptr+186], True, False) / 100, #dBm
                                           "LDROffset": halfw(rawdata[ptr+186:ptr+188], True, False) / 100, #dBz
                                           "ZDROffset": halfw(rawdata[ptr+188:ptr+190], True, False) / 100, #dBz
                                           "TCFCal1": task_calib_flags(halfw(rawdata[ptr+190:ptr+192], False, False)),
                                           "TCFCal2": task_calib_flags(halfw(rawdata[ptr+190:ptr+192], False, False)),
                                           }
        if self.product_hdr["product_configuration"]["productType"] == "RAW":
            ptr=6156
            self.ingest_header={}
            self.ingest_header["ingest_configuration"] = {"fileName": rawdata[ptr:ptr+80].rstrip(b"\x00").rstrip(),
                                                          "numberOfAssociatedDataFiles": halfw(rawdata[ptr+80:ptr+82], True, False),
                                                          "numberOfSweepsCompletedSoFar": halfw(rawdata[ptr+82:ptr+84], True, False),
                                                          "totalSizeOfAllFiles": word(rawdata[ptr+84:ptr+88], True, False),
                                                          "volumeScanStartTime": ymds_time(rawdata[ptr+88:ptr+100], False),
                                                          "bytesInRayHeaders": halfw(rawdata[ptr+112:ptr+114], True, False),
                                                          "bytesInExtendedRayHeaders": halfw(rawdata[ptr+114:ptr+116], True, False),
                                                          "playbackVersionNumber": halfw(rawdata[ptr+116:ptr+118], True, False),
                                                          "IRISversion": rawdata[ptr+124:ptr+132].rstrip(b"\x00").rstrip(),
                                                          "siteHWName": rawdata[ptr+132:ptr+148].rstrip(b"\x00").rstrip(),
                                                          "timeZone": halfw(rawdata[ptr+148:ptr+150], True, False),
                                                          "siteNameFromSetup": rawdata[ptr+150:ptr+166].rstrip(b"\x00").rstrip(),
                                                          "timeZoneReceived": halfw(rawdata[ptr+166:ptr+168], True, False),
                                                          "radarLatitude": binaryAngle(word(rawdata[ptr+168:ptr+172], False, False),32),
                                                          "radarLongitude": binaryAngle(word(rawdata[ptr+172:ptr+176], False, False), 32),
                                                          "groundHeightMSL": halfw(rawdata[ptr+176:ptr+178], True, False),
                                                          "radarHeightAGL": halfw(rawdata[ptr+178:ptr+180], True, False),
                                                          "nrays": halfw(rawdata[ptr+180:ptr+182], False, False),
                                                          "firstRayIndex": halfw(rawdata[ptr+182:ptr+184], False, False),
                                                          "nrays": halfw(rawdata[ptr+184:ptr+186], False, False),
                                                          "nBytesInEachGparam": halfw(rawdata[ptr+186:ptr+188], True, False),
                                                          "radarHeightMSL": word(rawdata[ptr+188:ptr+192], True, False) / 100, #Converted to meters
                                                          "radarPlatvormVelocity": [word(rawdata[ptr+192:ptr+196], True, False) / 100, word(rawdata[ptr+196:ptr+200], True, False) / 100, word(rawdata[ptr+200:ptr+204], True, False) / 100], #converted to m/s
                                                          "antennaOffsetFromINU": [word(rawdata[ptr+204:ptr+208], True, False) / 100, word(rawdata[ptr+208:ptr+2012], True, False) / 100, word(rawdata[ptr+212:ptr+216], True, False) / 100], #converted to m
                                                          "faultStatus": word(rawdata[ptr+216:ptr+220], False, False), #RAW VALUE, bits needs to be individually processed
                                                          "meltingLayerHeight": halfw(rawdata[ptr+220:ptr+222], True, True), #???? MSB complemented. (TRUMP SAYS WRONG!)
                                                          "tzString": rawdata[ptr+224:ptr+228].rstrip(b"\x00").rstrip(),
                                                          "flags": word(rawdata[ptr+232:ptr+236], False, False),
                                                          "confName": rawdata[ptr+236:ptr+252].rstrip(b"\00").rstrip()
                                                          }
            ptr+=492+120 #Skipping over to task_dsp_info
            
            self.ingest_header["task_configuration"]= {}
            self.ingest_header["task_configuration"]["task_dsp_info"] = {"majorMode": halfw(rawdata[ptr:ptr+2], False, False),
                                                                         "dspType": halfw(rawdata[ptr+2:ptr+4], False, False),
                                                                         "quantities": dataTypesFromMask(word(rawdata[ptr+4:ptr+8], False, False),0) + dataTypesFromMask(word(rawdata[ptr+12:ptr+16], False, False),32) + dataTypesFromMask(word(rawdata[ptr+16:ptr+20], False, True), 64) + dataTypesFromMask(word(rawdata[ptr+20:ptr+24], False, True), 96),
                                                                         "extendedHeaderType": rawdata[ptr+8:ptr+12],
                                                                         "PRF": word(rawdata[ptr+136:ptr+140], True, False),
                                                                         "pulseWidth": word(rawdata[ptr+140:ptr+144], True, False),
                                                                         "multiPRFflag": halfw(rawdata[ptr+144:ptr+146], False, False),
                                                                         "dualPRFDelay": halfw(rawdata[ptr+146:ptr+148], True, False),
                                                                         "AGCFeedbackCode": halfw(rawdata[ptr+148:ptr+150], False, False),
                                                                         "sampleSize": halfw(rawdata[ptr+150:ptr+152], True, False),
                                                                         "gainControlFlag": halfw(rawdata[ptr+152:ptr+154], False, False),
                                                                         "clutterFilterFileName": rawdata[ptr+154:ptr+166].rstrip(b"\x00").rstrip(),
                                                                         "customRayHeaderName": rawdata[ptr+184:ptr+200].rstrip(b"\x00").rstrip()}
            ptr+= 320+320 #Skipping over to task_range_info
            self.ingest_header["task_configuration"]["task_range_info"]={"firstBinRange": word(rawdata[ptr:ptr+4], True, False) / 100000, #Converted to km
                                                                                                 "lastBinRange": word(rawdata[ptr+4:ptr+8], True, False) / 100000,
                                                                                                 "numberOfInputBins": halfw(rawdata[ptr+8:ptr+10], True, False),
                                                                                                 "numberOfOutputBins": halfw(rawdata[ptr+10:ptr+12], True, False),
                                                                                                 "stepBetweenInputBins": word(rawdata[ptr+12:ptr+16], True, False) / 100000, #converted to km
                                                                                                 "stepBetweenOutputBins": word(rawdata[ptr+16:ptr+20], True, False) / 100000, #converted to km
                                                                                                 "variableBinSpacing": halfw(rawdata[ptr+20:ptr+22], False, False),
                                                                                                 "rangeBinAveraging": halfw(rawdata[ptr+22:ptr+24], False, True)
                }
            ptr+=160 #And onwards to task_scan_info
            scanMode=halfw(rawdata[ptr+0:ptr+2], False, False)
            self.ingest_header["task_configuration"]["task_scan_info"]={"scanMode": scanMode,
                                                                        "angResolution": halfw(rawdata[ptr+2:ptr+4], True, False) / 1000, #Converted to °
                                                                        "numberOfSweeps": halfw(rawdata[ptr+4:ptr+6], True, False)}
            if scanMode == 2: #If RHI
                self.ingest_header["task_configuration"]["task_scan_info"]["lowerElevationLimit"] = binaryAngle(halfw(rawdata[ptr+8:ptr+10], False, False) , 16)
                self.ingest_header["task_configuration"]["task_scan_info"]["upperElevationLimit"] = binaryAngle(halfw(rawdata[ptr+10:ptr+12], False, False) , 16)
                self.ingest_header["task_configuration"]["task_scan_info"]["azimuthsList"] = []
                for i in range(12, 82, 2):
                    az=binaryAngle(halfw(rawdata[ptr+i:ptr+i+2], False, False), 16)
                    if i > 12 and az == 0: break #No more azimuths
                    self.ingest_header["task_configuration"]["task_scan_info"]["azimuthsList"].append(az)
                self.ingest_header["task_configuration"]["task_scan_info"]["startOfFirstSectorSweep"] = ord(rawdata[ptr+207]) if python2 else rawdata[ptr+207]
            elif scanMode in [1, 4]:
                self.ingest_header["task_configuration"]["task_scan_info"]["leftAzLimit"] = binaryAngle(halfw(rawdata[ptr+8:ptr+10], False, False), 16)
                self.ingest_header["task_configuration"]["task_scan_info"]["rightAzLimit"] = binaryAngle(halfw(rawdata[ptr+10:ptr+10:12], False, False), 16)
                self.ingest_header["task_configuration"]["task_scan_info"]["elevations"] = []
                for i in range(12, 82, 2):
                    el = binaryAngle(halfw(rawdata[ptr+i:ptr+i+2], False, False), 16)
                    if i > 12 and el == 0: break #No more elevations
                    self.ingest_header["task_configuration"]["task_scan_info"]["elevations"].append(el)
                self.ingest_header["task_configuration"]["task_scan_info"]["startOfFirstSectorSweep"] = ord(rawdata[ptr+207]) if python2 else rawdata[ptr+207]
            elif scanMode == 3:
                self.ingest_header["task_configuration"]["task_scan_info"]["flags"] = halfw(rawdata[ptr+8:ptr+10], False, False)
            elif scanMode == 5:
                self.ingest_header["task_configuration"]["task_scan_info"]["firstAzimuth"] = binaryAngle(halfw(rawdata[ptr+8:ptr+10], False, False), 16)
                self.ingest_header["task_configuration"]["task_scan_info"]["firstElevation"] = binaryAngle(halfw(rawdata[ptr+10:ptr+12], False, False), 16)
                self.ingest_header["task_configuration"]["task_scan_info"]["antennaControlFileName"] = rawdata[ptr+12:ptr+24].rstrip(b"\x00").rstrip()
            ptr+=320 #Off to task_misc_info
            self.ingest_header["task_configuration"]["task_misc_info"]={"wavelength": word(rawdata[ptr:ptr+4], True, False) / 10000, #Converted to meters
                                                                        "TRSerial": rawdata[ptr+4:ptr+20].rstrip(b"\x00").rstrip(),
                                                                        "TXpower": word(rawdata[ptr+20:ptr+24], True, False),
                                                                        "flags": halfw(rawdata[ptr+24:ptr+26], False, False),
                                                                        "polarisation": halfw(rawdata[ptr+26:ptr+28], False, False),
                                                                        "truncationHeight": word(rawdata[ptr+28:ptr+32], True, False) / 100000, #converted to km
                                                                        "beamWidthH": binaryAngle(word(rawdata[ptr+64:ptr+68], False, False), 32),
                                                                        "beamWidthV": binaryAngle(word(rawdata[ptr+68:ptr+72], False, False), 32)
                                                                        }
            ptr+=320 #And finally, task_end_info
            self.ingest_header["task_configuration"]["task_end_info"]={"majorNumber": halfw(rawdata[ptr:ptr+2], True, False),
                                                                       "minorNumber": halfw(rawdata[ptr+2:ptr+4], True, False),
                                                                       "taskConfigFileName": rawdata[ptr+4:ptr+16].rstrip(b"\x00").rstrip(),
                                                                       "taskDescription": rawdata[ptr+16:ptr+96].rstrip(b"\x00").rstrip(),
                                                                       "numberOfTasks": word(rawdata[ptr+96:ptr+100], True, False),
                                                                       "taskState": halfw(rawdata[ptr+100:ptr+102], False, False),
                                                                       "timeOfTask": ymds_time(rawdata[ptr+104:ptr+116], False),
                                                                       "echoClassifiers": map(ord,rawdata[ptr+116:ptr+122]) if python2 else [x for x in rawdata[ptr+116:ptr+122]]}
            ptr+=320
            self.ingest_header["task_configuration"]["comments"]=rawdata[ptr:ptr+720].rstrip(b"\x00").rstrip()
            ptr+=720+732+128+920+1260 #onwards to raw_prod_bhdr
            self.records=[]
            sweepStartTimes=[]
            rawSweep=[] ##Collecting the contents of all records here sweep by sweep
            
            highprf = self.ingest_header["task_configuration"]["task_dsp_info"]["PRF"]
            lowprfmults = [1, 2/3, 3/4, 4/5] #Multipliers to get low PRF from high PRF.
            prfMode = self.ingest_header["task_configuration"]["task_dsp_info"]["multiPRFflag"]
            lowprf = highprf*lowprfmults[prfMode]
            self.wavelength = self.ingest_header["task_configuration"]["task_misc_info"]["wavelength"]
            vMax = highprf*self.wavelength/4
            
            eightBitDopplerOffset=vMax*128/127
            eightBitDopplerGain=vMax/127
            
            variableTypes={}
            #The table is here because we need to find the PRF and wavelength first
            dataParameters={1: [-32.0, 0.5, 0, 255], #Order: Offset, Gain, Undetect, Nodata
                            2: [-32.0, 0.5, 0, 255],
                            3: [-eightBitDopplerOffset, eightBitDopplerGain, 0, 0],
                            4: [0, 1/256.0, 0, 0], #[sic!]
                            5: [-8, 1/16, 0, 0],
                            7: [-32.0, 0.5, 0, 255], #Corrected reflectivity, assuming same characteristics as TH and DBZH"DBZH",
                            8: [-327.68, 0.01, 0, 65535],
                            9: [-327.68, 0.01, 0, 65535],
                            10: [-327.68, 0.01, 0, 65535],
                            11: [0, 0.01, 0, 65535],
                            12: [-327.68, 0.01, 0, 65535],
                            13: [0, 1, 0, 65535], #NOT LINEAR: NEED TO IMPLEMENT DECODING ON SOFTWARE SIDE. PASSING RAW DATA
                            14: [0, 1, 0, 255], #NOT LIENAR: NEED TO IMPLEMENT DECODING ON SOFTWARE SIDE. PASSING RAW DATA
                            15: [-327.68, 0.01, 0, 65535],
                            16: [-180/254, 180/254, 0, 255],
                            17: [-75+150/253.0, 150/253.0, 0, 255],
                            18: [0, 1, 0, 255], #NOT LINEAR: SEE NOTE ABOVE
                            19: [0, 1, 0, 255], #NOT LINEAR: SEE NOTE ABOVE
                            20: [-1/65533, 1/65533, 0, 65535],
                            21: [-327.68, 0.01, 0, 65535],
                            22: [-327.68, 0.01, 0, 65535],
                            23: [-1/65533, 1/65533, 0, 65535],
                            24: [-360/65534, 360/65534.0, 0, 65535],
                            25: [-45.5, 0.2, 0, 255],
                            26: [-327.68, 0.01, 0, 65535],
                            27: [-45.5, 0.2, 0, 255],
                            28: [-327.68, 0.01, 0, 65535],
                            32: [-0.1, 0.1, 0, 255],
                            33: [-0.001, 0.001, 0, 65535],
                            34: [0, 1, -999, -999], #raw
                            35: [-25.6, 0.2, 0, 255],
                            36: [0, 0.001, 32767, 32767],
                            37: [0, 1, -999, -999], #NOT LINEAR.
                            38: [0, 1, -999, -999], #Unspecified data. Keeping raw,
                            39: [0, 1, -999, -999], #Unspecified data,
                            40: [0, 0.001, 32767, 32767],
                            41: [0, -0.01, 32767, 32767],
                            42: [0, -0.01, 32767, 32767], #guessed - fixme
                            43: [0, 0.1, -32767, 32767], #guessed
                            44: [0, 0.1, -32767, 32767], #guessed
                            45: [0, 1, -999, -999], #Keeping raw, "DB_TIME2",
                            46: [0, 1, 0, 255],
                            47: [-1/65533, 1/65533, 0, 65535],
                            48: [0, 1, 0, 255],
                            49: [-1/65533, 1/65533, 0, 65535],
                            50: [-180/254, 180/254, 0, 255],
                            51: [-360/65534, 360/65534, 0, 65535],
                            52: [-180/254, 180/254, 0, 255],
                            53: [-360/65534, 360/65534, 0, 65535],
                            54: [0, 1, -999, -999], #raw
                            55: [0, 1, 0, 255], #to be processed during decoding.
                            56: [0, 1, 0, 65535], #ditto
                            57: [-8, 1/16, 0, 0],
                            58: [-327.68, 0.01, 0, 65535],
                            75: [0, 1, -999, -999],
                            76: [0, 1, -999, -999],
                            77: [-32.0, 0.5, 0, 255],
                            78: [-327.68, 0.01, 0, 65535], #Guessed- programmer's manual may have a mixup with 8 bit var,
                            79: [-32.0, 0.5, 0, 255],
                            80: [-327.68, 0.01, 0, 65535],
                            81: [0, 1, 0, 255], #Same caveat as with 1 byte RhoHV
                            82: [-1/65533, 1/65533, 0, 65535],
                            83: [-32.0, 0.5, 0, 255],
                            84: [-327.68, 0.01, 0, 65535],
                            85: [-32.0, 0.5, 0, 255],
                            86: [-327.68, 0.01, 0, 65535],
                            87: [-32.0, 0.5, 0, 255],
                            88: [-327.68, 0.01, 0, 65535]}
            while ptr < len(rawdata):
                recordBeginning = ptr
                sweepNr = halfw(rawdata[ptr+2:ptr+4], True, False)
                record={"recordNumber": halfw(rawdata[ptr:ptr+2], True, False),
                        "sweepNr": sweepNr,
                        "byteOffset": halfw(rawdata[ptr+4:ptr+6], True, False),
                        "rayNumber": halfw(rawdata[ptr+6:ptr+8], True, False),
                        "flags": halfw(rawdata[ptr+8:ptr+10], False, False)}
                ptr+=12
                record["headers"]=[]
                if sweepNr not in self.elevationNumbers:
                    self.nominalElevations.append(round(binaryAngle(halfw(rawdata[ptr+34:ptr+36], False, False), 16), 2))
                    self.elevationNumbers.append(sweepNr)
                    self.quantities.append([])
                    rawSweep.append(b"")
                    
                    ingestDataHeader = {}
                    starttime = ymds_time(rawdata[ptr+12:ptr+24], False)
                    ingestDataHeader["sweepStartTime"] = starttime
                    sweepStartTimes.append(starttime)
                    ingestDataHeader["sweepNumber"] = halfw(rawdata[ptr+24:ptr+26], True, False)
                    ingestDataHeader["resolution"] = halfw(rawdata[ptr+26:ptr+28], True, False) / 360.0 #angular resolution
                    ingestDataHeader["indexOfFirstRay"] = halfw(rawdata[ptr+28:ptr+30], True, False)
                    ingestDataHeader["nraysExpected"] = halfw(rawdata[ptr+30:ptr+32], True, False)
                    ingestDataHeader["nraysActually"] = halfw(rawdata[ptr+32:ptr+34], True, False)
                    for i in range(len(self.ingest_header["task_configuration"]["task_dsp_info"]["quantities"])):
                        quantityCode = halfw(rawdata[ptr+38:ptr+40], False, False)

                        ##POPULATING OPTIONS
                        quantity = IRISTypes[quantityCode]
                        if quantityCode in oneByteProducts:
                            valType = np.int8 if quantityCode in signedProducts else np.uint8
                        else:
                            valType = np.int16 if quantityCode in signedProducts else np.uint16
                        variableTypes[quantity] = {"type": valType,
                                                   "params": dataParameters[quantityCode]
                                                   }
                        self.quantities[self.elevationNumbers.index(sweepNr)].append(quantity)
                        record["headers"].append(ingestDataHeader)
                        ptr+=76
                bytesToNextRecord = 6144 - (ptr-recordBeginning)
                rawSweep[sweepNr-1]+=rawdata[ptr:ptr+bytesToNextRecord]
                ptr+= bytesToNextRecord
                self.records.append(record)
            #In the meantime here's some metadata for the data fields that we'll send to TRV
            rscale = self.ingest_header["task_configuration"]["task_range_info"]["stepBetweenOutputBins"]
            rstart = self.ingest_header["task_configuration"]["task_range_info"]["firstBinRange"]
            
            #And now let's process the record contents:
            for swpnr in range(len(rawSweep)):
                swp = rawSweep[swpnr]
                swpptr = 0
                blockLength = -1
                self.data.append({})
                self.elevations.append([])
                self.azimuths.append([])
                self.times.append([])
                while blockLength != -6:
                    for qty in self.quantities[swpnr]:
                        dataType = variableTypes[qty]["type"]
                        offset, gain, undetect, nodata = variableTypes[qty]["params"]
                        blockLength = halfw(swp[swpptr:swpptr+2], False, False) & 32767 #Length of continuous data before a zero run
                        startingAzimuth = binaryAngle(halfw(swp[swpptr+2:swpptr+4], False, False), 16)
                        if startingAzimuth not in self.azimuths[swpnr] and blockLength != 0:
                            startingElevation = binaryAngle(halfw(swp[swpptr+4:swpptr+6], False, False), 16)
                            time = halfw(swp[swpptr+12:swpptr+14], False, False)
                            timefull= sweepStartTimes[swpnr]["time"] + datetime.timedelta(seconds=time)
                            prfFlag = halfw(swp[swpptr+12:swpptr+14], False, False) #According to pyART, not seeing it in IRIS programmers manual, but makes sense when watching actual data.
                            self.times[swpnr].append(timefull) #Saving ray properties
                            self.elevations[swpnr].append(startingElevation)
                            self.azimuths[swpnr].append(startingAzimuth)
                        if qty not in self.data[swpnr]:
                            self.data[swpnr][qty] = {"data": [], "dataType": dataType, "rscale": rscale, "rstart": rstart, "highprf": highprf, "lowprf": lowprf, "gain": gain, "offset": offset, "undetect": undetect, "nodata": nodata} 
                        #endingAzimuth = binaryAngle(halfw(swp[swpptr+6:swpptr+8], False, False), 16)
                        #endingElevation = binaryAngle(halfw(swp[swpptr+8:swpptr+10], False, False), 16)
                        nbins = halfw(swp[swpptr+10:swpptr+12], True, False)
                        swpptr+=14
                        blockLength -= 6 #subtracting first 6 data blocks as we now iterate for data bins
                        val=None
                        datarow=[]
                        
                        if dataType == np.uint8 or dataType == np.int8: #Multiplier for zeroes count in RLE
                            zeroesCountMult = 2
                        else:
                            zeroesCountMult = 1
                            
                        while val != 1 and blockLength != -6:
                            datarow+=np.fromstring(swp[swpptr:swpptr+blockLength*2], dataType).tolist()
                            swpptr+=2*blockLength
                            zeroesCount = halfw(swp[swpptr:swpptr+2], True, False)
                            if blockLength < nbins and zeroesCount > 1:
                                datarow+=[0]*(zeroesCount*zeroesCountMult) #Zeroes count is also in halfwords - therefore must multiply by 2 when having 8 bit values
                                swpptr+=2
                            val=halfw(swp[swpptr:swpptr+2], True, False)
                            blockLength = val & 32767
                            swpptr+=2
                        rowSize = len(datarow)
                        if rowSize > 0:
                            if rowSize > nbins:
                                datarow=datarow[0:nbins] #Strip excess entries at the end
                            if rowSize < nbins: #If shorter than expected length
                                datarow+=[nodata]*(nbins-rowSize) #pad with nodata values
                            self.data[swpnr][qty]["data"].append(datarow)
            #Final stuff:
            self.headers["latitude"] = self.ingest_header["ingest_configuration"]["radarLatitude"]
            self.headers["longitude"] = self.ingest_header["ingest_configuration"]["radarLongitude"]
            if self.headers["longitude"] > 180: self.headers["longitude"]-=360
            self.headers["height"] = self.ingest_header["ingest_configuration"]["radarHeightMSL"]
            self.headers["timestamp"] = self.product_hdr["product_configuration"]["timeOfInputIngestSweep"]["time"]
        else:
            print("Unsupported product (RAW only!)")
class DORADE(): #SUPPORT IS VERY PRELIMINARY WITH SHORTCUTS TAKEN - probably not universally compatible. Example files and fixes welcome!
    def __init__(self,path):
        ## HMM. Documentation says big endian integers but they appear to be little endian instead!
        data = file_read(path)

        doradeTypes={1:NP_INT8,
                     2:NP_INT16,
                     3:NP_INT32,
                     4:NP_FLOAT}

        ## Initializing TRV's DATA objects.
        self.type = "DORADE"
        self.data = []
        self.azimuths = []
        self.times = []
        self.quantities = []
        self.headers = {}
        self.elevations = []
        self.elevationNumbers = []
        self.nominalElevations = []
        rscale = 1
        rstart = 0
        
        ##
        self.rawdata = data
        ptr = data.index(b"SSWB")

        #SSWB
        sswbSize = word(data[ptr+4:ptr+8], False, False)
            
        self.sswb = {"nbytes": sswbSize,
                     "last_used": datetime.datetime.utcfromtimestamp(word(data[ptr+8:ptr+12], False, False)),
                     "start_time": datetime.datetime.utcfromtimestamp(word(data[ptr+12:ptr+16], False, False)),
                     "stop_time": datetime.datetime.utcfromtimestamp(word(data[ptr+16:ptr+20], False, False)),
                     "sizeof_file": word(data[ptr+20:ptr+24], False, False),
                     "compression_flag": word(data[ptr+24:ptr+28], False, False),
                     "volume_time_stamp": datetime.datetime.utcfromtimestamp(word(data[ptr+28:ptr+32],False,False)),
                     "num_params": word(data[ptr+32:ptr+36], False, False),
                     "radar_name": data[ptr+36:ptr+44].rstrip(b"\x00").rstrip(),
                     "num_keytables": word(data[ptr+64:ptr+68], False,False),
                     "status": word(data[ptr+68:ptr+72], False,False),
                     "key_table": []}
        
        self.headers["timestamp"]=self.sswb["volume_time_stamp"] #Converting some of the quantities to TRV data model
        self.times=[[self.sswb["start_time"],self.sswb["stop_time"]]]
        
        ptr+=100
        for i in range(0,12*self.sswb["num_keytables"], 12):
            self.sswb["key_table"].append({"offset": word(data[ptr+i:ptr+i+4], False, False),
                                           "size": word(data[ptr+i+4:ptr+i+8], False, False),
                                           "type": word(data[ptr+i+8:ptr+i+12], False, False)})
        ptr+=sswbSize-100

        #VOLD

        voldSize=word(data[ptr+4:ptr+8], False, False)
        
        self.vold = {"nbytes": voldSize,
                     "format_version": halfw(data[ptr+8:ptr+10], False, False),
                     "volume_num": halfw(data[ptr+10:ptr+12], False, False),
                     "maximum_bytes": word(data[ptr+12:ptr+16], False, False),
                     "proj_name": data[ptr+16:ptr+36].rstrip(b"\x00").rstrip(),
                     "year": halfw(data[ptr+36:ptr+38], False, False),
                     "month": halfw(data[ptr+38:ptr+40], False, False),
                     "day": halfw(data[ptr+40:ptr+42], False, False),
                     "data_set_hour": halfw(data[ptr+42:ptr+44], False, False),
                     "data_set_minute": halfw(data[ptr+44:ptr+46], False, False),
                     "data_set_second": halfw(data[ptr+46:ptr+48], False, False),
                     "flight_number": data[ptr+48:ptr+56].rstrip(b"\x00").rstrip(),
                     "gen_facility": data[ptr+56:ptr+64].rstrip(b"\x00").rstrip(),
                     "gen_year": halfw(data[ptr+64:ptr+66], False, False),
                     "gen_month": halfw(data[ptr+66:ptr+68], False, False),
                     "gen_day": halfw(data[ptr+68:ptr+70], False, False),
                     "number_sensor_des": halfw(data[ptr+70:ptr+72], False, False)}

        ptr += voldSize 
        self.sensors = []

        for j in range(self.vold["number_sensor_des"]):
            radd={"nbytes": word(data[ptr+4:ptr+8], False, False),
                   "radar_name": data[ptr+8:ptr+16].rstrip(b"\x00").rstrip(),
                   "radar_const": floating(data[ptr+16:ptr+20], False),
                   "peak_power": floating(data[ptr+20:ptr+24], False),
                   "noise_power": round(floating(data[ptr+24:ptr+28], False),5),
                   "receiver_gain": floating(data[ptr+28:ptr+32], False),
                   "antenna_gain": floating(data[ptr+32:ptr+36], False),
                   "system_gain": floating(data[ptr+36:ptr+40], False),
                   "horz_beam_width": floating(data[ptr+40:ptr+44], False),
                   "vert_beam_width": floating(data[ptr+44:ptr+48], False),
                   "radar_type": halfw(data[ptr+48:ptr+50], False, False),
                   "scan_mode": halfw(data[ptr+50:ptr+52], False, False),
                   "req_rotat_vel": floating(data[ptr+52:ptr+56], False),
                   "scan_mode_pram0": floating(data[ptr+56:ptr+60], False),
                   "scan_mode_pram1": floating(data[ptr+60:ptr+64], False),
                   "num_parameters_des": halfw(data[ptr+64:ptr+66], False, False),
                   "total_num_des": halfw(data[ptr+66:ptr+68], False, False),
                   "data_compress": halfw(data[ptr+68:ptr+70], False, False),
                   "data_reduction": halfw(data[ptr+70:ptr+72], False, False),
                   "data_red_parm0": floating(data[ptr+72:ptr+76], False),
                   "data_red_parm1": floating(data[ptr+76:ptr+80], False),
                   "radar_longitude": floating(data[ptr+80:ptr+84], False),
                   "radar_latitude": floating(data[ptr+84:ptr+88], False),
                   "radar_altitude": floating(data[ptr+88:ptr+92], False),
                   "eff_unamb_vel": floating(data[ptr+92:ptr+96], False),
                   "eff_unamb_range": floating(data[ptr+96:ptr+100], False),
                   "num_freq_trans": halfw(data[ptr+100:ptr+102], False, False),
                   "num_ipps_trans": halfw(data[ptr+102:ptr+104], False, False),
                   "freqs":[], #Frequencies clearly in GHz
                   "ipps":[],
                   "prfs":[]}  #IPPS period appears to be in milliseconds.
            for j1 in range(104,104+4*radd["num_freq_trans"],4):
                radd["freqs"].append(floating(data[ptr+j1:ptr+j1+4], False))
            for j2 in range(124,124+4*radd["num_ipps_trans"],4):
                ipp = floating(data[ptr+j2:ptr+j2+4], False)
                radd["ipps"].append(ipp)
                radd["prfs"].append(round(1000/ipp,2))
            if radd["nbytes"] == 300: #Extended RADD
                radd["extention_num"] = word(data[ptr+144:ptr+148], False, False)
                radd["config_name"] = data[ptr+148:ptr+156].rstrip(b"\x00").rstrip()
                radd["config_num"] = word(data[ptr+156:ptr+160], False, False)
                radd["aperture_size"] = floating(data[ptr+160:ptr+164], False)
                radd["field_of_view"] = floating(data[ptr+164:ptr+168], False)
                radd["apperture_eff"] = floating(data[ptr+168:ptr+172], False)
                for j3 in range(172, 216, 4):
                    currentFreq = floating(data[ptr+j3:ptr+j3+4], False)
                    if currentFreq > 0:
                        radd["freqs"].append(currentFreq)
                for j4 in range(216, 260, 4):
                    currentIpps = floating(data[ptr+j4:ptr+j4+4], False)
                    if currentIpps > 0:
                        radd["ipps"].append(currentIpps)
                radd["pulse_width"] = floating(data[ptr+260:ptr+264], False)
                radd["primary_cop_baseln"] = floating(data[ptr+264:ptr+268], False)
                radd["secondary_comp_baseln"] = floating(data[ptr+268:ptr+272], False)
                radd["pc_xmtr_bandwidth"] = floating(data[ptr+272:ptr+276], False)
                radd["pc_waveform_type"] = word(data[ptr+276:ptr+280], False)
                radd["site_name"] = data[ptr+280:ptr+300].rstrip(b"\x00").rstrip()
            ptr+=radd["nbytes"]
            
            parms=[]

            #Parameters
            for j5 in range(radd["num_parameters_des"]):
                parm={"nbytes": word(data[ptr+4:ptr+8], False, False),
                      "parameter_name": data[ptr+8:ptr+16].rstrip(b"\x00").rstrip(),
                      "parameter_description": data[ptr+16:ptr+56].rstrip(b"\x00").rstrip(),
                      "param_units": data[ptr+56:ptr+64].rstrip(b"\x00").rstrip(),
                      "interpulse_time": halfw(data[ptr+64:ptr+66], False, False),
                      "xmitted_freq":  halfw(data[ptr+66:ptr+68], False, False),
                      "recvr_bandwidth": floating(data[ptr+68:ptr+72], False),
                      "pulse_width": halfw(data[ptr+72:ptr+74], False, False),
                      "polarization": halfw(data[ptr+74:ptr+76], False, False),
                      "num_samples": halfw(data[ptr+76:ptr+78], False, False),
                      "binary_format": doradeTypes[halfw(data[ptr+78:ptr+80], False, False)],
                      "threshold_field": data[ptr+80:ptr+88].rstrip(b"\x00").rstrip(),
                      "threshold_value": floating(data[ptr+88:ptr+92], False),
                      "parameter_scale": floating(data[ptr+92:ptr+96], False),
                      "parameter_bias": floating(data[ptr+96:ptr+100], False),
                      "bad_data": word(data[ptr+100:ptr+104], True, False)}
                if parm["nbytes"] == 216:
                    parm["extension_num"] = word(data[ptr+104:ptr+108], False, False)
                    parm["config_name"] = data[ptr+108:ptr+116].rstrip(b"\x00").rstrip()
                    parm["config_num"] = word(data[ptr+116:ptr+120], False, False)
                    parm["offset_to_data"] = word(data[ptr+120:ptr+124], False, False)
                    parm["mks_conversion"] = floating(data[ptr+124:ptr+128], False)
                    parm["num_qnames"] = word(data[ptr+128:ptr+132], False, False)
                    parm["qdata_names"] = []
                    for j6 in range(132,132+parm["num_qnames"]*8,8):
                        parm["qdata_names"].append(data[ptr+j6:ptr+j6+8].rstrip(b"\x00").rstrip())
                    parm["num_criteria"] = word(data[ptr+164:ptr+168], False, False)
                    parm["criteria_names"] = []
                    for j7 in range(168,168*parm["num_criteria"]*8,8):
                        parm["criteria_names"].append(data[ptr+j7:ptr+j7+8].rstrip(b"\x00").rstrip())
                    parm["number_cells"] = word(data[ptr+200:ptr+204], False, False)
                    parm["meters_to_first_cell"] = floating(data[ptr+204:ptr+208], False)
                    parm["meters_between_cells"] = floating(data[ptr+208:ptr+212], False)
                    parm["eff_unamb_vel"] = floating(data[ptr+212:ptr+216], False)
                ptr+=parm["nbytes"]
                parms.append(parm)

            nextItem = data[ptr:ptr+4] #Either CELV or CSFD
            celv={}
            csfd={}
            if nextItem == b"CELV":
                celv["nbytes"] = word(data[ptr+4:ptr+8], False, False)
                celv["number_cells"] = word(data[ptr+8:ptr+12], False, False)
                celv["dist_cells"] = []
                for j8 in range(12,12+celv["number_cells"]*4,4):
                    celv["dist_cells"].append(floating(data[ptr+j8:ptr+j8+4], False))
                rstart=celv["dist_cells"][0]*0.001
                rscale=(celv["dist_cells"][1]-celv["dist_cells"][0])*0.001
                ptr+=celv["nbytes"]
            elif nextItem == b"CSFD":
                csfd["nbytes"] = word(data[ptr+4:ptr+8], False, False)
                csfd["num_segments"] = word(data[ptr+8:ptr+12], False, False)
                csfd["dist_to_first"] = floating(data[ptr+12:ptr+16], False)
                csfd["spacing"] = []
                for j8 in range(16,48,4):
                    csfd["spacing"].append(floating(data[ptr+j8:ptr+j8+4], False))
                csfd["num_cells"] = halfw(data[ptr+48:ptr+50], False, False)
                ptr+=csfd["nbytes"]

            #CFAC
            cfac={"nbytes": word(data[ptr+4:ptr+8], False, False)}
            ptr+=8
            for key in ["azimuth_corr", "elevation_corr", "range_delay_corr", "longitude_corr", "latitude_corr", "pressure_alt_corr", "radar_alt_corr", "ew_gndspd_corr", "ns_gndspd_corr", "vert_vel_corr", "heading_corr", "roll_corr", "pitch_corr", "drift_corr", "rot_angle_corr", "tilt_corr"]:
                cfac[key] = floating(data[ptr:ptr+4], False)
                ptr+=4
            self.sensors.append({"radd":radd,"parms":parms,"celv":celv,"csfd":csfd,"cfac":cfac})

        #SWIB
        #DANGER WILL ROBINSON - ASSUMING A FILE WHERE THERE IS ONLY ONE SENSOR
        sweepCount=0
        while data[ptr:ptr+4] == b"SWIB":
            prfs = self.sensors[sweepCount]["radd"]["prfs"]
            highprf = max(prfs)
            lowprf = min(prfs)
            self.azimuths.append([])
            self.data.append({})
            self.quantities.append([])
            self.elevations.append([])
            self.swib={"nbytes":word(data[ptr+4:ptr+8], False, False),
                       "radar_name": data[ptr+8:ptr+16].rstrip(b"\x00").rstrip(),
                       "sweep_num": word(data[ptr+16:ptr+20], False, False),
                       "num_rays": word(data[ptr+20:ptr+24], False, False),
                       "start_angle": floating(data[ptr+24:ptr+28], False),
                       "stop_angle": floating(data[ptr+28:ptr+32], False),
                       "fixed_angle": floating(data[ptr+32:ptr+36], False),
                       "filter_flag": word(data[ptr+36:ptr+40], False, False)}

            ptr+=self.swib["nbytes"]

            for k in range(self.swib["num_rays"]):

                #RYIB

                self.ryib={"nbytes":word(data[ptr+4:ptr+8], False, False),
                           "sweep_num":word(data[ptr+8:ptr+12], False, False),
                           "julian_day":word(data[ptr+12:ptr+16], False, False),
                           "hour":halfw(data[ptr+16:ptr+18], False, False),
                           "minute":halfw(data[ptr+18:ptr+20], False, False),
                           "second":halfw(data[ptr+20:ptr+22], False, False),
                           "millisecond":halfw(data[ptr+22:ptr+24], False, False),
                           "azimuth":floating(data[ptr+24:ptr+28], False),
                           "elevation":floating(data[ptr+28:ptr+32], False),
                           "peak_power":floating(data[ptr+32:ptr+36], False),
                           "true_scan_rate":floating(data[ptr+36:ptr+40], False),
                           "ray_status": word(data[ptr+40:44], False, False)}
                ptr+=self.ryib["nbytes"]

                #print(self.ryib)
                self.azimuths[-1].append(self.ryib["azimuth"])
                self.elevations[-1].append(self.ryib["elevation"])

                #ASIB
                self.asib={"nbytes":word(data[ptr+4:ptr+8], False, False)}
                ptr+=8
                for key in ["longitude", "latitude", "altitude_msl", "altitude_agl", "ew_velocity", "ns_velocity", "vert_velocity", "heading", "roll", "pitch", "drift_angle", "rotation_angle", "tilt", "ew_horiz_wind", "ns_horiz_wind", "vert_wind", "heading_change", "pitch_change"]:
                    self.asib[key] = floating(data[ptr:ptr+4], False)
                    ptr+=4
                if k == 0: #Populate headers with location
                    self.headers["longitude"]=self.asib["longitude"]
                    self.headers["latitude"]=self.asib["latitude"]
                    self.headers["height"]=self.asib["altitude_msl"]

                for l in range(len(self.sensors[sweepCount]["parms"])):
                    nextItem = data[ptr:ptr+4] #RDAT or QDAT!
                    params=self.sensors[sweepCount]["parms"][l]
                    compression=self.sensors[sweepCount]["radd"]["data_compress"]
                    qty = params["parameter_name"].decode("utf-8")

                    if qty not in self.data[-1]:
                        baddata=params["bad_data"]
                        self.data[-1][qty]={"data":[],"highprf": highprf, "lowprf": lowprf if qty != "VF" else highprf, "gain":1/params["parameter_scale"],"offset":params["parameter_bias"],"undetect":params["bad_data"],"nodata":baddata,"rstart":rstart,"rscale":rscale}
                        self.quantities[-1].append(qty)
                    if nextItem == b"RDAT":
                        rdat={"nbytes": word(data[ptr+4:ptr+8], False, False),
                              "pdata_name": data[ptr+8:ptr+16].rstrip(b"\x00").rstrip()}
                        datarow=np.fromstring(data[ptr+16:ptr+rdat["nbytes"]],params["binary_format"]).tolist()
                        if compression == 1: #If HRD compression is being used
                            datarownew=[]
                            datarowptr=0
                            while datarowptr < len(datarow):
                                val = datarow[datarowptr]
                                if val < -30000 and val != baddata:
                                    amt = val & 32767
                                    datarowptr += 1
                                    datarownew += datarow[datarowptr:datarowptr+amt]
                                    datarowptr += amt-1
                                else:
                                    if val != 1:
                                        datarownew += [baddata]*val
                                    else: #1 = end of compression. Considering the ray ended
                                        break
                                datarowptr += 1
                            datarow=datarownew
                        self.data[-1][qty]["data"].append(datarow)
                        ptr+=rdat["nbytes"]

            if data[ptr:ptr+4] == b"NULL": #NULL block
                ptr+=word(data[ptr+4:ptr+8], False, False)

            if data[ptr:ptr+4] == b"RKTB": #NULL block
                ptr+=word(data[ptr+4:ptr+8], False, False)

            if data[ptr:ptr+4] == b"SEDS": #Editor History Block
                blockLength = word(data[ptr+4:ptr+8], False, False)
                self.seds=data[ptr+12:ptr+blockLength]

            self.wavelength = 0.299792458/self.sensors[sweepCount]["radd"]["freqs"][0]

            #Process azimuth data - in TRV data model they indicate the beginning of a ray not the centre
            for i in range(len(self.azimuths)):
                newazlist=[]
                for j in range(len(self.azimuths[i])):
                    oldaz = self.azimuths[i][j-1]
                    newaz = self.azimuths[i][j]
                    if oldaz > newaz and oldaz > 350:
                        oldaz -= 360
                    newazlist.append((oldaz+newaz)/2)
                self.azimuths[i] = newazlist
                
            self.nominalElevations.append(round(sum(self.elevations[-1])/len(self.elevations[-1]),2))
            self.elevationNumbers.append(len(self.nominalElevations)-1)
            sweepCount += 1

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

                    
                self.data=[{quantityInFile:{"data":[],"highprf":highprf,"lowprf":lowprf,"gain":0.1,"offset":-32.0 if quantityInFile == "DBZH" else -409.6, "nodata":2047 if quantityInFile == "DBZH" else 8191, "undetect":0, "rangefolding":1,"rscale":self.dataDescriptionSection["rscale"],"rstart":self.dataDescriptionSection["rstart"]}}]
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
                    messageSize=halfw(fullmsg[msgptr:msgptr+2], False)
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
                        if elevationNumber in [255]:
                            break #Okay, looks like empty data. Skipping.
                        else:
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
                            if rMax > 0:
                                PRF=round(150000/rMax)
                            else:
                                PRF=None
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
                                    if PRF:
                                        self.data[elIndex][quantityName]={"data":[],"gain":dataGain,"offset":dataOffset,"undetect":0,"rangefolding":1,"nodata":2**dataWordSize-1,"rscale":rscale,"rstart":halfw(msg[x+10:x+12])/1000-rscale/2,"highprf":PRF,"lowprf":PRF}
                                    else:
                                        self.data[elIndex][quantityName]={"data":[],"gain":dataGain,"offset":dataOffset,"undetect":0,"rangefolding":1,"nodata":2**dataWordSize-1,"rscale":rscale,"rstart":halfw(msg[x+10:x+12])/1000-rscale/2}
                                    self.quantities[elIndex].append(quantityName)

                                if dataWordSize == 8:
                                    dataRow=array("B",msg[x+28:x+28+dataQuantityGatesNr])
                                elif dataWordSize == 16:
                                    dataRow=array("H",msg[x+28:x+28+dataQuantityGatesNr*2])
                                    dataRow.byteswap() #CAVEAT: byteswap modifies the variable in place and returns None!
                                self.data[elIndex][quantityName]["data"].append(dataRow)
                        msgptr+=messageSize*2+12
                    else: #Not message 31 - skipping over and moving ahead by 2432 bytes.
                        msgptr+=2432
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
                    if x[j] < eelmine_az and eelmine_az-x[j] > 300: #If crossing North
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
                            dataarray=np.array(andmed[scanname]["scan_"+KNMIQtys[j]+"_data"])
                            scandata[ODIMQtys[j]]={"undetect":0,
                                                   "nodata":0,
                                                   "rstart":0,
                                                   "rscale":rscale,
                                                   "highprf":highPRF,
                                                   "lowprf":lowPRF,
                                                   "rangefolding": -999999,
                                                   "gain":gain,
                                                   "offset":offset,
                                                   "data":dataarray,
                                                   "dataType":type(dataarray[0][0])}
                        self.data.append(scandata)
                        self.azimuths.append(azimuthslist)
                        self.quantities.append(ODIMQtys)
                else:
                    raise FileFormatError("This is not an ODIM H5 file and neither looks it like KNMI's")
                    
        andmed.close()


IRISTypes={0: "DB_XHDR", 1: "TH", 2: "DBZH", 3: "VRADH", 4: "WRADH",
           5: "ZDR", 7: "DBZH", 8: "TH", 9: "DBZH", 10: "VRADH", #7 - CORRECTED
           11: "WRADH", 12: "ZDR", 13: "RATE", 14: "KDP",
           15: "KDP", 16: "PHIDP", 17: "VRADDH", 18: "SQI",
           19: "RHOHV", 20: "RHOHV", 21: "DBZH", 22: "VRADDH",
           23: "SQI", 24: "PHIDP", 25: "LDR", 26: "LDRH",
           27: "LDRV", 28: "LDRV", 32: "DB_HEIGHT", 33: "VIL",
           34: "RAW", 35: "DB_SHEAR", 36: "DB_DIVERGE2", 37: "DB_FLIQUID2",
           38: "DB_USER", 39: "DB_OTHER", 40: "DB_DEFORM2", 41: "DB_VVEL2",
           42: "DB_HVEL2", 43: "DB_HDIR2", 44: "DB_AXDIL2", 45: "DB_TIME2",
           46: "DB_RHOH", 47: "DB_RHOH2", 48: "DB_RHOV", 49: "DB_RHOV2",
           50: "DB_PHIH", 51: "DB_PHIH2", 52: "DB_PHIV", 53: "DB_PHIV2",
           54: "DB_USER2", 55: "HCLASS", 56: "HCLASS", 57: "ZDR",
           58: "ZDR", 75: "DB_PMI8", 76: "DB_PMI16", 77: "DB_LOG8",
           78: "DB_LOG16", 79: "DB_CSP8", 80: "DB_CSP16", 81: "CCORH",
           82: "CCORV", 83: "DB_AH8", 84: "DB_AH16", 85: "DB_AV8",
           86: "DB_AV16", 87: "DB_AZDR8", 88: "DB_AZDR16"}

#Format [gain, offset]

def dataTypesFromMask(dataWord,offset=0):
    products=[]
    for i in range(32):
        bit = (dataWord & (1 << i)) >> i
        if bit:
            products.append(IRISTypes[i+offset])
    return products
    
def task_calib_flags(i): #For IRIS data
    result={"bit15": (i & 0b1000000000000000) >> 15, #Speckle remover for log channel
            "bit14": (i & 0b0100000000000000) >> 14, #Unused?
            "bit13": (i & 0b0010000000000000) >> 13, #Unused?
            "bit12": (i & 0b0001000000000000) >> 12, #Speckle remover for linear channel
            "bit11": (i & 0b0000100000000000) >> 11, #Data is range normalized
            "bit10": (i & 0b0000010000000000) >> 10, #Pulse at beginning of ray
            "bit09": (i & 0b0000001000000000) >> 9, #Pulse at the end of ray
            "bit08": (i & 0b0000000100000000) >> 8, #Vary number of pulses in DualPRF
            "bit07": (i & 0b0000000010000000) >> 7, #Use 3 lag processing in PPO 2
            "bit06": (i & 0b0000000001000000) >> 6, #Apply vel correction for ship mtn
            "bit05": (i & 0b0000000000100000) >> 5, #Vc is unfolded
            "bit04": (i & 0b0000000000010000) >> 4, #Vc has fallspeed correction
            "bit03": (i & 0b0000000000001000) >> 3, #Zc has beam blockage correction
            "bit02": (i & 0b0000000000000100) >> 2, #Zc has Z-based attenuation correction
            "bit01": (i & 0b0000000000000010) >> 1, #Zc has target detection
            "bit00": (i & 1) #Vc has storm relative velocity correction
        }
    return result
def binaryAngle(angle, bits): #For IRIS data
    return 360*angle/2**(bits)
def ymds_time(b, bigEndian=True): #For IRIS data
    secondsSinceMidnight=word(b[0:4], True, bigEndian)
    millisecondsFull=halfw(b[4:6], False, bigEndian)
    milliseconds = millisecondsFull >> 6
    timeIsDST = millisecondsFull & 0b0000010000000000 >> 10
    timeIsUTC = millisecondsFull & 0b0000100000000000 >> 11
    localTimeIsDST = millisecondsFull & 0b0001000000001000 >> 12
    year = halfw(b[6:8], True, bigEndian)
    month = halfw(b[8:10], True, bigEndian)
    day = halfw(b[10:12], True, bigEndian)
    outdateTime=datetime.datetime(year, month, day) + datetime.timedelta(seconds = secondsSinceMidnight, milliseconds = milliseconds)
    return {"time":outdateTime, "timeisDST": timeIsDST, "timeisUTC": timeIsUTC, "localTimeIsDST": localTimeIsDST}


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
        newData = deepcopy(dataObject.data[index][quantity]["data"])
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
        elif dataObject.type == "IRIS":
            file["what"].attrs.create("source",b"PLC:" + dataObject.product_hdr["product_end"]["siteName"].title())
        elif dataObject.type == "DORADE":
            file["what"].attrs.create("source",b"CMT:" + dataObject.sensors[0]["radd"]["radar_name"])
            
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
            file[datasetName]["what"].attrs.create("startdate",min(dataObject.times[i]).strftime("%Y%m%d").encode("utf-8"))
            file[datasetName]["what"].attrs.create("starttime",min(dataObject.times[i]).strftime("%H%M%S").encode("utf-8"))
            file[datasetName]["what"].attrs.create("enddate",max(dataObject.times[i]).strftime("%Y%m%d").encode("utf-8"))
            file[datasetName]["what"].attrs.create("endtime",max(dataObject.times[i]).strftime("%H%M%S").encode("utf-8"))
            
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
                if "dataType" in dataObject.data[i][j]:
                    file[datasetName][dataName].create_dataset("data", (nrays,nbins), data=padData(dataObject.data[i][j]["data"]), dtype=dataObject.data[i][j]["dataType"], compression="gzip")
                else:
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
              "CLASS":fraasid["product_hclass"],
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
              "ZH":fraasid["product_reflectivity"],
              "DZ":fraasid["product_reflectivity"],
              "DCC":fraasid["product_reflectivity"],
              "VE":fraasid["product_radialvelocity"],
              "VC":fraasid["product_radialvelocity"],
              "VF":fraasid["product_radialvelocity"],
              "VW":fraasid["product_sw"],
              "ZD":fraasid["product_zdr"],
              "RH":fraasid["product_rhohv"],
              "PH":fraasid["product_phi"],
              "SH":fraasid["dorade_sh"],
              "SV":fraasid["dorade_sv"],
              "AH":fraasid["dorade_ah"],
              "AD":fraasid["dorade_ad"],
              "DM":fraasid["dorade_dm"],
              "NCP":fraasid["dorade_ncp"],
              "DCZ":fraasid["dorade_dcz"],
              }
    return products[quantity]

def rhiheadersdecoded(display,fraasid):
    if fraasid["LANG_ID"] != "AR":
        msg=productname(display.quantity,fraasid).capitalize()+" | "+fraasid["azimuth"]+": "+str(display.rhiAzimuth)+u"° | "+str(display.productTime)+" UTC"
    else:
        if platform.system() != "Linux":
            msg=fixArabic(productname(display.quantity,fraasid).capitalize())+u" | °"+str(display.rhiAzimuth)+u" :"+fixArabic(fraasid["azimuth"])+" | UTC "+str(display.productTime)
        else:
            msg=productname(display.quantity,fraasid).capitalize()+u" | °"+str(display.rhiAzimuth)+u" :"+fraasid["azimuth"]+" | UTC "+str(display.productTime)
    return msg
def headersdecoded(display,fraasid):
    if fraasid["LANG_ID"] != "AR":
        msg=str(round(float(display.elevation),3))+u"° "+productname(display.quantity,fraasid)+" | "+str(display.productTime)+" UTC"
    else:
        if platform.system() != "Linux":
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

def HDF5scaleValue(value,gain,offset,nodata,undetect,rangefolding,quantity,variabletype,wavelength):
    if value != nodata and value != undetect and value != rangefolding:
        if variabletype is NP_INT16:
            value=NP_UINT16(value)
        if quantity == "ZDR" and offset == 8.0: offset = -8 #A fix to bad offsets in some HDF5 files
        elif (quantity == "RHOHV" or quantity == "QIDX" or quantity == "SQI") and variabletype is NP_UINT8: #To get around IRIS's non-linear 8 bit variables for these quantities.
            if value > 0:
                return sqrt((value-1)/253)
            else:
                return None
        elif quantity == "KDP" and variabletype is NP_UINT8: #Once again work-around for IRIS's non-linear variables
            if value < 128:
                return (-0.25*600**((127-value)/126))/(wavelength*100)
            elif value > 128:
                return (0.25*600**((value-129)/126))/(wavelength*100)
            elif value == 128:
                return 0
            else:
                return None
        elif quantity == "HCLASS":
            return IrisMETEO(value)
        else:
            return value*gain+offset
    else:
        if value == rangefolding:
            return "RF"
        else:
            return None
