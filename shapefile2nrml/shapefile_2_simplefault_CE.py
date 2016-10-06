"""

Command line tool to convert line shapefile + various input parameters to an
openquake simple fault in nrml format with a characteristic
earthquake distribution.

Shapefile may contain multiple lines respresenting multiple 
fault traces

Run with 
> python shapefile_2_simplefault.py -h
to get help

Gareth Davies, Geoscience Australia, 2014
Jonathan Griffin, Geoscience Australia, June 2016

"""

import os
import ogr
from geopy import distance
from eq_hazard_tools.recurrence import fault_slip_rate_GR_conversion
from openquake.hazardlib.scalerel.wc1994 import WC1994

def parse_line_shapefile(shapefile,shapefile_faultname_attribute,
                         shapefile_dip_attribute, 
                         shapefile_sliprate_attribute):
    """Read the line shapefile with of fault surface traces and
    extrace data from attibute table
        Return a list of lists of [x,y] points defining each line
    and calculates the length of the fault
    """

    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.Open(shapefile, 0)

    layer = data_source.GetLayer()

    fault_traces = []
    faultnames = []
    dips = []
    sliprates = []
    fault_lengths = []
    distance.VincentyDistance.ELLIPSOID = 'WGS_84'
    d = distance.distance
    for feature in layer:
        line = feature.GetGeometryRef().GetPoints()
        try:
            faultname = str(feature.GetField(shapefile_faultname_attribute))
        except ValueError:
            faultname = '""'
        faultnames.append(faultname)
        try:
            dip = float(feature.GetField(shapefile_dip_attribute))
        except ValueError:
            dip = '""'
        dips.append(dip)
        try:
            sliprate = float(feature.GetField(shapefile_sliprate_attribute))
            # Convert from m/ma to mm/a
            sliprate = sliprate/1000
            #slip uncertainty
            #sliprate = sliprate-0.1*sliprate
        except ValueError:
            sliprate = '""'
        sliprates.append(sliprate)
        line = [list(pts) for pts in line]
        fault_length = 0
        for i in range(len(line)):
            if i == len(line) -1:
                break
            else:
                pt_distance = d(line[i],line[i+1]).meters/1000
                fault_length+=pt_distance
        fault_lengths.append(fault_length)
        fault_traces.append(line)

    msg = 'Line shapefile must contain at least 1 fault'
    assert len(fault_traces) > 0, msg
#    print fault_traces
#    print len(fault_traces)

    # Make sure the ordering of depth is from smallest to largest
#    new_fault_contours = []
#    contour_depths = [fc[0][2] for fc in fault_contours]
#    contour_depths.sort()

#    for cd in contour_depths:
#        for j in range(len(fault_contours)):
#            if fault_contours[j][0][2] == cd:
#                new_fault_contours.append(fault_contours[j])
#                break


    return fault_traces, faultnames, dips, sliprates, fault_lengths


def append_xml_header(output_xml,
                      source_model_name):
    """Add information to the nrml which goes above the fault contours

    """

    # I think this breaks openquake
    # First line = blank
#    output_xml.append('')

    # Various header info which the user does not control
    output_xml.append("<?xml version='1.0' encoding='utf-8'?>")
    output_xml.append('<nrml xmlns:gml="http://www.opengis.net/gml"' +
                      ' xmlns="http://openquake.org/xmlns/nrml/0.4">')

    # Source model information
    output_xml.append('  <sourceModel name="' + str(source_model_name) + '">')
    #output_xml.append('')

    return


def append_gml_Linestring(output_xml, fc):
    """Convenience function to append the xyz coordinates as a gml Linestring

        @param output_xml List holding lines of the output xml being built
        @param fc List of lists of the form [x,y,z], defining the contour

        @return nothing, but the gml linestring is appended to the output_xml

    """
    output_xml.append('          <gml:LineString>')
    output_xml.append('            <gml:posList>')

    # Add the geometry
    for i in range(len(fc)):
        output_xml.append(
            '               ' + str(fc[i][0]) + ' ' + str(fc[i][1]))

    # Footer
    output_xml.append('            </gml:posList>')
    output_xml.append('          </gml:LineString>')

    return


def append_rupture_geometry(output_xml, trace, dip,
                            simple_fault_id, simple_fault_name,
                            upper_depth, lower_depth, 
                            simple_fault_tectonic_region):
    """Append the fault contours to the nrml

    """

    # Basic fault info
    output_xml.append('')
    output_xml.append('  <simpleFaultSource id="' + str(simple_fault_id) +
                      '"' + ' name="' + str(simple_fault_name) + '"' +
                      ' tectonicRegion="' +
                      str(simple_fault_tectonic_region) + '">')
    # Geometry
    output_xml.append('      <simpleFaultGeometry>')
    append_gml_Linestring(output_xml, trace)
