#Tarmo Tanilsoo, 2013

from math import floor

colortables=[[[0,0,0], #Z
             [50,79,79], 
             [102,139,139],
             [150,205,205],
             [174,238,238],
             [187,255,255],
             [0,236,236],
             [1,160,246], 
             [0,0,246], 
             [0,255,0], 
             [0,200,0], 
             [0,144,0], 
             [255,255,0], 
             [231,192,0], 
             [255,144,0], 
             [255,0,0], 
             [214,0,0], 
             [192,0,0], 
             [255,0,255], 
             [153,85,201], 
             [235,235,235]],
             [[0,255,0], #V
             [25,25,25],
             [255,0,0]],
            [[65,65,65], #RHOHV
             [0,0,51],
             [0,0,102],
             [0,0,153],
             [0,0,255],
             [0,102,255],
             [0,204,0],
             [255,255,0],
             [255,0,0]],
            [[25,25,25], #ZDR
             [55,55,55],
             [85,85,85],
             [115,115,115],
             [145,145,145],
             [175,175,175],
             [0,0,255],
             [125,125,255],
             [255,255,0],
             [125,255,0],
             [255,0,0],
             [255,125,125],
             [255,255,255]],
            [[125,125,125], #KDP
             [65,65,65],
             [65,0,25],
             [255,0,255],
             [0,255,255],
             [0,255,0],
             [255,255,0],
             [255,125,0],
             [255,125,255],
             [255,255,255]],
            [[175,175,175],
             [125,125,125],
             [255,200,200],
             [0,255,255],
             [0,200,200],
             [125,255,125],
             [0,180,0],
             [200,255,0],
             [255,125,125],
             [255,0,0],
             [255,0,255],
             [125,0,125]]]
default_limits=[[-25,75],
                [-63.5,63.5],
                [0.2,1],
                [-6,6],
                [-2,7],
                [0,11]]
def getcolor(val,index=0,smoothing=True,minlevel=-25,maxlevel=75):
    global colortables
    global defaultlimits
    r=0
    g=0
    b=0
    if minlevel==-25 and maxlevel==75: #Kui ei antud oma piire ette
        limit=default_limits[index]
        minlevel=limit[0]
        maxlevel=limit[1]
    coloramt=len(colortables[index])-1
    arrayspan=float((maxlevel-minlevel))
    colortable=colortables[index]
    if val < maxlevel and val >= minlevel:
        element=coloramt*(val-minlevel)/arrayspan
        intelement=int(element)
        curcolor=colortables[index][intelement]
        if smoothing:
            nextcolor=colortables[index][intelement+1]
            mod=element%1
            r=int(curcolor[0]+(nextcolor[0]-curcolor[0])*mod)
            g=int(curcolor[1]+(nextcolor[1]-curcolor[1])*mod)
            b=int(curcolor[2]+(nextcolor[2]-curcolor[2])*mod)
        else:
            r,g,b=curcolor
            
    elif val < minlevel:
        r,g,b=colortables[index][0]
    elif val > maxlevel:
        r,g,b=colortables[index][-1]
    return (r,g,b)
