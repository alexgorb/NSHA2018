import shapefile
from os import path
from shapely.geometry import Point, Polygon
from mapping_tools import get_field_data, get_field_index


###############################################################################
# parse AUS6 shp exported from MIF
###############################################################################

domshp = path.join('shapefiles', 'Domains_Sep2011_edit.shp')

print 'Reading source shapefile...'
sf = shapefile.Reader(domshp)
shapes = sf.shapes()
polygons = []
for poly in shapes:
    polygons.append(Polygon(poly.points))
    
# get src name
src_name = get_field_data(sf, 'CODE', 'str')

###############################################################################
# parse AUS6 lookup csv
###############################################################################

domcsv = 'Domains_Sep2011_lookup.csv'

dom = []
mmax = []
code = []
name = []
mcomp = []
ycomp = []
trt = []

lines = open(domcsv).readlines()[1:]
for line in lines:
    dat = line.strip().split(',')
    dom.append(int(round(float(dat[0]))))
    code.append(dat[1])
    name.append(dat[2])
    mmax.append(float(dat[3]))
    mcomp.append(dat[4])
    ycomp.append(dat[5])
    trt.append(dat[6])
    
###############################################################################
# write initial shapefile
###############################################################################

outshp = path.join('shapefiles', 'DOMAINS_NSHA18.shp')

# set shapefile to write to
w = shapefile.Writer(shapefile.POLYGON)
w.field('SRC_NAME','C','50')
w.field('CODE','C','10')
#w.field('SRC_REGION','C','100')
#w.field('SRC_REG_WT','F', 8, 3)
w.field('SRC_TYPE','C','10')
w.field('SRC_WEIGHT','F', 8, 2)
w.field('DEP_BEST','F', 8, 1)
w.field('DEP_UPPER','F', 8, 1)
w.field('DEP_LOWER','F', 8, 1)
w.field('MIN_MAG','F', 8, 2)
w.field('MIN_RMAG','F', 8, 2)
w.field('MMAX_BEST','F', 8, 2)
w.field('MMAX_LOWER','F', 8, 2)
w.field('MMAX_UPPER','F', 8, 2)
w.field('N0_BEST','F', 8, 5)
w.field('N0_LOWER','F', 8, 5)
w.field('N0_UPPER','F', 8, 5)
w.field('BVAL_BEST','F', 8, 5)
w.field('BVAL_LOWER','F', 8, 5)
w.field('BVAL_UPPER','F', 8, 5)
w.field('BVAL_FIX','F', 8, 2)
w.field('BVAL_FIX_S','F', 8, 2)
w.field('YCOMP','C','70')
w.field('MCOMP','C','30')
w.field('YMAX','F', 8, 0)
w.field('TRT','C','100')
w.field('DOMAIN','I', 2, 0)
w.field('CAT_FILE','C','50')

src_wt = 1.0
src_ty = 'area'
dep_b = 10.
dep_u = 5.
dep_l = 15.
min_mag = 4.8
min_rmag = 2.5
#mmax[i]
#mmax_l = mmax[i]-0.2
#mmax_u = mmax[i]+0.2
n0 = -99
n0_l = -99
n0_u = -99
bval = -99
bval_l = -99
bval_u = -99
bval_fix = -99
bval_fix_sig = -99
#ycomp = '1980;1970;1965;1962;1958;1910;1880'
#mcomp = '3.0;3.5;4.0;4.5;5.0;6.0;6.4'
ymax  = 2016
#dom   = -99
cat   = 'GGcat-161025.csv'

# loop through original records
for i, shape in enumerate(shapes):

    # set shape polygon
    w.line(parts=[shape.points], shapeType=shapefile.POLYGON)
        
    # write new records
    if i >= 0:
        w.record(name[i], code[i], src_ty, src_wt, dep_b, dep_u, dep_l, min_mag, min_rmag, mmax[i], mmax[i]-0.2, mmax[i]+0.2, \
                 n0, n0_l, n0_u, bval, bval_l, bval_u, bval_fix, bval_fix_sig, ycomp[i], mcomp[i], ymax, trt[i], dom[i], cat)
        
# now save area shapefile
w.save(outshp)

# write projection file
prjfile = outshp.strip().split('.shp')[0]+'.prj'
f = open(prjfile, 'wb')
f.write('GEOGCS["GCS_WGS_1984",DATUM["D_WGS_1984",SPHEROID["WGS_1984",6378137.0,298.257223563]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]]')
f.close()