#    output_xml.append('')
    output_xml.append('          <dip>' + str(dip) + '</dip>')
    output_xml.append('          <upperSeismoDepth>' + str(upper_depth) + '</upperSeismoDepth>')
    output_xml.append('          <lowerSeismoDepth>' + str(lower_depth) + '</lowerSeismoDepth>')
    output_xml.append('      </simpleFaultGeometry>')
#    output_xml.append('')
    return


def append_earthquake_information(output_xml, magnitude_scaling_relation,
                                  rupture_aspect_ratio, characteristic_mag, b_value,
                                  min_mag, max_mag, rake, moment_rate, bin_width):
    """

    """
    output_xml.append('      <magScaleRel>' +
                      str(magnitude_scaling_relation) + '</magScaleRel>')
  #  output_xml.append('')

    output_xml.append(
        '      <ruptAspectRatio>' + str(rupture_aspect_ratio) + '</ruptAspectRatio>')
 #   output_xml.append('')

    output_xml.append('      <YoungsCoppersmith1985MFD minMag="' +
                      str(min_mag) + '" bValue="' + str(b_value) +
                      '" binWidth="' + str(bin_width) +
                      '" characteristicMag="' + str(characteristic_mag) +
                      '" totalMomentRate="' + str(moment_rate) + '" />')
#    output_xml.append('')

    output_xml.append('      <rake>' + str(rake) + '</rake>')
    output_xml.append('    </simpleFaultSource>')

    return


def nrml_from_shapefile(shapefile,
                        shapefile_faultname_attribute,
                        shapefile_dip_attribute,
                        shapefile_sliprate_attribute,
                        source_model_name,
                        simple_fault_tectonic_region,
                        magnitude_scaling_relation,
                        rupture_aspect_ratio,
                        upper_depth,
                        lower_depth,
                        a_value,
                        b_value,
                        min_mag,
                        max_mag,
                        rake,
                        output_dir,
                        quiet):
    """Driver routine to convert nrml to shapefile
     
    """
    # Get geometry
    fault_traces, faultnames, dips, \
    sliprate, fault_lengths = parse_line_shapefile(shapefile,
                                                  shapefile_faultname_attribute,
                                                  shapefile_dip_attribute, 
                                                  shapefile_sliprate_attribute)

     # Output is written line-by-line to this list
    output_xml = []

    append_xml_header(output_xml, source_model_name)


    # Loop through each fault and add source specific info
    for i in range(len(fault_traces)):
        simple_fault_id = i
        A = fault_lengths[i]*(float(lower_depth)-float(upper_depth))
        # Calculate M_max from scaling relations
        scalrel = WC1994()
        bin_width = 0.1
        max_mag = scalrel.get_median_mag(A, float(rake))
        char_mag = max_mag - 0.25 #characteristic magnitude for OQ def
#        print A
        # Calculate characteristic incremental occurrence rates from slip rate
        if sliprate[i] != '""':
            print sliprate[i]
            # just to calculate the moment rate, need to fix this function
            a_value, moment_rate = fault_slip_rate_GR_conversion.slip2GR(sliprate[i], A,
                                                                         float(b_value), 
                                                                         float(max_mag),
                                                                         M_min=0.0)
            a_value=None # We aren't using the a value
            
            
#            mfd = YoungsCoppersmith1985MFD.from_total_moment_rate(min_mag=min_mag,
#                                                                  b_val=float(b_value), 
#                                                                  char_mag=float(max_mag), 
#                                                                  total_moment_rate=moment_rate, 
#                                                                  bin_width=0.1)
#            mags,rates=zip(*mfd.get_annual_occurrence_rates())


        append_rupture_geometry(output_xml, fault_traces[i],
                                dips[i], simple_fault_id,
                                faultnames[i], upper_depth,
                                lower_depth, simple_fault_tectonic_region)

        append_earthquake_information(output_xml,
                                      magnitude_scaling_relation,
                                      rupture_aspect_ratio, char_mag, b_value,
                                      min_mag, max_mag, rake, moment_rate, bin_width)

    # Close xml
    output_xml.append('  </sourceModel>')
    output_xml.append('</nrml>')

    # Add newlines
    output_xml = [oxml + '\n' for oxml in output_xml]

    return output_xml

