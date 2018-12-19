#!/usr/bin/env python
#
# LSST Data Management System
# Copyright 2008-2013 LSST Corporation.
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
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the LSST License Statement and
# the GNU General Public License along with this program.  If not,
# see <http://www.lsstcorp.org/LegalNotices/>.
#
import numpy

import lsst.afw.image as afwImage
import lsst.afw.geom as afwGeom
import lsst.afw.math as afwMath
import lsst.pex.config as pexConfig
import lsst.pipe.base as pipeBase


__all__ = ["FileIsrTask"]


class FileIsrConfig(pexConfig.Config):
    """Config for FileIsr"""
    addNoise = pexConfig.Field(dtype=bool, default=False,
                               doc="Add a flat Poisson noise background to the eimage?")
    doMask = pexConfig.Field(dtype=bool, default=False, doc="Calculate mask?")
    gain = pexConfig.Field(dtype=float, default=0.0, doc="Gain (e/ADU) for image")
    noise = pexConfig.Field(dtype=float, default=0.0, doc="Noise (ADU) in image")
    saturation = pexConfig.Field(dtype=float, default=65535, doc="Saturation limit")
    low = pexConfig.Field(dtype=float, default=0.0, doc="Low limit")
    isBackgroundSubtracted = pexConfig.Field(dtype=bool, default=False,
                                             doc="Input image is already background subtracted")
    datasetType = pexConfig.Field(
        dtype = str,
        doc = "Dataset type for input data; users will typically leave this alone, "
              "but camera-specific ISR tasks will override it",
        default = "raw",
    )


class FileIsrTask(pipeBase.Task):
    ConfigClass = FileIsrConfig
    _DefaultName = "FileIsr"

    @pipeBase.timeMethod
    def runDataRef(self, sensorRef):
        """ISR one CCD

        @param sensorRef: sensor-level butler data reference
        @return pipe_base Struct containing these fields:
        - exposure: post ISR exposure
        """
        self.log.info("FileIsr:  %s" % (sensorRef.dataId))

        # initialize outputs
        #
        # We need to be read straight Fits images with no
        # mask planes or Wcs
        #
        postIsrExposure = sensorRef.get("raw", immediate=True)
        raw_md = sensorRef.get("raw_md", immediate=True)

        postIsrExposure.getMaskedImage().getMask()[:] &= \
            afwImage.Mask.getPlaneBitMask(["SAT", "INTRP", "BAD", "EDGE"])
        if self.config.addNoise:
            self.addNoise(postIsrExposure)

        self.setVariance(postIsrExposure)
        if self.config.doMask:
            self.setMask(postIsrExposure)

        # I'm not sure why this is necessary since the Exposure constructor should set the wcs
        wcs = afwGeom.makeSkyWcs(raw_md)
        if wcs:
            postIsrExposure.setWcs(wcs)
        else:
            self.log.warn("No WCS found in %s; caveat emptor" % (sensorRef.dataId))

        return pipeBase.Struct(exposure=postIsrExposure)

    def addNoise(self, inputExposure):
        mi = inputExposure.getMaskedImage()
        (x, y) = mi.getDimensions()
        noiseArr = numpy.random.poisson(self.config.noise, size=x*y).reshape(y, x)
        noiseArr = noiseArr.astype(numpy.float32)
        noiseImage = afwImage.makeImageFromArray(noiseArr)
        mi += noiseImage
        if self.config.isBackgroundSubtracted:
            mi -= self.config.noise

    def setVariance(self, exposure):
        mi = exposure.getMaskedImage()
        image = mi.getImage().getArray()
        variance = mi.getVariance().getArray()
        if self.config.isBackgroundSubtracted:
            bkgdVariance = afwMath.makeStatistics(mi.getImage(), afwMath.VARIANCECLIP).getValue()
            self.log.info("Setting variance: background variance = %g ADU" % (bkgdVariance))
        else:
            self.log.info("Setting variance: noise=%g ADU" % (self.config.noise))
            bkgdVariance = self.config.noise**2

        variance[:] = bkgdVariance

        if self.config.gain > 0.0:
            self.log.info("Setting variance: gain=%g e/ADU" % (self.config.gain))
            variance[:] += image/self.config.gain

    def setMask(self, exposure):
        mi = exposure.getMaskedImage()
        image = mi.getImage().getArray()
        mask = mi.getMask().getArray()
        isLow = image < self.config.low
        isSat = image > self.config.saturation
        self.log.info("Masking %d low and %d saturated pixels" % (isLow.sum(), isSat.sum()))
        mask += numpy.where(isLow, afwImage.MaskU.getPlaneBitMask("BAD"), 0)
        mask += numpy.where(isSat, afwImage.MaskU.getPlaneBitMask("SAT"), 0)

