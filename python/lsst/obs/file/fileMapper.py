#!/usr/bin/env python

import os

from lsst.obs.base import CameraMapper
import lsst.afw.cameraGeom as afwCg
import lsst.afw.image.utils as afwImageUtils
import lsst.pex.policy as pexPolicy
from filecam import FileCam

from .makeFileRawVisitInfo import MakeFileRawVisitInfo

class FileMapper(CameraMapper):
    """Provides abstract-physical mapping for data found in the filesystem"""
    packageName = 'obs_file'
    MakeRawVisitInfoClass = MakeFileRawVisitInfo
    
    def __init__(self, **kwargs):
        policyFile = pexPolicy.DefaultPolicyFile("obs_file", "FileMapper.paf", "policy")
        policy = pexPolicy.Policy(policyFile)
        if False:
            if not kwargs.get('root', None):
                raise RuntimeError("Please specify a root")
            if not kwargs.get('calibRoot', None):
                kwargs['calibRoot'] = os.path.join(kwargs['root'], 'CALIB')

        super(FileMapper, self).__init__(policy, policyFile.getRepositoryPath(), **kwargs)
        
        # Ensure each dataset type of interest knows about the full range of keys available from the registry
        keys = dict(fileroot=str,
                )
        for name in ("calexp", "src"):
            self.mappings[name].keyDict = keys

        afwImageUtils.resetFilters()

        afwImageUtils.defineFilter(name='tmp', lambdaEff=0.)
        
        self.filters = {
            "tmp"  : "tmp",
            }

        # next line makes a dict that maps filter names to sequential integers (arbitrarily sorted),
        # for use in generating unique IDs for sources.
        self.filterIdMap = dict(zip(self.filters, range(len(self.filters))))

    def _extractDetectorName(self, dataId):
        return '0'

    def _computeCcdExposureId(self, dataId):
        """Compute the 64-bit (long) identifier for a CCD exposure.

        @param dataId (dict) Data identifier with visit, ccd
        """
        return 0

        pathId = self._transformId(dataId)
        visit = pathId['visit']
        ccd = pathId['ccd']
        return visit*200 + ccd

    def bypass_ccdExposureId(self, datasetType, pythonType, location, dataId):
        return self._computeCcdExposureId(dataId)

    def bypass_ccdExposureId_bits(self, datasetType, pythonType, location, dataId):
        """How many bits are required for the maximum exposure ID"""
        return 32 # just a guess, but this leaves plenty of space for sources

    def queryMetadata(self, datasetType, key, format, dataId):
        return tuple()

    def _makeCamera(self, policy, repositoryDir):
        """Make a camera (instance of lsst.afw.cameraGeom.Camera) describing the camera geometry
        """
        return FileCam()
