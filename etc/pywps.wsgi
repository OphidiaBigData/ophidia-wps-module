#!/usr/bin/env python
from pywps.app.Service import Service
from processes.ophidia import OphExecuteMain
processes = [
    OphExecuteMain()
]
application = Service(
    processes,
    ['/usr/local/ophidia/extra/wps/etc/pywps.cfg']
)

