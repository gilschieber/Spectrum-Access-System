#    Copyright 2017 SAS Project Authors. All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import os
import logging
import numpy as np
import shutil
import unittest

from reference_models.geo import testutils
from reference_models.geo import nlcd

TEST_DIR = os.path.join(os.path.dirname(__file__), 'testdata', 'nlcd')
logging.disable(30)

class TestNlcd(unittest.TestCase):

  @classmethod
  def setUpClass(cls):
    cls.unzip_files = testutils.UnzipTestDir(TEST_DIR)
    # Copy the tile to simulate neighboring tile
    new_tile = "nlcd_n37w123_ref.int"
    shutil.copyfile(os.path.join(TEST_DIR, "nlcd_n38w123_ref.int"),
                    os.path.join(TEST_DIR, new_tile))
    cls.unzip_files.append(new_tile)

  @classmethod
  def tearDownClass(cls):
    testutils.RemoveFiles(TEST_DIR, cls.unzip_files)

  def setUp(self):
    self.nlcd_driver = nlcd.NlcdDriver(TEST_DIR)

  def test_get_land(self):
    # Selected pixels hand picked in SF region
    # to validate that no offset introduced

    # Twin Peaks - SF
    # - general pixel
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.751458, lon=-122.447831)
    region = nlcd.GetRegionType(code)
    self.assertEqual(code, 21)
    self.assertEqual(region, 'RURAL')

    # - single pixel at Suburban
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.750835, lon=-122.447780)
    self.assertEqual(code, 22)
    # - Single pixel at dense urban
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.551113, lon=-122.449722)
    self.assertEqual(code, 24)

    # Downtown - SF
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.794494, lon=-122.405920)
    region = nlcd.GetRegionType(code)
    self.assertEqual(code, 24)
    self.assertEqual(region, 'URBAN')
    # - single pixel at suburban
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.785269, lon=-122.405007)
    self.assertEqual(code, 22)

    # Bay Bridge
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.79692, lon=-122.37920)
    self.assertEqual(code, 21)

    # Residential Sunset - SF
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.761592, lon=-122.469308)
    region = nlcd.GetRegionType(code)
    self.assertEqual(code, 22)
    self.assertEqual(region, 'SUBURBAN')

    # Pacific Ocean SF - In the sea
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.750036, lon=-122.51527)
    region = nlcd.GetRegionType(code)
    self.assertEqual(code, 11)
    self.assertEqual(region, 'RURAL')

    # Ocean - far away from the coast
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.750036, lon=-122.999)
    region = nlcd.GetRegionType(code)
    self.assertEqual(code, 11)
    self.assertEqual(region, 'RURAL')

  def test_outside_grid(self):
    # Outside database tiles
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.75, lon=-121.9999)
    self.assertEqual(code, 0.0)
    code = self.nlcd_driver.GetLandCoverCodes(
        lat=37.75, lon=-121.9998)
    self.assertEqual(code, 0.0)

  def test_region_vote(self):
    points = [
        (37.751458, -122.447831),  # SF downtown (URBAN)
        (37.761592, 122.469308),  # Residential (SUBURBAN)
        (37.751458, -122.447831),  # Twin Peaks (RURAL)
        (37.750036, -122.51527),  # Ocean Beach (RURAL)
        (37.750036, -122.999) # Far Ocean (RURAL)
    ]
    self.assertEqual(self.nlcd_driver.RegionNlcdVote(points[0:1]), 'URBAN')
    self.assertEqual(self.nlcd_driver.RegionNlcdVote(points[0:2]), 'URBAN')
    self.assertEqual(self.nlcd_driver.RegionNlcdVote(points[0:3]), 'SUBURBAN')
    self.assertEqual(self.nlcd_driver.RegionNlcdVote(points[0:4]), 'RURAL')
    self.assertEqual(self.nlcd_driver.RegionNlcdVote(points[0:5]), 'RURAL')

  def test_multitile(self):
    lats = 36.5 + np.arange(0.01, 0.99, 0.01)
    lons = -122.99 + np.arange(0.01, 0.99, 0.01)

    codes1 = np.array([self.nlcd_driver.GetLandCoverCodes(lat, lon)
                       for (lat, lon) in zip(lats, lons)])
    codes2 = self.nlcd_driver.GetLandCoverCodes(lats, lons)
    self.assertEqual(np.max(np.abs(codes1 - codes2)), 0)

  def test_cache(self):
    lats = 36.5 + np.arange(0.01, 0.99, 0.01)
    lons = -122.99 + np.arange(0.01, 0.99, 0.01)
    self.nlcd_driver.cache_size = 1
    codes = self.nlcd_driver.GetLandCoverCodes(lats, lons)
    self.assertEqual(len(self.nlcd_driver._tile_cache), 1)
    self.assertEqual(len(self.nlcd_driver._tile_lru), 1)

    self.nlcd_driver.cache_size = 2
    codes = self.nlcd_driver.GetLandCoverCodes(lats, lons)
    self.assertEqual(len(self.nlcd_driver._tile_cache), 2)
    self.assertEqual(len(self.nlcd_driver._tile_lru), 2)

if __name__ == '__main__':
  unittest.main()