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

## Attempt to fix Arabic rendering problems
import os

def fixArabic(nas="مرحبا"):
    punctuationLatin = [u".", u",", u":", u";", u"?", u"(", u")"]
    punctuationArabic = [u".", u"،", u":", u"؛", u"؟", u")", u"("]
    alifs = [u"ا", u"إ", u"أ", u"آ"]
    laamAlifs = [u"ﻻ", u"ﻹ", u"ﻷ", u"ﻵ"]
    laamAlifsFinal = [u"ﻼ", u"ﻺ", u"ﻸ", u"ﻶ"]
    finalOnly = [u"ذ", u"د", u"ا", u"ؤ", u"ر", u"ى", u"ة", u"و", u"ز", u"إ", u"أ", u"آ", u"ﻻ", u"ﻹ", u"ﻷ", u"ﻵ"] #Words that only have isolated and final position
    isolated = [u"ذ", u"ض", u"ص", u"ث", u"ق", u"ف", u"غ", u"ع", u"ه", u"خ", u"ح", u"ج", u"د", u"ش", u"س", u"ي", u"ب", u"ل", u"ا", u"ت", u"ن", u"م", u"ك", u"ط", u"ئ", u"ؤ", u"ر", u"ى", u"ة", u"و", u"ز", u"ظ", u"إ", u"أ", u"آ", u"ﻻ", u"ﻹ", u"ﻷ", u"ﻵ"]
    initial = [None, u"ﺿ", u"ﺻ", u"ﺛ", u"ﻗ", u"ﻓ", u"ﻏ", u"ﻋ", u"ﻫ", u"ﺧ", u"ﺣ", u"ﺟ", None, u"ﺷ", u"ﺳ", u"ﻳ", u"ﺑ", u"ﻟ", None, u"ﺗ", u"ﻧ", u"ﻣ", u"ﻛ", u"ﻃ", u"ﺋ", None, None, None, None, None, None, u"ﻇ", None, None, None, None, None, None, None]
    medial = [None, u"ﻀ", u"ﺼ", u"ﺜ", u"ﻘ", u"ﻔ", u"ﻐ", u"ﻌ", u"ﻬ", u"ﺨ", u"ﺤ", u"ﺠ", None, u"ﺸ", u"ﺴ", u"ﻴ", u"ﺒ", u"ﻠ", None, u"ﺘ", u"ﻨ", u"ﻤ", u"ﻜ", u"ﻄ", u"ﺌ", None, None, None, None, None, None, u"ﻈ", None, None, None, None, None, None, None]
    final = [u"ﺬ", u"ﺾ", u"ﺺ", u"ﺚ", u"ﻖ", u"ﻒ", u"ﻎ", u"ﻊ", u"ﻪ", u"ﺦ", u"ﺢ", u"ﺞ", u"ﺪ", u"ﺶ", u"ﺲ", u"ﻲ", u"ﺐ", u"ﻞ", u"ﺎ", u"ﺖ", u"ﻦ", u"ﻢ", u"ﻚ", u"ﻂ", u"ﺊ", u"ﺆ", u"ﺮ", u"ﻰ", u"ﺔ", u"ﻮ", u"ﺰ", u"ﻆ", u"ﺈ", u"ﺄ", u"ﺂ", u"ﻼ", u"ﻺ", u"ﻸ", u"ﻶ"]

    output=""
    rows = nas.split("\n")
    rows.reverse()
    isArabic = False
    for words in rows:
        outputRow=""
        for i in words.split():
            registers = [isolated, initial, medial, final]
            register = isolated
            ptr = 0
            mode = 0 #0 - Non-Arabic, 1 - Arabic
            position = 0 #0 - Isolated, 1 - Initial, 2 - Medial, 3 - final
            initialNext=1
            wordOut = u""

            #Creating LaamAlifs, initially laam and alif are separated.
            for x in range(len(alifs)):
                i=i.replace(u"ل"+alifs[x],laamAlifs[x])
            wordlength = len(i) #Length of the word

            while ptr < wordlength:
                letter = i[ptr]
                if letter in isolated:
                    mode = 1
                    isArabic = True
                    if ptr == wordlength-1:
                        if initialNext:
                            position = 0
                        else:
                            position = 3
                    else:
                        if letter not in finalOnly:
                            if i[ptr+1] not in isolated:
                                if initialNext:
                                    position = 0
                                else:
                                    position = 3
                                    initialNext = 1
                            else:
                                if initialNext:
                                    position = 1
                                    initialNext = 0
                                else:
                                    position = 2
                        else:
                            if position > 0 and not initialNext:
                                position = 3
                                initialNext = 1
                            else:
                                position = 0
                                initialNext = 1
                    register = registers [position]
                    letterProcessed = register[isolated.index(letter)]
                else:
                    brackets = ["(", ")", "[", "]"]
                    mode = 1 if (letter == u"ء" or (mode == 1 and letter in punctuationArabic) or (mode == "1" and letter in brackets)) else 0
                    if letter not in brackets:
                        letterProcessed = letter
                    else:
                        replacement = [")", "(", "]", "["]
                        letterProcessed = replacement[brackets.index(letter)]
                    
                if mode == 0:
                    wordOut += letterProcessed
                else:
                    wordOut = letterProcessed + wordOut
                ptr+=1
            if not isArabic:
                outputRow += u" "+wordOut
            else:
                outputRow = wordOut + u" " + outputRow
        if len(outputRow) > 0:
            outputRow=outputRow.strip()
            if outputRow[0] == ":":
                outputRow = outputRow[1:]+u":"
            if outputRow[-1] == u".":
                outputRow = u"."+outputRow[:-1]
        output="\n" + outputRow + output
    output = output.strip() #Let's get rid of the last newline
    
    return output

