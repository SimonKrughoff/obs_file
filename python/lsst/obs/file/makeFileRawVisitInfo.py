from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from lsst.afw.geom import degrees
from lsst.afw.coord import Observatory
from lsst.obs.base import MakeRawVisitInfo

__all__ = ["MakeFileRawVisitInfo"]


class MakeFileRawVisitInfo(MakeRawVisitInfo):
    """Make a VisitInfo from the FITS header of a raw LSST simulated image
    The convention for ROTANG is as follows:
    at  0 degrees E = +Y CCD = -X Focal Plane, N = +X CCD = +Y Focal Plane: 90 boresightRotAng
    at 90 degrees E = -X CCD = -Y Focal Plane, N = +Y CCD = -X Focal Plane:  0 boresightRotAng
    So boresightRotAng = 90 - ROTANG
    """
    observatory = Observatory(0*degrees, 0*degrees, np.nan)  # long, lat, elev

    def getDateAvg(self, md, exposureTime):
        """Return date at the middle of the exposure
        @param[in,out] md  FITS metadata; changed in place
        @param[in] exposureTime  exposure time in sec
        """
        startDate = self.popMjdDate(md, "TAI", timesys="TAI")
        return self.offsetDate(startDate, 0.5*exposureTime)