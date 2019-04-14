#
#    Ophidia WPS Module
#    Copyright (C) 2015-2019 CMCC Foundation
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from pywps import Process, LiteralInput, ComplexInput, LiteralOutput, ComplexOutput, Format
from pywps.app.Common import Metadata
from pywps.validator.mode import MODE
from pywps.inout.formats import FORMATS

import logging
import subprocess
import StringIO
from PyOphidia import client as _client, ophsubmit as _ophsubmit

_host = "127.0.0.1"
_port = 11732
_version = "2.0.0"

class OphExecuteMain(Process):

    def __init__(self):
        inputs = []
        outputs = []

        userid = LiteralInput(
        'userid',
        'Username',
        abstract="User identifier for Ophidia system",
        data_type=type(''))
        
        passwd = LiteralInput(
        'passwd',
        'Password',
        abstract="Password to access Ophidia",
        data_type=type(''))

        request = ComplexInput(
        'request',
        'JSON Request',
        supported_formats=[FORMATS('text/json', encoding='base64'), FORMATS('text/plain', encoding='utf-8')])
        #maxmegabites=1 ?-> max_occurrence=1

        jobid = LiteralOutput(
        'jobid',        
        'Ophidia JobID',
        data_type=type(''))         

        response = ComplexOutput(
        'response',
        'JSON Response',
        supported_formats=[FORMATS('text/json', encoding='base64'), FORMATS('text/plain', encoding='utf-8')])
        
        error = LiteralOutput(
        'return',       
        'Return code',  
        data_type=type(1))

        inputs = [userid, passwd, request]
        outputs = [jobid, response, error]

        super(OphExecuteMain, self).__init__(
        self._handler,
        identifier='ophexecutemain',
        title='Ophidia Execute Main Process',
        abstract="Submit a generic workflow",
        version=_version,
        inputs=inputs,
        outputs=outputs,
        store_supported=True,   #or False??
        status_supported=True   #or False??
        )

    def _handler(self, request, response):

        self.status.set("Pre-processing", 1)
        logging.debug("Incoming a request with format %s" % self.request.format)

        request.outputs['return'][0].file = 1
        request.outputs['jobid'][0].file = ""

        logging.debug("Building request for oph_server")
        file = open(request.inputs['request'][0].file, 'r')

        buffer = file.read()
        file.close()

        if request.inputs['request'][0].data_format == "base64":
            logging.debug("Decoding request")
            buffer = buffer.decode("base64")

        logging.debug("Request: %s" % buffer)

        self.status.set("Running", 2)
        logging.debug("Execute the job")
        buffer, request.outputs['jobid'][0].file, new_session, return_value, request.outputs['return'][0].file = 1 = _ophsubmit.submit(request.inputs['userid'][0].file, request.inputs['passwd'][0].file, _host, _port, buffer)

        logging.debug("Return value: %s" % return_value)
        logging.debug("JobID: %s" % jobid)
        logging.debug("Response: %s" % buffer)
        logging.debug("Error message: %s" % error)

        self.status.set("Post-processing", 98)
        if return_value == 0 and len(buffer) > 0 and request.inputs['request'][0].data_format == "base64":
            logging.debug("Encoding response")
            buffer = buffer.encode("base64")

        self.status.set("Outputting", 99)
        output = StringIO.StringIO()
        response.outputs['error'].file = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].file = jobid
            if len(buffer) > 0:
                output.write(buffer)
        response.outputs['response'].file = output

        self.status.set("Succeded", 100)