#Phrases for TRV software
#Estonian
import sys

phrases={"estonian":
         {
             "LANG_ID":"ET",
             "name":"TRV 2018.3.7",
             "loading_states":"Laen andmeid... osariigid",
             "coastlines":"Rannajooned",
             "countries":"Maismaapiirid",
             "country_boundaries":"riigipiirid",
             "lakes":u"Järved",
             "rivers":u"Jõed",
             "placenames":"andmepunktid",
             "states_counties":"osariigid/maakonnad",
             "NA_roads":u"Põhja-Ameerika suured maanteed",
             "add_rmax":"Liida Rmax",
             "az0":"Algasimuut(°):",
             "az1":u"Lõppasimuut(°):",
             "r0":"Algkaugus(km):",
             "r1":u"Lõppkaugus(km):",
             "prf":"PRF(Hz):",
             "add":"Liida",
             "nexrad_choice":"NEXRAD jaama valik",
             "choose_station":"Vali jaam",
             "okbutton":"OK",
             "choose_station_error":"Palun vali jaam!",
             "open_url":"Ava fail internetist",
             "open":"Ava",
             "download_failed":u"Allalaadimine ebaõnnestus!",
             "hca_names":["Bioloogiline",
                   u"Anomaalne levi/pinnamüra",
                   u"Jääkristallid",
                   "Kuiv lumi",
                   u"Märg lumi",
                   "Vihm",
                   "Tugev vihm",
                   "Suured piisad",
                   "Lumekruubid",
                   "Rahe",
                   "Tundmatu",
                   "RF"],
             "iris_hca":["",
                         "Mittemeteoroloogiline",
                         "Vihm",
                         u"Märg lumi",
                         "Lumi",
                         "Lumekruubid",
                         "Rahe"],
             "level3_slice":u"Lõik /NR/",
             "export_success":"Eksport edukas",
             "export_format_fail":u"Valitud vormingusse ei saa salvestada või puudub asukohas kirjutamisõigus.",
             "no_data":"Andmed puuduvad",
             "about_text":"Tarmo Tanilsoo, 2018\ntarmotanilsoo@gmail.com\n\nPythoni versioon: "+sys.version,
             "key_shortcuts_dialog_text":u"Otseteed klaviatuuril:\n\nz - suurendamisrežiimi\np - ringiliikumisrežiimi\ni - inspektsioonirežiim\nr - algsuurendusse tagasi",
             "azimuth":"Asimuut",
             "range":"Kaugus",
             "value":u"Väärtus",
             "beam_height":u"Kiire kõrgus",
             "g2g_shear":"G2G nihe",
             "height":u"Kõrgus",
             "drawing":"Joonistan...",
             "radar_image":"radaripilt",
             "ready":"Valmis",
             "decoding":"Dekodeerin...",
             "incorrect_format":u"Viga: Tegemist ei ole õiges formaadis failiga", #Apparently none of supported formats
             "not_found_at_this_level":u"Sellel kõrgustasemel seda produkti ei leitud.",
             "error_during_loading":"Laadimisel juhtus viga",
             "choose_pseudorhi_status":"Kliki asimuudil, millest soovid PseudoRHI'd teha",
             "cant_make_pseudorhi":u"PseudoRHI'd ei ole nende andmetega võimalik teha",
             "reading_elevation":"Loen elevatsiooni: ",
             "drawing_pseudorhi":"Joonistan pseudoRHI'd",
             "file":"Fail",
             "nexrad":"NEXRAD Level 3",
             "tools":u"Tööriistad",
             "help":"Abi",
             "open_datafile":"Ava andmefail",
             "export_img":"Ekspordi pilt",
             "quit":u"Lõpeta",
             "current_data":"Jooksvad andmed",
             "level3_station_selection":"Jaama valik",
             "dealiasing":"Radiaalkiiruste dealiasing",
             "key_shortcuts_menuentry":"Otseteed klaviatuuril",
             "about_program":"Info programmi kohta",
             "th":u"täielik peegelduvus (h)",
             "tv":u"täielik peegelduvus (v)",
             "product_reflectivity":"peegelduvus",
             "dbzh":"peegelduvus (h)",
             "dbzv":"peegelduvus (v)", 
             "sqi":"signaalikvaliteedi indeks", 
             "sqih":"signaalikvaliteedi indeks (h)",
             "sqiv":"signaalikvaliteedi indeks (v)",
             "product_radialvelocity":"radiaalkiirus",
             "vradh":"radiaalkiirus (h)",
             "vradv":"radiaalkiirus (v)",
             "vraddh":"dealiasitud radiaalkiirus (h)",
             "vraddv":"dealiasitud radiaalkiirus (v)",
             "product_rhohv":"korrelatsioonikoefitsent",
             "product_zdr":"diferentsiaalne peegelduvus",
             "product_kdp":"spetsiifiline diferentsiaalne faas",
             "product_hclass":u"hüdrometeoori klassifikatsioon",
             "product_sw":"spektrilaius",
             "wradh":"spektrilaius (h)",
             "wradv":"spektrilaius (v)",
             "product_phi":"diferentsiaalne faas",
             "qidx":"kvaliteet",
             "no_data_loaded":"Andmeid pole laetud!",
             "current_language":"Keel",
             "language_estonian":"Eesti keel",
             "language_english":"English",
             "language_arabic":"عربي" if os.name == "nt" else fixArabic(u"عربي"),
             "conf_restart_required":u"Muutus aktiveerub programmi taaskäivitamisel.",
             "dyn_labels":u"Dünaamilised andmepunktid",
             "color_table":u"Värvitabeli vahetus",
             "default_colors":u"Vaikimisi värvid",
             "dyn_new":"Lisa",
             "dyn_edit":"Muuda",
             "dyn_rm":"Kustuta",
             "dyn_rm_sure":"Kindel, et soovid seda allikat kustutada?",
             "dyn_online":"Internetis",
             "dyn_local":"Kohalik",
             "dyn_path":"Aadress:",
             "dyn_interval":"Miinimumvahe uuenduste vahel(min): ",
             "dyn_enabled":u"Sisse lülitatud",
             "batch_export":"Ekspordi hulgi",
             "batch_input":"Andmete kaust: ",
             "batch_output":u"Väljundi kaust: ",
             "batch_pick":"Vali kaust",
             "batch_fmt":u"Väljundi vorming",
             "batch_quantity":u"Väärtus",
             "batch_el":"Kaldenurk",
             "batch_notfound":u"Päritud andmeid ei leitud sellel kõrgustasemel failis ",
             "batch_notfound2":"Eksport katkestatakse.",
             "batch_notfilled":u"Palun vaadake, et nii andmete kui ka väljundi kaust oleks määratud.",
             "ddp_error":u"Viga dünaamiliste andmepunktide failis: ",
             "dwd_credit":"Andmete allikas: Deutscher Wetterdienst",
             "download_entire_volume":"Lae alla kogu ruumiskaneering...",
             "linear_interp":"Lineaarne interpolatsioon",
             "dwd_volume_download":"DWD ruumiskanneeringu alla laadimine",
             "radar_site":"Radarijaam: ",
             "output_file":"Väljundi fail: ",
             "start_download":"Laadi alla",
             "loading_in_progress":"Laadin...",
             "invalid_date":"Kuupäev/kellaaeg ei ole korrektselt sisestatud",
             "volume_incomplete":"Ruumiskannering ei ole täielik. See võib olla veel pooleli",
             "volume_not_found":"Andmeid ei leitud",
             "saving_as_HDF5":"Salvestan ODIM HDF5 formaadis...",
             "downloading_file":"Laen alla faili:",
             "loading_from_cache":"Laen puhvrist:",
             "downloading...":"Laen alla...",
             "checkingKNMI":"Kontrollin, kas allalaadimine on vajalik",
             "export_odim_h5":"Ekspordi ODIM HDF5'na",
             "delete_cache":"Tühjenda puhver",
             "delete_cache_complete":"Puhver on tühjendatud.",
             "date": "Kuupäev",
             "time": "Kell",
             "dealiassequence1": "Järjestikku 1-2-3-2-1",
             "dealiassequence2": "Järjestikku 2-1-4-3-1",
             "dealias1":"1 - piki kiirt radarist eemale",
             "dealias2":"2 - kiirega risti, päripäeva",
             "dealias3":"3 - piki kiirt radari poole",
             "dealias4":"4 - kiirega risti, vastupäeva",
             "nodependencies":"Kõik vajalikud moodulid ei ole paigaldatud. Sulen 5 sekundi pärast"
             },
         "english":
         {
             "LANG_ID":"EN",
             "name":"TRV 2018.3.7",
             "loading_states":"Loading data... states",
             "coastlines":"Coastlines",
             "countries":"Countries",
             "country_boundaries":"country boundaries",
             "lakes":"Lakes",
             "rivers":"Rivers",
             "placenames":"data points",
             "states_counties":"states/counties",
             "NA_roads":"Major North American highways",
             "add_rmax":"Add Rmax",
             "az0":"Initial azimuth(°):",
             "az1":"Final azimuth(°):",
             "r0":"Initial range(km):",
             "r1":u"Final range(km):",
             "prf":"PRF(Hz):",
             "add":"Add",
             "nexrad_choice":"NEXRAD station choice",
             "choose_station":"Choose a station",
             "okbutton":"OK",
             "choose_station_error":"Please choose a station!",
             "open_url":"Open an URL",
             "open":"Open",
             "download_failed":u"Download failed!",
             "hca_names":["Biological",
                   "Anomalous propagation/ground clutter",
                   u"Ice crystals",
                   "Dry snow",
                   u"Wet snow",
                   "Rain",
                   "Heavy rain",
                   "Large drops",
                   "Graupel",
                   "Hail",
                   "Unknown",
                   "RF"],
             "iris_hca":["",
                         "Non-meteorological",
                         "Rain",
                         "Wet snow",
                         "Snow",
                         "Graupel",
                         "Hail"],
             "level3_slice":u"Slice /NR/",
             "export_success":"Export successful",
             "export_format_fail":"Either unable to save into this format or lacking writing permissions at the destination.",
             "no_data":"No data",
             "about_text":"Tarmo Tanilsoo, 2018\ntarmotanilsoo@gmail.com\n\nPython version: "+sys.version,
             "key_shortcuts_dialog_text":u"Shortcuts on keyboard:\n\nz - zoom mode\np - panning mode\ni - data inspection mode\nr - reset zoom",
             "azimuth":"Azimuth",
             "range":"Range",
             "value":u"Value",
             "beam_height":u"Beam height",
             "g2g_shear":"G2G shear",
             "height":u"Height",
             "drawing":"Drawing...",
             "radar_image":"radar image",
             "ready":"Ready",
             "decoding":"Decoding...",
             "incorrect_format":u"Error. File is not in a supported format", #Apparently none of supported formats
             "not_found_at_this_level":u"Product not found at this elevation.",
             "error_during_loading":"Error during loading",
             "choose_pseudorhi_status":"Click at the desired azimuth to generate a pseudoRHI",
             "cant_make_pseudorhi":u"It is not possible to make a pseudoRHI using this data file",
             "reading_elevation":"Reading elevation: ",
             "drawing_pseudorhi":"Drawing a pseudoRHI",
             "file":"File",
             "nexrad":"NEXRAD Level 3",
             "tools":u"Tools",
             "help":"Help",
             "open_datafile":"Open data file",
             "export_img":"Export image",
             "quit":u"Quit",
             "current_data":"Current data",
             "level3_station_selection":"Station selection",
             "dealiasing":"Radial velocities dealiasing",
             "key_shortcuts_menuentry":"Keyboard shortcuts",
             "about_program":"About",
             "product_reflectivity":"reflectivity",
             "th":u"total reflectivity (h)",
             "tv":u"total reflectivity (v)",
             "dbzh":"reflectivity (h)",
             "dbzv":"reflectivity (v)", 
             "sqi":"signal quality index",
             "sqih":"signal quality index (h)",
             "sqiv":"signal quality index (v)",
             "qidx":"quality",
             "product_radialvelocity":"radial velocity",
             "vradh":"radial velocity (h)",
             "vradv":"radial velocity (v)",
             "vraddh":"dealiased radial velocity (h)",
             "vraddv":"dealiased radial velocity (v)",
             "product_zdr":"differential reflectivity",
             "product_rhohv":"correlation coefficient",
             "product_kdp":"specific differential phase",
             "product_hclass":"hydrometeor classification",
             "product_sw":"spectrum width",
             "wradh":"spectrum width (h)",
             "wradv":"spectrum width (v)",
             "product_phi":"differential phase",
             "no_data_loaded":"No data loaded!",
             "current_language":"Language",
             "language_estonian":"Eesti keel",
             "language_english":"English",
             "language_arabic":"عربي" if os.name == "nt" else fixArabic(u"عربي"),
             "conf_restart_required":"Change will take effect upon next startup.",
             "dyn_labels":"Dynamic data points",
             "color_table":"Color table override",
             "default_colors":"Default colors",
             "dyn_new":"Add",
             "dyn_edit":"Edit",
             "dyn_rm":"Delete",
             "dyn_rm_sure":"Are you sure you want to delete this entry?",
             "dyn_online":"Online",
             "dyn_local":"Local",
             "dyn_path":"Path:",
             "dyn_interval":"Minimum interval between updates(min):",
             "dyn_enabled":"Enabled",
             "batch_export":"Batch export",
             "batch_input":"Input directory: ",
             "batch_output":"Output directory: ",
             "batch_pick":"Pick a directory",
             "batch_fmt":"Output format",
             "batch_quantity":"Quantity",
             "batch_el":"Elevation",
             "batch_notfound":"Requested data not found at this elevation in file ",
             "batch_notfound2":"Export will be stopped.",
             "batch_notfilled":"Please ensure that input and output directories are both specified",
             "ddp_error":"Error in dynamic data point file: ",
             "dwd_credit":"Data source: Deutscher Wetterdienst",
             "download_entire_volume":"Download entire volume...",
             "linear_interp":"Linear interpolation",
             "dwd_volume_download":"DWD volume scan download",
             "radar_site":"Radar site: ",
             "output_file":"Output file: ",
             "start_download":"Download",
             "loading_in_progress":"Loading...",
             "invalid_date":"Date or time is invalid",
             "volume_incomplete":"Volume scan is incomplete - it might still be in progress.",
             "volume_not_found":"Volume not found",
             "saving_as_HDF5":"Saving as ODIM HDF5...",
             "downloading_file":"Downloading file:",
             "loading_from_cache":"Loading from cache:",
             "downloading...":"Downloading...",
             "checkingKNMI":"Checking if downloading is necessary",
             "export_odim_h5":"Export as ODIM HDF5",
             "delete_cache":"Clear cache",
             "delete_cache_complete":"Cache has been emptied.",
             "date": "Date",
             "time": "Time",
             "dealiassequence1": "Sequence: 1-2-3-2-1",
             "dealiassequence2": "Sequence: 2-1-4-3-1",
             "dealias1":"1 - along the ray away from radar",
             "dealias2":"2 - orthogonal to the ray, clockwise",
             "dealias3":"3 - along the ray towards the radar",
             "dealias4":"4 - orthogonal to the ray, counter-clockwise",
             "nodependencies":"Some dependencies are not installed. Exiting in 5 seconds",
             },
         "arabic":  #NOTE: I am not a native speaker. Corrections are more than welcome as pull requests, especially from radar meteorologists(even from PME!)
         {
             "LANG_ID":"AR",
             "name":u"TRV 2018.3.7",
             "loading_states":u"فتح البيانات غيوغرافي... ولايات",
             "coastlines":u"خطوط الساحل",
             "countries":u"دول",
             "country_boundaries":u"حدود الدول",
             "lakes":u"بحيرات",
             "rivers":u"نهور",
             "placenames":u"نقطات البيانات",
             "states_counties":u"ولايات او مقاطعات",
             "NA_roads":u"الطرق رئيسي في الامريكا شمالية",
             "add_rmax":u"Rmax اضاقة",
             "add_rmax_ar":u"اضاقة Rmax", #For non-Windows systems using Arabic
             "az0":u"(°) السمت اولي:" if os.name == "nt" else u":السمت اولي )°( ",
             "az1":u"(°) السمت الأخير:" if os.name == "nt" else u":السمت الأخير )°(",
             "r0":u"(km) المسافة اولي:" if os.name == "nt" else u":المسافة اولي )km(",
             "r1":u"(km) المسافة الأخير:" if os.name == "nt" else u":المسافة الأخير )km(",
             "prf":u"(Hz) PRF:",
             "add":u"إضافة",
             "nexrad_choice":u"اختيار المحطة NEXRAD",
             "choose_station":u"اختيار المحطة",
             "okbutton":u"حسنا",
             "choose_station_error":u"اختر المحطة من فضلك",
             "open_url":u"افتح الرباط",
             "open":u"افنج",
             "download_failed":u"تحميل من الخادم غير ناجح.",
             "hca_names":[u"بيولوجية",
                   u"AP / شوائب",
                   u"بلورات جليدية",
                   u"ثلوج الجاف",
                   u"ثلوج مبلل",
                   u"امطار",
                   u"امطار شديدة",
                   u"قطرات مطر كبير",
                   u"كريات ثلجية",
                   u"برد",
                   u"غير معروف",
                   u"RF"],
             "iris_hca":["",
                         u"غير أرصادي",
                         u"امطار",
                         u"ثلوج مبلل",
                         u"ثلوج",
                         u"كريات ثلجية",
                         u"برد"],
             "level3_slice":u"شريحة /NR/",
             "export_success":u"التصدير ناجح",
             "export_format_fail":u"لا استطيع حفظ الملف في هذا تنسيق او لا عندي إذان لخلق ملفات في هذا عنوان.",
             "no_data":u"غير بيانات",
             "about_text":u"تارمو تانيلسُو، 2018\ntarmotanilsoo@gmail.com\n\n:الإصادر بايثون\n"+sys.version+u"" if os.name == "nt" else u"تارمو تانيلسو، 2018\ntarmotanilsoo@gmail.com\n\nالإصادر بايثون:\n"+fixArabic(sys.version)+u"",
             "key_shortcuts_dialog_text":u"اختصارات لوحة المفاتيح:\n\nوضع التكبير - z\nوصع التحرك الخريطة - p\nوضع فحص البيانات - i\nعاد إلى التكبير اصلي - r",
             "azimuth":u"السمت",
             "range":u"المسافة",
             "value":u"قيمة",
             "beam_height":u"ارتفاع الشعاع",
             "g2g_shear":u"القص G2G",
             "height":u"ارتفاع",
             "drawing":u"...ارسم" if os.name == "nt" else u"ارسم...",
             "radar_image":u"صورة الرادار",
             "ready":u"جاهز",
             "decoding":u"...اقرأ" if os.name == "nt" else u"اقرأ...",
             "incorrect_format":u"خطأ: الملف ليس في تنسيق معتمد", #Apparently none of supported formats
             "not_found_at_this_level":u"هذا منتج لا يوجد في هذه زاوية الارتفاع",
             "error_during_loading":u"خطا خلال فتح",
             "choose_pseudorhi_status":u"انقر على السمت المرغوب لخلق الصورة PseudoRHI",
             "cant_make_pseudorhi":u"لا استطيع خلق PseudoRHI من هذا ملف",
             "reading_elevation":u"اقرا زاوية الارتفاع:",
             "drawing_pseudorhi":u"ارسم PseudoRHI",
             "file":u"الملف",
             "nexrad":u"NEXRAD Level 3",
             "tools":u"ادوات",
             "help":u"مساعدة",
             "open_datafile":u"افتج الملف البيانات",
             "export_img":u"التصدير الصورة",
             "quit":u"اخرج",
             "current_data":u"البيانات الحالية",
             "level3_station_selection":u"اختيار المحطة",
             "dealiasing":u"تصحيح سرعات الدوبليرية",
             "key_shortcuts_menuentry":u"اختصارات لوحة المفاتيح",
             "about_program":u"عن البرنامج",
             "product_reflectivity":u"الانعكاسية",
             "th":u"الانعكاسية الخامة (افقية)",
             "tv":u"الانعكاسية الخامة (رأسية)",
             "dbzh":u"الانعكاسية (افقية)",
             "dbzv":u"الانعكاسية (رأسية)", 
             "sqi":u"المؤشر جودة الاشارة",
             "sqih":u"المؤشر جودة الاشارة (افقية)",
             "sqiv":u"المؤشر جودة الاشارة (رأسية)",
             "qidx":u"الجودة",
             "product_radialvelocity":u"السرعة دوبلير",
             "vradh":u"السرعة دوبلير (افقية)",
             "vradv":u"السرعة دوبلير (رأسية)",
             "vraddh":u"السرعة دوبلير المصححة (افقية)",
             "vraddv":u"السرعة دوبلير المصححة (رأسية)",
             "product_zdr":u"الانعكاسية التفاضلية",
             "product_rhohv":u"المعامل الإرتباط إستقطابي",
             "product_kdp":u"المعدل تغير الطور التفاضلي في المسافة اخصي",
             "product_hclass":u"التصنيف المصدر الانعكاس",
             "product_sw":u"العرض الطيف السرعة الدوبلير",
             "wradh":u"العرض الطيف السرعة الدوبلير (افقية)",
             "wradv":u"العرض الطيف السرعة الدوبلير (رأسية)",
             "product_phi":u"الطور التفاضلي",
             "no_data_loaded":u"ملف البيانات غير مفتوح!",
             "current_language":u"اللغة",
             "language_estonian":u"Eesti keel",
             "language_english":u"English",
             "language_arabic":u"عربي",
             "conf_restart_required":u"اللغة جديدة ستكون نشطة\nبعد إعادة التشغيل البرنامج.",
             "dyn_labels":u"نقطات البيانات ديناميكي",
             "color_table":u"تغير نظام الوان",
             "default_colors":u"الوان المبدئية",
             "dyn_new":u"إضافة",
             "dyn_edit":u"تغير",
             "dyn_rm":u"حذف",
             "dyn_rm_sure":u"هل انت اكيد ان يريد حذف هذا المصدر؟",
             "dyn_online":u"في إنترنت",
             "dyn_local":u"محلية",
             "dyn_path":u"عنوان:",
             "dyn_interval":u"اصغر فترة زمنية بين تحديثين(د):",
             "dyn_enabled":u"نشطة",
             "batch_export":u"التصدير الصور كثير",
             "batch_input":u"من دليل: ",
             "batch_output":u"إلى دليل: ",
             "batch_pick":u"اختر دليل",
             "batch_fmt":u"تنسيق الصور",
             "batch_quantity":u"المنتج: ",
             "batch_el":u"زاوية الارتفاع: ",
             "batch_notfound":u"بيانات لا يوجد في هذه زاوية الارتفاع",
             "batch_notfound2":u"تصدير ستوقف",
             "batch_notfilled":u"تاكد من فضلك ان اختر كل دليلين",
             "ddp_error":u"خطأ في الملف النقطات البيانات ديناميكي.: ",
             "dwd_credit":u"Deutscher Wetterdienst :مصدر البيانات" if os.name =="nt" else u"مصدر البيانات: Wetterdienst Deutscher",
             "download_entire_volume":u"تحميل كل ارتفاعات..." if os.name != "nt" else u"...تحميل كل ارتفاعات",
             "linear_interp":u"الاستيفاء الخطي",
             "dwd_volume_download":u"تحميل كل ارتفاعات في الدورة المسح من المانيا",
             "radar_site":u"محطة الرادار: ",
             "output_file":u"الملف الهدف: ",
             "start_download":u"اطلاق تحميل",
             "loading_in_progress":u"فتح..." if os.name != "nt" else "...فتح",
             "invalid_date":u"التاريخ او الوقت غير صالحة",
             "volume_incomplete":u"المسح ليس مكتمل - ربما يحدثها حتى الآن.",
             "volume_not_found":u"لا يوجد المسح",
             "saving_as_HDF5":u"...ODIM HDF5 تصدير إلى" if os.name == "nt" else u"ODIM HDF5 تصدير إلى...",
             "downloading_file":u":تحميل الملف" if os.name == "nt" else u"تحميل الملف:",
             "loading_from_cache":u":افتح من الذاكرة" if os.name == "nt" else u"افتح من الذاكرة:",
             "downloading...":u"تحميل..." if os.name != "nt" else u"...تحميل",
             "checkingKNMI":u"تحقق لو تحميل الملف بحاجة.",
             "export_odim_h5":u"HDF5 ODIM تصدير إلى" if os.name == "nt" else u"تصدير إلى HDF5 ODIM",
             "delete_cache":u"حذف ذاكرة مخبئة",
             "delete_cache_complete":u".حذفت ذاكرة مخبئة",
             "date":u"تاريخ",
             "time":u"وقت",
             "dealiassequence1": u"تعاقب: 1، 2، 3، 2، 1" if os.name == "nt" else u"تعاقب: ،1 ،2 ،3 ،2 1",
             "dealiassequence2": u"تعاقب: 2، 1، 4، 3، 1" if os.name == "nt" else u"تعاقب: ،2 ،1 ،4 ،3 1",
             "dealias1":u" - 1 على طول شعاع - بعيدا عن الرادار" if os.name != "nt" else u"على طول شعاع - بعيدا عن الرادار - 1",
             "dealias2":u" - 2 متعامد للشعاع - عقارب الساعة" if os.name != "nt" else u"متعامد للشعاع - عقارب الساعة - 2",
             "dealias3":u" - 3 على طول شعاع - نحو الرادار" if os.name != "nt" else u"على طول شعاع - نحو الرادار - 3",
             "dealias4":u" - 4 متعامد للشعاع - عكس عقارب الساعة" if os.name != "nt" else u"متعامد للشعاع - عكس عقارب الساعة - 4",
             "nodependencies":u"كل وحدات مطلوب غير مثبت. الخروج بعد 5 ثانيات"
             }
    }

if os.name != "nt": #On Windows Arabic seems to be OK. Assume every one else have it like Linux:
    strings = phrases["arabic"].keys()
    doNotFix = ["LANG_ID", "dwd_volume_download", "batch_export", "add_rmax", "nexrad_choice", "dyn_labels", "name", "prf", "language_estonian", "language_english"] #Stuff that is shown on title bar on Linux
    for i in strings:
        if i not in doNotFix:
            if type(phrases["arabic"][i]) is list:
                for j in range(len(phrases["arabic"][i])):
                    phrases["arabic"][i][j]=fixArabic(phrases["arabic"][i][j])
            else:
                phrases["arabic"][i]=fixArabic(phrases["arabic"][i])
