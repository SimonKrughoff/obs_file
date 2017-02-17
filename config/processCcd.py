from lsst.obs.file.fileisr import FileIsrTask

import os.path

from lsst.utils import getPackageDir
config.calibrate.measurement.load(os.path.join(getPackageDir("meas_extensions_shapeHSM"), "config", "enable.py"))
config.calibrate.measurement.plugins["ext_shapeHSM_HsmShapeRegauss"].deblendNChild = "deblend_nChild"


config.isr.retarget(FileIsrTask)
config.calibrate.doAstrometry = False
config.calibrate.doPhotoCal = False
