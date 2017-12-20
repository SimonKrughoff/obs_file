import os

import lsst.afw.image as afwImage
import lsst.pex.exceptions as pexExceptions
from lsst.pex.config import Field
from lsst.pipe.tasks.ingest import ParseTask, ParseConfig
import hashlib
import astropy.io.fits as fitsio

__all__ = ['FileParseTask']


class FileParseConfig(ParseConfig):
    discover_extensions = Field(dtype=bool, default=False,
                                          doc="Attempt to find extensions in the file. "+\
                                              "The extnames config is ignored if this is set.")

class FileParseTask(ParseTask):
    ConfigClass = FileParseConfig
    def getInfo(self, filename):
        """Get information about the image from the filename and its contents

        Here, we open the image and parse the header, but one could also look at the filename itself
        and derive information from that, or set values from the configuration.

        @param filename    Name of file to inspect
        @return File properties; list of file properties for each extension
        """
        extnames = self.config.extnames
        md = afwImage.readMetadata(filename, self.config.hdu)
        # We want to use the filename as a key, so putting it in here
        md.set('filename', filename)
        md.set('extnum', 0)
        phuInfo = self.getInfoFromMetadata(md)
        if self.config.discover_extensions:
            def getExtensionList(filename):
                hdus = fitsio.open(filename)
                if len(hdus) < 2:
                    return []
                else:
                    return [self.getExtensionName(hdu.header) for hdu in hdus[1:]]
            extnames = getExtensionList(filename)
        if len(extnames) == 0:
            # No extensions to worry about
            return phuInfo, [phuInfo]
        # Look in the provided extensions
        extnames = set(extnames)
        extnum = 0
        infoList = []
        while len(extnames) > 0:
            extnum += 1
            try:
                md = afwImage.readMetadata(filename, extnum)
                md.set('extnum', extnum)
                md.set('filename', filename)
            except:
                self.log.warn("Error reading %s extensions %s" % (filename, extnames))
                break
            ext = self.getExtensionName(md)
            if ext in extnames:
                infoList.append(self.getInfoFromMetadata(md, info=phuInfo.copy()))
                extnames.discard(ext)
        return phuInfo, infoList

    def translate_fileroot(self, md):
        filename = md.get('filename')
        head, tail = os.path.split(filename)
        return tail.split('.')[0]

    def translate_extname(self, md):
        return self.getExtensionName(md)

    def translate_extension(self, md):
        return md.get('extnum')

    def translate_filter(self, md):
        return 'tmp'

    def translate_filename(self, md):
        head, tail = os.path.split(md.get('filename'))
        return tail

    def translate_visit(self, md):
         filename = md.get('filename')
         return int(hashlib.sha1(filename).hexdigest(), 16)%(10**16)

    def getDestination(self, butler, info, filename):
        """Get destination for the file

        @param butler      Data butler
        @param info        File properties, used as dataId for the butler
        @param filename    Input filename
        @return Destination filename
        """
        filename = butler.get("raw_filename", {'filename': os.path.split(filename)[-1],
                                               'extension':info['extension']})[0]
        # take off the extension part
        return filename.split('[')[0]

    @staticmethod
    def getExtensionName(md):
        """ Get the name of an extension.
        @param md: PropertySet like one obtained from afwImage.readMetadata)
        @return Name of the extension if it exists.  None otherwise.
        """
        try:
            ext = md.get("EXTNAME")
            # This returns a tuple sometimes
            if hasattr(ext, '__iter__'):
                return ext[1]
            # Else it's a string
            else:
                return ext
        except pexExceptions.Exception:
            return None
