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
from PyOphidia import client as _client, ophsubmit as _ophsubmit

import subprocess
import logging

LOGGER = logging.getLogger("PYWPS")

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
            data_type='string')

        passwd = LiteralInput(
            'passwd',
            'Password',
            abstract="Password to access Ophidia",
            data_type='string')

        request = ComplexInput(
            'request',
            'JSON Request',
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        jobid = LiteralOutput(
            'jobid',
            'Ophidia JobID',
            data_type='string')

        response = ComplexOutput(
            'response',
            'JSON Response',
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            'return',
            'Return code',
            data_type='integer')

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
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        LOGGER.debug("Incoming a request with format %s" % request.inputs['request'][0].data_format.encoding)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        buffer = request.inputs['request'][0].data

        LOGGER.debug("Request: %s" % buffer)

        response.update_status("Running", 2)

        LOGGER.debug("Execute the job")

        buffer, jobid, new_session, return_value, error = _ophsubmit.submit(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port, buffer)

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % buffer)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response
