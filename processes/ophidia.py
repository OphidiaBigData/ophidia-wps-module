#
#    Ophidia WPS Module
#    Copyright (C) 2015-2017 CMCC Foundation
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

from pywps.Process import WPSProcess
import logging
import subprocess
import StringIO
from PyOphidia import client as _client, ophsubmit as _ophsubmit

_host = "127.0.0.1"
_port = 11732


class OphExecuteMainProcess(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="ophexecutemain",
            title="Ophidia",
            version="1.0.0",
            metadata=[],
            abstract="Submit a generic workflow",
            storeSupported=True,
            statusSupported=True)

        self.userid = self.addLiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            type=type(''))

        self.passwd = self.addLiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            type=type(''))

        self.request = self.addComplexInput(
            identifier="request",
            title="JSON Request",
            formats=[{"mimeType": "text/json", "encoding": "base64"}, {"mimeType": "text/plain", "encoding": "utf-8"}],
            metadata=[],
            maxmegabites=1)

        self.jobid = self.addLiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            type=type(''))

        self.response = self.addComplexOutput(
            identifier="response",
            title="JSON Response",
            metadata=[],
            formats=[{"mimeType": "text/json", "encoding": "base64"}, {"mimeType": "text/plain", "encoding": "utf-8"}])

        self.error = self.addLiteralOutput(
            identifier="return",
            title="Return code",
            type=type(1))

    def execute(self):

        self.status.set("Pre-processing", 1)
        logging.debug("Incoming a request with format %s" % self.request.format)

        self.error.setValue(1)
        self.jobid.setValue("")

        logging.debug("Building request for oph_server")
        file = open(self.request.getValue(), 'r')
        buffer = file.read()
        file.close()

        if self.request.format["encoding"] == "base64":
            logging.debug("Decoding request")
            buffer = buffer.decode("base64")

        logging.debug("Request: %s" % buffer)

        self.status.set("Running", 2)
        logging.debug("Execute the job")
        buffer, jobid, new_session, return_value, error = _ophsubmit.submit(self.userid.getValue(), self.passwd.getValue(), _host, _port, buffer)

        logging.debug("Return value: %s" % return_value)
        logging.debug("JobID: %s" % jobid)
        logging.debug("Response: %s" % buffer)
        logging.debug("Error message: %s" % error)

        self.status.set("Post-processing", 98)
        if return_value == 0 and len(buffer) > 0 and self.response.format["encoding"] == "base64":
            logging.debug("Encoding response")
            buffer = buffer.encode("base64")

        self.status.set("Outputting", 99)
        output = StringIO.StringIO()
        self.error.setValue(return_value)
        if return_value == 0:
            if jobid is not None:
                self.jobid.setValue(jobid)
            if len(buffer) > 0:
                output.write(buffer)
        self.response.setValue(output)

        self.status.set("Succeded", 100)


class oph_subset(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_subset",
            title="Ophidia",
            version="1.0.0",
            metadata=[],
            abstract="Subset a cube",
            storeSupported=True,
            statusSupported=True)

        self.userid = self.addLiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            type=type(''))

        self.passwd = self.addLiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            type=type(''))

        self.ncores = self.addLiteralInput(
            identifier="ncores",
            title="Number of cores",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.exec_mode = self.addLiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            minOccurs=0,
            maxOccurs=1,
            default="async",
            type=type(''))

        self.sessionid = self.addLiteralInput(
            identifier="sessionid",
            title="Session identifier",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Current working directory",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.grid = self.addLiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Grid of dimensions to be used (if the grid already exists) or the one to be created (if the grid has a new name). If it isn't specified, no grid will be used",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.subset_dims = self.addLiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting",
            minOccurs=0,
            maxOccurs=1,
            default="none",
            type=type(''))

        self.subset_filter = self.addLiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default="0",
            type=type(1))

        self.jobid = self.addLiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            type=type(''))

        self.response = self.addComplexOutput(
            identifier="response",
            title="JSON Response",
            metadata=[],
            formats=[{"mimeType": "text/json", "encoding": "base64"}, {"mimeType": "text/plain", "encoding": "utf-8"}])

        self.error = self.addLiteralOutput(
            identifier="return",
            title="Return code",
            type=type(1))

    def execute(self):

        self.status.set("Pre-processing", 1)

        self.error.setValue(1)
        self.jobid.setValue("")

        self.status.set("Running", 2)

        logging.debug("Build the query")
        query = 'oph_subset '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.cwd.getValue() is not None:
            query += 'cwd=' + str(self.cwd.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.subset_dims.getValue() is not None:
            query += 'subset_dims=' + str(self.subset_dims.getValue()) + ';'
        if self.subset_filter.getValue() is not None:
            query += 'subset_filter=' + str(self.subset_filter.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port, False)
        oph_client.api_mode = False

        logging.debug("Submit the query")
        oph_client.submit(query)

        logging.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        logging.debug("Return value: %s" % return_value)
        logging.debug("JobID: %s" % jobid)
        logging.debug("Response: %s" % response)
        logging.debug("Error message: %s" % error)

        self.status.set("Post-processing", 98)
        if return_value == 0 and self.exec_mode.getValue() == "sync" and len(response) > 0 and self.response.format["encoding"] == "base64":
            logging.debug("Encoding response")
            response = response.encode("base64")

        self.status.set("Outputting", 99)
        output = StringIO.StringIO()
        self.error.setValue(return_value)
        if return_value == 0:
            if jobid is not None:
                self.jobid.setValue(jobid)
            if self.exec_mode.getValue() == "sync" and len(response) > 0:
                output.write(response)
        self.response.setValue(output)

        self.status.set("Succeded", 100)
