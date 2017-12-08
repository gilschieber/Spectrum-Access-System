# This software was developed by employees of the National Institute
# of Standards and Technology (NIST), an agency of the Federal
# Government. Pursuant to title 17 United States Code Section 105, works
# of NIST employees are not subject to copyright protection in the United
# States and are considered to be in the public domain. Permission to freely
# use, copy, modify, and distribute this software and its documentation
# without fee is hereby granted, provided that this notice and disclaimer
# of warranty appears in all copies.
#
# THE SOFTWARE IS PROVIDED 'AS IS' WITHOUT ANY WARRANTY OF ANY KIND,
# EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED
# TO, ANY WARRANTY THAT THE SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY
# IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE,
# AND FREEDOM FROM INFRINGEMENT, AND ANY WARRANTY THAT THE DOCUMENTATION
# WILL CONFORM TO THE SOFTWARE, OR ANY WARRANTY THAT THE SOFTWARE WILL BE
# ERROR FREE. IN NO EVENT SHALL NIST BE LIABLE FOR ANY DAMAGES, INCLUDING,
# BUT NOT LIMITED TO, DIRECT, INDIRECT, SPECIAL OR CONSEQUENTIAL DAMAGES,
# ARISING OUT OF, RESULTING FROM, OR IN ANY WAY CONNECTED WITH THIS
# SOFTWARE, WHETHER OR NOT BASED UPON WARRANTY, CONTRACT, TORT, OR
# OTHERWISE, WHETHER OR NOT INJURY WAS SUSTAINED BY PERSONS OR PROPERTY
# OR OTHERWISE, AND WHETHER OR NOT LOSS WAS SUSTAINED FROM, OR AROSE OUT
# OF THE RESULTS OF, OR USE OF, THE SOFTWARE OR SERVICES PROVIDED HEREUNDER.
#
# Distributions of NIST software should also include copyright and licensing
# statements of any third-party software that are legally bundled with
# the code in compliance with the conditions of those licenses.

#=============================================================================
# Test move_list calculation.
# Expected result is 'Move list output: [True, True, True, False, True, False]'
#=============================================================================


import json
import os
from pykml import parser
import move_list
import time
from collections import namedtuple

if __name__ == '__main__':

    # Inputs
    low_freq = 3600000000 	# low frequency of protection constraint (Hz)
    high_freq = 3610000000  # high frequency of protection constraint (Hz)
    protection_thres = -144	# protection threshold (dBm/10 MHz)
    num_iter = 2000			# number of Monte Carlo iterations

    # Data directory
    current_dir = os.getcwd()
    _BASE_DATA_DIR = os.path.join(current_dir, 'test_data')

    # Populate a list of CBSD registration requests 		
    reg_request_filename = ['RegistrationRequest_1.json',
                            'RegistrationRequest_2.json',
                            'RegistrationRequest_3.json',
                            'RegistrationRequest_4.json',
                            'RegistrationRequest_5.json',
                            'RegistrationRequest_6.json']
    reg_request_list = []
    for reg_file in reg_request_filename:
        reg_request = json.load(open(os.path.join(_BASE_DATA_DIR, reg_file)))
        reg_request_list.append(reg_request)

    # Populate a list of grant requests
    grant_request_filename = ['GrantRequest_1.json',
                              'GrantRequest_2.json',
                              'GrantRequest_3.json',
                              'GrantRequest_4.json',
                              'GrantRequest_5.json',
                              'GrantRequest_6.json']
    grant_request_list = []
    for grant_file in grant_request_filename:
        grant_request = json.load(open(os.path.join(_BASE_DATA_DIR, grant_file)))
        grant_request_list.append(grant_request)

    # Get east-gulf coastal exclusion zones (enclosed coastal exclusion zones with U.S. border)
    filename = os.path.join(_BASE_DATA_DIR, 'protection_zones.kml')
    with open(filename, 'r') as kml_file:
        coastalZoneDoc = parser.parse(kml_file).getroot()
    placemarks = list(coastalZoneDoc.Document.Placemark)
    exclusion_zone = []
    for pm in placemarks:
        name = pm.name.text
        if (name == 'East-Gulf Combined Contour'):
            line = pm.MultiGeometry.Polygon.outerBoundaryIs.LinearRing.coordinates.text
            coords = line.split(' ')
            lat_long = []
            for c in coords:
                if c.strip():
                    xy = c.strip().split(',')
                    lat_long.append([float(xy[1]), float(xy[0])])
                    exclusion_zone = lat_long
					
    # Populate protection points (a list of namedtuples with fields 'latitude' and 'longitude')
    ProtectionPoints = namedtuple('ProtectionPoints', ['latitude', 'longitude'])
    protection_points = {ProtectionPoints(latitude=36.9400, longitude=-75.9989),
                         ProtectionPoints(latitude=37.7579, longitude=-75.4105),
                         ProtectionPoints(latitude=36.1044, longitude=-73.3147),
                         ProtectionPoints(latitude=36.1211, longitude=-75.5939)}

    # Determine which CBSD grants are on the move list
    start_time = time.time()
    res = move_list.findMoveList(protection_points, low_freq, high_freq, protection_thres, num_iter, reg_request_list,
                                 grant_request_list, exclusion_zone)
    end_time = time.time()
    print 'Move list output: ' + str(res)
    print 'Computation time: ' + str(end_time - start_time)