############################################################################

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(
        description='Convert a line shapefile to an openquake complex fault' +
        ' in nrml format')

    parser.add_argument('-shapefile', type=str, default="",
                        help='Filename of line shapefile with rupture ' +
                        'plain contours. Each line geometry has an ' +
                        'attribute defining its depth')

#    parser.add_argument('-shapefile_depth_attribute', type=str, default=None,
#                        help='Name of the attribute table column ' +
#                        '(in shapefile) which contains the depth of each ' +
#                        'contour')

    parser.add_argument('-shapefile_faultname_attribute', type=str, default=None,
                        help='Name of the attribute table column ' +
                        '(in shapefile) which contains the name of each ' +
                        'fault')

    parser.add_argument('-shapefile_dip_attribute', type=str, default=None,
                        help='Name of the attribute table column ' +
                        '(in shapefile) which contains the dip of each ' +
                        'fault')

    parser.add_argument('-shapefile_sliprate_attribute', type=str, default=None,
                        help='Name of the attribute table column ' +
                        '(in shapefile) which contains the sliprate of each ' +
                        'fault')

    parser.add_argument('-source_model_name', type=str,
                        default='unnamed_source',
                        help='Name for the source model')

#    parser.add_argument('-simple_fault_id', type=int, default=0,
#                        help='integer id for the complex_fault')

#    parser.add_argument('-complex_fault_name', type=str,
#                        default='unnamed_complex_fault',
#                        help='Name for the complex fault')

    parser.add_argument(
        '-simple_fault_tectonic_region',
        type=str,
        default='unnamed_complex_fault_region',
        help='Name for the tectonic region of the complex fault')

    parser.add_argument(
        '-magnitude_scaling_relation',
        type=str,
        default='/magScaleRel',
        help='Openquake magnitude scaling relation descriptor (see manual)')

    parser.add_argument('-rupture_aspect_ratio', type=str,
                        default='/ruptAspectRatio',
                        help='Openquake rupture aspect ratio (see manual)')
  
    parser.add_argument('-upper_depth', type=str,
                        default='""',
                        help='Openquake upper seismogenic depth (see manual)')

    parser.add_argument('-lower_depth', type=str,
                        default='""',
                        help='Openquake lower seismogenic depth (see manual)')

    parser.add_argument(
        '-a_value',
        type=str,
        default='""',
        help='Openquake truncated Gutenberg Richter MFD a-value (see manual)')

    parser.add_argument(
        '-b_value',
        type=str,
        default='""',
        help='Openquake truncated Gutenberg Richter MFD b-value (see manual)')

    parser.add_argument(
        '-min_mag',
        type=str,
        default='""',
        help='Openquake truncated Gutenberg Richter MFD minMag (see manual)')

    parser.add_argument(
        '-max_mag',
        type=str,
        default='""',
        help='Openquake truncated Gutenberg Richter MFD maxMag (see manual)')

    parser.add_argument('-rake', type=str,
                        default='/rake',
                        help='earthquake rake')

    parser.add_argument(
        '-output_dir',
        type=str,
        default='nrml',
        help='Location for output files. Created if necessary.')

    parser.add_argument('-quiet', action='store_true', default=False,
                        help="Don't print anything")

    args = parser.parse_args()

    try:
        shapefile_exists = os.path.exists(args.shapefile)
    except:
        parser.print_help()
        raise Exception('shapefile ' + str(args.shapefile) + ' not found')

    if not shapefile_exists:
        parser.print_help()
        raise Exception('shapefile ' + str(args.shapefile) + ' not found')

    # Main code here
    output_xml_text = nrml_from_shapefile(args.shapefile,
                                          args.shapefile_faultname_attribute,
                                          args.shapefile_dip_attribute,
                                          args.shapefile_sliprate_attribute,
                                          args.source_model_name,
                                          args.simple_fault_tectonic_region,
                                          args.magnitude_scaling_relation,
                                          args.rupture_aspect_ratio,
                                          args.upper_depth,
                                          args.lower_depth,
                                          args.a_value,
                                          args.b_value,
                                          args.min_mag,
                                          args.max_mag,
                                          args.rake,
                                          args.output_dir,
                                          args.quiet)

    # Write to file
    try:
        os.mkdir(args.output_dir)
    except:
        pass

    f = open(os.path.join(args.output_dir, args.source_model_name + '.xml'),
             'w')
    f.writelines(output_xml_text)
    f.close()
