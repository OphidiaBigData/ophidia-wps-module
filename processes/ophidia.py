#
#    Ophidia WPS Module
#    Copyright (C) 2015-2018 CMCC Foundation
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
            title="Ophidia execute",
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

class oph_aggregate(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_aggregate",
            title="Ophidia aggregate",
            version="1.0.0",
            metadata=[],
            abstract="Aggregate cubes along explicit dimensions",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Input container",
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

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.group_size = self.addLiteralInput(
            identifier="group_size",
            title="Group size",
            abstract="Number of tuples per group to consider in the aggregation function. If set to 'all' the aggregation, will occur on all tuples of the table",
            minOccurs=1,
            default="all",
            type=type(''))

        self.missingvalue = self.addLiteralInput(
            identifier="missingvalue",
            title="Missingvalue",
            minOccurs=0,
            maxOccurs=1,
            default="NAN",
            type=type(1.0))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.operation = self.addLiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the operation. Possible values are count, max, min, avg, sum",
            type=type(''))

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
        query = 'oph_aggregate '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.group_size.getValue() is not None:
            query += 'group_size=' + str(self.group_size.getValue()) + ';'
        if self.missingvalue.getValue() is not None:
            query += 'missingvalue=' + str(self.missingvalue.getValue()) + ';'

        query += 'operation=' + str(self.operation.getValue()) + ';'
        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_aggregate2(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_aggregate2",
            title="Ophidia aggregate2",
            version="1.0.0",
            metadata=[],
            abstract="Execute an aggregation operation based on hierarchy on a datacube",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
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
            default=0,
            type=type(1))

        self.operation = self.addLiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the operation. Possible values are count, max, min, avg, sum",
            type=type(''))

        self.dim = self.addLiteralInput(
            identifier="dim",
            title="Dim",
            abstract="Name of dimension on which the operation will be applied",
            type=type(''))

        self.concept_level = self.addLiteralInput(
            identifier="concept_level",
            title="Concept Level",
            abstract="Concept level inside the hierarchy used for the operation",
            minOccurs=0,
            maxOccurs=1,
            default="A",
            type=type(''))

        self.midnight = self.addLiteralInput(
            identifier="midnight",
            title="Midnight",
            abstract="Possible values are: 00, 24. If 00, the edge point of two consecutive aggregate time sets will be aggregated into the right set; if 24 to the left set",
            minOccurs=0,
            maxOccurs=1,
            default="24",
            type=type(''))

        self.missingvalue = self.addLiteralInput(
            identifier="missingvalue",
            title="Missingvalue",
            abstract="Value to be considered as missing value",
            minOccurs=0,
            maxOccurs=1,
            default="NAN",
            type=type(1.0))

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
        query = 'oph_aggregate2 '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.concept_level.getValue() is not None:
            query += 'concept_level=' + str(self.concept_level.getValue()) + ';'
        if self.midnight.getValue() is not None:
            query += 'midnight=' + str(self.midnight.getValue()) + ';'
        if self.missingvalue.getValue() is not None:
            query += 'missingvalue=' + str(self.missingvalue.getValue()) + ';'

        query += 'dim=' + str(self.dim.getValue()) + ';'
        query += 'operation=' + str(self.operation.getValue()) + ';'
        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_apply(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_apply",
            title="Ophidia apply",
            version="1.0.0",
            metadata=[],
            abstract="Execute a query on a datacube",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
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
            default=0,
            type=type(1))

        self.query = self.addLiteralInput(
            identifier="query",
            title="Query",
            abstract="User-defined SQL query. Use keyword 'measure' to refer to time series; use the keyword 'dimension' to refer to the input dimension array (only if one dimension of input cube is implicit)",
            minOccurs=0,
            maxOccurs=1,
            default="measure",
            type=type(''))

        self.dim_query = self.addLiteralInput(
            identifier="dim_query",
            title="Dim Query",
            abstract="Dimension of query defined by user",
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.measure = self.addLiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the new measure resulting from the specified operation",
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.measure_type = self.addLiteralInput(
            identifier="measure_type",
            title="Measure Type",
            abstract="Two possible values: 'auto' and 'manual'. If 'auto', dimension type will be set automatically to that of input datacube and the related primitive arguments have to be omitted in 'query'; if 'manual' (default), dimension type and the related primitive arguments have to be set in 'query'",
            minOccurs=0,
            maxOccurs=1,
            default="manual",
            type=type(''))

        self.dim_type = self.addLiteralInput(
            identifier="dim_type",
            title="Dim Type",
            abstract="Two possible values: 'auto' and 'manual'. If 'auto', dimension type will be set automatically to that of input datacube and the related primitive arguments have to be omitted in 'dim_query'; if 'manual' (default), dimension type and the related primitive arguments have to be set in 'dim_query'",
            minOccurs=0,
            maxOccurs=1,
            default="manual",
            type=type(''))

        self.check_type = self.addLiteralInput(
            identifier="check_type",
            title="Check Type",
            abstract="Two possible values: 'yes' and 'no'. If 'yes', the agreement between input and output data types of nested primitives will be checked; if 'no', data type will be mot cjecked",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.on_reduce = self.addLiteralInput(
            identifier="on_reduce",
            title="Operation to be applied to dimension on reduce",
            abstract="Two possible values: 'update' and 'skip'. If 'update' the values of implicit dimension are automatically set to a list of long integers starting from 1 even if dimension size does not decrease; f 'skip' (default) the values are updated to a list of long integers only in case dimension size decrease due to a reduction primitive",
            minOccurs=0,
            maxOccurs=1,
            default="skip",
            type=type(''))

        self.compressed = self.addLiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Three possible values: 'auto', 'yes' and 'no'. If 'auto', new data will be compressed according to compression status of input datacube; if 'yes', new data will be compressed; if 'no', data will be inserted without compression",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

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
        query = 'oph_apply '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.query.getValue() is not None:
            query += 'query=' + str(self.query.getValue()) + ';'
        if self.dim_query.getValue() is not None:
            query += 'dim_query=' + str(self.dim_query.getValue()) + ';'
        if self.measure.getValue() is not None:
            query += 'measure=' + str(self.measure.getValue()) + ';'
        if self.measure_type.getValue() is not None:
            query += 'measure_type=' + str(self.measure_type.getValue()) + ';'
        if self.dim_type.getValue() is not None:
            query += 'dim_type=' + str(self.dim_type.getValue()) + ';'
        if self.check_type.getValue() is not None:
            query += 'check_type=' + str(self.check_type.getValue()) + ';'
        if self.on_reduce.getValue() is not None:
            query += 'on_reduce=' + str(self.on_reduce.getValue()) + ';'
        if self.compressed.getValue() is not None:
            query += 'compressed=' + str(self.compressed.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_b2drop(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_b2drop",
            title="Ophidia B2DROP",
            version="1.0.0",
            metadata=[],
            abstract="Upload a file onto a B2DROP remote folder; note that in order to be able to use the operator, a netrc file with the credentials to B2DROP is required. Commonly the hidden .netrc file resides in the user's home directory",
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

        self.type = self.addLiteralInput(
            identifier="",
            title="",
            abstract="",
            minOccurs=0,
            maxOccurs=1,
            default="",
            type=type(''))

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
        query = 'oph_cancel '
        if self.type.getValue() is not None:
            query += 'type=' + str(self.type.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        query += 'id=' + str(self.id.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_cancel(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_cancel",
            title="Ophidia cancel",
            version="1.0.0",
            metadata=[],
            abstract="Stop the execution of a running workflow",
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

        self.auth_path = self.addLiteralInput(
            identifier="auth_path",
            title="Authorization data",
            abstract="Absolute path to the netrc file containing the B2DROP login information; note that it is not possible to use double dots (..) within the path; if no path is provided, the user's home will be used (default)",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.src_path = self.addLiteralInput(
            identifier="src_path",
            title="Source path",
            abstract="Path to the file to be uploaded to B2DROP. The path can be absolute or relative; in case of relative path the cdd argument will be pre-pended; note that it is not possible to use double dots (..) within the path",
            type=type(''))

        self.dest_path = self.addLiteralInput(
            identifier="dest_path",
            title="Destination path",
            abstract="Path where the file will be uploaded on B2DROP. In case no path is specified, the base path and the input file name will be used (default)",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Current Data Directory",
            abstract="Absolute path corresponding to the current directory on data repository",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

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
        query = 'oph_b2drop '
        if self.auth_path.getValue() is not None:
            query += 'auth_path=' + str(self.auth_path.getValue()) + ';'
        if self.dest_path.getValue() is not None:
            query += 'dest_path=' + str(self.dest_path.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        query += 'src_path=' + str(self.src_path.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_cluster(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_cluster",
            title="Ophidia input",
            version="1.0.0",
            metadata=[],
            abstract="Start and stop a cluster of I/O servers",
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

        self.action = self.addLiteralInput(
            identifier="action",
            title="Action",
            abstract="Two possibile actions are available: 'deploy' and 'undeploy'. 'deploy': try to reserve hosts and starts I/O servers (default); 'undeploy': stop reservation and I/O servers",
            minOccurs=0,
            maxOccurs=1,
            default="deploy",
            type=type(''))

        self.nhost = self.addLiteralInput(
            identifier="nhost",
            title="Number of hosts",
            abstract="Number of hosts to be reserved as well as number of I/O servers to be started over them",
            minOccurs=0,
            maxOccurs=1,
            default="1",
            type=type(1))

        self.host_partition = self.addLiteralInput(
            identifier="host_partititon",
            title="Host partition",
            abstract="Name of user-defined partition to be used to group hosts in the cluster",
            type=type(''))

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
        query = 'oph_input '
        if self.id.getValue() is not None:
            query += 'id=' + str(self.id.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.action.getValue() is not None:
            query += 'action=' + str(self.action.getValue()) + ';'
        if self.nhost.getValue() is not None:
            query += 'nhost=' + str(self.nhost.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        query += 'host_partition=' + str(self.host_partition.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_containerschema(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_containerschema",
            title="Ophidia containerschema",
            version="1.0.0",
            metadata=[],
            abstract="Show some information about a container: description, vocabulary, dimension list, etc.",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="Name of the container to be created",
            type=type(''))

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
        query = 'oph_containerschema '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'

        query += 'container=' + str(self.container.getValue()) + ';'
        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_createcontainer(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_createcontainer",
            title="Ophidia createcontainer",
            version="1.0.0",
            metadata=[],
            abstract="Create an empty container",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="Name of the container to be created",
            type=type(''))

        self.dim = self.addLiteralInput(
            identifier="dim",
            title="Dimension name",
            abstract="Name of dimension allowed. Multiple-value field: list of dimensions separated by '|' can be provided",
            type=type(''))

        self.dim_type = self.addLiteralInput(
            identifier="dim_type",
            title="Dim Type",
            abstract="Types of dimensions. Possible values are 'double', 'float', 'int', or 'long'. Multiple-value field: list of types separated by '|' can be provided. Default value is 'double'",
            minOccurs=0,
            maxOccurs=1,
            default="double",
            type=type(''))

        self.compressed = self.addLiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="If 'yes', new data will be compressed. With 'no' (default), data will be inserted without compression",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.hierarchy = self.addLiteralInput(
            identifier="hierarchy",
            title="Hierarchy",
            abstract="Concept hierarchy name of the dimensions. Default value is 'oph_base'. Multi-value field: list of concept levels separed by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="oph_base",
            type=type(''))

        self.vocabulary = self.addLiteralInput(
            identifier="vocabulary",
            title="Vocabulary",
            abstract="Optional argument used to indicate a vocabulary to be used to associate metadata to the container",
            minOccurs=0,
            maxOccurs=1,
            default="CF",
            type=type(''))

        self.base_time = self.addLiteralInput(
            identifier="base_time",
            title="Base time",
            abstract="In case of time hierarchy, it indicates the base time of the dimension. Default value is 1900-01-01",
            minOccurs=0,
            maxOccurs=1,
            default="1900-01-01 00:00:00",
            type=type(''))

        self.units = self.addLiteralInput(
            identifier="units",
            title="Units",
            abstract="In case of time hierarchy, it indicates the units of the dimension. Possible values are: s,m,h,3,6,d",
            minOccurs=0,
            maxOccurs=1,
            default="d",
            type=type(''))

        self.calendar = self.addLiteralInput(
            identifier="calendar",
            title="Calendar",
            abstract="In case of time hierarchy, it indicates the calendar type",
            minOccurs=0,
            maxOccurs=1,
            default="standard",
            type=type(''))

        self.month_lenghts = self.addLiteralInput(
            identifier="month_lenghts",
            title="Month lenghts",
            abstract="In case of time dimension and user-defined calendar, it indicates the sizes of each month in days. There byst be 12 positive integers separated by commas",
            minOccurs=0,
            maxOccurs=1,
            default="31,28,31,30,31,30,31,31,30,31,30,31",
            type=type(''))

        self.leap_year = self.addLiteralInput(
            identifier="leap_year",
            title="Leap year",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap year. By default it is set to 0",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.leap_month = self.addLiteralInput(
            identifier="leap_month",
            title="Leap month",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap month. By default it is set to 2 (February)",
            minOccurs=0,
            maxOccurs=1,
            default=2,
            type=type(1))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output container",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_createcontainer '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.dim_type.getValue() is not None:
            query += 'dim_type=' + str(self.dim_type.getValue()) + ';'
        if self.compressed.getValue() is not None:
            query += 'compressed=' + str(self.compressed.getValue()) + ';'
        if self.hierarchy.getValue() is not None:
            query += 'hierarchy=' + str(self.hierarchy.getValue()) + ';'
        if self.vocabulary.getValue() is not None:
            query += 'vocabulary=' + str(self.vocabulary.getValue()) + ';'
        if self.base_time.getValue() is not None:
            query += 'base_time=' + str(self.base_time.getValue()) + ';'
        if self.units.getValue() is not None:
            query += 'units=' + str(self.units.getValue()) + ';'
        if self.calendar.getValue() is not None:
            query += 'calendar=' + str(self.calendar.getValue()) + ';'
        if self.month_lenghts.getValue() is not None:
            query += 'month_lenghts=' + str(self.month_lenghts.getValue()) + ';'
        if self.leap_year.getValue() is not None:
            query += 'leap_year=' + str(self.leap_year.getValue()) + ';'
        if self.leap_month.getValue() is not None:
            query += 'leap_month=' + str(self.leap_month.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'container=' + str(self.container.getValue()) + ';'
        query += 'cwd=' + str(self.cwd.getValue()) + ';'
        query += 'dim=' + str(self.dim.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_cubeelements(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_cubeelements",
            title="Ophidia cubeelements",
            version="1.0.0",
            metadata=[],
            abstract="Compute and display the number of elements stored in the input datacube",
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

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.sessionid = self.addLiteralInput(
            identifier="sessionid",
            title="Session identifier",
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.algorithm = self.addLiteralInput(
            identifier="algorithm",
            title="Algorithm",
            abstract="Algorithm used to count elements. Possible value are: 'dim_product' (default) to compute elements mathematically; 'count' to count elements in each fragment",
            minOccurs=0,
            maxOccurs=1,
            default="dim_product",
            type=type(''))

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
        query = 'oph_cubeelements '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.algorithm.getValue() is not None:
            query += 'algorithm=' + str(self.algorithm.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_cubeio(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_cubeio",
            title="Ophidia cubeio",
            version="1.0.0",
            metadata=[],
            abstract="Show the hierarchy of all datacubes used to generate the input datacube and of those derived from it",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.branch = self.addLiteralInput(
            identifier="branch",
            title="Branch",
            abstract="It is possible to visualize all datacubes with 'all', only the parent branch with 'parent' and only the children branch with 'children'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

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
        query = 'oph_cubeio '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.branch.getValue() is not None:
            query += 'branch=' + str(self.branch.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_cubeschema(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_cubeschema",
            title="Ophidia cubeschema",
            version="1.0.0",
            metadata=[],
            abstract="Show metadata information about a datacube and the dimensions related to it",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.action = self.addLiteralInput(
            identifier="action",
            title="Action",
            abstract="Command type. Use: 'read' to access information (default); 'add' to add a new dimension (size will be 1); 'clear' to clear collapsed dimensions",
            minOccurs=0,
            maxOccurs=1,
            default="read",
            type=type(''))

        self.level = self.addLiteralInput(
            identifier="level",
            title="Level",
            abstract="Level of information shown. '0': shows only metadata (default); '1': shows only dimension values; '2': shows metadata and dimension values",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.dim = self.addLiteralInput(
            identifier="dim",
            title="Dimension name",
            abstract="Name of dimension to show. Only valid with level bigger than 0; in case of action 'read', all dimension are shown by default and multiple values can be set (separated by |); in case of action 'add' only one dimension has to be set",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.show_index = self.addLiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimensions ids. With 'yes', it will also show the dimension id next to the value",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.show_time = self.addLiteralInput(
            identifier="show_time",
            title="Show time",
            abstract="If 'no' (default), the values of time dimension are shown as numbers. With 'yes', the values are converted as a string with date and time",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.base64 = self.addLiteralInput(
            identifier="base64",
            title="Base64",
            abstract="If 'no' (default), dimension values are returned as strings. With 'yes', the values are returned as base64-coded strings",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.concept_level = self.addLiteralInput(
            identifier="concept_level",
            title="Concept level",
            abstract="Concept level to be associated with new dimnesion",
            minOccurs=0,
            maxOccurs=1,
            default="c",
            type=type(''))

        self.dim_level = self.addLiteralInput(
            identifier="dim_level",
            title="Dimension level",
            abstract="Level of the new dimension to be added in dimension table",
            minOccurs=0,
            maxOccurs=1,
            default="1",
            type=type(1))

        self.dim_array = self.addLiteralInput(
            identifier="dim_array",
            title="Dimension array",
            abstract="Use 'yes' to add an implicit dimension (default), use 'no' to add an explicit dimension",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

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
        query = 'oph_cubeschema '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.action.getValue() is not None:
            query += 'action=' + str(self.action.getValue()) + ';'
        if self.level.getValue() is not None:
            query += 'level=' + str(self.level.getValue()) + ';'
        if self.dim.getValue() is not None:
            query += 'dim=' + str(self.dim.getValue()) + ';'
        if self.show_index.getValue() is not None:
            query += 'show_index=' + str(self.show_index.getValue()) + ';'
        if self.show_time.getValue() is not None:
            query += 'show_time=' + str(self.show_time.getValue()) + ';'
        if self.base64.getValue() is not None:
            query += 'base64=' + str(self.base64.getValue()) + ';'
        if self.concept_level.getValue() is not None:
            query += 'concept_level=' + str(self.concept_level.getValue()) + ';'
        if self.dim_level.getValue() is not None:
            query += 'dim_level=' + str(self.dim_level.getValue()) + ';'
        if self.dim_array.getValue() is not None:
            query += 'dim_array=' + str(self.dim_array.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_cubesize(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_cubesize",
            title="Ophidia cubesize",
            version="1.0.0",
            metadata=[],
            abstract="Compute and display the size of the input datacube",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.byte_unit = self.addLiteralInput(
            identifier="byte_unit",
            title="Byte unit",
            abstract="Measure unit used to show datacube size. The unit can be KB, MB (default), GB, TB or PB",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

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
        query = 'oph_cubesize '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.byte_unit.getValue() is not None:
            query += 'byte_unit=' + str(self.byte_unit.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_delete(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_delete",
            title="Ophidia delete",
            version="1.0.0",
            metadata=[],
            abstract="Remove a datacube",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
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
        query = 'oph_delete '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_deletecontainer(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_deletecontainer",
            title="Ophidia deletecontainer",
            version="1.0.0",
            metadata=[],
            abstract="Remove a container with related dimensions and grids. The container can be deleted logically or physically",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used; used only when the force argument is set to 'yes'",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.force = self.addLiteralInput(
            identifier="force",
            title="Force",
            abstract="Flag used to force the removal of a non-empy container, note that with 'yes' all datacubes inside the container will be deleted, whereas with 'no' (default) the container will be removed only if it is already empty",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.delete_type = self.addLiteralInput(
            identifier="delete_type",
            title="Delete type",
            abstract="Type of removal: 'logical' (logical cancellation that set the container status to hidden); 'physical' (physical cancellation)",
            minOccurs=0,
            maxOccurs=1,
            default="logical",
            type=type(''))

        self.hidden = self.addLiteralInput(
            identifier="hidden",
            title="Hidden",
            abstract="Status of the container to be deleted, considered only when delete_type is 'physical': 'yes' (container to be removed is hidden); 'no' (container to be removed isn't hidden)",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Container",
            abstract="Name of the container to be removed",
            type=type(''))

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
        query = 'oph_deletecontainer '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.force.getValue() is not None:
            query += 'force=' + str(self.force.getValue()) + ';'
        if self.delete_type.getValue() is not None:
            query += 'delete_type=' + str(self.delete_type.getValue()) + ';'
        if self.hidden.getValue() is not None:
            query += 'hidden=' + str(self.hidden.getValue()) + ';'

        query += 'container=' + str(self.container.getValue()) + ';'
        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_drilldown(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_drilldown",
            title="Ophidia drilldown",
            version="1.0.0",
            metadata=[],
            abstract="Perform a drill-down on a datacube, i.e. it transforms dimensions from implicit to explicit",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.ndim = self.addLiteralInput(
            identifier="ndim",
            title="Number of Implicit Dimensions",
            abstract="Number of implicit dimensions that will be transformed in explicit dimensions",
            minOccurs=0,
            maxOccurs=1,
            default=1,
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
        query = 'oph_drilldown '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.ndim.getValue() is not None:
            query += 'ndim=' + str(self.ndim.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_duplicate(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_duplicate",
            title="Ophidia duplicate",
            version="1.0.0",
            metadata=[],
            abstract="Duplicate a datacube creating an exact copy of the input one",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_duplicate '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_explorecube(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_explorecube",
            title="Ophidia explorecube",
            version="1.0.0",
            metadata=[],
            abstract="Print a data stored into a datacube, and offer to subset the data along its dimensions; dimensions values are used as input filters for subsetting",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.limit_filter = self.addLiteralInput(
            identifier="limit_filter",
            title="Limit filter",
            abstract="Optional filter on the maxumum number of rows",
            minOccurs=0,
            maxOccurs=1,
            default=100,
            type=type(1))

        self.time_filter = self.addLiteralInput(
            identifier="time_filter",
            title="Time filter",
            abstract="Enable filters using dates for time dimensions; enabled by default",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.show_index = self.addLiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimensions ids. With 'yes', it will also show the dimension id next to the value",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.show_id = self.addLiteralInput(
            identifier="show_id",
            title="Show id",
            abstract="If 'no' (default), it won't show fragment row ID. With 'yes', it will also show the fragment row ID",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.show_time = self.addLiteralInput(
            identifier="show_time",
            title="Show time",
            abstract="If 'no' (default), the values of time dimension are shown as numbers. With 'yes', the values are converted as a string with date and time",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.level = self.addLiteralInput(
            identifier="level",
            title="Level",
            abstract="With '1' (default), only measure values are shown, if it is set to '2', the dimension values are also returned",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.output_path = self.addLiteralInput(
            identifier="output_path",
            title="Output path",
            abstract="Absolute path of the JSON Response. By default, JSON Response is saved in core environment",
            minOccurs=0,
            maxOccurs=1,
            default="default",
            type=type(''))

        self.output_name = self.addLiteralInput(
            identifier="output_name",
            title="Output name",
            abstract="Filename of the JSON Response. The default value is the PID of the input dataube. File is saved provided that 'output_path' is set",
            minOccurs=0,
            maxOccurs=1,
            default="default",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.base64 = self.addLiteralInput(
            identifier="base64",
            title="Base64",
            abstract="If 'no' (default), dimension values are returned as strings",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.subset_dims = self.addLiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="none",
            type=type(''))

        self.subset_type = self.addLiteralInput(
            identifier="subset_type",
            title="Subset type",
            abstract="If set to 'index' (defaylt), the 'subset_filter' is considered on dimension index: with 'coord', filter is considered on dimension values",
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

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
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
        query = 'oph_explorecube '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.time_filter.getValue() is not None:
            query += 'time_filter=' + str(self.time_filter.getValue()) + ';'
        if self.limit_filter.getValue() is not None:
            query += 'limit_filter=' + str(self.limit_filter.getValue()) + ';'
        if self.show_index.getValue() is not None:
            query += 'show_index=' + str(self.show_index.getValue()) + ';'
        if self.show_id.getValue() is not None:
            query += 'show_id=' + str(self.show_id.getValue()) + ';'
        if self.show_time.getValue() is not None:
            query += 'show_time=' + str(self.show_time.getValue()) + ';'
        if self.level.getValue() is not None:
            query += 'level=' + str(self.level.getValue()) + ';'
        if self.output_path.getValue() is not None:
            query += 'output_path=' + str(self.output_path.getValue()) + ';'
        if self.output_name.getValue() is not None:
            query += 'output_name=' + str(self.output_name.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.base64.getValue() is not None:
            query += 'base64=' + str(self.base64.getValue()) + ';'
        if self.subset_dims.getValue() is not None:
            query += 'subset_dims=' + str(self.subset_dims.getValue()) + ';'
        if self.subset_type.getValue() is not None:
            query += 'subset_type=' + str(self.subset_type.getValue()) + ';'
        if self.subset_filter.getValue() is not None:
            query += 'subset_filter=' + str(self.subset_filter.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_explorenc(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_explorenc",
            title="Ophidia explorenc",
            version="1.0.0",
            metadata=[],
            abstract="Read a NetCDF file (both measure and dimensions)",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.measure = self.addLiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure related to the NetCDF. The argument is mandatory in case level different from '0'",
            minOccurs=0,
            maxOccurs=1,
            type=type(''))

        self.level = self.addLiteralInput(
            identifier="level",
            title="Level",
            abstract="'0' to show the list of dimensions; '1' to show the values of a specific measure; '2' to show the values of a specific measure and the values of the corresponding dimensions",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.src_path = self.addLiteralInput(
            identifier="src_path",
            title="Path of the FITS file",
            abstract="Path of the FITS file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.exp_dim = self.addLiteralInput(
            identifier="exp_dim",
            title="Explicit dimensions",
            abstract="Names of explicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            type=type(''))

        self.imp_dim = self.addLiteralInput(
            identifier="imp_dim",
            title="Implicit dimensions",
            abstract="Names of implicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            type=type(''))

        self.subset_dims = self.addLiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="none",
            type=type(''))

        self.subset_type = self.addLiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord. If set to 'index' (default), the subset_filter is considered on a dimension index; otherwise on dimension values",
            minOccurs=0,
            maxOccurs=1,
            default="index",
            type=type(''))

        self.subset_filter = self.addLiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.limit_filter = self.addLiteralInput(
            identifier="limit_filter",
            title="Limit filter",
            abstract="Optional filter on the maxumum number of rows",
            minOccurs=0,
            maxOccurs=1,
            default=100,
            type=type(1))

        self.show_index = self.addLiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimensions ids. With 'yes', it will also show the dimension id next to the value",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.show_id = self.addLiteralInput(
            identifier="show_id",
            title="Show id",
            abstract="If 'no' (default), it won't show fragment row ID. With 'yes', it will also show the fragment row ID",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.show_time = self.addLiteralInput(
            identifier="show_time",
            title="Show time",
            abstract="If 'no' (default), the values of time dimension are shown as numbers. With 'yes', the values are converted as a string with date and time",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.show_stats = self.addLiteralInput(
            identifier="show_stats",
            title="Show stats",
            abstract="If one of the following mask is set, a list of statistics is returned for each time series; output data type is always 'oph_double'",
            minOccurs=0,
            maxOccurs=1,
            default="00000000000000",
            type=type(''))

        self.show_fit = self.addLiteralInput(
            identifier="show_fit",
            title="Show fit",
            abstract="If 'yes', linear regression of each time serie is returned. It can be adopted only in case only one implicit dimension exists. With 'no' (default), linear regression is not evaluated",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.imp_num_points = self.addLiteralInput(
            identifier="imp_num_points",
            title="Imp number of points",
            abstract="Indicates the number of points which measure values must be distribuited along by interpolation. If 'imp_num_points' is higher than the number of actual points, then interpolation is evaluated; otherwhise, 'operation' is applied. It can be adopted only in case one implicit dimension exists. With '0', no interpolation/reduction is applied (default)",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.offset = self.addLiteralInput(
            identifier="offset",
            title="Offset",
            abstract="Relative offset to be used to set reduction interval bounds (percentage). By default is set to '50'",
            minOccurs=0,
            maxOccurs=1,
            default=50,
            type=type(1.0))

        self.operation = self.addLiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the operation. Possible values are count, max, min, avg, sum",
            minOccurs=0,
            maxOccurs=1,
            default="avg",
            type=type(''))

        self.wavelet = self.addLiteralInput(
            identifier="wavelet",
            title="Wavelet",
            abstract="Used to apply the wavelet filter provided 'wavelet_points' is set. Possibile values are: 'yes' (orginal data and filterd data are returned); 'only' (only filtered data are returned), 'no' (only original data are returnered, default value)",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.wavelet_ratio = self.addLiteralInput(
            identifier="wavelet_ratio",
            title="Wavelet ratio",
            abstract="Is the fraction of wavelet transform coefficients that are cleared by the filter (percentage). It can be adopted only in case one implicit dimension existes. With '0', no compression is applied (default)",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1.0))

        self.wavelet_coeff = self.addLiteralInput(
            identifier="wavelet_coeff",
            title="Wavelet coefficient",
            abstract="If 'yes', wavelet coefficients are also shown; output data type is always 'oph_double'; if necessary, their number is expanded to the first power of 2. It can be adopted only in case one implicit dimension exists",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
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
        query = 'oph_explorenc '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.level.getValue() is not None:
            query += 'level=' + str(self.level.getValue()) + ';'
        if self.measure.getValue() is not None:
            query += 'measure=' + str(self.measure.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.exp_dim.getValue() is not None:
            query += 'exp_dim=' + str(self.exp_dim.getValue()) + ';'
        if self.imp_dim.getValue() is not None:
            query += 'imp_dim=' + str(self.imp_dim.getValue()) + ';'
        if self.subset_dims.getValue() is not None:
            query += 'subset_dims=' + str(self.subset_dims.getValue()) + ';'
        if self.subset_type.getValue() is not None:
            query += 'subset_type=' + str(self.subset_type.getValue()) + ';'
        if self.subset_filter.getValue() is not None:
            query += 'subset_filter=' + str(self.subset_filter.getValue()) + ';'
        if self.limit_filter.getValue() is not None:
            query += 'limit_filter=' + str(self.limit_filter.getValue()) + ';'
        if self.show_index.getValue() is not None:
            query += 'show_index=' + str(self.show_index.getValue()) + ';'
        if self.show_id.getValue() is not None:
            query += 'show_id=' + str(self.show_id.getValue()) + ';'
        if self.show_time.getValue() is not None:
            query += 'show_time=' + str(self.show_time.getValue()) + ';'
        if self.show_stats.getValue() is not None:
            query += 'show_stats=' + str(self.show_stats.getValue()) + ';'
        if self.show_fit.getValue() is not None:
            query += 'show_fit=' + str(self.show_fit.getValue()) + ';'
        if self.imp_num_points.getValue() is not None:
            query += 'imp_num_points=' + str(self.imp_num_points.getValue()) + ';'
        if self.offset.getValue() is not None:
            query += 'offset=' + str(self.offset.getValue()) + ';'
        if self.operation.getValue() is not None:
            query += 'operation=' + str(self.operation.getValue()) + ';'
        if self.wavelet.getValue() is not None:
            query += 'wavelet=' + str(self.wavelet.getValue()) + ';'
        if self.wavelet_ratio.getValue() is not None:
            query += 'wavelet_ratio=' + str(self.wavelet_ratio.getValue()) + ';'
        if self.wavelet_coeff.getValue() is not None:
            query += 'wavelet_coeff=' + str(self.wavelet_coeff.getValue()) + ';'

        query += 'src_path=' + str(self.src_path.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_exportnc(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_exportnc",
            title="Ophidia exportnc",
            version="1.0.0",
            metadata=[],
            abstract="Export data of a datacube into multiple NetCDF files",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            minOccurs=0,
            maxOccurs=1,
            type=type(''))

        self.misc = self.addLiteralInput(
            identifier="misc",
            title="Misc",
            abstract="If 'yes', data are saved in session folder called 'export/misc'; if 'no', data are saved within 'export/nc' in a subfolder associated with the PID of the cube (default)",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.output_path = self.addLiteralInput(
            identifier="output_path",
            title="Output path",
            abstract="Absolute path of the NetCDF output files. By default, all the files will be saved in session folder 'export/nc/containerid/datacubeid; in case it is set to 'local' the file will be saved in current directory on data repository (see 'cdd')",
            minOccurs=0,
            maxOccurs=1,
            default="default",
            type=type(''))

        self.output_name = self.addLiteralInput(
            identifier="output_name",
            title="Output name",
            abstract="Filename of the NetCDF output files. In case of multiple fragments, filenames will be 'output_name0.nc', 'output_name1.nc', etc. The default value is the measure name of the input datacube",
            default="default",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.force = self.addLiteralInput(
            identifier="force",
            title="Force",
            abstract="Flag used to force file creation. An existant file is overwriten with 'yes', whereas the file is reated only if it does not exist with 'no' (default)",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.export_metadata = self.addLiteralInput(
            identifier="export_metadata",
            title="Export metadata",
            abstract="With 'yes' (default), it is possible to export also metadata; with 'no', it will export only data",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
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
        query = 'oph_exportnc '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.misc.getValue() is not None:
            query += 'misc=' + str(self.misc.getValue()) + ';'
        if self.output_path.getValue() is not None:
            query += 'output_path=' + str(self.output_path.getValue()) + ';'
        if self.output_name.getValue() is not None:
            query += 'output_name=' + str(self.output_name.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.force.getValue() is not None:
            query += 'force=' + str(self.force.getValue()) + ';'
        if self.export_metadata.getValue() is not None:
            query += 'export_metadata=' + str(self.export_metadata.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_exportnc2(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_exportnc2",
            title="Ophidia exportnc2",
            version="1.0.0",
            metadata=[],
            abstract="Export data of a datacube into a single NetCDF file",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.misc = self.addLiteralInput(
            identifier="misc",
            title="Misc",
            abstract="If 'yes', data are saved in session folder called 'export/misc'; if 'no', data are saved within 'export/nc' in a subfolder associated with the PID of the cube (default)",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.output_path = self.addLiteralInput(
            identifier="output_path",
            title="Output path",
            abstract="Absolute path of the NetCDF output files. By default, all the files will be saved in session folder 'export/nc/containerid/datacubeid; in case it is set to 'local' the file will be saved in current directory on data repository (see 'cdd')",
            minOccurs=0,
            maxOccurs=1,
            default="default",
            type=type(''))

        self.output_name = self.addLiteralInput(
            identifier="output_name",
            title="Output name",
            abstract="Filename of the NetCDF output files. In case of multiple fragments, filenames will be 'output_name0.nc', 'output_name1.nc', etc. The default value is the measure name of the input datacube",
            minOccurs=0,
            maxOccurs=1,
            default="default",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.force = self.addLiteralInput(
            identifier="force",
            title="Force",
            abstract="Flag used to force file creation. An existant file is overwriten with 'yes', whereas the file is reated only if it does not exist with 'no' (default)",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.export_metadata = self.addLiteralInput(
            identifier="export_metadata",
            title="Export metadata",
            abstract="With 'yes' (default), it is possible to export also metadata; with 'no', it will export only data; with 'postpone' metadata are also saved, but only after all the data are written",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
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
        query = 'oph_exportnc2 '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.misc.getValue() is not None:
            query += 'misc=' + str(self.misc.getValue()) + ';'
        if self.output_path.getValue() is not None:
            query += 'output_path=' + str(self.output_path.getValue()) + ';'
        if self.output_name.getValue() is not None:
            query += 'output_name=' + str(self.output_name.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.force.getValue() is not None:
            query += 'force=' + str(self.force.getValue()) + ';'
        if self.export_metadata.getValue() is not None:
            query += 'export_metadata=' + str(self.export_metadata.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_folder(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_folder",
            title="Ophidia folder",
            version="1.0.0",
            metadata=[],
            abstract="Manage folder of the Ophidia filesystem",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.command = self.addLiteralInput(
            identifier="command",
            title="Command",
            abstract="Command to be executed among these: 'cd' (change directory); 'mkdir' (create a new directory); 'rm' (delete an empty directory); 'mv' move/rename a folder",
            type=type(''))

        self.path = self.addLiteralInput(
            identifier="path",
            title="Path",
            abstract="0, 1 or 2 absolute/relative paths needed by commands. In case of mv, 2 paths are mandatory parameters and must end with a name of a folder. In case of cd, without a path the new directory will be the session folder. In all other cases, it can be used only 1 path",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

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
        query = 'oph_folder '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.path.getValue() is not None:
            query += 'path=' + str(self.path.getValue()) + ';'

        query += 'command=' + str(self.command.getValue()) + ';'
        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_fs(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_fs",
            title="Ophidia fs",
            version="1.0.0",
            metadata=[],
            abstract="Manage folders of the real Ophidia filesystem",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.command = self.addLiteralInput(
            identifier="command",
            title="Command",
            abstract="Command to be executed among: 'ls' (default value, list the files in a directory); 'cd' (change directory)",
            minOccurs=0,
            maxOccurs=1,
            default="ls",
            type=type(''))

        self.dpath = self.addLiteralInput(
            identifier="dpath",
            title="Dpath",
            abstract="0 or 1 path needed by commands. In case of 'cd', without a path the new directoru will be root folder BASE_SRC_PATH. In all other cases, it can be used only 1 path",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.file = self.addLiteralInput(
            identifier="file",
            title="File",
            abstract="The filter based on glob library",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory",
            abstract="Absolute path corresponding to the current directory on data repository. It is appended to BASE_SRC_PATH to build the effective path to files",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.recursive = self.addLiteralInput(
            identifier="recursive",
            title="Recursive",
            abstract="Specifies if the search is done recursively or not; the argument is considered only for the first three levels and may have values of 'no' or 'yes'",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.depth = self.addLiteralInput(
            identifier="depth",
            title="Depth",
            abstract="Set to maximum folder depth has to be explored in case of recursion; level '1' corresponds to 'no recursion'; by default no limit is applied",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.realpath = self.addLiteralInput(
            identifier="realpath",
            title="Real paths",
            abstract="Set to 'yes' to list real paths to files; by default only the names of files and directories are shown",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

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
        query = 'oph_fs '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.command.getValue() is not None:
            query += 'command=' + str(self.command.getValue()) + ';'
        if self.dpath.getValue() is not None:
            query += 'dpath=' + str(self.dpath.getValue()) + ';'
        if self.file.getValue() is not None:
            query += 'file=' + str(self.file.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.recursive.getValue() is not None:
            query += 'recursive=' + str(self.recursive.getValue()) + ';'
        if self.depth.getValue() is not None:
            query += 'depth=' + str(self.depth.getValue()) + ';'
        if self.realpath.getValue() is not None:
            query += 'realpath=' + str(self.realpath.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_get_config(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_get_config",
            title="Ophidia get_config",
            version="1.0.0",
            metadata=[],
            abstract="Request the configuration parameters",
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

        self.key = self.addLiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the metadata to be requested",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

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
        query = 'oph_get_config '
        if self.key.getValue() is not None:
            query += 'key=' + str(self.key.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_hierarchy(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_hierarchy",
            title="Ophidia hierarchy",
            version="1.0.0",
            metadata=[],
            abstract="Show the list of the hierarchies or the description of a specified hierarchy",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.hierarchy = self.addLiteralInput(
            identifier="hierarchy",
            title="Hierarchy",
            abstract="Name of the requested hierarchy. If the value 'all' is specified, then the list of all hierarchies is shown",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.hierarchy_version = self.addLiteralInput(
            identifier="hierarchy_version",
            title="Hierarchy version",
            abstract="Version of the requested hierarchy. If not specified, it will be used its default value 'latest' in order to get info about the latest version of the hierarchy",
            minOccurs=0,
            maxOccurs=1,
            default="latest",
            type=type(''))

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
        query = 'oph_hierarchy '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.hierarchy.getValue() is not None:
            query += 'hierarchy=' + str(self.hierarchy.getValue()) + ';'
        if self.hierarchy_version.getValue() is not None:
            query += 'hierarchy_version=' + str(self.hierarchy_version.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_importfits(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_importfits",
            title="Ophidia importfits",
            version="1.0.0",
            metadata=[],
            abstract="Imports a FITS file into a datacube (both data and axis); support is provided only for FITS images",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.host_partition = self.addLiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="Name of I/O host partition used to store data. Default value 'auto' indicates that the first host partition availble is used",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.filesystem = self.addLiteralInput(
            identifier="filesystem",
            title="Filesystem",
            abstract="Type of filesystem used to store data. Possible values are 'locl', 'global' or 'auto' (default). In the laswt case the first filesystem available will be used",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.ioserver = self.addLiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data. Possible values are: 'mysql_table' (default) or 'ophidiaio_memory'",
            minOccurs=0,
            maxOccurs=1,
            default="mysql_table",
            type=type(''))

        self.import_metadata = self.addLiteralInput(
            identifier="import_metadata",
            title="Import metatadata",
            abstract="With 'yes' (default), it will import also metadata; with 'no', it will import only data",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.nhost = self.addLiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.ndbms = self.addLiteralInput(
            identifier="ndbms",
            title="Number of output DBMS per host",
            abstract="Number of output DBMS per host. With default value '0', all DBMS instance available per host are used",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.ndb = self.addLiteralInput(
            identifier="ndb",
            title="Number of output database per host",
            abstract="Number of output database per host. Default value is '1'",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.nfrag = self.addLiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database. With default value '0', the number of fragments will be ratio of the product of sizes of the n-1 most outer explicit dimensions to the product of the other arguments",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.measure = self.addLiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the new measure related to the FITS file. If not provided 'image' will be used (default)",
            minOccurs=0,
            maxOccurs=1,
            default="image",
            type=type(''))

        self.run = self.addLiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the import and computes the fragmentation parameters that would be used else. If set to 'yes', the actual import operation is executed",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.src_path = self.addLiteralInput(
            identifier="src_path",
            title="Path of the FITS file",
            abstract="Path of the FITS file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.hdu = self.addLiteralInput(
            identifier="hdu",
            title="Hdu",
            abstract="Import data from the select HDU. If not specified, Primary HDU '1' (default) will be considered",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.exp_dim = self.addLiteralInput(
            identifier="exp_dim",
            title="Explicit dimensions",
            abstract="Names of explicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.imp_dim = self.addLiteralInput(
            identifier="imp_dim",
            title="Implicit dimensions",
            abstract="Names of implicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.subset_dims = self.addLiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
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

        self.compressed = self.addLiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_importfits '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.host_partition.getValue() is not None:
            query += 'host_partition=' + str(self.host_partition.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.filesystem.getValue() is not None:
            query += 'filesystem=' + str(self.filesystem.getValue()) + ';'
        if self.ioserver.getValue() is not None:
            query += 'ioserver=' + str(self.ioserver.getValue()) + ';'
        if self.import_metadata.getValue() is not None:
            query += 'import_metadata=' + str(self.import_metadata.getValue()) + ';'
        if self.nhost.getValue() is not None:
            query += 'nhost=' + str(self.nhost.getValue()) + ';'
        if self.ndbms.getValue() is not None:
            query += 'ndbms=' + str(self.ndbms.getValue()) + ';'
        if self.ndb.getValue() is not None:
            query += 'ndb=' + str(self.ndb.getValue()) + ';'
        if self.nfrag.getValue() is not None:
            query += 'nfrag=' + str(self.nfrag.getValue()) + ';'
        if self.run.getValue() is not None:
            query += 'run=' + str(self.run.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.hdu.getValue() is not None:
            query += 'hdu=' + str(self.hdu.getValue()) + ';'
        if self.exp_dim.getValue() is not None:
            query += 'exp_dim=' + str(self.exp_dim.getValue()) + ';'
        if self.imp_dim.getValue() is not None:
            query += 'imp_dim=' + str(self.imp_dim.getValue()) + ';'
        if self.subset_dims.getValue() is not None:
            query += 'subset_dims=' + str(self.subset_dims.getValue()) + ';'
        if self.subset_filter.getValue() is not None:
            query += 'subset_filter=' + str(self.subset_filter.getValue()) + ';'
        if self.compressed.getValue() is not None:
            query += 'compressed=' + str(self.compressed.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.measure.getValue() is not None:
            query += 'measure=' + str(self.measure.getValue()) + ';'

        query += 'cwd=' + str(self.cwd.getValue()) + ';'
        query += 'src_path=' + str(self.src_path.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_importnc(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_importnc",
            title="Ophidia importnc",
            version="1.0.0",
            metadata=[],
            abstract="Import a NetCDF file into a datacube (both measure and dimensions)",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.host_partition = self.addLiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="Name of I/O host partition used to store data. Default value 'auto' indicates that the first host partition availble is used",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.filesystem = self.addLiteralInput(
            identifier="filesystem",
            title="Filesystem",
            abstract="Type of filesystem used to store data. Possible values are 'locl', 'global' or 'auto' (default). In the laswt case the first filesystem available will be used",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.ioserver = self.addLiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data. Possible values are: 'mysql_table' (default) or 'ophidiaio_memory'",
            minOccurs=0,
            maxOccurs=1,
            default="mysql_table",
            type=type(''))

        self.import_metadata = self.addLiteralInput(
            identifier="import_metadata",
            title="Import metatadata",
            abstract="With 'yes' (default), it will import also metadata; with 'no', it will import only data",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.check_compliance = self.addLiteralInput(
            identifier="check_compliance",
            title="Check compliance",
            abstract="Checks if all the metadata registered for reference vocabulary are available. No check is done by default",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.nhost = self.addLiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.ndbms = self.addLiteralInput(
            identifier="ndbms",
            title="Number of output DBMS per host",
            abstract="Number of output DBMS per host. With default value '0', all DBMS instance available per host are used",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.ndb = self.addLiteralInput(
            identifier="ndb",
            title="Number of output database per host",
            abstract="Number of output database per host. Default value is '1'",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.nfrag = self.addLiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database. With default value '0', the number of fragments will be ratio of the product of sizes of the n-1 most outer explicit dimensions to the product of the other arguments",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.measure = self.addLiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure related to the NetCDF file",
            type=type(''))

        self.run = self.addLiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the import and computes the fragmentation parameters that would be used else. If set to 'yes', the actual import operation is executed",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.src_path = self.addLiteralInput(
            identifier="src_path",
            title="Path of the NetCDF file",
            abstract="Path or OPeNDAP URL of the NetCDF file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.exp_dim = self.addLiteralInput(
            identifier="exp_dim",
            title="Explicit dimensions",
            abstract="Names of explicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.imp_dim = self.addLiteralInput(
            identifier="imp_dim",
            title="Implicit dimensions",
            abstract="Names of implicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.subset_dims = self.addLiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
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

        self.subset_type = self.addLiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord. If set to 'index' (default), the subset_filter is considered on a dimension index; otherwise on dimension values",
            minOccurs=0,
            maxOccurs=1,
            default="index",
            type=type(''))

        self.time_filter = self.addLiteralInput(
            identifier="time_filter",
            title="Time filter",
            abstract="Enable filters using dates for time dimensions; enabled by default",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.offset = self.addLiteralInput(
            identifier="offset",
            title="Offset",
            abstract="It is added to the bounds of subset intervals defined with 'subset_filter' in case of 'coord' filter type is used",
             minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1.0))

        self.exp_concept_level = self.addLiteralInput(
            identifier="exp_concept_level",
            title="Explicit concept level",
            abstract="Concept level short name (must be a single char) of explicit dimensions. Default value is 'c'. Multi-value field: list of concept levels separed by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="c",
            type=type(''))

        self.imp_concept_level = self.addLiteralInput(
            identifier="imp_concept_level",
            title="Implicit concept level",
            abstract="Concept level short name (must be a single char) of implicit dimensions. Default value is 'c'. Multi-value field: list of concept levels separed by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="c",
            type=type(''))

        self.compressed = self.addLiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            default="no",
            type=type(''))

        self.grid = self.addLiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            default="-",
            type=type(''))

        self.hierarchy = self.addLiteralInput(
            identifier="hierarchy",
            title="Hierarchy",
            abstract="Concept hierarchy name of the dimensions. Default value is 'oph_base'. Multi-value field: list of concept levels separed by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="oph_base",
            type=type(''))

        self.vocabulary = self.addLiteralInput(
            identifier="vocabulary",
            title="Vocabulary",
            abstract="Optional argument used to indicate a vocabulary to be used to associate metadata to the container",
            minOccurs=0,
            maxOccurs=1,
            default="CF",
            type=type(''))

        self.base_time = self.addLiteralInput(
            identifier="base_time",
            title="Base time",
            abstract="In case of time hierarchy, it indicates the base time of the dimension. Default value is 1900-01-01",
            minOccurs=0,
            maxOccurs=1,
            default="1900-01-01 00:00:00",
            type=type(''))

        self.units = self.addLiteralInput(
            identifier="units",
            title="Units",
            abstract="In case of time hierarchy, it indicates the units of the dimension. Possible values are: s,m,h,3,6,d",
            minOccurs=0,
            maxOccurs=1,
            default="d",
            type=type(''))

        self.calendar = self.addLiteralInput(
            identifier="calendar",
            title="Calendar",
            abstract="In case of time hierarchy, it indicates the calendar type",
            minOccurs=0,
            maxOccurs=1,
            default="standard",
            type=type(''))

        self.month_lenghts = self.addLiteralInput(
            identifier="month_lenghts",
            title="Month lenghts",
            abstract="In case of time dimension and user-defined calendar, it indicates the sizes of each month in days. There byst be 12 positive integers separated by commas",
            minOccurs=0,
            maxOccurs=1,
            default="31,28,31,30,31,30,31,31,30,31,30,31",
            type=type(''))

        self.leap_year = self.addLiteralInput(
            identifier="leap_year",
            title="Leap year",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap year. By default it is set to 0",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.leap_month = self.addLiteralInput(
            identifier="leap_month",
            title="Leap month",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap month. By default it is set to 2 (February)",
            minOccurs=0,
            maxOccurs=1,
            default=2,
            type=type(1))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_importnc '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.host_partition.getValue() is not None:
            query += 'host_partition=' + str(self.host_partition.getValue()) + ';'
        if self.check_compliance.getValue() is not None:
            query += 'check_compliance=' + str(self.check_compliance.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.filesystem.getValue() is not None:
            query += 'filesystem=' + str(self.filesystem.getValue()) + ';'
        if self.ioserver.getValue() is not None:
            query += 'ioserver=' + str(self.ioserver.getValue()) + ';'
        if self.import_metadata.getValue() is not None:
            query += 'import_metadata=' + str(self.import_metadata.getValue()) + ';'
        if self.nhost.getValue() is not None:
            query += 'nhost=' + str(self.nhost.getValue()) + ';'
        if self.ndbms.getValue() is not None:
            query += 'ndbms=' + str(self.ndbms.getValue()) + ';'
        if self.ndb.getValue() is not None:
            query += 'ndb=' + str(self.ndb.getValue()) + ';'
        if self.nfrag.getValue() is not None:
            query += 'nfrag=' + str(self.nfrag.getValue()) + ';'
        if self.run.getValue() is not None:
            query += 'run=' + str(self.run.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.exp_dim.getValue() is not None:
            query += 'exp_dim=' + str(self.exp_dim.getValue()) + ';'
        if self.imp_dim.getValue() is not None:
            query += 'imp_dim=' + str(self.imp_dim.getValue()) + ';'
        if self.subset_dims.getValue() is not None:
            query += 'subset_dims=' + str(self.subset_dims.getValue()) + ';'
        if self.subset_filter.getValue() is not None:
            query += 'subset_filter=' + str(self.subset_filter.getValue()) + ';'
        if self.subset_type.getValue() is not None:
            query += 'subset_type=' + str(self.subset_type.getValue()) + ';'
        if self.time_filter.getValue() is not None:
            query += 'time_filter=' + str(self.time_filter.getValue()) + ';'
        if self.offset.getValue() is not None:
            query += 'offset=' + str(self.offset.getValue()) + ';'
        if self.exp_concept_level.getValue() is not None:
            query += 'exp_concept_level=' + str(self.exp_concept_level.getValue()) + ';'
        if self.imp_concept_level.getValue() is not None:
            query += 'imp_concept_level=' + str(self.imp_concept_level.getValue()) + ';'
        if self.compressed.getValue() is not None:
            query += 'compressed=' + str(self.compressed.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.hierarchy.getValue() is not None:
            query += 'hierarchy=' + str(self.hierarchy.getValue()) + ';'
        if self.vocabulary.getValue() is not None:
            query += 'vocabulary=' + str(self.vocabulary.getValue()) + ';'
        if self.base_time.getValue() is not None:
            query += 'base_time=' + str(self.base_time.getValue()) + ';'
        if self.units.getValue() is not None:
            query += 'units=' + str(self.units.getValue()) + ';'
        if self.calendar.getValue() is not None:
            query += 'calendar=' + str(self.calendar.getValue()) + ';'
        if self.month_lenghts.getValue() is not None:
            query += 'month_lenghts=' + str(self.month_lenghts.getValue()) + ';'
        if self.leap_year.getValue() is not None:
            query += 'leap_year=' + str(self.leap_year.getValue()) + ';'
        if self.leap_month.getValue() is not None:
            query += 'leap_month=' + str(self.leap_month.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'cwd=' + str(self.cwd.getValue()) + ';'
        query += 'measure=' + str(self.measure.getValue()) + ';'
        query += 'src_path=' + str(self.src_path.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_importnc2(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_importnc2",
            title="Ophidia importnc2",
            version="1.0.0",
            metadata=[],
            abstract="Import a NetCDF file into a datacube (both measure and dimensions); optimized version of oph_importnc",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.host_partition = self.addLiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="Name of I/O host partition used to store data. Default value 'auto' indicates that the first host partition availble is used",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.filesystem = self.addLiteralInput(
            identifier="filesystem",
            title="Filesystem",
            abstract="Type of filesystem used to store data. Possible values are 'locl', 'global' or 'auto' (default). In the laswt case the first filesystem available will be used",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.ioserver = self.addLiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data; only possible values is 'ophidiaio_memory'",
            minOccurs=0,
            maxOccurs=1,
            default="mysql_table",
            type=type(''))

        self.import_metadata = self.addLiteralInput(
            identifier="import_metadata",
            title="Import metatadata",
            abstract="With 'yes' (default), it will import also metadata; with 'no', it will import only data",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.check_compliance = self.addLiteralInput(
            identifier="check_compliance",
            title="Check compliance",
            abstract="Checks if all the metadata registered for reference vocabulary are available. No check is done by default",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.nhost = self.addLiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.ndbms = self.addLiteralInput(
            identifier="ndbms",
            title="Number of output DBMS per host",
            abstract="Number of output DBMS per host. With default value '0', all DBMS instance available per host are used",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.ndb = self.addLiteralInput(
            identifier="ndb",
            title="Number of output database per host",
            abstract="Number of output database per host. Default value is '1'",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.nfrag = self.addLiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database. With default value '0', the number of fragments will be ratio of the product of sizes of the n-1 most outer explicit dimensions to the product of the other arguments",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.measure = self.addLiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure related to the NetCDF file",
            type=type(''))

        self.run = self.addLiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the import and computes the fragmentation parameters that would be used else. If set to 'yes', the actual import operation is executed",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.src_path = self.addLiteralInput(
            identifier="src_path",
            title="Path of the NetCDF file",
            abstract="Path or OPeNDAP URL of the NetCDF file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            type=type(''))

        self.cdd = self.addLiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            minOccurs=0,
            maxOccurs=1,
            default="/",
            type=type(''))

        self.exp_dim = self.addLiteralInput(
            identifier="exp_dim",
            title="Explicit dimensions",
            abstract="Names of explicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.imp_dim = self.addLiteralInput(
            identifier="imp_dim",
            title="Implicit dimensions",
            abstract="Names of implicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.subset_dims = self.addLiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
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

        self.subset_type = self.addLiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord. If set to 'index' (default), the subset_filter is considered on a dimension index; otherwise on dimension values",
            minOccurs=0,
            maxOccurs=1,
            default="index",
            type=type(''))

        self.time_filter = self.addLiteralInput(
            identifier="time_filter",
            title="Time filter",
            abstract="Enable filters using dates for time dimensions; enabled by default",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.offset = self.addLiteralInput(
            identifier="offset",
            title="Offset",
            abstract="It is added to the bounds of subset intervals defined with 'subset_filter' in case of 'coord' filter type is used",
             minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1.0))

        self.exp_concept_level = self.addLiteralInput(
            identifier="exp_concept_level",
            title="Explicit concept level",
            abstract="Concept level short name (must be a single char) of explicit dimensions. Default value is 'c'. Multi-value field: list of concept levels separed by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="c",
            type=type(''))

        self.imp_concept_level = self.addLiteralInput(
            identifier="imp_concept_level",
            title="Implicit concept level",
            abstract="Concept level short name (must be a single char) of implicit dimensions. Default value is 'c'. Multi-value field: list of concept levels separed by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="c",
            type=type(''))

        self.compressed = self.addLiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            default="no",
            type=type(''))

        self.grid = self.addLiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            default="-",
            type=type(''))

        self.hierarchy = self.addLiteralInput(
            identifier="hierarchy",
            title="Hierarchy",
            abstract="Concept hierarchy name of the dimensions. Default value is 'oph_base'. Multi-value field: list of concept levels separed by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="oph_base",
            type=type(''))

        self.vocabulary = self.addLiteralInput(
            identifier="vocabulary",
            title="Vocabulary",
            abstract="Optional argument used to indicate a vocabulary to be used to associate metadata to the container",
            minOccurs=0,
            maxOccurs=1,
            default="CF",
            type=type(''))

        self.base_time = self.addLiteralInput(
            identifier="base_time",
            title="Base time",
            abstract="In case of time hierarchy, it indicates the base time of the dimension. Default value is 1900-01-01",
            minOccurs=0,
            maxOccurs=1,
            default="1900-01-01 00:00:00",
            type=type(''))

        self.units = self.addLiteralInput(
            identifier="units",
            title="Units",
            abstract="In case of time hierarchy, it indicates the units of the dimension. Possible values are: s,m,h,3,6,d",
            minOccurs=0,
            maxOccurs=1,
            default="d",
            type=type(''))

        self.calendar = self.addLiteralInput(
            identifier="calendar",
            title="Calendar",
            abstract="In case of time hierarchy, it indicates the calendar type",
            minOccurs=0,
            maxOccurs=1,
            default="standard",
            type=type(''))

        self.month_lenghts = self.addLiteralInput(
            identifier="month_lenghts",
            title="Month lenghts",
            abstract="In case of time dimension and user-defined calendar, it indicates the sizes of each month in days. There byst be 12 positive integers separated by commas",
            minOccurs=0,
            maxOccurs=1,
            default="31,28,31,30,31,30,31,31,30,31,30,31",
            type=type(''))

        self.leap_year = self.addLiteralInput(
            identifier="leap_year",
            title="Leap year",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap year. By default it is set to 0",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.leap_month = self.addLiteralInput(
            identifier="leap_month",
            title="Leap month",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap month. By default it is set to 2 (February)",
            minOccurs=0,
            maxOccurs=1,
            default=2,
            type=type(1))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_importnc '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.host_partition.getValue() is not None:
            query += 'host_partition=' + str(self.host_partition.getValue()) + ';'
        if self.check_compliance.getValue() is not None:
            query += 'check_compliance=' + str(self.check_compliance.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.filesystem.getValue() is not None:
            query += 'filesystem=' + str(self.filesystem.getValue()) + ';'
        if self.ioserver.getValue() is not None:
            query += 'ioserver=' + str(self.ioserver.getValue()) + ';'
        if self.import_metadata.getValue() is not None:
            query += 'import_metadata=' + str(self.import_metadata.getValue()) + ';'
        if self.nhost.getValue() is not None:
            query += 'nhost=' + str(self.nhost.getValue()) + ';'
        if self.ndbms.getValue() is not None:
            query += 'ndbms=' + str(self.ndbms.getValue()) + ';'
        if self.ndb.getValue() is not None:
            query += 'ndb=' + str(self.ndb.getValue()) + ';'
        if self.nfrag.getValue() is not None:
            query += 'nfrag=' + str(self.nfrag.getValue()) + ';'
        if self.run.getValue() is not None:
            query += 'run=' + str(self.run.getValue()) + ';'
        if self.cdd.getValue() is not None:
            query += 'cdd=' + str(self.cdd.getValue()) + ';'
        if self.exp_dim.getValue() is not None:
            query += 'exp_dim=' + str(self.exp_dim.getValue()) + ';'
        if self.imp_dim.getValue() is not None:
            query += 'imp_dim=' + str(self.imp_dim.getValue()) + ';'
        if self.subset_dims.getValue() is not None:
            query += 'subset_dims=' + str(self.subset_dims.getValue()) + ';'
        if self.subset_filter.getValue() is not None:
            query += 'subset_filter=' + str(self.subset_filter.getValue()) + ';'
        if self.subset_type.getValue() is not None:
            query += 'subset_type=' + str(self.subset_type.getValue()) + ';'
        if self.time_filter.getValue() is not None:
            query += 'time_filter=' + str(self.time_filter.getValue()) + ';'
        if self.offset.getValue() is not None:
            query += 'offset=' + str(self.offset.getValue()) + ';'
        if self.exp_concept_level.getValue() is not None:
            query += 'exp_concept_level=' + str(self.exp_concept_level.getValue()) + ';'
        if self.imp_concept_level.getValue() is not None:
            query += 'imp_concept_level=' + str(self.imp_concept_level.getValue()) + ';'
        if self.compressed.getValue() is not None:
            query += 'compressed=' + str(self.compressed.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.hierarchy.getValue() is not None:
            query += 'hierarchy=' + str(self.hierarchy.getValue()) + ';'
        if self.vocabulary.getValue() is not None:
            query += 'vocabulary=' + str(self.vocabulary.getValue()) + ';'
        if self.base_time.getValue() is not None:
            query += 'base_time=' + str(self.base_time.getValue()) + ';'
        if self.units.getValue() is not None:
            query += 'units=' + str(self.units.getValue()) + ';'
        if self.calendar.getValue() is not None:
            query += 'calendar=' + str(self.calendar.getValue()) + ';'
        if self.month_lenghts.getValue() is not None:
            query += 'month_lenghts=' + str(self.month_lenghts.getValue()) + ';'
        if self.leap_year.getValue() is not None:
            query += 'leap_year=' + str(self.leap_year.getValue()) + ';'
        if self.leap_month.getValue() is not None:
            query += 'leap_month=' + str(self.leap_month.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'cwd=' + str(self.cwd.getValue()) + ';'
        query += 'measure=' + str(self.measure.getValue()) + ';'
        query += 'src_path=' + str(self.src_path.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_input(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_input",
            title="Ophidia input",
            version="1.0.0",
            metadata=[],
            abstract="Send commands or data to an interactive task ('OPH_WAIT'); set parameters in a workflow environment",
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

        self.id = self.addLiteralInput(
            identifier="id",
            title="Id",
            abstract="Workflow identifier. By default the hosting workflow is selected. The target workflow must have been subitted the same session",
            minOccurs=0,
            maxOccurs=1,
            default="@OPH_WORKFLOW_ID",
            type=type(1))

        self.taskname = self.addLiteralInput(
            identifier="taskname",
            title="Taskname",
            abstract="Name of the interactive task. By default is set to 'Task 0' and it can be automatically set to the interactive task of target workflow if it unique",
            minOccurs=0,
            maxOccurs=1,
            default="Task 0",
            type=type(''))

        self.action = self.addLiteralInput(
            identifier="action",
            title="Action",
            abstract="Name of the command to be sent to the interactive task. Use: 'continue' to unlock the task (default); 'abort' to abort the task; 'wait' in case of no action",
            minOccurs=0,
            maxOccurs=1,
            default="continue",
            type=type(''))

        self.key = self.addLiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the parameter",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.value = self.addLiteralInput(
            identifier="value",
            title="Value",
            abstract="Value of the parameter. By default it will set to 1",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_input '
        if self.id.getValue() is not None:
            query += 'id=' + str(self.id.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.taskname.getValue() is not None:
            query += 'taskname=' + str(self.taskname.getValue()) + ';'
        if self.action.getValue() is not None:
            query += 'action=' + str(self.action.getValue()) + ';'
        if self.key.getValue() is not None:
            query += 'key=' + str(self.key.getValue()) + ';'
        if self.value.getValue() is not None:
            query += 'value=' + str(self.value.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_instances(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_instances",
            title="Ophidia instances",
            version="1.0.0",
            metadata=[],
            abstract="Show information about host partitions, hosts and dbms instances",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.action = self.addLiteralInput(
            identifier="action",
            title="Action",
            abstract="Command type. Use: 'read' to access information (default); 'add' to create user-defined host partitions, 'remove' to remove user-defined host partitions",
            minOccurs=0,
            maxOccurs=1,
            default="read",
            type=type(''))

        self.level = self.addLiteralInput(
            identifier="level",
            title="Level",
            abstract="Shows hosts with '1', DBMS instances with '2' or host partitions with '3'",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.host_filter = self.addLiteralInput(
            identifier="host_filter",
            title="Host filter",
            abstract="In 'read' mode it is an optional filter on host name and can be used only with level 2; in 'add' or 'remove' mode it is the list of host identifiers to be grouped in the user-defined partition",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.nhost = self.addLiteralInput(
            identifier="nhost",
            title="Numner of hosts",
            abstract="In 'add' or 'remove' mode it is the number of hosts to be grouped in the user-defined partition; if it is non-zero then 'host_filter' is negleted",
            minOccurs=0,
            maxOccurs=1,
            default="1",
            type=type(1))

        self.host_partition = self.addLiteralInput(
            identifier="host_partition",
            title="Host partition",
            abstract="In 'read' mode it is an optional filter on host partition name and can be used only with level 3; if no partition is specified, then the list of all partitions is shown; in 'add' mode it is the name of the new partition; in 'remove' mode it is the name of the partition to be removed",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.filesystem_filter = self.addLiteralInput(
            identifier="filesystem_filter",
            title="Filesystem filter",
            abstract="Optional filter on the type of filesystem used. Used only with level 2. Possible values are: 'local' for local disks, 'global' for GPFS disks, 'all' (default) for both types of disks",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.ioserver_filter = self.addLiteralInput(
            identifier="ioserver_filter",
            title="Ioserver filter",
            abstract="Optional filter on the type of filesystem used. Used only with level 2. Possible values are: 'mysql_table' for MySQL I/O servers, 'ophidiaio_memory' for Ophidia I/O servers only for 'all' (default) for any type of I/O server",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.host_status = self.addLiteralInput(
            identifier="host_status",
            title="Host status",
            abstract="Optional filter on status of I/O nodes. Possible values are: 'up' for up hosts, 'down' for down hosts, 'all' (default) for all hosts",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.dbms_status = self.addLiteralInput(
            identifier="dbms_status",
            title="Dbms status",
            abstract="Optional filter on the status of dbms instances. Used ony with level 2. Possible values are 'up' for instances in un state, 'down' for instances in down state, 'all' (default) for all instances",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

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
        query = 'oph_instances '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.host_partition.getValue() is not None:
            query += 'host_partition=' + str(self.host_partition.getValue()) + ';'
        if self.nhost.getValue() is not None:
            query += 'nhost=' + str(self.nhost.getValue()) + ';'
        if self.host_filter.getValue() is not None:
            query += 'host_filter=' + str(self.host_filter.getValue()) + ';'
        if self.filesystem_filter.getValue() is not None:
            query += 'filesystem_filter=' + str(self.filesystem_filter.getValue()) + ';'
        if self.ioserver_filter.getValue() is not None:
            query += 'ioserver_filter=' + str(self.ioserver_filter.getValue()) + ';'
        if self.host_status.getValue() is not None:
            query += 'host_status=' + str(self.host_status.getValue()) + ';'
        if self.dbms_status.getValue() is not None:
            query += 'dbms_status=' + str(self.dbms_status.getValue()) + ';'
        if self.level.getValue() is not None:
            query += 'level=' + str(self.level.getValue()) + ';'
        if self.action.getValue() is not None:
            query += 'action=' + str(self.action.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_intercube(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_intercube",
            title="Ophidia intercube",
            version="1.0.0",
            metadata=[],
            abstract="Execute an operation between two datacubes with the same fragmentation structure and return a new datacube as result of the specified operation applied element by element",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.pid2 = self.addLiteralInput(
            identifier="cube2",
            title="Input cube2",
            abstract="Name of the second input datacube in PID format",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.measure = self.addLiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the new measure resulting from the specified operation",
            minOccurs=0,
            maxOccurs=1,
            default="null",
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
            default=0,
            type=type(1))

        self.operation = self.addLiteralInput(
            identifier="operation",
            title="Operation",
            minOccurs=0,
            maxOccurs=1,
            default="sub",
            abstract="Indicates the operation. Possible values are sum, sub, mul, div, abs, arg, corr, mask, max, min",
            type=type(''))

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
        query = 'oph_intercube '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.operation.getValue() is not None:
            query += 'operation=' + str(self.operation.getValue()) + ';'
        if self.measure.getValue() is not None:
            query += 'measure=' + str(self.measure.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'
        query += 'cube2=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_list(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_list",
            title="Ophidia list",
            version="1.0.0",
            metadata=[],
            abstract="Show information about folders, container and datacubes fragmentation (file system)",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.level = self.addLiteralInput(
            identifier="level",
            title="Level",
            abstract="Level of verbosity. Possible values are '0' (shows folders); '1' (shows folders and containers); '2' (show folders, containers and datacubes; '3' (shows containers path, datacubes pid, measure, source and transformation level); 4 (shows containers path and datacubes); 5 (shows containers, datacubes and hosts); 6 (shows containers, datacubes, hosts and dbmss); 7 (shows containers, datacubes, hosts, dbmss and dbs); 8 (shows containers, datacubes, hosts, dbmss, dbs and fragments)",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.path = self.addLiteralInput(
            identifier="path",
            title="Path",
            abstract="Optional filter on absoute/relative path. Path is expanded, so it can also contain '.' and '..'",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

        self.container_filter = self.addLiteralInput(
            identifier="container_filter",
            title="Container filter",
            abstract="Optional filter on containers. The argument is considered only for the firt three levels. Default is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format. This argument is mandatory only when level is >=3, otherwise it is not considered",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.host_filter = self.addLiteralInput(
            identifier="host_filter",
            title="Host filter",
            abstract="Optional filter on hosts. Default is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.dbms_filter = self.addLiteralInput(
            identifier="dbms_filter",
            title="Dbms filter",
            abstract="Optional filter on DBMSs. Default is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(1))

        self.measure_filter = self.addLiteralInput(
            identifier="measure_filter",
            title="Measure filter",
            abstract="Optional filter on measure. Default is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.ntransform = self.addLiteralInput(
            identifier="ntransform",
            title="Number of transformation",
            abstract="Optional filter on operation level (number of transformation applied since import). Default is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(1))

        self.src_filter = self.addLiteralInput(
            identifier="src_filter",
            title="Source filter",
            abstract="Optional filter on source. Default is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.db_filter = self.addLiteralInput(
            identifier="db_filter",
            title="Db filter",
            abstract="Optional filter on databases. Default is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.recursive = self.addLiteralInput(
            identifier="recursive",
            title="Recursive",
            abstract="Specifies if the search is done recursively or not. The argument is considered only for the first three levels and may have the following values: 'no' (research only in current path); 'yes' (research recursively starting from current path)",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.hidden = self.addLiteralInput(
            identifier="hidden",
            title="Hidden",
            abstract="Types of containers to be shown. The argument is considered only for the first three levels and may have the following values: 'no' (only visible containers are shown); 'yes' both hidden and visible containers are shown",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

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
        query = 'oph_list '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.path.getValue() is not None:
            query += 'path=' + str(self.path.getValue()) + ';'
        if self.container_filter.getValue() is not None:
            query += 'container_filter=' + str(self.container_filter.getValue()) + ';'
        if self.pid.getValue() is not None:
             query += 'cube=' + str(self.pid.getValue()) + ';'
        if self.host_filter.getValue() is not None:
            query += 'host_filter=' + str(self.host_filter.getValue()) + ';'
        if self.dbms_filter.getValue() is not None:
            query += 'dbms_filter=' + str(self.dbms_filter.getValue()) + ';'
        if self.measure_filter.getValue() is not None:
            query += 'measure_filter=' + str(self.measure_filter.getValue()) + ';'
        if self.ntransform.getValue() is not None:
            query += 'ntransform=' + str(self.ntransform.getValue()) + ';'
        if self.src_filter.getValue() is not None:
            query += 'src_filter=' + str(self.src_filter.getValue()) + ';'
        if self.db_filter.getValue() is not None:
            query += 'db_filter=' + str(self.db_filter.getValue()) + ';'
        if self.recursive.getValue() is not None:
            query += 'recursive=' + str(self.recursive.getValue()) + ';'
        if self.hidden.getValue() is not None:
            query += 'hidden=' + str(self.hidden.getValue()) + ';'
        if self.level.getValue() is not None:
            query += 'level=' + str(self.level.getValue()) + ';'

        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_log_info(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_log_info",
            title="Ophidia log_info",
            version="1.0.0",
            metadata=[],
            abstract="Read the last lines from the server log or from a specific container log; this operator requires administrator privileges",
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
            default="sync",
            type=type(''))

        self.sessionid = self.addLiteralInput(
            identifier="sessionid",
            title="Session identifier",
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.log_type = self.addLiteralInput(
            identifier="log_type",
            title="Log type",
            abstract="Type of log to be read. Possible values are 'server', 'container' and 'ioserver'. If not specified, it will be used its default value 'server'",
            minOccurs=0,
            maxOccurs=1,
            default="server",
            type=type(''))

        self.container_id = self.addLiteralInput(
            identifier="container_id",
            title="Container id",
            abstract="Optional filter on host name. Used only with level 2",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.ioserver = self.addLiteralInput(
            identifier="ioserver",
            title="Ioserver",
            abstract="Type of the ioserver related to the requested log, valid only when requested log type is 'ioserver'",
            minOccurs=0,
            maxOccurs=1,
            default="mysql",
            type=type(''))

        self.nlines = self.addLiteralInput(
            identifier="nlines",
            title="Nlines",
            abstract="Maximum number of lines to be displayed, starting from the end of the log. Default value is '10'",
            minOccurs=0,
            maxOccurs=1,
            default=10,
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
        query = 'oph_log_info '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.log_type.getValue() is not None:
            query += 'log_type=' + str(self.log_type.getValue()) + ';'
        if self.container_id.getValue() is not None:
            query += 'container_id=' + str(self.container_id.getValue()) + ';'
        if self.ioserver.getValue() is not None:
            query += 'ioserver=' + str(self.ioserver.getValue()) + ';'
        if self.nlines.getValue() is not None:
            query += 'nlines=' + str(self.nlines.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_loggingbk(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_loggingbk",
            title="Ophidia loggingbk",
            version="1.0.0",
            metadata=[],
            abstract="Show info about sumbitted jobs",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.session_level = self.addLiteralInput(
            identifier="session_level",
            title="Session level",
            abstract="0 (session id (+ session label) (default)) or 1 (sessionid (+ session label) + session creation date)",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.job_level = self.addLiteralInput(
            identifier="job_level",
            title="Job level",
            abstract="0 (nothing (default)) or 1 (job id (+ parent job id) + workflow id + marker id) or 2 (job id (+ parent job id) + workflow id + marker id + job submission date)",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.mask = self.addLiteralInput(
            identifier="mask",
            title="Mask",
            abstract="3-digit mask, considered if job_level is bigger than 0",
            minOccurs=0,
            maxOccurs=1,
            default="000",
            type=type(''))

        self.session_filter = self.addLiteralInput(
            identifier="session_filter",
            title="Session filter",
            abstract="Filter on a particular sessionID",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.session_label_filter = self.addLiteralInput(
            identifier="session_label_filter",
            title="Session label filter",
            abstract="Filter on a particular session label",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.session_creation_filter = self.addLiteralInput(
            identifier="session_creation_filter",
            title="Session creation filter",
            abstract="Filter on session's creation date (yyyy-mm-dd hh:mm:ss <= date <= yyyy:mm:dd hh:mm:ss)",
            minOccurs=0,
            maxOccurs=1,
            default="1900-01-01 00:00:00,2100-01-01 00:00:00",
            type=type(''))

        self.workflowid_filter = self.addLiteralInput(
            identifier="workflowid_filter",
            title="Workflowid filter",
            abstract="Filter on a particular workflow ID",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.markerid_filter = self.addLiteralInput(
            identifier="markerid_filter",
            title="Markerid filter",
            abstract="Filter on a particular marker ID",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.parent_job_filter = self.addLiteralInput(
            identifier="parent_job_filter",
            title="Parent job filter",
            abstract="Filter on a particular parent job ID. If wildcard % is used, then only jobs with a parent will be shown",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.job_creation_filter = self.addLiteralInput(
            identifier="job_creation_filter",
            title="Job creation filter",
            abstract="Filter on a particular parent job ID. If wildcard % is used, then only jobs with a parent will be shown",
            minOccurs=0,
            maxOccurs=1,
            default="1900-01-01 00:00:00,2100-01-01 00:00:00",
            type=type(''))

        self.job_status_filter = self.addLiteralInput(
            identifier="job_status_filter",
            title="Job status filter",
            abstract="Filter on job status",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.submission_string_filter = self.addLiteralInput(
            identifier="submission_string_filter",
            title="Submission string filter",
            abstract="Filter on submission string",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.job_start_filter = self.addLiteralInput(
            identifier="job_start_filter",
            title="Job start filter",
            abstract="Filter on job's start date as with session_creation_filter",
            minOccurs=0,
            maxOccurs=1,
            default="1900-01-01 00:00:00,2100-01-01 00:00:00",
            type=type(''))

        self.job_end_filter = self.addLiteralInput(
            identifier="job_end_filter",
            title="Job end filter",
            abstract="Filter on job's end date as with session_creation_filter",
            minOccurs=0,
            maxOccurs=1,
            default="1900-01-01 00:00:00,2100-01-01 00:00:00",
            type=type(''))

        self.nlines = self.addLiteralInput(
            identifier="nlines",
            title="Nlines",
            abstract="Maximum number of lines to be displayed, starting from the end of the log. Default value is '100'",
            minOccurs=0,
            maxOccurs=1,
            default=100,
            type=type(''))

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
        query = 'oph_loggingbk '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.session_level.getValue() is not None:
            query += 'session_level=' + str(self.session_level.getValue()) + ';'
        if self.job_level.getValue() is not None:
            query += 'job_level=' + str(self.job_level.getValue()) + ';'
        if self.mask.getValue() is not None:
            query += 'mask=' + str(self.mask.getValue()) + ';'
        if self.session_filter.getValue() is not None:
            query += 'session_filter=' + str(self.session_filter.getValue()) + ';'
        if self.session_label_filter.getValue() is not None:
            query += 'session_label_filter=' + str(self.session_label_filter.getValue()) + ';'
        if self.session_creation_filter.getValue() is not None:
            query += 'session_creation_filter=' + str(self.session_creation_filter.getValue()) + ';'
        if self.workflowid_filter.getValue() is not None:
            query += 'workflowid_filter=' + str(self.workflowid_filter.getValue()) + ';'
        if self.markerid_filter.getValue() is not None:
            query += 'markerid_filter=' + str(self.markerid_filter.getValue()) + ';'
        if self.parent_job_filter.getValue() is not None:
            query += 'parent_job_filter=' + str(self.parent_job_filter.getValue()) + ';'
        if self.job_creation_filter.getValue() is not None:
            query += 'job_creation_filter=' + str(self.job_creation_filter.getValue()) + ';'
        if self.job_status_filter.getValue() is not None:
            query += 'job_status_filter=' + str(self.job_status_filter.getValue()) + ';'
        if self.submission_string_filter.getValue() is not None:
            query += 'submission_string_filter=' + str(self.submission_string_filter.getValue()) + ';'
        if self.job_start_filter.getValue() is not None:
            query += 'job_start_filter=' + str(self.job_start_filter.getValue()) + ';'
        if self.job_end_filter.getValue() is not None:
            query += 'job_end_filter=' + str(self.job_end_filter.getValue()) + ';'
        if self.nlines.getValue() is not None:
            query += 'nlines=' + str(self.nlines.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_man(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_man",
            title="Ophidia man",
            version="1.0.0",
            metadata=[],
            abstract="Show a description of the behaviour of an operator/primitive",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.function = self.addLiteralInput(
            identifier="function",
            title="Function",
            abstract="Name of the requested operator/primitive",
            type=type(''))

        self.function_version = self.addLiteralInput(
            identifier="function_version",
            title="Function version",
            abstract="Version of the requested operator/primitive. If not specified, it will be used its default value 'latest' in order to get info about the latest version of the operator",
            minOccurs=0,
            maxOccurs=1,
            default="latest",
            type=type(''))

        self.function_type = self.addLiteralInput(
            identifier="function_type",
            title="Function type",
            abstract="Type of function to describe; it can be operator or primitive. If not specified, it will be used its default value 'operator'",
            minOccurs=0,
            maxOccurs=1,
            default="operator",
            type=type(''))

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
        query = 'oph_man '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.function_version.getValue() is not None:
            query += 'function_version=' + str(self.function_version.getValue()) + ';'
        if self.function_type.getValue() is not None:
            query += 'function_type=' + str(self.function_type.getValue()) + ';'

        query += 'function=' + str(self.function.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_manage_session(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_manage_session",
            title="Ophidia manage_session",
            version="1.0.0",
            metadata=[],
            abstract="Request or set session data: session list, session creation date, authorized users, etc. Only session owner and administrators can submit the command",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.action = self.addLiteralInput(
            identifier="action",
            title="Action",
            abstract="Name of the action to be applied to session parameter",
            type=type(''))

        self.session = self.addLiteralInput(
            identifier="session",
            title="Session",
            abstract="Link to intended session, by default it is the working session",
            minOccurs=0,
            maxOccurs=1,
            default="this",
            type=type(''))

        self.key = self.addLiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the parameter to be get/set",
            minOccurs=0,
            maxOccurs=1,
            default="user",
            type=type(''))

        self.value = self.addLiteralInput(
            identifier="value",
            title="Value",
            abstract="Value of the key set with the argument 'key'",
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

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
        query = 'oph_manage_session '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.session.getValue() is not None:
            query += 'session=' + str(self.session.getValue()) + ';'
        if self.key.getValue() is not None:
            query += 'key=' + str(self.key.getValue()) + ';'
        if self.value.getValue() is not None:
            query += 'value=' + str(self.value.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        query += 'action=' + str(self.action.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_merge(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_merge",
            title="Ophidia merge",
            version="1.0.0",
            metadata=[],
            abstract="Create a new datacube grouping nmerge input fragments in a new output fragment",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.nmerge = self.addLiteralInput(
            identifier="nmerge",
            title="Number of Input Fragments",
            minOccurs=0,
            default=0,
            type=type(1))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_merge '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.nmerge.getValue() is not None:
            query += 'nmerge=' + str(self.nmerge.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_mergecubes(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_mergecubes",
            title="Ophidia mergecubes",
            version="1.0.0",
            metadata=[],
            abstract="Merge the measures of n input datacubes with the same fragmentation structure and creates a new datacube with the union of the n measures; only single measure data cubes can be merged",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pids = self.addLiteralInput(
            identifier="cubes",
            title="Input cubes",
            abstract="Name of the input datacubes, in PID format, to merge. Multiple-values field: list of cubes separated by '|' can be provided. At least two datacbubes must be specified",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.mode = self.addLiteralInput(
            identifier="mode",
            title="Mode",
            abstract="Possible values are 'i' (default) to interlace, 'a' to append input measures",
            minOccurs=0,
            maxOccurs=1,
            default="i",
            type=type(''))

        self.hold_values = self.addLiteralInput(
            identifier="hold_values",
            title="Hold Values",
            abstract="Possible values are 'yes' and 'no' (default). Enables the copy of the original values of implicit dimension; by defaylt new values are incremental integer",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.number = self.addLiteralInput(
            identifier="number",
            title="Number",
            abstract="Number of replies of the first cube; by default the first cube is considered only once",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_mergecubes '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.mode.getValue() is not None:
            query += 'mode=' + str(self.mode.getValue()) + ';'
        if self.hold_values.getValue() is not None:
            query += 'hold_values=' + str(self.hold_values.getValue()) + ';'
        if self.number.getValue() is not None:
            query += 'number=' + str(self.number.getValue()) + ';'

        query += 'cubes=' + str(self.pids.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_mergecubes2(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_mergecubes2",
            title="Ophidia mergecubes2",
            version="1.0.0",
            metadata=[],
            abstract="Merge the measures of n input datacubes with the same fragmentation structure and creates a new datacube with the union of the n measures; only single measure data cubes can be merged and a new implicit dimension will be created",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pids = self.addLiteralInput(
            identifier="cubes",
            title="Input cubes",
            abstract="Name of the input datacubes, in PID format, to merge. Multiple-values field: list of cubes separated by '|' can be provided. At least two datacbubes must be specified",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.dim = self.addLiteralInput(
            identifier="dim",
            title="Dimension name",
            abstract="Name of the new dimension to be created. By default a unique random name is chosen",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.dim_type = self.addLiteralInput(
            identifier="dim_type",
            title="Dimension type",
            abstract="Data type associated with the new dimension",
            minOccurs=0,
            maxOccurs=1,
            default="long",
            type=type(''))

        self.number = self.addLiteralInput(
            identifier="number",
            title="Number",
            abstract="Number of replies of the first cube; by default the first cube is considered only once",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=1,
            default="-",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_mergecubes2 '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.dim.getValue() is not None:
            query += 'dim=' + str(self.dim.getValue()) + ';'
        if self.dim_type.getValue() is not None:
            query += 'dim_type=' + str(self.dim_type.getValue()) + ';'
        if self.number.getValue() is not None:
            query += 'number=' + str(self.number.getValue()) + ';'

        query += 'cubes=' + str(self.pids.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_metadata(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_metadata",
            title="Ophidia metadata",
            version="1.0.0",
            metadata=[],
            abstract="Provide CRUD operations (Create, Read, Update and Delete) on OphidiaDB metadata",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.mode = self.addLiteralInput(
            identifier="mode",
            title="Mode",
            abstract="Set the appropiate operation among: insert, read, update, delete",
            minOccurs=0,
            maxOccurs=1,
            default="read",
            type=type(''))

        self.metadata_key = self.addLiteralInput(
            identifier="metadata_key",
            title="Metadata key",
            abstract="Name of the key identifying requested metadata. It can be used always byt not n update mode, where it necessary the id of the to-be-updated metadata",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.variable = self.addLiteralInput(
            identifier="variable",
            title="Variable",
            abstract="Name of the variable to which we can associate a new metadata key; its default value ('global') can be used to refer to a global metadata",
            minOccurs=0,
            maxOccurs=1,
            default="global",
            type=type(''))

        self.metadata_id = self.addLiteralInput(
            identifier="metadata_id",
            title="Metadata id",
            abstract="Id of the particular metadata instance to interact with. It cannot be used in insert mode. It is mandatory in update mode. It can be used in read pr delete mode to specify a particuar instance to be read or deleted. In read or delete modes, if specifed, it will mute the values of the parameter metadata_key; if not specified, it will be used its default value (0) in order to use metadata_key to select appropriate content",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.metadata_type = self.addLiteralInput(
            identifier="metadata_type",
            title="Metadata type",
            abstract="Name of the type of the to-be-inserted metadata. To change the type of already-inserted metadata, use a combination of a deletion and a insertion. default value is 'text', but other values include 'image', 'video', 'audio' and 'url', even if all contents will be saved as strings. Numerical data types are also available as well",
            minOccurs=0,
            maxOccurs=1,
            default="text",
            type=type(''))

        self.metadata_value = self.addLiteralInput(
            identifier="metadata_value",
            title="Metadata value",
            abstract="String value to be assigned to specified metadata. Valid only in insert or update nodes. In insert mode, more values ca be listed by using '|' as separator. Default value is 'null'",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.variable_filter = self.addLiteralInput(
            identifier="variable_filter",
            title="Variable filter",
            abstract="Optional filter on variable name, valid in read/delete mode only",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.metadata_type_filter = self.addLiteralInput(
            identifier="metadata_type_filter",
            title="Metadata type filter",
            abstract="Optional filter on the type of returned metadata valid in read mode only",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.metadata_value_filter = self.addLiteralInput(
            identifier="metadata_value_filter",
            title="Metadata value filter",
            abstract="Optional filter on the value of returned metadata valid in read mode only",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.force = self.addLiteralInput(
            identifier="force",
            title="Force",
            abstract="Force update or deletion of a functional metadata associated to a vocabulary. By defaylt, update or deletion of functional metadata is not allowed ('n'). Set to 'yes' to allow modification of functional metadata",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

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
        query = 'oph_metadata '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.mode.getValue() is not None:
            query += 'mode=' + str(self.mode.getValue()) + ';'
        if self.metadata_key.getValue() is not None:
            query += 'metadata_key=' + str(self.metadata_key.getValue()) + ';'
        if self.variable.getValue() is not None:
            query += 'variable=' + str(self.variable.getValue()) + ';'
        if self.metadata_id.getValue() is not None:
            query += 'metadata_id=' + str(self.metadata_id.getValue()) + ';'
        if self.metadata_type.getValue() is not None:
            query += 'metadata_type=' + str(self.metadata_type.getValue()) + ';'
        if self.metadata_value.getValue() is not None:
            query += 'metadata_value=' + str(self.metadata_value.getValue()) + ';'
        if self.variable_filter.getValue() is not None:
            query += 'variable_filter=' + str(self.variable_filter.getValue()) + ';'
        if self.metadata_type_filter.getValue() is not None:
            query += 'metadata_type_filter=' + str(self.metadata_type_filter.getValue()) + ';'
        if self.metadata_value_filter.getValue() is not None:
            query += 'metadata_value_filter=' + str(self.metadata_value_filter.getValue()) + ';'
        if self.force.getValue() is not None:
            query += 'force=' + str(self.force.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_movecontainer(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_movecontainer",
            title="Ophidia movecontainer",
            version="1.0.0",
            metadata=[],
            abstract="Move/rename a visible container",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Container",
            abstract="Exactly 2 paths (separated by |) for the input and the ouput containers (with his ordering) must be specified",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

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
        query = 'oph_movecontainer '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'

        query += 'container=' + str(self.container.getValue()) + ';'
        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_operators_list(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_operators_list",
            title="Ophidia operators_list",
            version="1.0.0",
            metadata=[],
            abstract="Show the list of all active operators",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.operator_filter = self.addLiteralInput(
            identifier="operator_filter",
            title="Operator filter",
            abstract="Optional filter on the name of the displayed operators, with pattern 'filter'",
            minOccurs=0,
            maxOccurs=1,
            default="operator",
            type=type(''))

        self.limit_filter = self.addLiteralInput(
            identifier="limit_filter",
            title="Limit filter",
            abstract="Optional filter on the maximum number of displayed operators. Default value is 0, used to show all operators",
            minOccurs=0,
            maxOccurs=1,
            default=0,
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
        query = 'oph_operators_list '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.operator_filter.getValue() is not None:
            query += 'operator_filter=' + str(self.operator_filter.getValue()) + ';'
        if self.limit_filter.getValue() is not None:
            query += 'limit_filter=' + str(self.limit_filter.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_permute(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_permute",
            title="Ophidia permute",
            version="1.0.0",
            metadata=[],
            abstract="Perform a permutation of the dimension of a datacube; this version operates only on implicit dimensions",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.dim_pos = self.addLiteralInput(
            identifier="dim_pos",
            title="Dim pos",
            abstract="Permutation of implicit dimensions as a comma-separated list of dimension levels. Number of elements in the list must be equal to the number of implicit dimensions of input datacube. Each element indicates the new level of the implicit dimension, drom the outermost to the innermost, in the output datacube",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_permute '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'dim_pos=' + str(self.dim_pos.getValue()) + ';'
        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_primitives_list(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_primitives_list",
            title="Ophidia primitives_list",
            version="1.0.0",
            metadata=[],
            abstract="Show a list with info about active Ophidia Primitives loaded into a specifiv DBMS instance",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.level = self.addLiteralInput(
            identifier="level",
            title="Level",
            abstract="Level of verbosity. '1': shows the primitive's name; '2': shows the type of the returned value, array or number; '3': shows also the name of the related dynamic library; '4': shows also the type of the primitive, simple or aggregate; '5': shows also the related DBMS id",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.dbms_filter = self.addLiteralInput(
            identifier="dbms_filter",
            title="Dbms filter",
            abstract="Id of the specific DBMS instance look up. If no values is specified, then DBMS used will be the first available",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(1))

        self.return_type = self.addLiteralInput(
            identifier="return_type",
            title="Return type",
            abstract="Optional filter on the type of the returned value. Possible values are 'array' for a set of data and 'number' for a singleton. Mute this filter with the default value 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.primitive_type = self.addLiteralInput(
            identifier="primitive_type",
            title="Primitive type",
            abstract="Optional filter on the type of the primitive. Possible values are 'simple' for row-based functions and 'aggregate' for column-based aggregate functions. Mute this filter with 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.primitive_filter = self.addLiteralInput(
            identifier="primitive_filter",
            title="Primitive filter",
            abstract="Optional filter on the name of the displayed primitives, with pattern 'filter'",
            minOccurs=0,
            maxOccurs=1,
            default="",
            type=type(''))

        self.limit_filter = self.addLiteralInput(
            identifier="limit_filter",
            title="Limit filter",
            abstract="Optional filter on the maximum number of displayed operators. Default value is 0, used to show all operators",
            minOccurs=0,
            maxOccurs=1,
            default=0,
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
        query = 'oph_primitives_list '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.level.getValue() is not None:
            query += 'level=' + str(self.level.getValue()) + ';'
        if self.dbms_filter.getValue() is not None:
            query += 'dbms_filter=' + str(self.dbms_filter.getValue()) + ';'
        if self.return_type.getValue() is not None:
            query += 'return_type=' + str(self.return_type.getValue()) + ';'
        if self.primitive_type.getValue() is not None:
            query += 'primitive_type=' + str(self.primitive_type.getValue()) + ';'
        if self.primitive_filter.getValue() is not None:
            query += 'primitive_filter=' + str(self.primitive_filter.getValue()) + ';'
        if self.limit_filter.getValue() is not None:
            query += 'limit_filter=' + str(self.limit_filter.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_publish(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_publish",
            title="Ophidia publish",
            version="1.0.0",
            metadata=[],
            abstract="Create HTML pages with data and other information from a datacube",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.show_index = self.addLiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimensions ids. With 'yes', it will also show the dimension id next to the value",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.show_id = self.addLiteralInput(
            identifier="show_id",
            title="Show id",
            abstract="If 'no' (default), it won't show fragment row ID. With 'yes', it will also show the fragment row ID",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.show_time = self.addLiteralInput(
            identifier="show_time",
            title="Show time",
            abstract="If 'no' (default), the values of time dimension are shown as numbers. With 'yes', the values are converted as a string with date and time",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.content = self.addLiteralInput(
            identifier="content",
            title="Content",
            abstract="Optional argument identifying the type of the content to be published: 'all' allows to publish data and metadata (default); 'data' allows to publish only data; 'metadata' allows to publish only metadata",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
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
        query = 'oph_publish '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.show_index.getValue() is not None:
            query += 'show_index=' + str(self.show_index.getValue()) + ';'
        if self.show_id.getValue() is not None:
            query += 'show_id=' + str(self.show_id.getValue()) + ';'
        if self.show_time.getValue() is not None:
            query += 'show_time=' + str(self.show_time.getValue()) + ';'
        if self.content.getValue() is not None:
            query += 'content=' + str(self.content.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_randcube(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_randcube",
            title="Ophidia randcube",
            version="1.0.0",
            metadata=[],
            abstract="Create a new datacube with random data and dimensions",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            type=type(''))

        self.host_partition = self.addLiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="Name of I/O host partition used to store data. Default value 'auto' indicates that the first host partition availble is used",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.filesystem = self.addLiteralInput(
            identifier="filesystem",
            title="Filesystem",
            abstract="Type of filesystem used to store data. Possible values are 'locl', 'global' or 'auto' (default). In the laswt case the first filesystem available will be used",
            minOccurs=0,
            maxOccurs=1,
            default="auto",
            type=type(''))

        self.ioserver = self.addLiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data. Possible values are: 'mysql_table' (default) or 'ophidiaio_memory'",
            minOccurs=0,
            maxOccurs=1,
            default="mysql_table",
            type=type(''))

        self.nhost = self.addLiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.ndbms = self.addLiteralInput(
            identifier="ndbms",
            title="Number of output DBMS per host",
            abstract="Number of output DBMS per host. With default value '0', all DBMS instance available per host are used",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.ndb = self.addLiteralInput(
            identifier="ndb",
            title="Number of output database per host",
            abstract="Number of output database per host. Default value is '1'",
            minOccurs=1,
            default=1,
            type=type(1))

        self.nfrag = self.addLiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database",
            minOccurs=0,
            maxOccurs=1,
            type=type(1))

        self.ntuple = self.addLiteralInput(
            identifier="ntuple",
            title="Number of tuples per fragment",
            abstract="Number of tuples per fragment",
            type=type(1))

        self.measure = self.addLiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure used in the datacube",
            type=type(''))

        self.measure_type = self.addLiteralInput(
            identifier="measure_type",
            title="Measure type",
            abstract="Type of measures. Possible values are 'double', 'float' or 'int'",
            type=type(''))

        self.exp_ndim = self.addLiteralInput(
            identifier="exp_ndim",
            title="Exp ndim",
            abstract="Used to specify how many dimensions in dim argument, starting from the first one, must be considered as explicit dimensions",
            type=type(1))

        self.dim = self.addLiteralInput(
            identifier="dim",
            title="Dim",
            abstract="Name of the dimension. Multi-value field: list of dimensions separated by '|' can be provided",
            type=type(''))

        self.concept_level = self.addLiteralInput(
            identifier="concept_level",
            title="Concept Level",
            abstract="Concept level short name (must be a singe char). Default value is 'c'. Multi-value field: list of concept levels separated by '|' can be provided",
            minOccurs=0,
            maxOccurs=1,
            default="c",
            type=type(''))

        self.dim_size = self.addLiteralInput(
            identifier="dim_size",
            title="Dim size",
            abstract="Size of random dimension. Multi-value field: list of dimensions separated by '|' can be provided",
            type=type(''))

        self.run = self.addLiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the creation and computes the fragmentation parameters that would be used else. If set to 'yes', the actual cube creation is executed",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.compressed = self.addLiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.grid = self.addLiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_randcube '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.host_partition.getValue() is not None:
            query += 'host_partition=' + str(self.host_partition.getValue()) + ';'
        if self.filesystem.getValue() is not None:
            query += 'filesystem=' + str(self.filesystem.getValue()) + ';'
        if self.ioserver.getValue() is not None:
            query += 'ioserver=' + str(self.ioserver.getValue()) + ';'
        if self.nhost.getValue() is not None:
            query += 'nhost=' + str(self.nhost.getValue()) + ';'
        if self.ndbms.getValue() is not None:
            query += 'ndbms=' + str(self.ndbms.getValue()) + ';'
        if self.ndb.getValue() is not None:
            query += 'ndb=' + str(self.ndb.getValue()) + ';'
        if self.run.getValue() is not None:
            query += 'run=' + str(self.run.getValue()) + ';'
        if self.concept_level.getValue() is not None:
            query += 'concept_level=' + str(self.concept_level.getValue()) + ';'
        if self.compressed.getValue() is not None:
            query += 'compressed=' + str(self.compressed.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'container=' + str(self.container.getValue()) + ';'
        query += 'nfrag=' + str(self.nfrag.getValue()) + ';'
        query += 'ntuple=' + str(self.ntuple.getValue()) + ';'
        query += 'measure=' + str(self.measure.getValue()) + ';'
        query += 'measure_type=' + str(self.measure_type.getValue()) + ';'
        query += 'dim=' + str(self.dim.getValue()) + ';'
        query += 'exp_ndim=' + str(self.exp_ndim.getValue()) + ';'
        query += 'dim_size=' + str(self.dim_size.getValue()) + ';'
        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_reduce(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_reduce",
            title="Ophidia reduce",
            version="1.0.0",
            metadata=[],
            abstract="Perform a reduction operation on a datacube with respect to implicit dimensions",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
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
            default=0,
            type=type(1))

        self.group_size = self.addLiteralInput(
            identifier="group_size",
            title="Group size",
            abstract="Size of the aggregation set. If set to 'all', the reduction will occur on all elements of each tuple",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.operation = self.addLiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the reduction operation. Possible values are count, max, min, avg, sum, std, var, cmoment, acmoment, rmoment, armoment, quantile, arg_max, arg_min",
            type=type(''))

        self.order = self.addLiteralInput(
            identifier="order",
            title="Order",
            minOccurs=0,
            maxOccurs=1,
            default=2,
            type=type(1.0))

        self.missingvalue = self.addLiteralInput(
            identifier="missingvalue",
            title="Missing value",
            minOccurs=0,
            maxOccurs=1,
            default="NAN",
            type=type(1.0))

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
        query = 'oph_reduce '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.group_size.getValue() is not None:
            query += 'group_size=' + str(self.group_size.getValue()) + ';'
        if self.order.getValue() is not None:
            query += 'order=' + str(self.order.getValue()) + ';'
        if self.missingvalue.getValue() is not None:
            query += 'missingvalue=' + str(self.missingvalue.getValue()) + ';'

        query += 'operation=' + str(self.operation.getValue()) + ';'
        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_reduce2(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_reduce2",
            title="Ophidia reduce2",
            version="1.0.0",
            metadata=[],
            abstract="Perform a reduction operation based on hierarchy on a datacube",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
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
            default=0,
            type=type(1))

        self.dim = self.addLiteralInput(
            identifier="dim",
            title="Dim",
            abstract="Name of dimension on which the operation will be applied",
            type=type(''))

        self.concept_level = self.addLiteralInput(
            identifier="concept_level",
            title="Concept Level",
            abstract="Concept level inside the hierarchy used for the operation",
            minOccurs=0,
            maxOccurs=1,
            default="A",
            type=type(''))

        self.midnight = self.addLiteralInput(
            identifier="midnight",
            title="Midnight",
            abstract="Possible values are: 00, 24. If 00, the edge point of two consecutive aggregate time sets will be aggregated into the right set; if 24 to the left set",
            minOccurs=0,
            maxOccurs=1,
            default="24",
            type=type(''))

        self.order = self.addLiteralInput(
            identifier="order",
            title="Order",
            abstract="Order used in evaluation of the moments or value of the quantile in range [0,1]",
            minOccurs=0,
            maxOccurs=1,
            default=2,
            type=type(1.0))

        self.missingvalue = self.addLiteralInput(
            identifier="missingvalue",
            title="Missing value",
            minOccurs=0,
            maxOccurs=1,
            default="NAN",
            type=type(1.0))

        self.operation = self.addLiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the reduction operation. Possible values are count, max, min, avg, sum, std, var, cmoment, acmoment, rmoment, armoment, quantile, arg_max, arg_min",
            type=type(''))

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
        query = 'oph_reduce2 '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'
        if self.concept_level.getValue() is not None:
            query += 'concept_level=' + str(self.concept_level.getValue()) + ';'
        if self.midnight.getValue() is not None:
            query += 'midnight=' + str(self.midnight.getValue()) + ';'
        if self.order.getValue() is not None:
            query += 'order=' + str(self.order.getValue()) + ';'
        if self.missingvalue.getValue() is not None:
            query += 'missingvalue=' + str(self.missingvalue.getValue()) + ';'

        query += 'dim=' + str(self.dim.getValue()) + ';'
        query += 'operation=' + str(self.operation.getValue()) + ';'
        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_restorecontainer(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_restorecontainer",
            title="Ophidia restorecontainer",
            version="1.0.0",
            metadata=[],
            abstract="Restore a hidden container",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="Name of the output container to restore",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            type=type(''))

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
        query = 'oph_restorecontainer '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'

        query += 'container=' + str(self.container.getValue()) + ';'
        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_resume(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_resume",
            title="Ophidia resume",
            version="1.0.0",
            metadata=[],
            abstract="Request the list of the commands submitted within a session or the output of a command",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.session = self.addLiteralInput(
            identifier="session",
            title="Session",
            abstract="Identifier of the intended session; by default, it is the working session",
            minOccurs=0,
            maxOccurs=1,
            default="this",
            type=type(''))

        self.id = self.addLiteralInput(
            identifier="id",
            title="Id",
            abstract="Identifier of the intended workflow or marker; by default, no filter is applied",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.id_type = self.addLiteralInput(
            identifier="id_type",
            title="Id type",
            abstract="Use 'workflow' (default) or 'marker' to set the filter 'id'",
            minOccurs=0,
            maxOccurs=1,
            default="workflow",
            type=type(''))

        self.document_type = self.addLiteralInput(
            identifier="document_type",
            title="Document type",
            abstract="Document type, 'request' or 'response'",
            minOccurs=0,
            maxOccurs=1,
            default="response",
            type=type(''))

        self.level = self.addLiteralInput(
            identifier="level",
            title="Level",
            abstract="Use level '0' to ask for submitted commands (short version) or workflow progress ratio; Use level '1' to ask for submitted commands (short version) or workflow output; use level '2' to ask for submitted commands (extendend version) or the list of workflow tasks; use level '3' to ask for JSON Requests or the list of workflow task outputs; use level '4' to ask for the list of commands associated to tasks of a workflow (valid only for a specific workflow); use level '5' to ask for original JSON Request (valid only for a specufuc workflow)",
            minOccurs=0,
            maxOccurs=1,
            default=1,
            type=type(1))

        self.user = self.addLiteralInput(
            identifier="user",
            title="User",
            abstract="Filter by name of the submitter; by default, no filter is applied. Valid only for workflow list ('id'=0)",
            minOccurs=0,
            maxOccurs=1,
            default="",
            type=type(''))

        self.status_filter = self.addLiteralInput(
            identifier="status_filter",
            title="Status filter",
            abstract="In case of running workflows, filter by job status according some bitmaps",
            minOccurs=0,
            maxOccurs=1,
            default=11111111,
            type=type(1))

        self.save = self.addLiteralInput(
            identifier="save",
            title="Save",
            abstract="Used to save session identifier on server",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

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
        query = 'oph_resume '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.session.getValue() is not None:
            query += 'session=' + str(self.session.getValue()) + ';'
        if self.id.getValue() is not None:
            query += 'id=' + str(self.id.getValue()) + ';'
        if self.id_type.getValue() is not None:
            query += 'id_type=' + str(self.id_type.getValue()) + ';'
        if self.document_type.getValue() is not None:
            query += 'document_type=' + str(self.document_type.getValue()) + ';'
        if self.level.getValue() is not None:
            query += 'level=' + str(self.level.getValue()) + ';'
        if self.user.getValue() is not None:
            query += 'user=' + str(self.user.getValue()) + ';'
        if self.status_filter.getValue() is not None:
            query += 'status_filter=' + str(self.status_filter.getValue()) + ';'
        if self.save.getValue() is not None:
            query += 'save=' + str(self.save.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_rollup(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_rollup",
            title="Ophidia rollup",
            version="1.0.0",
            metadata=[],
            abstract="Perform a roll-up on a datacube, i.e. it transform dimensions from explicit to implicit",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

        self.schedule = self.addLiteralInput(
            identifier="schedule",
            title="Schedule",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.description = self.addLiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.ndim = self.addLiteralInput(
            identifier="ndim",
            title="Number of Implicit Dimensions",
            abstract="Number of explicit dimensions that will be transformed in implicit dimensions",
            minOccurs=0,
            maxOccurs=1,
            default=1,
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
        query = 'oph_rollup '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.ndim.getValue() is not None:
            query += 'ndim=' + str(self.ndim.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_script(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_script",
            title="Ophidia script",
            version="1.0.0",
            metadata=[],
            abstract="Execute a bash script",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.script = self.addLiteralInput(
            identifier="script",
            title="Script",
            abstract="Name of the script to be executed; by default no operation is performed. The script has to be registered at server side",
            minOccurs=0,
            maxOccurs=1,
            default=":",
            type=type(''))

        self.args = self.addLiteralInput(
            identifier="args",
            title="Input arguments",
            abstract="List of pipe-separated arguments to be passed to te script",
            minOccurs=0,
            maxOccurs=1,
            default="",
            type=type(''))

        self.stdout = self.addLiteralInput(
            identifier="stdout",
            title="Stdout",
            abstract="File where screen output (stdout) wil be redirected (appended); set to 'stdout' for no redirection",
            minOccurs=0,
            maxOccurs=1,
            default="stdout",
            type=type(''))

        self.stderr = self.addLiteralInput(
            identifier="stderr",
            title="Stderr",
            abstract="File where errors (stderr) will be redirected (appended); set to 'stderr' for no diredirection",
            minOccurs=0,
            maxOccurs=1,
            default="stderr",
            type=type(''))

        self.list = self.addLiteralInput(
            identifier="list",
            title="List",
            abstract="Get the available scripts. You can choose 'yes' or 'no'",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

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
        query = 'oph_script '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.script.getValue() is not None:
            query += 'script=' + str(self.script.getValue()) + ';'
        if self.args.getValue() is not None:
            query += 'args=' + str(self.args.getValue()) + ';'
        if self.stdout.getValue() is not None:
            query += 'stdout=' + str(self.stdout.getValue()) + ';'
        if self.stderr.getValue() is not None:
            query += 'stderr=' + str(self.stderr.getValue()) + ';'
        if self.list.getValue() is not None:
            query += 'list=' + str(self.list.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
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

class oph_search(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_search",
            title="Ophidia search",
            version="1.0.0",
            metadata=[],
            abstract="Provide enhanced searching on metadata",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.container_filter = self.addLiteralInput(
            identifier="container_filter",
            title="Container filter",
            abstract="Zero, one or more filters on container's names. Filters separated by '|'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.metadata_key_filter = self.addLiteralInput(
            identifier="metadata_key_filter",
            title="Metadata key filter",
            abstract="Zero, one or more filters on metadata keys. Filters separated by '|'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.metadata_value_filter = self.addLiteralInput(
            identifier="metadata_value_filter",
            title="Metadata value filter",
            abstract="Zero, one or more filters on metadata values. Filters separated by '|'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.path = self.addLiteralInput(
            identifier="pathr",
            title="Path",
            abstract="Abslolute/relative path used as the starting point of the recursive search. If not specified or in case of '-' (default), the recursive search will start at the cwd",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, necessary to correctly parse paths. ALl resolved paths must be associated to the calling session",
            type=type(''))

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
        query = 'oph_search '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.container_filter.getValue() is not None:
            query += 'container_filter=' + str(self.container_filter.getValue()) + ';'
        if self.metadata_key_filter.getValue() is not None:
            query += 'metadata_key_filter=' + str(self.metadata_key_filter.getValue()) + ';'
        if self.metadata_value_filter.getValue() is not None:
            query += 'metadata_value_filter=' + str(self.metadata_value_filter.getValue()) + ';'
        if self.path.getValue() is not None:
            query += 'path=' + str(self.path.getValue()) + ';'

        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_service(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_service",
            title="Ophidia service",
            version="1.0.0",
            metadata=[],
            abstract="Request or set the service status",
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

        self.state = self.addLiteralInput(
            identifier="status",
            title="Status",
            abstract="New service status, 'up' or 'down'",
            minOccurs=0,
            maxOccurs=1,
            default="",
            type=type(''))

        self.level = self.addLiteralInput(
            identifier="level",
            title="Level",
            abstract="Use level '1' (default) to ask for service status only; use level '2' to ask for job list",
            minOccurs=0,
            maxOccurs=1,
            default=1,
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
        query = 'oph_service '
        if self.state.getValue() is not None:
            query += 'status=' + str(self.state.getValue()) + ';'
        if self.level.getValue() is not None:
            query += 'level=' + str(self.level.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_set(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_set",
            title="Ophidia set",
            version="1.0.0",
            metadata=[],
            abstract="Set parameters in the workflow environment",
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

        self.id = self.addLiteralInput(
            identifier="id",
            title="Id",
            abstract="Workflow identifier. By default the hosting workflow is selected. The target workflow must have been subitted the same session",
            minOccurs=0,
            maxOccurs=1,
            default="@OPH_WORKFLOW_ID",
            type=type(1))

        self.key = self.addLiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the parameter",
            type=type(''))

        self.value = self.addLiteralInput(
            identifier="value",
            title="Value",
            abstract="Value of the parameter. By default it will set to 1",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

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
        query = 'oph_set '
        if self.id.getValue() is not None:
            query += 'id=' + str(self.id.getValue()) + ';'
        if self.value.getValue() is not None:
            query += 'value=' + str(self.value.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        query += 'key=' + str(self.key.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_showgrid(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_showgrid",
            title="Ophidia showgrid",
            version="1.0.0",
            metadata=[],
            abstract="Show information about one or more grids related to the specified container",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Input container",
            abstract="Name of the input container",
            type=type(''))

        self.grid = self.addLiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Name of the grid to visualize. With no name, all grids are shown",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.dim = self.addLiteralInput(
            identifier="dim",
            title="Dimension name",
            abstract="Name of dimension to visualize. Multiple-value field: list of dimensions separated by '|' can be provided. If not specified, all dimensions are shown",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.show_index = self.addLiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimension ids. With 'yes', it will also show the dimension id next to the value",
            minOccurs=0,
            maxOccurs=1,
            default="no",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, necessary to correctly parse paths. ALl resolved paths must be associated to the calling session",
            type=type(''))

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
        query = 'oph_showgrid '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.grid.getValue() is not None:
            query += 'grid=' + str(self.grid.getValue()) + ';'
        if self.dim.getValue() is not None:
            query += 'dim=' + str(self.dim.getValue()) + ';'
        if self.show_index.getValue() is not None:
            query += 'show_index=' + str(self.show_index.getValue()) + ';'

        query += 'container=' + str(self.container.getValue()) + ';'
        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_split(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_split",
            title="Ophidia split",
            version="1.0.0",
            metadata=[],
            abstract="Create a new datacube by splitting input fragments in nsplit output fragments in the same origin database",
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

        self.nthreads = self.addLiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
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

        self.nsplit = self.addLiteralInput(
            identifier="nsplit",
            title="Nsplit",
            abstract="Number of output fragments per input fragment",
            type=type(1))

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
            default=0,
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
        query = 'oph_split '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.nthreads.getValue() is not None:
            query += 'nthreads=' + str(self.nthreads.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.schedule.getValue() is not None:
            query += 'schedule=' + str(self.schedule.getValue()) + ';'
        if self.nsplit.getValue() is not None:
            query += 'nsplit=' + str(self.nsplit.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.description.getValue() is not None:
            query += 'description=' + str(self.description.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_subset(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_subset",
            title="Ophidia subset",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
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
            default=0,
            type=type(1))

        self.subset_type = self.addLiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord",
            minOccurs=0,
            maxOccurs=1,
            default="index",
            type=type(''))

        self.time_filter = self.addLiteralInput(
            identifier="time_filter",
            title="Time Filter",
            abstract="Possibile values are: yes, no",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.offset = self.addLiteralInput(
            identifier="offset",
            title="Offset",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1.0))

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
        if self.subset_type.getValue() is not None:
            query += 'subset_type=' + str(self.subset_type.getValue()) + ';'
        if self.time_filter.getValue() is not None:
            query += 'time_filter=' + str(self.time_filter.getValue()) + ';'
        if self.offset.getValue() is not None:
            query += 'offset=' + str(self.offset.getValue()) + ';'
        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_subset2(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_subset2",
            title="Ophidia subset2",
            version="1.0.0",
            metadata=[],
            abstract="Perform a subsetting along dimensions of a datacube; dimension values are used as input filters",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
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
            default=0,
            type=type(1))

        self.time_filter = self.addLiteralInput(
            identifier="time_filter",
            title="Time Filter",
            abstract="Possibile values are: yes, no",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

        self.offset = self.addLiteralInput(
            identifier="offset",
            title="Offset",
            abstract="It is added to the bounds of subset intervals defined with 'subset_filter' in case of 'coord' filter type is used",
            minOccurs=0,
            maxOccurs=1,
            default=0,
            type=type(1.0))

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
        query = 'oph_subset2 '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
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
        if self.time_filter.getValue() is not None:
            query += 'time_filter=' + str(self.time_filter.getValue()) + ';'
        if self.offset.getValue() is not None:
            query += 'offset=' + str(self.offset.getValue()) + ';'
        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_tasks(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_tasks",
            title="Ophidia tasks",
            version="1.0.0",
            metadata=[],
            abstract="Show information about executed tasks; default arguments allow to show all the tasks executed; if a container is given, then only tasks that involve the container as shown",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.cube_filter = self.addLiteralInput(
            identifier="cube_filter",
            title="Cube filter",
            abstract="Optional filter on the name of input/output datacubes. The name must be in PID format. Default value is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.operator_filter = self.addLiteralInput(
            identifier="operator_filter",
            title="Operator filter",
            abstract="Optional filter on the name of the operators implied in tasks. Default value is 'all'",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

        self.path = self.addLiteralInput(
            identifier="pathr",
            title="Path",
            abstract="Optional filter of abslolute/relative path. Path is expanded so it can also contain '.' and '..'. It is only cnsidered when container_filter is specified",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.cwd = self.addLiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, necessary to correctly parse paths. ALl resolved paths must be associated to the calling session",
            type=type(''))

        self.container = self.addLiteralInput(
            identifier="container",
            title="Input container",
            abstract="Name of the input container",
            minOccurs=0,
            maxOccurs=1,
            default="all",
            type=type(''))

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
        query = 'oph_tasks '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.container.getValue() is not None:
            query += 'container=' + str(self.container.getValue()) + ';'
        if self.cube_filter.getValue() is not None:
            query += 'cube_filter=' + str(self.cube_filter.getValue()) + ';'
        if self.operator_filter.getValue() is not None:
            query += 'operator_filter=' + str(self.operator_filter.getValue()) + ';'
        if self.path.getValue() is not None:
            query += 'path=' + str(self.path.getValue()) + ';'

        query += 'cwd=' + str(self.cwd.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_unpublish(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_unpublish",
            title="Ophidia unpublish",
            version="1.0.0",
            metadata=[],
            abstract="Remove the HTML pages created by the PUBLISH2 operator; note that it doesn't remove the container folder",
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
            minOccurs=0,
            maxOccurs=1,
            default="null",
            type=type(''))

        self.pid = self.addLiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            type=type(''))

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
        query = 'oph_unpublish '
        if self.sessionid.getValue() is not None:
            query += 'sessionid=' + str(self.sessionid.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'

        query += 'cube=' + str(self.pid.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

class oph_wait(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="oph_wait",
            title="Ophidia wait",
            version="1.0.0",
            metadata=[],
            abstract="Wait until an event occurs; the task can be unlocked by means of the command 'OPH_INPUT'",
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

        self.type = self.addLiteralInput(
            identifier="type",
            title="Type",
            abstract="Waiting type. Use: 'clock' for fixed time; 'inpit' to ask to input data and set a new 'value' for 'key'; 'file' to check the existence of a file",
            minOccurs=0,
            maxOccurs=1,
            default="clock",
            type=type(''))

        self.timeout = self.addLiteralInput(
            identifier="timeout",
            title="Timeout",
            abstract="According to the value of parameter 'timeout_type', it is the duration (in seconds) or the end instant of the waiting interval",
            minOccurs=0,
            maxOccurs=1,
            default=-1,
            type=type(1))

        self.timeout_type = self.addLiteralInput(
            identifier="timeout_type",
            title="Timeout type",
            abstract="Meaning the value of 'timeout'. Use 'duration' to set the duration of waiting interval; 'deadline' to set the end time instant of waiting interval",
            minOccurs=0,
            maxOccurs=1,
            default="duration",
            type=type(''))

        self.key = self.addLiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the parameter",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.value = self.addLiteralInput(
            identifier="value",
            title="Value",
            abstract="Value of the parameter. By default it will set to 1",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.filename = self.addLiteralInput(
            identifier="filename",
            title="Filename",
            abstract="Name of the file to be checked (only for type 'file'); base folder to refer files in BASE_SRC_PATH",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.message = self.addLiteralInput(
            identifier="message",
            title="Message",
            abstract="This user-defined message is appended to response in order to notify the waiting reason",
            minOccurs=0,
            maxOccurs=1,
            default="-",
            type=type(''))

        self.run = self.addLiteralInput(
            identifier="run",
            title="Run",
            abstract="Set to 'yes' (default) to wait effectively",
            minOccurs=0,
            maxOccurs=1,
            default="yes",
            type=type(''))

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
        query = 'oph_wait '
        if self.type.getValue() is not None:
            query += 'type=' + str(self.type.getValue()) + ';'
        if self.exec_mode.getValue() is not None:
            query += 'exec_mode=' + str(self.exec_mode.getValue()) + ';'
        if self.timeout.getValue() is not None:
            query += 'timeout=' + str(self.timeout.getValue()) + ';'
        if self.timeout_type.getValue() is not None:
            query += 'timeout_type=' + str(self.timeout_type.getValue()) + ';'
        if self.key.getValue() is not None:
            query += 'key=' + str(self.key.getValue()) + ';'
        if self.value.getValue() is not None:
            query += 'value=' + str(self.value.getValue()) + ';'
        if self.filename.getValue() is not None:
            query += 'filename=' + str(self.filename.getValue()) + ';'
        if self.message.getValue() is not None:
            query += 'message=' + str(self.message.getValue()) + ';'
        if self.run.getValue() is not None:
            query += 'run=' + str(self.run.getValue()) + ';'
        if self.ncores.getValue() is not None:
            query += 'ncores=' + str(self.ncores.getValue()) + ';'

        logging.debug("Create Ophidia client")
        oph_client = _client.Client(self.userid.getValue(), self.passwd.getValue(), _host, _port)
        oph_client.api_mode = False

        logging.debug("Submit the query: "+ query)
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

