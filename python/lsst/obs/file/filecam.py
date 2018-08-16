#
# LSST Data Management System
# Copyright 2016 LSST Corporation.
#
# This product includes software developed by the
# LSST Project (http://www.lsst.org/).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import numpy
import lsst.afw.cameraGeom as cameraGeom
import lsst.afw.geom as afwGeom
from lsst.afw.table import AmpInfoCatalog, AmpInfoTable, LL
from lsst.afw.cameraGeom.cameraFactory import makeDetector


class FileCam(cameraGeom.Camera):
    """A fake Camera that should be good for generic files.

    There is one ccd with name "0"

    """

    def __init__(self):
        """Construct a TestCamera
        """
        # This is basically the same as specifying the scale in pixels
        plateScale = afwGeom.Angle(1., afwGeom.arcseconds)  # plate scale, in angle on sky/mm
        radialDistortion = 0.  # radial distortion in mm/rad^2, i.e. no distortion
        radialCoeff = numpy.array((0.0, 1.0, 0.0, radialDistortion)) / plateScale.asRadians()
        focalPlaneToFieldAngle = afwGeom.makeRadialTransform(radialCoeff)
        fieldAngleToFocalPlane = focalPlaneToFieldAngle.getInverse()
        cameraTransformMap = cameraGeom.TransformMap(cameraGeom.FOCAL_PLANE,
                                                     {cameraGeom.FIELD_ANGLE: fieldAngleToFocalPlane})
        detectorList = self._makeDetectorList(fieldAngleToFocalPlane, plateScale)
        cameraGeom.Camera.__init__(self, "file", detectorList, cameraTransformMap)

    def _makeDetectorList(self, focalPlaneToPupil, plateScale):
        """!Make a list of detectors

        @param[in] focalPlaneToPupil  lsst.afw.geom.XYTransform from FOCAL_PLANE to PUPIL coordinates
        @param[in] plateScale  plate scale, in angle on sky/mm
        @return a list of detectors (lsst.afw.cameraGeom.Detector)
        """
        detectorList = []
        detectorConfigList = self._makeDetectorConfigList()
        for detectorConfig in detectorConfigList:
            ampInfoCatalog = self._makeAmpInfoCatalog()
            detector = makeDetector(detectorConfig, ampInfoCatalog, focalPlaneToPupil)
            detectorList.append(detector)
        return detectorList

    def _makeDetectorConfigList(self):
        """!Make a list of detector configs

        @return a list of detector configs (lsst.afw.cameraGeom.DetectorConfig)
        """
        # There is only a single detector assumed perfectly centered and aligned.
        detector0Config = cameraGeom.DetectorConfig()
        detector0Config.name = '0'
        detector0Config.id = 0
        detector0Config.serial = 'abcd1234'
        detector0Config.detectorType = 0 # SCIENCE type
        # This is the orientation we need to put the serial direciton along the x-axis
        # This bounding box is not true in general, but I don't think it's used, so specify
        # zero size, so we'll know if it is.
        detector0Config.bbox_x0 = 0
        detector0Config.bbox_x1 = 0
        detector0Config.bbox_y0 = 0
        detector0Config.bbox_y1 = 0
        detector0Config.pixelSize_x = 1.  # in mm
        detector0Config.pixelSize_y = 1.  # in mm
        detector0Config.transformDict.nativeSys = 'Pixels'
        detector0Config.transformDict.transforms = None
        detector0Config.refpos_x = 0.
        detector0Config.refpos_y = 0.
        detector0Config.offset_x = 0.0
        detector0Config.offset_y = 0.0
        detector0Config.transposeDetector = False
        detector0Config.pitchDeg = 0.0
        detector0Config.yawDeg = 0.0  # this is where chip rotation goes in.
        detector0Config.rollDeg = 0.0
        return [detector0Config]

    def _makeAmpInfoCatalog(self):
        """Construct an amplifier info catalog
        """
        # Fake amp of zero size.  Not needed unless ISR is run
        xDataExtent = 0
        yDataExtent = 0


        saturation = 65535

        schema = AmpInfoTable.makeMinimalSchema()

        ampCatalog = AmpInfoCatalog(schema)
        record = ampCatalog.addNew()
        ampX, ampY = (0, 0)
        record.setName("%d%d" % (ampX, ampY))

        if bool(ampY):
            record.setBBox(afwGeom.Box2I(
                afwGeom.Point2I(ampX*xDataExtent, ampY*yDataExtent),
                afwGeom.Extent2I(xDataExtent, yDataExtent),
            ))
        else:
            record.setBBox(afwGeom.Box2I(
                afwGeom.Point2I(ampX*xDataExtent, ampY*yDataExtent),
                afwGeom.Extent2I(xDataExtent, yDataExtent),
            ))

        readCorner = LL  # in raw frames; always LL because raws are in amp coords
        record.setReadoutCorner(readCorner)
        record.setGain(1.)
        record.setReadNoise(0.)
        record.setSaturation(saturation)
        record.setHasRawInfo(False)
        return ampCatalog
