from lsst.obs.file.ingest import FileParseTask
config.parse.retarget(FileParseTask)
config.parse.translators = {'fileroot': 'translate_fileroot',
                            'filename': 'translate_filename',
                            'filter':'translate_filter',
                            'visit':'translate_visit',
                            'extension':'translate_extension',
                            'extname':'translate_extname'}

config.register.columns = {'visit': 'int', 'filename': 'text', 'fileroot': 'text', 'filter': 'text',
                           'extension':'int', 'extname':'text'}

config.register.visit = ['fileroot', 'visit']
config.register.unique = ['fileroot', 'extension']