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


class oph_aggregate(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Input container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Grid of dimensions to be used (if the grid already exists) or the one to be created (if the grid has a new name). If it isn't specified, no grid will be used",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        group_size = LiteralInput(
            identifier="group_size",
            title="Group size",
            abstract="Number of tuples per group to consider in the aggregation function. If set to 'all' the aggregation, will occur on all tuples of the table",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        missingvalue = LiteralInput(
            identifier="missingvalue",
            title="Missingvalue",
            min_occurs=0,
            max_occurs=1,
            default="NAN",
            data_type='float')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        operation = LiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the operation. Possible values are count, max, min, avg, sum",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, container, grid, description, group_size, missingvalue, schedule, operation]
        outputs = [jobid, response, error]

        super(oph_aggregate, self).__init__(
            self._handler,
            identifier="oph_aggregate",
            title="Ophidia aggregate",
            version=_version,
            abstract="Aggregate cubes along explicit dimensions",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_aggregate '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['group_size'][0].data is not None:
            query += 'group_size=' + str(request.inputs['group_size'][0].data) + ';'
        if request.inputs['missingvalue'][0].data is not None:
            query += 'missingvalue=' + str(request.inputs['missingvalue'][0].data) + ';'

        query += 'operation=' + str(request.inputs['operation'][0].data) + ';'
        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_aggregate2(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Grid of dimensions to be used (if the grid already exists) or the one to be created (if the grid has a new name). If it isn't specified, no grid will be used",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        operation = LiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the operation. Possible values are count, max, min, avg, sum",
            data_type='string')

        dim = LiteralInput(
            identifier="dim",
            title="Dim",
            abstract="Name of dimension on which the operation will be applied",
            data_type='string')

        concept_level = LiteralInput(
            identifier="concept_level",
            title="Concept Level",
            abstract="Concept level inside the hierarchy used for the operation",
            min_occurs=0,
            max_occurs=1,
            default="A",
            data_type='string')

        midnight = LiteralInput(
            identifier="midnight",
            title="Midnight",
            abstract="Possible values are: 00, 24. If 00, the edge point of two consecutive aggregate time sets will be aggregated into the right set; if 24 to the left set",
            min_occurs=0,
            max_occurs=1,
            default="24",
            data_type='string')

        missingvalue = LiteralInput(
            identifier="missingvalue",
            title="Missingvalue",
            abstract="Value to be considered as missing value",
            min_occurs=0,
            max_occurs=1,
            default="NAN",
            data_type='float')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, container, grid, description, schedule, operation, dim, concept_level, midnight, missingvalue]
        outputs = [jobid, response, error]

        super(oph_aggregate2, self).__init__(
            self._handler,
            identifier="oph_aggregate2",
            title="Ophidia aggregate2",
            version=_version,
            abstract="Execute an aggregation operation based on hierarchy on a datacube",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_aggregate2 '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['concept_level'][0].data is not None:
            query += 'concept_level=' + str(request.inputs['concept_level'][0].data) + ';'
        if request.inputs['midnight'][0].data is not None:
            query += 'midnight=' + str(request.inputs['midnight'][0].data) + ';'
        if request.inputs['missingvalue'][0].data is not None:
            query += 'missingvalue=' + str(request.inputs['missingvalue'][0].data) + ';'

        query += 'dim=' + str(request.inputs['dim'][0].data) + ';'
        query += 'operation=' + str(request.inputs['operation'][0].data) + ';'
        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_apply(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        query = LiteralInput(
            identifier="query",
            title="Query",
            abstract="User-defined SQL query. Use keyword 'measure' to refer to time series; use the keyword 'dimension' to refer to the input dimension array (only if one dimension of input cube is implicit)",
            min_occurs=0,
            max_occurs=1,
            default="measure",
            data_type='string')

        dim_query = LiteralInput(
            identifier="dim_query",
            title="Dim Query",
            abstract="Dimension of query defined by user",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        measure = LiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the new measure resulting from the specified operation",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        measure_type = LiteralInput(
            identifier="measure_type",
            title="Measure Type",
            abstract="Two possible values: 'auto' and 'manual'. If 'auto', dimension type will be set automatically to that of input datacube and the related primitive arguments have to be omitted in 'query'; if 'manual' (default), dimension type and the related primitive arguments have to be set in 'query'",
            min_occurs=0,
            max_occurs=1,
            default="manual",
            data_type='string')

        dim_type = LiteralInput(
            identifier="dim_type",
            title="Dim Type",
            abstract="Two possible values: 'auto' and 'manual'. If 'auto', dimension type will be set automatically to that of input datacube and the related primitive arguments have to be omitted in 'dim_query'; if 'manual' (default), dimension type and the related primitive arguments have to be set in 'dim_query'",
            min_occurs=0,
            max_occurs=1,
            default="manual",
            data_type='string')

        check_type = LiteralInput(
            identifier="check_type",
            title="Check Type",
            abstract="Two possible values: 'yes' and 'no'. If 'yes', the agreement between input and output data types of nested primitives will be checked; if 'no', data type will be mot cjecked",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        on_reduce = LiteralInput(
            identifier="on_reduce",
            title="Operation to be applied to dimension on reduce",
            abstract="Two possible values: 'update' and 'skip'. If 'update' the values of implicit dimension are automatically set to a list of long integers starting from 1 even if dimension size does not decrease; f 'skip' (default) the values are updated to a list of long integers only in case dimension size decrease due to a reduction primitive",
            min_occurs=0,
            max_occurs=1,
            default="skip",
            data_type='string')

        compressed = LiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Three possible values: 'auto', 'yes' and 'no'. If 'auto', new data will be compressed according to compression status of input datacube; if 'yes', new data will be compressed; if 'no', data will be inserted without compression",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, container, description, schedule, query, dim_query, measure, measure_type, dim_type, check_type, on_reduce, compressed]
        outputs = [jobid, response, error]

        super(oph_apply, self).__init__(
            self._handler,
            identifier="oph_apply",
            title="Ophidia apply",
            version=_version,
            abstract="Execute a query on a datacube",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_apply '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['query'][0].data is not None:
            query += 'query=' + str(request.inputs['query'][0].data) + ';'
        if request.inputs['dim_query'][0].data is not None:
            query += 'dim_query=' + str(request.inputs['dim_query'][0].data) + ';'
        if request.inputs['measure'][0].data is not None:
            query += 'measure=' + str(request.inputs['measure'][0].data) + ';'
        if request.inputs['measure_type'][0].data is not None:
            query += 'measure_type=' + str(request.inputs['measure_type'][0].data) + ';'
        if request.inputs['dim_type'][0].data is not None:
            query += 'dim_type=' + str(request.inputs['dim_type'][0].data) + ';'
        if request.inputs['check_type'][0].data is not None:
            query += 'check_type=' + str(request.inputs['check_type'][0].data) + ';'
        if request.inputs['on_reduce'][0].data is not None:
            query += 'on_reduce=' + str(request.inputs['on_reduce'][0].data) + ';'
        if request.inputs['compressed'][0].data is not None:
            query += 'compressed=' + str(request.inputs['compressed'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_b2drop(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        auth_path = LiteralInput(
            identifier="auth_path",
            title="Authorization data",
            abstract="Absolute path to the netrc file containing the B2DROP login information; note that it is not possible to use double dots (..) within the path; if no path is provided, the user's home will be used (default)",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        src_path = LiteralInput(
            identifier="src_path",
            title="Source path",
            abstract="Path to the file to be uploaded to B2DROP. The path can be absolute or relative; in case of relative path the cdd argument will be pre-pended; note that it is not possible to use double dots (..) within the path",
            data_type='string')

        dest_path = LiteralInput(
            identifier="dest_path",
            title="Destination path",
            abstract="Path where the file will be uploaded on B2DROP. In case no path is specified, the base path and the input file name will be used (default)",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Current Data Directory",
            abstract="Absolute path corresponding to the current directory on data repository",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, auth_path, src_path, dest_path, cdd]
        outputs = [jobid, response, error]

        super(oph_b2drop, self).__init__(
            self._handler,
            identifier="oph_b2drop",
            title="Ophidia B2DROP",
            version=_version,
            abstract="Upload a file onto a B2DROP remote folder; note that in order to be able to use the operator, a netrc file with the credentials to B2DROP is required. Commonly the hidden .netrc file resides in the user's home directory",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_b2drop '

        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['auth_path'][0].data is not None:
            query += 'auth_path=' + str(request.inputs['auth_path'][0].data) + ';'
        if request.inputs['dest_path'][0].data is not None:
            query += 'dest_path=' + str(request.inputs['dest_path'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'

        query += 'src_path=' + str(request.inputs['src_path'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_cancel(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        id = LiteralInput(
            identifier="id",
            title="Identifier of the workflow to be stopped",
            data_type='integer')

        type = LiteralInput(
            identifier="type",
            title="Cancellation type",
            abstract="Use 'kill' to abort workflow and submitted tasks (default), 'abort' to abort workflow and pending tasks (running tasks continue), 'stop' to abort workflow, submitted tasks continue",
            min_occurs=0,
            max_occurs=1,
            default="kill",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, id, type]
        outputs = [jobid, response, error]

        super(oph_cancel, self).__init__(
            self._handler,
            identifier="oph_cancel",
            title="Ophidia cancel",
            version=_version,
            abstract="Stop the execution of a running workflow",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_cancel '
        if request.inputs['type'][0].data is not None:
            query += 'type=' + str(request.inputs['type'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'

        query += 'id=' + str(request.inputs['id'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_cluster(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        action = LiteralInput(
            identifier="action",
            title="Action",
            abstract="Four possibile actions are available: 'info' (default) returns information about user-defined clusters; 'info_cluster' returns global information about clusters (reserved to administrators); 'deploy' tries to reserve hosts and starts I/O servers (default); 'undeploy' stops reservation and I/O servers",
            min_occurs=0,
            max_occurs=1,
            default="info",
            data_type='string')

        nhost = LiteralInput(
            identifier="nhost",
            title="Number of hosts",
            abstract="Number of hosts to be reserved as well as number of I/O servers to be started over them",
            min_occurs=0,
            max_occurs=1,
            default="0",
            data_type='integer')

        host_partition = LiteralInput(
            identifier="host_partititon",
            title="Host partition",
            abstract="Name of user-defined partition to be used to group hosts in the cluster",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        user_filter = LiteralInput(
            identifier="user_filter",
            title="User Filter",
            abstract="Filter on username in case action 'info_cluster' is selected (reserved to administrators)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, action, nhost, host_partition, user_filter]
        outputs = [jobid, response, error]

        super(oph_cluster, self).__init__(
            self._handler,
            identifier="oph_cluster",
            title="Ophidia input",
            version=_version,
            abstract="Start, stop and get information about clusters of I/O servers",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_cluster '
        if request.inputs['id'][0].data is not None:
            query += 'id=' + str(request.inputs['id'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['action'][0].data is not None:
            query += 'action=' + str(request.inputs['action'][0].data) + ';'
        if request.inputs['nhost'][0].data is not None:
            query += 'nhost=' + str(request.inputs['nhost'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['host_partition'][0].data is not None:
            query += 'host_partition=' + str(request.inputs['host_partition'][0].data) + ';'
        if request.inputs['user_filter'][0].data is not None:
            query += 'user_filter=' + str(request.inputs['user_filter'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_concatnc(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        src_path = LiteralInput(
            identifier="src_path",
            title="Path of the NetCDF file",
            abstract="Path or OPeNDAP URL of the NetCDF file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        check_exp_dim = LiteralInput(
            identifier="check_exp_dim",
            title="Check explicit dimensions",
            abstract="If set to 'yes' (default) explicit dimensions of the two sources (NetCDF file and datacube) will be compared to assure they have the same values, if set to 'no' the check will not be performed",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        subset_type = LiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord. If set to 'index' (default), the subset_filter is considered on a dimension index; otherwise on dimension values",
            min_occurs=0,
            max_occurs=1,
            default="index",
            data_type='string')

        time_filter = LiteralInput(
            identifier="time_filter",
            title="Time filter",
            abstract="Enable filters using dates for time dimensions; enabled by default",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        offset = LiteralInput(
            identifier="offset",
            title="Offset",
            abstract="It is added to the bounds of subset intervals defined with 'subset_filter' in case of 'coord' filter type is used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        dim_offset = LiteralInput(
            identifier="dim_offset",
            title="Dimension Offset",
            abstract="Offset to be added to dimension values of imported data; default setting aims to held the difference between consecutive values",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        dim_continue = LiteralInput(
            identifier="dim_continue",
            title="Dimension Continue Flag",
            abstract="If enabled the last value of implicit dimension of input cube is used to evaluate the new values of the dimension",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, schedule, src_path, cdd, pid, check_exp_dim,
            subset_dims, subset_filter, subset_type, time_filter, offset, dim_offset, dim_continue, grid, description]
        outputs = [jobid, response, error]

        super(oph_concatnc, self).__init__(
            self._handler,
            identifier="oph_concatnc",
            title="Ophidia concatnc",
            version=_version,
            abstract="Creates a new datacube concatenating a NetCDF file to an existing datacube (both measure and dimensions)",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_concatnc '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['check_exp_dim'][0].data is not None:
            query += 'check_exp_dim=' + str(request.inputs['check_exp_dim'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['subset_type'][0].data is not None:
            query += 'subset_type=' + str(request.inputs['subset_type'][0].data) + ';'
        if request.inputs['time_filter'][0].data is not None:
            query += 'time_filter=' + str(request.inputs['time_filter'][0].data) + ';'
        if request.inputs['offset'][0].data is not None:
            query += 'offset=' + str(request.inputs['offset'][0].data) + ';'
        if request.inputs['dim_offset'][0].data is not None:
            query += 'dim_offset=' + str(request.inputs['dim_offset'][0].data) + ';'
        if request.inputs['dim_continue'][0].data is not None:
            query += 'dim_continue=' + str(request.inputs['dim_continue'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'src_path=' + str(request.inputs['src_path'][0].data) + ';'
        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_concatnc2(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        src_path = LiteralInput(
            identifier="src_path",
            title="Path of the NetCDF file",
            abstract="Path or OPeNDAP URL of the NetCDF file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        check_exp_dim = LiteralInput(
            identifier="check_exp_dim",
            title="Check explicit dimensions",
            abstract="If set to 'yes' (default) explicit dimensions of the two sources (NetCDF file and datacube) will be compared to assure they have the same values, if set to 'no' the check will not be performed",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        subset_type = LiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord. If set to 'index' (default), the subset_filter is considered on a dimension index; otherwise on dimension values",
            min_occurs=0,
            max_occurs=1,
            default="index",
            data_type='string')

        time_filter = LiteralInput(
            identifier="time_filter",
            title="Time filter",
            abstract="Enable filters using dates for time dimensions; enabled by default",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        offset = LiteralInput(
            identifier="offset",
            title="Offset",
            abstract="It is added to the bounds of subset intervals defined with 'subset_filter' in case of 'coord' filter type is used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        dim_offset = LiteralInput(
            identifier="dim_offset",
            title="Dimension Offset",
            abstract="Offset to be added to dimension values of imported data; default setting aims to held the difference between consecutive values",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        dim_continue = LiteralInput(
            identifier="dim_continue",
            title="Dimension Continue Flag",
            abstract="If enabled the last value of implicit dimension of input cube is used to evaluate the new values of the dimension",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, schedule, src_path, cdd, pid, check_exp_dim,
            subset_dims, subset_filter, subset_type, time_filter, offset, dim_offset, dim_continue, grid, description]
        outputs = [jobid, response, error]

        super(oph_concatnc2, self).__init__(
            self._handler,
            identifier="oph_concatnc2",
            title="Ophidia concatnc2",
            version=_version,
            abstract="Creates a new datacube concatenating a NetCDF file to an existing datacube (both measure and dimensions)",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_concatnc2 '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['check_exp_dim'][0].data is not None:
            query += 'check_exp_dim=' + str(request.inputs['check_exp_dim'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['subset_type'][0].data is not None:
            query += 'subset_type=' + str(request.inputs['subset_type'][0].data) + ';'
        if request.inputs['time_filter'][0].data is not None:
            query += 'time_filter=' + str(request.inputs['time_filter'][0].data) + ';'
        if request.inputs['offset'][0].data is not None:
            query += 'offset=' + str(request.inputs['offset'][0].data) + ';'
        if request.inputs['dim_offset'][0].data is not None:
            query += 'dim_offset=' + str(request.inputs['dim_offset'][0].data) + ';'
        if request.inputs['dim_continue'][0].data is not None:
            query += 'dim_continue=' + str(request.inputs['dim_continue'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'src_path=' + str(request.inputs['src_path'][0].data) + ';'
        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_containerschema(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="Name of the container to be created",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, cwd, container]
        outputs = [jobid, response, error]

        super(oph_containerschema, self).__init__(
            self._handler,
            identifier="oph_containerschema",
            title="Ophidia containerschema",
            version=_version,
            abstract="Show some information about a container: description, vocabulary, dimension list, etc.",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_containerschema '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'

        query += 'container=' + str(request.inputs['container'][0].data) + ';'
        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_createcontainer(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="Name of the container to be created",
            data_type='string')

        dim = LiteralInput(
            identifier="dim",
            title="Dimension name",
            abstract="Name of dimension allowed. Multiple-value field: list of dimensions separated by '|' can be provided",
            data_type='string')

        dim_type = LiteralInput(
            identifier="dim_type",
            title="Dim Type",
            abstract="Types of dimensions. Possible values are 'double', 'float', 'int', or 'long'. Multiple-value field: list of types separated by '|' can be provided. Default value is 'double'",
            min_occurs=0,
            max_occurs=1,
            default="double",
            data_type='string')

        compressed = LiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="If 'yes', new data will be compressed. With 'no' (default), data will be inserted without compression",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        hierarchy = LiteralInput(
            identifier="hierarchy",
            title="Hierarchy",
            abstract="Concept hierarchy name of the dimensions. Default value is 'oph_base'. Multi-value field: list of concept levels separed by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="oph_base",
            data_type='string')

        vocabulary = LiteralInput(
            identifier="vocabulary",
            title="Vocabulary",
            abstract="Optional argument used to indicate a vocabulary to be used to associate metadata to the container",
            min_occurs=0,
            max_occurs=1,
            default="CF",
            data_type='string')

        base_time = LiteralInput(
            identifier="base_time",
            title="Base time",
            abstract="In case of time hierarchy, it indicates the base time of the dimension. Default value is 1900-01-01",
            min_occurs=0,
            max_occurs=1,
            default="1900-01-01 00:00:00",
            data_type='string')

        units = LiteralInput(
            identifier="units",
            title="Units",
            abstract="In case of time hierarchy, it indicates the units of the dimension. Possible values are: s,m,h,3,6,d",
            min_occurs=0,
            max_occurs=1,
            default="d",
            data_type='string')

        calendar = LiteralInput(
            identifier="calendar",
            title="Calendar",
            abstract="In case of time hierarchy, it indicates the calendar type",
            min_occurs=0,
            max_occurs=1,
            default="standard",
            data_type='string')

        month_lenghts = LiteralInput(
            identifier="month_lenghts",
            title="Month lenghts",
            abstract="In case of time dimension and user-defined calendar, it indicates the sizes of each month in days. There byst be 12 positive integers separated by commas",
            min_occurs=0,
            max_occurs=1,
            default="31,28,31,30,31,30,31,31,30,31,30,31",
            data_type='string')

        leap_year = LiteralInput(
            identifier="leap_year",
            title="Leap year",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap year. By default it is set to 0",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        leap_month = LiteralInput(
            identifier="leap_month",
            title="Leap month",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap month. By default it is set to 2 (February)",
            min_occurs=0,
            max_occurs=1,
            default=2,
            data_type='integer')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output container",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, cwd, container, dim, dim_type, compressed,
            hierarchy, vocabulary, base_time, units, calendar, month_lenghts, leap_year, leap_month, description]
        outputs = [jobid, response, error]

        super(oph_createcontainer, self).__init__(
            self._handler,
            identifier="oph_createcontainer",
            title="Ophidia createcontainer",
            version=_version,
            abstract="Create an empty container",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_createcontainer '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['dim_type'][0].data is not None:
            query += 'dim_type=' + str(request.inputs['dim_type'][0].data) + ';'
        if request.inputs['compressed'][0].data is not None:
            query += 'compressed=' + str(request.inputs['compressed'][0].data) + ';'
        if request.inputs['hierarchy'][0].data is not None:
            query += 'hierarchy=' + str(request.inputs['hierarchy'][0].data) + ';'
        if request.inputs['vocabulary'][0].data is not None:
            query += 'vocabulary=' + str(request.inputs['vocabulary'][0].data) + ';'
        if request.inputs['base_time'][0].data is not None:
            query += 'base_time=' + str(request.inputs['base_time'][0].data) + ';'
        if request.inputs['units'][0].data is not None:
            query += 'units=' + str(request.inputs['units'][0].data) + ';'
        if request.inputs['calendar'][0].data is not None:
            query += 'calendar=' + str(request.inputs['calendar'][0].data) + ';'
        if request.inputs['month_lenghts'][0].data is not None:
            query += 'month_lenghts=' + str(request.inputs['month_lenghts'][0].data) + ';'
        if request.inputs['leap_year'][0].data is not None:
            query += 'leap_year=' + str(request.inputs['leap_year'][0].data) + ';'
        if request.inputs['leap_month'][0].data is not None:
            query += 'leap_month=' + str(request.inputs['leap_month'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'container=' + str(request.inputs['container'][0].data) + ';'
        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'
        query += 'dim=' + str(request.inputs['dim'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_cubeelements(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        algorithm = LiteralInput(
            identifier="algorithm",
            title="Algorithm",
            abstract="Algorithm used to count elements. Possible value are: 'dim_product' (default) to compute elements mathematically; 'count' to count elements in each fragment",
            min_occurs=0,
            max_occurs=1,
            default="dim_product",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, schedule, sessionid, pid, algorithm]
        outputs = [jobid, response, error]

        super(oph_cubeelements, self).__init__(
            self._handler,
            identifier="oph_cubeelements",
            title="Ophidia cubeelements",
            version=_version,
            abstract="Compute and display the number of elements stored in the input datacube",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_cubeelements '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['algorithm'][0].data is not None:
            query += 'algorithm=' + str(request.inputs['algorithm'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_cubeio(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        branch = LiteralInput(
            identifier="branch",
            title="Branch",
            abstract="It is possible to visualize all datacubes with 'all', only the parent branch with 'parent' and only the children branch with 'children'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, branch]
        outputs = [jobid, response, error]

        super(oph_cubeio, self).__init__(
            self._handler,
            identifier="oph_cubeio",
            title="Ophidia cubeio",
            version=_version,
            abstract="Show the hierarchy of all datacubes used to generate the input datacube and of those derived from it",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_cubeio '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['branch'][0].data is not None:
            query += 'branch=' + str(request.inputs['branch'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_cubeschema(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        action = LiteralInput(
            identifier="action",
            title="Action",
            abstract="Command type. Use: 'read' to access information (default); 'add' to add a new dimension (size will be 1); 'clear' to clear collapsed dimensions",
            min_occurs=0,
            max_occurs=1,
            default="read",
            data_type='string')

        level = LiteralInput(
            identifier="level",
            title="Level",
            abstract="Level of information shown. '0': shows only metadata (default); '1': shows only dimension values; '2': shows metadata and dimension values",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        dim = LiteralInput(
            identifier="dim",
            title="Dimension name",
            abstract="Name of dimension to show. Only valid with level bigger than 0; in case of action 'read', all dimension are shown by default and multiple values can be set (separated by |); in case of action 'add' only one dimension has to be set",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        show_index = LiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimensions ids. With 'yes', it will also show the dimension id next to the value",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        show_time = LiteralInput(
            identifier="show_time",
            title="Show time",
            abstract="If 'no' (default), the values of time dimension are shown as numbers. With 'yes', the values are converted as a string with date and time",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        base64 = LiteralInput(
            identifier="base64",
            title="Base64",
            abstract="If 'no' (default), dimension values are returned as strings. With 'yes', the values are returned as base64-coded strings",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        concept_level = LiteralInput(
            identifier="concept_level",
            title="Concept level",
            abstract="Concept level to be associated with new dimnesion",
            min_occurs=0,
            max_occurs=1,
            default="c",
            data_type='string')

        dim_level = LiteralInput(
            identifier="dim_level",
            title="Dimension level",
            abstract="Level of the new dimension to be added in dimension table",
            min_occurs=0,
            max_occurs=1,
            default="1",
            data_type='integer')

        dim_array = LiteralInput(
            identifier="dim_array",
            title="Dimension array",
            abstract="Use 'yes' to add an implicit dimension (default), use 'no' to add an explicit dimension",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, action, level, dim, show_index, show_time, base64, concept_level, dim_level, dim_array]
        outputs = [jobid, response, error]

        super(oph_cubeschema, self).__init__(
            self._handler,
            identifier="oph_cubeschema",
            title="Ophidia cubeschema",
            version=_version,
            abstract="Show metadata information about a datacube and the dimensions related to it",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_cubeschema '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['action'][0].data is not None:
            query += 'action=' + str(request.inputs['action'][0].data) + ';'
        if request.inputs['level'][0].data is not None:
            query += 'level=' + str(request.inputs['level'][0].data) + ';'
        if request.inputs['dim'][0].data is not None:
            query += 'dim=' + str(request.inputs['dim'][0].data) + ';'
        if request.inputs['show_index'][0].data is not None:
            query += 'show_index=' + str(request.inputs['show_index'][0].data) + ';'
        if request.inputs['show_time'][0].data is not None:
            query += 'show_time=' + str(request.inputs['show_time'][0].data) + ';'
        if request.inputs['base64'][0].data is not None:
            query += 'base64=' + str(request.inputs['base64'][0].data) + ';'
        if request.inputs['concept_level'][0].data is not None:
            query += 'concept_level=' + str(request.inputs['concept_level'][0].data) + ';'
        if request.inputs['dim_level'][0].data is not None:
            query += 'dim_level=' + str(request.inputs['dim_level'][0].data) + ';'
        if request.inputs['dim_array'][0].data is not None:
            query += 'dim_array=' + str(request.inputs['dim_array'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_cubesize(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        byte_unit = LiteralInput(
            identifier="byte_unit",
            title="Byte unit",
            abstract="Measure unit used to show datacube size. The unit can be KB, MB (default), GB, TB or PB",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        algorithm = LiteralInput(
            identifier="algorithm",
            title="Algorithm to evaluate cube size",
            abstract="Algorithm used to compute the size. Possible values are: 'euristic' (default) to estimate the size with an euristic method; 'count' to get the actual size of each fragment",
            min_occurs=0,
            max_occurs=1,
            default="euristic",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, schedule, pid, byte_unit, algorithm]
        outputs = [jobid, response, error]

        super(oph_cubesize, self).__init__(
            self._handler,
            identifier="oph_cubesize",
            title="Ophidia cubesize",
            version=_version,
            abstract="Compute and display the size of the input datacube",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_cubesize '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['byte_unit'][0].data is not None:
            query += 'byte_unit=' + str(request.inputs['byte_unit'][0].data) + ';'
        if request.inputs['algorithm'][0].data is not None:
            query += 'algorithm=' + str(request.inputs['algorithm'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_delete(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, schedule]
        outputs = [jobid, response, error]

        super(oph_delete, self).__init__(
            self._handler,
            identifier="oph_delete",
            title="Ophidia delete",
            version=_version,
            abstract="Remove a datacube",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_delete '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_deletecontainer(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used; used only when the force argument is set to 'yes'",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        force = LiteralInput(
            identifier="force",
            title="Force",
            abstract="Flag used to force the removal of a non-empy container, note that with 'yes' all datacubes inside the container will be deleted, whereas with 'no' (default) the container will be removed only if it is already empty",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Container",
            abstract="Name of the container to be removed",
            data_type='string')

        container_pid = LiteralInput(
            identifier="container_pid",
            title="Container PID",
            abstract="PID of the input container. If it is set, arguments 'container' and 'cwd' are negleted",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, force, cwd, container, container_pid]
        outputs = [jobid, response, error]

        super(oph_deletecontainer, self).__init__(
            self._handler,
            identifier="oph_deletecontainer",
            title="Ophidia deletecontainer",
            version=_version,
            abstract="Remove a container with related dimensions and grids. The container can be deleted logically or physically",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_deletecontainer '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['force'][0].data is not None:
            query += 'force=' + str(request.inputs['force'][0].data) + ';'
        if request.inputs['container_pid'][0].data is not None:
            query += 'container_pid=' + str(request.inputs['container_pid'][0].data) + ';'

        query += 'container=' + str(request.inputs['container'][0].data) + ';'
        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_drilldown(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        ndim = LiteralInput(
            identifier="ndim",
            title="Number of Implicit Dimensions",
            abstract="Number of implicit dimensions that will be transformed in explicit dimensions",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, schedule, container, description, ndim]
        outputs = [jobid, response, error]

        super(oph_drilldown, self).__init__(
            self._handler,
            identifier="oph_drilldown",
            title="Ophidia drilldown",
            version=_version,
            abstract="Perform a drill-down on a datacube, i.e. it transforms dimensions from implicit to explicit",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_drilldown '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['ndim'][0].data is not None:
            query += 'ndim=' + str(request.inputs['ndim'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_duplicate(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, schedule, container, description]
        outputs = [jobid, response, error]

        super(oph_duplicate, self).__init__(
            self._handler,
            identifier="oph_duplicate",
            title="Ophidia duplicate",
            version=_version,
            abstract="Duplicate a datacube creating an exact copy of the input one",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_duplicate '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_explorecube(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        limit_filter = LiteralInput(
            identifier="limit_filter",
            title="Limit filter",
            abstract="Optional filter on the maxumum number of rows",
            min_occurs=0,
            max_occurs=1,
            default=100,
            data_type='integer')

        time_filter = LiteralInput(
            identifier="time_filter",
            title="Time filter",
            abstract="Enable filters using dates for time dimensions; enabled by default",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        show_index = LiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimensions ids. With 'yes', it will also show the dimension id next to the value",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        show_id = LiteralInput(
            identifier="show_id",
            title="Show id",
            abstract="If 'no' (default), it won't show fragment row ID. With 'yes', it will also show the fragment row ID",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        show_time = LiteralInput(
            identifier="show_time",
            title="Show time",
            abstract="If 'no' (default), the values of time dimension are shown as numbers. With 'yes', the values are converted as a string with date and time",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        level = LiteralInput(
            identifier="level",
            title="Level",
            abstract="With '1' (default), only measure values are shown, if it is set to '2', the dimension values are also returned",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        output_path = LiteralInput(
            identifier="output_path",
            title="Output path",
            abstract="Absolute path of the JSON Response. By default, JSON Response is saved in core environment",
            min_occurs=0,
            max_occurs=1,
            default="default",
            data_type='string')

        output_name = LiteralInput(
            identifier="output_name",
            title="Output name",
            abstract="Filename of the JSON Response. The default value is the PID of the input dataube. File is saved provided that 'output_path' is set",
            min_occurs=0,
            max_occurs=1,
            default="default",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        base64 = LiteralInput(
            identifier="base64",
            title="Base64",
            abstract="If 'no' (default), dimension values are returned as strings",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_type = LiteralInput(
            identifier="subset_type",
            title="Subset type",
            abstract="If set to 'index' (defaylt), the 'subset_filter' is considered on dimension index: with 'coord', filter is considered on dimension values",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, limit_filter, time_filter, show_index, show_id,
            show_time, level, output_path, output_name, cdd, base64, subset_dims, subset_type, subset_filter, schedule]
        outputs = [jobid, response, error]

        super(oph_explorecube, self).__init__(
            self._handler,
            identifier="oph_explorecube",
            title="Ophidia explorecube",
            version=_version,
            abstract="Print a data stored into a datacube, and offer to subset the data along its dimensions; dimensions values are used as input filters for subsetting",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_explorecube '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['time_filter'][0].data is not None:
            query += 'time_filter=' + str(request.inputs['time_filter'][0].data) + ';'
        if request.inputs['limit_filter'][0].data is not None:
            query += 'limit_filter=' + str(request.inputs['limit_filter'][0].data) + ';'
        if request.inputs['show_index'][0].data is not None:
            query += 'show_index=' + str(request.inputs['show_index'][0].data) + ';'
        if request.inputs['show_id'][0].data is not None:
            query += 'show_id=' + str(request.inputs['show_id'][0].data) + ';'
        if request.inputs['show_time'][0].data is not None:
            query += 'show_time=' + str(request.inputs['show_time'][0].data) + ';'
        if request.inputs['level'][0].data is not None:
            query += 'level=' + str(request.inputs['level'][0].data) + ';'
        if request.inputs['output_path'][0].data is not None:
            query += 'output_path=' + str(request.inputs['output_path'][0].data) + ';'
        if request.inputs['output_name'][0].data is not None:
            query += 'output_name=' + str(request.inputs['output_name'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['base64'][0].data is not None:
            query += 'base64=' + str(request.inputs['base64'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_type'][0].data is not None:
            query += 'subset_type=' + str(request.inputs['subset_type'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_explorenc(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        measure = LiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure related to the NetCDF. The argument is mandatory in case level different from '0'",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        level = LiteralInput(
            identifier="level",
            title="Level",
            abstract="'0' to show the list of dimensions; '1' to show the values of a specific measure; '2' to show the values of a specific measure and the values of the corresponding dimensions",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        src_path = LiteralInput(
            identifier="src_path",
            title="Path of the FITS file",
            abstract="Path of the FITS file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        exp_dim = LiteralInput(
            identifier="exp_dim",
            title="Explicit dimensions",
            abstract="Names of explicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        imp_dim = LiteralInput(
            identifier="imp_dim",
            title="Implicit dimensions",
            abstract="Names of implicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_type = LiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord. If set to 'index' (default), the subset_filter is considered on a dimension index; otherwise on dimension values",
            min_occurs=0,
            max_occurs=1,
            default="index",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        limit_filter = LiteralInput(
            identifier="limit_filter",
            title="Limit filter",
            abstract="Optional filter on the maxumum number of rows",
            min_occurs=0,
            max_occurs=1,
            default=100,
            data_type='integer')

        show_index = LiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimensions ids. With 'yes', it will also show the dimension id next to the value",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        show_id = LiteralInput(
            identifier="show_id",
            title="Show id",
            abstract="If 'no' (default), it won't show fragment row ID. With 'yes', it will also show the fragment row ID",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        show_time = LiteralInput(
            identifier="show_time",
            title="Show time",
            abstract="If 'no' (default), the values of time dimension are shown as numbers. With 'yes', the values are converted as a string with date and time",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        show_stats = LiteralInput(
            identifier="show_stats",
            title="Show stats",
            abstract="If one of the following mask is set, a list of statistics is returned for each time series; output data type is always 'oph_double'",
            min_occurs=0,
            max_occurs=1,
            default="00000000000000",
            data_type='string')

        show_fit = LiteralInput(
            identifier="show_fit",
            title="Show fit",
            abstract="If 'yes', linear regression of each time serie is returned. It can be adopted only in case only one implicit dimension exists. With 'no' (default), linear regression is not evaluated",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        imp_num_points = LiteralInput(
            identifier="imp_num_points",
            title="Imp number of points",
            abstract="Indicates the number of points which measure values must be distribuited along by interpolation. If 'imp_num_points' is higher than the number of actual points, then interpolation is evaluated; otherwhise, 'operation' is applied. It can be adopted only in case one implicit dimension exists. With '0', no interpolation/reduction is applied (default)",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        offset = LiteralInput(
            identifier="offset",
            title="Offset",
            abstract="Relative offset to be used to set reduction interval bounds (percentage). By default is set to '50'",
            min_occurs=0,
            max_occurs=1,
            default=50,
            data_type='float')

        operation = LiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the operation. Possible values are count, max, min, avg, sum",
            min_occurs=0,
            max_occurs=1,
            default="avg",
            data_type='string')

        wavelet = LiteralInput(
            identifier="wavelet",
            title="Wavelet",
            abstract="Used to apply the wavelet filter provided 'wavelet_points' is set. Possibile values are: 'yes' (orginal data and filterd data are returned); 'only' (only filtered data are returned), 'no' (only original data are returnered, default value)",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        wavelet_ratio = LiteralInput(
            identifier="wavelet_ratio",
            title="Wavelet ratio",
            abstract="Is the fraction of wavelet transform coefficients that are cleared by the filter (percentage). It can be adopted only in case one implicit dimension existes. With '0', no compression is applied (default)",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        wavelet_coeff = LiteralInput(
            identifier="wavelet_coeff",
            title="Wavelet coefficient",
            abstract="If 'yes', wavelet coefficients are also shown; output data type is always 'oph_double'; if necessary, their number is expanded to the first power of 2. It can be adopted only in case one implicit dimension exists",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, measure, level, src_path, cdd, exp_dim, imp_dim, subset_dims, subset_type, subset_filter,
            limit_filter, show_index, show_id, show_time, show_stats, show_fit, imp_num_points, offset, operation, wavelet, wavelet_ratio, wavelet_coeff, schedule]
        outputs = [jobid, response, error]

        super(oph_explorenc, self).__init__(
            self._handler,
            identifier="oph_explorenc",
            title="Ophidia explorenc",
            version=_version,
            abstract="Read a NetCDF file (both measure and dimensions)",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_explorenc '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['level'][0].data is not None:
            query += 'level=' + str(request.inputs['level'][0].data) + ';'
        if request.inputs['measure'][0].data is not None:
            query += 'measure=' + str(request.inputs['measure'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['exp_dim'][0].data is not None:
            query += 'exp_dim=' + str(request.inputs['exp_dim'][0].data) + ';'
        if request.inputs['imp_dim'][0].data is not None:
            query += 'imp_dim=' + str(request.inputs['imp_dim'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_type'][0].data is not None:
            query += 'subset_type=' + str(request.inputs['subset_type'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['limit_filter'][0].data is not None:
            query += 'limit_filter=' + str(request.inputs['limit_filter'][0].data) + ';'
        if request.inputs['show_index'][0].data is not None:
            query += 'show_index=' + str(request.inputs['show_index'][0].data) + ';'
        if request.inputs['show_id'][0].data is not None:
            query += 'show_id=' + str(request.inputs['show_id'][0].data) + ';'
        if request.inputs['show_time'][0].data is not None:
            query += 'show_time=' + str(request.inputs['show_time'][0].data) + ';'
        if request.inputs['show_stats'][0].data is not None:
            query += 'show_stats=' + str(request.inputs['show_stats'][0].data) + ';'
        if request.inputs['show_fit'][0].data is not None:
            query += 'show_fit=' + str(request.inputs['show_fit'][0].data) + ';'
        if request.inputs['imp_num_points'][0].data is not None:
            query += 'imp_num_points=' + str(request.inputs['imp_num_points'][0].data) + ';'
        if request.inputs['offset'][0].data is not None:
            query += 'offset=' + str(request.inputs['offset'][0].data) + ';'
        if request.inputs['operation'][0].data is not None:
            query += 'operation=' + str(request.inputs['operation'][0].data) + ';'
        if request.inputs['wavelet'][0].data is not None:
            query += 'wavelet=' + str(request.inputs['wavelet'][0].data) + ';'
        if request.inputs['wavelet_ratio'][0].data is not None:
            query += 'wavelet_ratio=' + str(request.inputs['wavelet_ratio'][0].data) + ';'
        if request.inputs['wavelet_coeff'][0].data is not None:
            query += 'wavelet_coeff=' + str(request.inputs['wavelet_coeff'][0].data) + ';'

        query += 'src_path=' + str(request.inputs['src_path'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_exportnc(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        misc = LiteralInput(
            identifier="misc",
            title="Misc",
            abstract="If 'yes', data are saved in session folder called 'export/misc'; if 'no', data are saved within 'export/nc' in a subfolder associated with the PID of the cube (default)",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        output_path = LiteralInput(
            identifier="output_path",
            title="Output path",
            abstract="Absolute path of the NetCDF output files. By default, all the files will be saved in session folder 'export/nc/containerid/datacubeid; in case it is set to 'local' the file will be saved in current directory on data repository (see 'cdd')",
            min_occurs=0,
            max_occurs=1,
            default="default",
            data_type='string')

        output_name = LiteralInput(
            identifier="output_name",
            title="Output name",
            abstract="Filename of the NetCDF output files. In case of multiple fragments, filenames will be 'output_name0.nc', 'output_name1.nc', etc. The default value is the measure name of the input datacube",
            default="default",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        force = LiteralInput(
            identifier="force",
            title="Force",
            abstract="Flag used to force file creation. An existant file is overwritten with 'yes', whereas the file is reated only if it does not exist with 'no' (default)",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        export_metadata = LiteralInput(
            identifier="export_metadata",
            title="Export metadata",
            abstract="With 'yes' (default), it is possible to export also metadata; with 'no', it will export only data",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, misc, output_path, output_name, cdd, force, export_metadata, schedule]
        outputs = [jobid, response, error]

        super(oph_exportnc, self).__init__(
            self._handler,
            identifier="oph_exportnc",
            title="Ophidia exportnc",
            version=_version,
            abstract="Export data of a datacube into multiple NetCDF files",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_exportnc '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['misc'][0].data is not None:
            query += 'misc=' + str(request.inputs['misc'][0].data) + ';'
        if request.inputs['output_path'][0].data is not None:
            query += 'output_path=' + str(request.inputs['output_path'][0].data) + ';'
        if request.inputs['output_name'][0].data is not None:
            query += 'output_name=' + str(request.inputs['output_name'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['force'][0].data is not None:
            query += 'force=' + str(request.inputs['force'][0].data) + ';'
        if request.inputs['export_metadata'][0].data is not None:
            query += 'export_metadata=' + str(request.inputs['export_metadata'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_exportnc2(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        misc = LiteralInput(
            identifier="misc",
            title="Misc",
            abstract="If 'yes', data are saved in session folder called 'export/misc'; if 'no', data are saved within 'export/nc' in a subfolder associated with the PID of the cube (default)",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        output_path = LiteralInput(
            identifier="output_path",
            title="Output path",
            abstract="Absolute path of the NetCDF output files. By default, all the files will be saved in session folder 'export/nc/containerid/datacubeid; in case it is set to 'local' the file will be saved in current directory on data repository (see 'cdd')",
            min_occurs=0,
            max_occurs=1,
            default="default",
            data_type='string')

        output_name = LiteralInput(
            identifier="output_name",
            title="Output name",
            abstract="Filename of the NetCDF output files. In case of multiple fragments, filenames will be 'output_name0.nc', 'output_name1.nc', etc. The default value is the measure name of the input datacube",
            min_occurs=0,
            max_occurs=1,
            default="default",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        force = LiteralInput(
            identifier="force",
            title="Force",
            abstract="Flag used to force file creation. An existant file is overwritten with 'yes', whereas the file is reated only if it does not exist with 'no' (default)",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        export_metadata = LiteralInput(
            identifier="export_metadata",
            title="Export metadata",
            abstract="With 'yes' (default), it is possible to export also metadata; with 'no', it will export only data; with 'postpone' metadata are also saved, but only after all the data are written",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, misc, output_path, output_name, cdd, force, export_metadata, schedule]
        outputs = [jobid, response, error]

        super(oph_exportnc2, self).__init__(
            self._handler,
            identifier="oph_exportnc2",
            title="Ophidia exportnc2",
            version=_version,
            abstract="Export data of a datacube into a single NetCDF file",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_exportnc2 '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['misc'][0].data is not None:
            query += 'misc=' + str(request.inputs['misc'][0].data) + ';'
        if request.inputs['output_path'][0].data is not None:
            query += 'output_path=' + str(request.inputs['output_path'][0].data) + ';'
        if request.inputs['output_name'][0].data is not None:
            query += 'output_name=' + str(request.inputs['output_name'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['force'][0].data is not None:
            query += 'force=' + str(request.inputs['force'][0].data) + ';'
        if request.inputs['export_metadata'][0].data is not None:
            query += 'export_metadata=' + str(request.inputs['export_metadata'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_folder(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        command = LiteralInput(
            identifier="command",
            title="Command",
            abstract="Command to be executed among these: 'cd' (change directory); 'mkdir' (create a new directory); 'rm' (delete an empty directory); 'mv' move/rename a folder",
            data_type='string')

        path = LiteralInput(
            identifier="path",
            title="Path",
            abstract="0, 1 or 2 absolute/relative paths needed by commands. In case of mv, 2 paths are mandatory parameters and must end with a name of a folder. In case of cd, without a path the new directory will be the session folder. In all other cases, it can be used only 1 path",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, command, path, cwd]
        outputs = [jobid, response, error]

        super(oph_folder, self).__init__(
            self._handler,
            identifier="oph_folder",
            title="Ophidia folder",
            version=_version,
            abstract="Manage folder of the Ophidia filesystem",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_folder '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['path'][0].data is not None:
            query += 'path=' + str(request.inputs['path'][0].data) + ';'

        query += 'command=' + str(request.inputs['command'][0].data) + ';'
        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_fs(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        command = LiteralInput(
            identifier="command",
            title="Command",
            abstract="Command to be executed among: 'ls' (default value, list the files in a directory); 'cd' (change directory)",
            min_occurs=0,
            max_occurs=1,
            default="ls",
            data_type='string')

        dpath = LiteralInput(
            identifier="dpath",
            title="Dpath",
            abstract="0 or 1 path needed by commands. In case of 'cd', without a path the new directoru will be root folder BASE_SRC_PATH. In all other cases, it can be used only 1 path",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        file = LiteralInput(
            identifier="file",
            title="File",
            abstract="The filter based on glob library",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory",
            abstract="Absolute path corresponding to the current directory on data repository. It is appended to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        recursive = LiteralInput(
            identifier="recursive",
            title="Recursive",
            abstract="Specifies if the search is done recursively or not; the argument is considered only for the first three levels and may have values of 'no' or 'yes'",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        depth = LiteralInput(
            identifier="depth",
            title="Depth",
            abstract="Set to maximum folder depth has to be explored in case of recursion; level '1' corresponds to 'no recursion'; by default no limit is applied",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        realpath = LiteralInput(
            identifier="realpath",
            title="Real paths",
            abstract="Set to 'yes' to list real paths to files; by default only the names of files and directories are shown",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, command, dpath, file, cdd, recursive, depth, realpath]
        outputs = [jobid, response, error]

        super(oph_fs, self).__init__(
            self._handler,
            identifier="oph_fs",
            title="Ophidia fs",
            version=_version,
            abstract="Manage folders of the real Ophidia filesystem",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_fs '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['command'][0].data is not None:
            query += 'command=' + str(request.inputs['command'][0].data) + ';'
        if request.inputs['dpath'][0].data is not None:
            query += 'dpath=' + str(request.inputs['dpath'][0].data) + ';'
        if request.inputs['file'][0].data is not None:
            query += 'file=' + str(request.inputs['file'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['recursive'][0].data is not None:
            query += 'recursive=' + str(request.inputs['recursive'][0].data) + ';'
        if request.inputs['depth'][0].data is not None:
            query += 'depth=' + str(request.inputs['depth'][0].data) + ';'
        if request.inputs['realpath'][0].data is not None:
            query += 'realpath=' + str(request.inputs['realpath'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_get_config(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        key = LiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the metadata to be requested",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, key]
        outputs = [jobid, response, error]

        super(oph_get_config, self).__init__(
            self._handler,
            identifier="oph_get_config",
            title="Ophidia get_config",
            version=_version,
            abstract="Request the configuration parameters",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_get_config '
        if request.inputs['key'][0].data is not None:
            query += 'key=' + str(request.inputs['key'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_hierarchy(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        hierarchy = LiteralInput(
            identifier="hierarchy",
            title="Hierarchy",
            abstract="Name of the requested hierarchy. If the value 'all' is specified, then the list of all hierarchies is shown",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        hierarchy_version = LiteralInput(
            identifier="hierarchy_version",
            title="Hierarchy version",
            abstract="Version of the requested hierarchy. If not specified, it will be used its default value 'latest' in order to get info about the latest version of the hierarchy",
            min_occurs=0,
            max_occurs=1,
            default="latest",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, hierarchy, hierarchy_version]
        outputs = [jobid, response, error]

        super(oph_hierarchy, self).__init__(
            self._handler,
            identifier="oph_hierarchy",
            title="Ophidia hierarchy",
            version=_version,
            abstract="Show the list of the hierarchies or the description of a specified hierarchy",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_hierarchy '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['hierarchy'][0].data is not None:
            query += 'hierarchy=' + str(request.inputs['hierarchy'][0].data) + ';'
        if request.inputs['hierarchy_version'][0].data is not None:
            query += 'hierarchy_version=' + str(request.inputs['hierarchy_version'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_importfits(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        host_partition = LiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="name of I/O host partition used to store data. By default the first available host partition will be used",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        ioserver = LiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data. Possible values are: 'mysql_table' (default) or 'ophidiaio_memory'",
            min_occurs=0,
            max_occurs=1,
            default="mysql_table",
            data_type='string')

        import_metadata = LiteralInput(
            identifier="import_metadata",
            title="Import metatadata",
            abstract="With 'yes' (default), it will import also metadata; with 'no', it will import only data",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        nhost = LiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        nfrag = LiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database. With default value '0', the number of fragments will be ratio of the product of sizes of the n-1 most outer explicit dimensions to the product of the other arguments",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        measure = LiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the new measure related to the FITS file. If not provided 'image' will be used (default)",
            min_occurs=0,
            max_occurs=1,
            default="image",
            data_type='string')

        run = LiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the import and computes the fragmentation parameters that would be used else. If set to 'yes', the actual import operation is executed",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        src_path = LiteralInput(
            identifier="src_path",
            title="Path of the FITS file",
            abstract="Path of the FITS file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        hdu = LiteralInput(
            identifier="hdu",
            title="Hdu",
            abstract="Import data from the select HDU. If not specified, Primary HDU '1' (default) will be considered",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exp_dim = LiteralInput(
            identifier="exp_dim",
            title="Explicit dimensions",
            abstract="Names of explicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        imp_dim = LiteralInput(
            identifier="imp_dim",
            title="Implicit dimensions",
            abstract="Names of implicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            default="none",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        compressed = LiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, cwd, container, host_partition, ioserver, import_metadata, nhost,
            nfrag, measure, run, schedule, src_path, cdd, hdu, exp_dim, imp_dim, subset_dims, subset_filter, compressed, description]
        outputs = [jobid, response, error]

        super(oph_importfits, self).__init__(
            self._handler,
            identifier="oph_importfits",
            title="Ophidia importfits",
            version=_version,
            abstract="Imports a FITS file into a datacube (both data and axis); support is provided only for FITS images",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_importfits '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['host_partition'][0].data is not None:
            query += 'host_partition=' + str(request.inputs['host_partition'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['ioserver'][0].data is not None:
            query += 'ioserver=' + str(request.inputs['ioserver'][0].data) + ';'
        if request.inputs['import_metadata'][0].data is not None:
            query += 'import_metadata=' + str(request.inputs['import_metadata'][0].data) + ';'
        if request.inputs['nhost'][0].data is not None:
            query += 'nhost=' + str(request.inputs['nhost'][0].data) + ';'
        if request.inputs['nfrag'][0].data is not None:
            query += 'nfrag=' + str(request.inputs['nfrag'][0].data) + ';'
        if request.inputs['run'][0].data is not None:
            query += 'run=' + str(request.inputs['run'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['hdu'][0].data is not None:
            query += 'hdu=' + str(request.inputs['hdu'][0].data) + ';'
        if request.inputs['exp_dim'][0].data is not None:
            query += 'exp_dim=' + str(request.inputs['exp_dim'][0].data) + ';'
        if request.inputs['imp_dim'][0].data is not None:
            query += 'imp_dim=' + str(request.inputs['imp_dim'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['compressed'][0].data is not None:
            query += 'compressed=' + str(request.inputs['compressed'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['measure'][0].data is not None:
            query += 'measure=' + str(request.inputs['measure'][0].data) + ';'

        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'
        query += 'src_path=' + str(request.inputs['src_path'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_importnc(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        host_partition = LiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="Name of I/O host partition used to store data. By default the first available host partition will be used",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        ioserver = LiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data. Possible values are: 'mysql_table' (default) or 'ophidiaio_memory'",
            min_occurs=0,
            max_occurs=1,
            default="mysql_table",
            data_type='string')

        import_metadata = LiteralInput(
            identifier="import_metadata",
            title="Import metatadata",
            abstract="With 'yes' (default), it will import also metadata; with 'no', it will import only data",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        check_compliance = LiteralInput(
            identifier="check_compliance",
            title="Check compliance",
            abstract="Checks if all the metadata registered for reference vocabulary are available. No check is done by default",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        nhost = LiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        nfrag = LiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database. With default value '0', the number of fragments will be ratio of the product of sizes of the n-1 most outer explicit dimensions to the product of the other arguments",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        measure = LiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure related to the NetCDF file",
            data_type='string')

        run = LiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the import and computes the fragmentation parameters that would be used else. If set to 'yes', the actual import operation is executed",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        src_path = LiteralInput(
            identifier="src_path",
            title="Path of the NetCDF file",
            abstract="Path or OPeNDAP URL of the NetCDF file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        exp_dim = LiteralInput(
            identifier="exp_dim",
            title="Explicit dimensions",
            abstract="Names of explicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        imp_dim = LiteralInput(
            identifier="imp_dim",
            title="Implicit dimensions",
            abstract="Names of implicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        subset_type = LiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord. If set to 'index' (default), the subset_filter is considered on a dimension index; otherwise on dimension values",
            min_occurs=0,
            max_occurs=1,
            default="index",
            data_type='string')

        time_filter = LiteralInput(
            identifier="time_filter",
            title="Time filter",
            abstract="Enable filters using dates for time dimensions; enabled by default",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        offset = LiteralInput(
            identifier="offset",
            title="Offset",
            abstract="It is added to the bounds of subset intervals defined with 'subset_filter' in case of 'coord' filter type is used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        exp_concept_level = LiteralInput(
            identifier="exp_concept_level",
            title="Explicit concept level",
            abstract="Concept level short name (must be a single char) of explicit dimensions. Default value is 'c'. Multi-value field: list of concept levels separed by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="c",
            data_type='string')

        imp_concept_level = LiteralInput(
            identifier="imp_concept_level",
            title="Implicit concept level",
            abstract="Concept level short name (must be a single char) of implicit dimensions. Default value is 'c'. Multi-value field: list of concept levels separed by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="c",
            data_type='string')

        compressed = LiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            default="no",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            default="-",
            data_type='string')

        hierarchy = LiteralInput(
            identifier="hierarchy",
            title="Hierarchy",
            abstract="Concept hierarchy name of the dimensions. Default value is 'oph_base'. Multi-value field: list of concept levels separed by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="oph_base",
            data_type='string')

        vocabulary = LiteralInput(
            identifier="vocabulary",
            title="Vocabulary",
            abstract="Optional argument used to indicate a vocabulary to be used to associate metadata to the container",
            min_occurs=0,
            max_occurs=1,
            default="CF",
            data_type='string')

        base_time = LiteralInput(
            identifier="base_time",
            title="Base time",
            abstract="In case of time hierarchy, it indicates the base time of the dimension. Default value is 1900-01-01",
            min_occurs=0,
            max_occurs=1,
            default="1900-01-01 00:00:00",
            data_type='string')

        units = LiteralInput(
            identifier="units",
            title="Units",
            abstract="In case of time hierarchy, it indicates the units of the dimension. Possible values are: s,m,h,3,6,d",
            min_occurs=0,
            max_occurs=1,
            default="d",
            data_type='string')

        calendar = LiteralInput(
            identifier="calendar",
            title="Calendar",
            abstract="In case of time hierarchy, it indicates the calendar type",
            min_occurs=0,
            max_occurs=1,
            default="standard",
            data_type='string')

        month_lenghts = LiteralInput(
            identifier="month_lenghts",
            title="Month lenghts",
            abstract="In case of time dimension and user-defined calendar, it indicates the sizes of each month in days. There byst be 12 positive integers separated by commas",
            min_occurs=0,
            max_occurs=1,
            default="31,28,31,30,31,30,31,31,30,31,30,31",
            data_type='string')

        leap_year = LiteralInput(
            identifier="leap_year",
            title="Leap year",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap year. By default it is set to 0",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        leap_month = LiteralInput(
            identifier="leap_month",
            title="Leap month",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap month. By default it is set to 2 (February)",
            min_occurs=0,
            max_occurs=1,
            default=2,
            data_type='integer')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, cwd, container, host_partition, ioserver, import_metadata, check_compliance, nhost, nfrag, measure, run, schedule, src_path, cdd, exp_dim, imp_dim, subset_dims,
            subset_filter, subset_type, time_filter, offset, exp_concept_level, imp_concept_level, compressed, grid, hierarchy, vocabulary, base_time, units, calendar, month_lenghts, leap_year, leap_month, description]
        outputs = [jobid, response, error]

        super(oph_importnc, self).__init__(
            self._handler,
            identifier="oph_importnc",
            title="Ophidia importnc",
            version=_version,
            abstract="Import a NetCDF file into a datacube (both measure and dimensions)",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_importnc '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['host_partition'][0].data is not None:
            query += 'host_partition=' + str(request.inputs['host_partition'][0].data) + ';'
        if request.inputs['check_compliance'][0].data is not None:
            query += 'check_compliance=' + str(request.inputs['check_compliance'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['ioserver'][0].data is not None:
            query += 'ioserver=' + str(request.inputs['ioserver'][0].data) + ';'
        if request.inputs['import_metadata'][0].data is not None:
            query += 'import_metadata=' + str(request.inputs['import_metadata'][0].data) + ';'
        if request.inputs['nhost'][0].data is not None:
            query += 'nhost=' + str(request.inputs['nhost'][0].data) + ';'
        if request.inputs['nfrag'][0].data is not None:
            query += 'nfrag=' + str(request.inputs['nfrag'][0].data) + ';'
        if request.inputs['run'][0].data is not None:
            query += 'run=' + str(request.inputs['run'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['exp_dim'][0].data is not None:
            query += 'exp_dim=' + str(request.inputs['exp_dim'][0].data) + ';'
        if request.inputs['imp_dim'][0].data is not None:
            query += 'imp_dim=' + str(request.inputs['imp_dim'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['subset_type'][0].data is not None:
            query += 'subset_type=' + str(request.inputs['subset_type'][0].data) + ';'
        if request.inputs['time_filter'][0].data is not None:
            query += 'time_filter=' + str(request.inputs['time_filter'][0].data) + ';'
        if request.inputs['offset'][0].data is not None:
            query += 'offset=' + str(request.inputs['offset'][0].data) + ';'
        if request.inputs['exp_concept_level'][0].data is not None:
            query += 'exp_concept_level=' + str(request.inputs['exp_concept_level'][0].data) + ';'
        if request.inputs['imp_concept_level'][0].data is not None:
            query += 'imp_concept_level=' + str(request.inputs['imp_concept_level'][0].data) + ';'
        if request.inputs['compressed'][0].data is not None:
            query += 'compressed=' + str(request.inputs['compressed'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['hierarchy'][0].data is not None:
            query += 'hierarchy=' + str(request.inputs['hierarchy'][0].data) + ';'
        if request.inputs['vocabulary'][0].data is not None:
            query += 'vocabulary=' + str(request.inputs['vocabulary'][0].data) + ';'
        if request.inputs['base_time'][0].data is not None:
            query += 'base_time=' + str(request.inputs['base_time'][0].data) + ';'
        if request.inputs['units'][0].data is not None:
            query += 'units=' + str(request.inputs['units'][0].data) + ';'
        if request.inputs['calendar'][0].data is not None:
            query += 'calendar=' + str(request.inputs['calendar'][0].data) + ';'
        if request.inputs['month_lenghts'][0].data is not None:
            query += 'month_lenghts=' + str(request.inputs['month_lenghts'][0].data) + ';'
        if request.inputs['leap_year'][0].data is not None:
            query += 'leap_year=' + str(request.inputs['leap_year'][0].data) + ';'
        if request.inputs['leap_month'][0].data is not None:
            query += 'leap_month=' + str(request.inputs['leap_month'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'
        query += 'measure=' + str(request.inputs['measure'][0].data) + ';'
        query += 'src_path=' + str(request.inputs['src_path'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_importnc2(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        host_partition = LiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="Name of I/O host partition used to store data. By default the first available host partition will be used",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        ioserver = LiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data; only possible values is 'ophidiaio_memory'",
            min_occurs=0,
            max_occurs=1,
            default="mysql_table",
            data_type='string')

        import_metadata = LiteralInput(
            identifier="import_metadata",
            title="Import metatadata",
            abstract="With 'yes' (default), it will import also metadata; with 'no', it will import only data",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        check_compliance = LiteralInput(
            identifier="check_compliance",
            title="Check compliance",
            abstract="Checks if all the metadata registered for reference vocabulary are available. No check is done by default",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        nhost = LiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        nfrag = LiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database. With default value '0', the number of fragments will be ratio of the product of sizes of the n-1 most outer explicit dimensions to the product of the other arguments",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        measure = LiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure related to the NetCDF file",
            data_type='string')

        run = LiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the import and computes the fragmentation parameters that would be used else. If set to 'yes', the actual import operation is executed",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        src_path = LiteralInput(
            identifier="src_path",
            title="Path of the NetCDF file",
            abstract="Path or OPeNDAP URL of the NetCDF file. Local files have to be stored in folder BASE_SRC_PATH or its sub-folders",
            data_type='string')

        cdd = LiteralInput(
            identifier="cdd",
            title="Absolute path of the current directory on data repository",
            abstract="Absolute path corresponding to the current directory on data repository. It is appened to BASE_SRC_PATH to build the effective path to files",
            min_occurs=0,
            max_occurs=1,
            default="/",
            data_type='string')

        exp_dim = LiteralInput(
            identifier="exp_dim",
            title="Explicit dimensions",
            abstract="Names of explicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        imp_dim = LiteralInput(
            identifier="imp_dim",
            title="Implicit dimensions",
            abstract="Names of implicit dimensions (axis). Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting. Multi value field: list of dimensions separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        subset_type = LiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord. If set to 'index' (default), the subset_filter is considered on a dimension index; otherwise on dimension values",
            min_occurs=0,
            max_occurs=1,
            default="index",
            data_type='string')

        time_filter = LiteralInput(
            identifier="time_filter",
            title="Time filter",
            abstract="Enable filters using dates for time dimensions; enabled by default",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        offset = LiteralInput(
            identifier="offset",
            title="Offset",
            abstract="It is added to the bounds of subset intervals defined with 'subset_filter' in case of 'coord' filter type is used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        exp_concept_level = LiteralInput(
            identifier="exp_concept_level",
            title="Explicit concept level",
            abstract="Concept level short name (must be a single char) of explicit dimensions. Default value is 'c'. Multi-value field: list of concept levels separed by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="c",
            data_type='string')

        imp_concept_level = LiteralInput(
            identifier="imp_concept_level",
            title="Implicit concept level",
            abstract="Concept level short name (must be a single char) of implicit dimensions. Default value is 'c'. Multi-value field: list of concept levels separed by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="c",
            data_type='string')

        compressed = LiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            default="no",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            default="-",
            data_type='string')

        hierarchy = LiteralInput(
            identifier="hierarchy",
            title="Hierarchy",
            abstract="Concept hierarchy name of the dimensions. Default value is 'oph_base'. Multi-value field: list of concept levels separed by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="oph_base",
            data_type='string')

        vocabulary = LiteralInput(
            identifier="vocabulary",
            title="Vocabulary",
            abstract="Optional argument used to indicate a vocabulary to be used to associate metadata to the container",
            min_occurs=0,
            max_occurs=1,
            default="CF",
            data_type='string')

        base_time = LiteralInput(
            identifier="base_time",
            title="Base time",
            abstract="In case of time hierarchy, it indicates the base time of the dimension. Default value is 1900-01-01",
            min_occurs=0,
            max_occurs=1,
            default="1900-01-01 00:00:00",
            data_type='string')

        units = LiteralInput(
            identifier="units",
            title="Units",
            abstract="In case of time hierarchy, it indicates the units of the dimension. Possible values are: s,m,h,3,6,d",
            min_occurs=0,
            max_occurs=1,
            default="d",
            data_type='string')

        calendar = LiteralInput(
            identifier="calendar",
            title="Calendar",
            abstract="In case of time hierarchy, it indicates the calendar type",
            min_occurs=0,
            max_occurs=1,
            default="standard",
            data_type='string')

        month_lenghts = LiteralInput(
            identifier="month_lenghts",
            title="Month lenghts",
            abstract="In case of time dimension and user-defined calendar, it indicates the sizes of each month in days. There byst be 12 positive integers separated by commas",
            min_occurs=0,
            max_occurs=1,
            default="31,28,31,30,31,30,31,31,30,31,30,31",
            data_type='string')

        leap_year = LiteralInput(
            identifier="leap_year",
            title="Leap year",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap year. By default it is set to 0",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        leap_month = LiteralInput(
            identifier="leap_month",
            title="Leap month",
            abstract="In case of time dimension and user-defined calendar, it indicates the leap month. By default it is set to 2 (February)",
            min_occurs=0,
            max_occurs=1,
            default=2,
            data_type='integer')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, cwd, container, host_partition, ioserver, import_metadata, check_compliance, nhost, nfrag, measure, run, schedule, src_path, cdd, exp_dim, imp_dim,
            subset_dims, subset_filter, subset_type, time_filter, offset, exp_concept_level, imp_concept_level, compressed, grid, hierarchy, vocabulary, base_time, units, calendar, month_lenghts, leap_year, leap_month, description]
        outputs = [jobid, response, error]

        super(oph_importnc2, self).__init__(
            self._handler,
            identifier="oph_importnc2",
            title="Ophidia importnc2",
            version=_version,
            abstract="Import a NetCDF file into a datacube (both measure and dimensions); optimized version of oph_importnc",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_importnc2 '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['host_partition'][0].data is not None:
            query += 'host_partition=' + str(request.inputs['host_partition'][0].data) + ';'
        if request.inputs['check_compliance'][0].data is not None:
            query += 'check_compliance=' + str(request.inputs['check_compliance'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['ioserver'][0].data is not None:
            query += 'ioserver=' + str(request.inputs['ioserver'][0].data) + ';'
        if request.inputs['import_metadata'][0].data is not None:
            query += 'import_metadata=' + str(request.inputs['import_metadata'][0].data) + ';'
        if request.inputs['nhost'][0].data is not None:
            query += 'nhost=' + str(request.inputs['nhost'][0].data) + ';'
        if request.inputs['nfrag'][0].data is not None:
            query += 'nfrag=' + str(request.inputs['nfrag'][0].data) + ';'
        if request.inputs['run'][0].data is not None:
            query += 'run=' + str(request.inputs['run'][0].data) + ';'
        if request.inputs['cdd'][0].data is not None:
            query += 'cdd=' + str(request.inputs['cdd'][0].data) + ';'
        if request.inputs['exp_dim'][0].data is not None:
            query += 'exp_dim=' + str(request.inputs['exp_dim'][0].data) + ';'
        if request.inputs['imp_dim'][0].data is not None:
            query += 'imp_dim=' + str(request.inputs['imp_dim'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['subset_type'][0].data is not None:
            query += 'subset_type=' + str(request.inputs['subset_type'][0].data) + ';'
        if request.inputs['time_filter'][0].data is not None:
            query += 'time_filter=' + str(request.inputs['time_filter'][0].data) + ';'
        if request.inputs['offset'][0].data is not None:
            query += 'offset=' + str(request.inputs['offset'][0].data) + ';'
        if request.inputs['exp_concept_level'][0].data is not None:
            query += 'exp_concept_level=' + str(request.inputs['exp_concept_level'][0].data) + ';'
        if request.inputs['imp_concept_level'][0].data is not None:
            query += 'imp_concept_level=' + str(request.inputs['imp_concept_level'][0].data) + ';'
        if request.inputs['compressed'][0].data is not None:
            query += 'compressed=' + str(request.inputs['compressed'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['hierarchy'][0].data is not None:
            query += 'hierarchy=' + str(request.inputs['hierarchy'][0].data) + ';'
        if request.inputs['vocabulary'][0].data is not None:
            query += 'vocabulary=' + str(request.inputs['vocabulary'][0].data) + ';'
        if request.inputs['base_time'][0].data is not None:
            query += 'base_time=' + str(request.inputs['base_time'][0].data) + ';'
        if request.inputs['units'][0].data is not None:
            query += 'units=' + str(request.inputs['units'][0].data) + ';'
        if request.inputs['calendar'][0].data is not None:
            query += 'calendar=' + str(request.inputs['calendar'][0].data) + ';'
        if request.inputs['month_lenghts'][0].data is not None:
            query += 'month_lenghts=' + str(request.inputs['month_lenghts'][0].data) + ';'
        if request.inputs['leap_year'][0].data is not None:
            query += 'leap_year=' + str(request.inputs['leap_year'][0].data) + ';'
        if request.inputs['leap_month'][0].data is not None:
            query += 'leap_month=' + str(request.inputs['leap_month'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'
        query += 'measure=' + str(request.inputs['measure'][0].data) + ';'
        query += 'src_path=' + str(request.inputs['src_path'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_input(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        id = LiteralInput(
            identifier="id",
            title="Id",
            abstract="Workflow identifier. By default the hosting workflow is selected. The target workflow must have been subitted the same session. Default value is @OPH_WORKFLOW_ID",
            min_occurs=0,
            max_occurs=1,
            default='@OPH_WORKFLOW_ID',
            data_type='integer')

        taskname = LiteralInput(
            identifier="taskname",
            title="Taskname",
            abstract="Name of the interactive task. By default is set to 'Task 0' and it can be automatically set to the interactive task of target workflow if it unique",
            min_occurs=0,
            max_occurs=1,
            default="Task 0",
            data_type='string')

        action = LiteralInput(
            identifier="action",
            title="Action",
            abstract="Name of the command to be sent to the interactive task. Use: 'continue' to unlock the task (default); 'abort' to abort the task; 'wait' in case of no action",
            min_occurs=0,
            max_occurs=1,
            default="continue",
            data_type='string')

        key = LiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the parameter",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        value = LiteralInput(
            identifier="value",
            title="Value",
            abstract="Value of the parameter. By default it will set to 1",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, id, taskname, action, key, value]
        outputs = [jobid, response, error]

        super(oph_input, self).__init__(
            self._handler,
            identifier="oph_input",
            title="Ophidia input",
            version=_version,
            abstract="Send commands or data to an interactive task ('OPH_WAIT'); set parameters in a workflow environment",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_input '
        if request.inputs['id'][0].data is not None:
            query += 'id=' + str(request.inputs['id'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['taskname'][0].data is not None:
            query += 'taskname=' + str(request.inputs['taskname'][0].data) + ';'
        if request.inputs['action'][0].data is not None:
            query += 'action=' + str(request.inputs['action'][0].data) + ';'
        if request.inputs['key'][0].data is not None:
            query += 'key=' + str(request.inputs['key'][0].data) + ';'
        if request.inputs['value'][0].data is not None:
            query += 'value=' + str(request.inputs['value'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_instances(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        action = LiteralInput(
            identifier="action",
            title="Action",
            abstract="Command type. Use: 'read' to access information (default); 'add' to create user-defined host partitions, 'remove' to remove user-defined host partitions",
            min_occurs=0,
            max_occurs=1,
            default="read",
            data_type='string')

        level = LiteralInput(
            identifier="level",
            title="Level",
            abstract="Shows hosts with '1', DBMS instances with '2' or host partitions with '3'",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        host_filter = LiteralInput(
            identifier="host_filter",
            title="Host filter",
            abstract="In 'read' mode it is an optional filter on host name and can be used only with level 2; in 'add' or 'remove' mode it is the list of host identifiers to be grouped in the user-defined partition",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        nhost = LiteralInput(
            identifier="nhost",
            title="Numner of hosts",
            abstract="In 'add' or 'remove' mode it is the number of hosts to be grouped in the user-defined partition; if it is non-zero then 'host_filter' is negleted",
            min_occurs=0,
            max_occurs=1,
            default="1",
            data_type='integer')

        host_partition = LiteralInput(
            identifier="host_partition",
            title="Host partition",
            abstract="In 'read' mode it is an optional filter on host partition name and can be used only with level 3; if no partition is specified, then the list of all partitions is shown; in 'add' mode it is the name of the new partition; in 'remove' mode it is the name of the partition to be removed",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        filesystem_filter = LiteralInput(
            identifier="filesystem_filter",
            title="Filesystem filter",
            abstract="Optional filter on the type of filesystem used. Used only with level 2. Possible values are: 'local' for local disks, 'global' for GPFS disks, 'all' (default) for both types of disks",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        ioserver_filter = LiteralInput(
            identifier="ioserver_filter",
            title="Ioserver filter",
            abstract="Optional filter on the type of filesystem used. Used only with level 2. Possible values are: 'mysql_table' for MySQL I/O servers, 'ophidiaio_memory' for Ophidia I/O servers only for 'all' (default) for any type of I/O server",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        host_status = LiteralInput(
            identifier="host_status",
            title="Host status",
            abstract="Optional filter on status of I/O nodes. Possible values are: 'up' for up hosts, 'down' for down hosts, 'all' (default) for all hosts",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        dbms_status = LiteralInput(
            identifier="dbms_status",
            title="Dbms status",
            abstract="Optional filter on the status of dbms instances. Used ony with level 2. Possible values are 'up' for instances in un state, 'down' for instances in down state, 'all' (default) for all instances",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, action, level, host_filter, nhost, host_partition, filesystem_filter, ioserver_filter, host_status, dbms_status]
        outputs = [jobid, response, error]

        super(oph_instances, self).__init__(
            self._handler,
            identifier="oph_instances",
            title="Ophidia instances",
            version=_version,
            abstract="Show information about host partitions, hosts and dbms instances",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_instances '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['host_partition'][0].data is not None:
            query += 'host_partition=' + str(request.inputs['host_partition'][0].data) + ';'
        if request.inputs['nhost'][0].data is not None:
            query += 'nhost=' + str(request.inputs['nhost'][0].data) + ';'
        if request.inputs['host_filter'][0].data is not None:
            query += 'host_filter=' + str(request.inputs['host_filter'][0].data) + ';'
        if request.inputs['filesystem_filter'][0].data is not None:
            query += 'filesystem_filter=' + str(request.inputs['filesystem_filter'][0].data) + ';'
        if request.inputs['ioserver_filter'][0].data is not None:
            query += 'ioserver_filter=' + str(request.inputs['ioserver_filter'][0].data) + ';'
        if request.inputs['host_status'][0].data is not None:
            query += 'host_status=' + str(request.inputs['host_status'][0].data) + ';'
        if request.inputs['dbms_status'][0].data is not None:
            query += 'dbms_status=' + str(request.inputs['dbms_status'][0].data) + ';'
        if request.inputs['level'][0].data is not None:
            query += 'level=' + str(request.inputs['level'][0].data) + ';'
        if request.inputs['action'][0].data is not None:
            query += 'action=' + str(request.inputs['action'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_intercube(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        pid2 = LiteralInput(
            identifier="cube2",
            title="Input cube2",
            abstract="Name of the second input datacube in PID format",
            data_type='string')

        pids = LiteralInput(
            identifier="cubes",
            title="Input cubes",
            abstract="Name of the input datacubes, in PID format, alternatively to parameters 'cube' and 'cube2'. Multiple-values field: list of cubes separated by '|' can be provided. Only two datacbubes shall be specified",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        measure = LiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the new measure resulting from the specified operation",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        operation = LiteralInput(
            identifier="operation",
            title="Operation",
            min_occurs=0,
            max_occurs=1,
            default="sub",
            abstract="Indicates the operation. Possible values are: sum, sub, mul, div, abs, arg, corr, mask, max, min, arg_max, arg_min",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, pid2, container, measure, description, schedule, operation]
        outputs = [jobid, response, error]

        super(oph_intercube, self).__init__(
            self._handler,
            identifier="oph_intercube",
            title="Ophidia intercube",
            version=_version,
            abstract="Execute an operation between two datacubes with the same fragmentation structure and return a new datacube as result of the specified operation applied element by element",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_intercube '

        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['operation'][0].data is not None:
            query += 'operation=' + str(request.inputs['operation'][0].data) + ';'
        if request.inputs['measure'][0].data is not None:
            query += 'measure=' + str(request.inputs['measure'][0].data) + ';'
        if request.inputs['cube'][0].data is not None:
            query += 'cube=' + str(request.inputs['cube'][0].data) + ';'
        if request.inputs['cube2'][0].data is not None:
            query += 'cube2=' + str(request.inputs['cube2'][0].data) + ';'
        if request.inputs['cubes'][0].data is not None:
            query += 'cubes=' + str(request.inputs['cubes'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_list(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        level = LiteralInput(
            identifier="level",
            title="Level",
            abstract="Level of verbosity. Possible values are '0' (shows folders); '1' (shows folders and containers); '2' (show folders, containers and datacubes; '3' (shows containers path, datacubes pid, measure, source and transformation level); 4 (shows containers path and datacubes); 5 (shows containers, datacubes and hosts); 6 (shows containers, datacubes, hosts and dbmss); 7 (shows containers, datacubes, hosts, dbmss and dbs); 8 (shows containers, datacubes, hosts, dbmss, dbs and fragments)",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        path = LiteralInput(
            identifier="path",
            title="Path",
            abstract="Optional filter on absoute/relative path. Path is expanded, so it can also contain '.' and '..'",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container_filter = LiteralInput(
            identifier="container_filter",
            title="Container filter",
            abstract="Optional filter on containers. The argument is considered only for the firt three levels. Default is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format. This argument is mandatory only when level is >=3, otherwise it is not considered",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        host_filter = LiteralInput(
            identifier="host_filter",
            title="Host filter",
            abstract="Optional filter on hosts. Default is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        dbms_filter = LiteralInput(
            identifier="dbms_filter",
            title="Dbms filter",
            abstract="Optional filter on DBMSs. Default is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='integer')

        measure_filter = LiteralInput(
            identifier="measure_filter",
            title="Measure filter",
            abstract="Optional filter on measure. Default is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        ntransform = LiteralInput(
            identifier="ntransform",
            title="Number of transformation",
            abstract="Optional filter on operation level (number of transformation applied since import). Default is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='integer')

        src_filter = LiteralInput(
            identifier="src_filter",
            title="Source filter",
            abstract="Optional filter on source. Default is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        db_filter = LiteralInput(
            identifier="db_filter",
            title="Db filter",
            abstract="Optional filter on databases. Default is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        recursive = LiteralInput(
            identifier="recursive",
            title="Recursive",
            abstract="Specifies if the search is done recursively or not. The argument is considered only for the first three levels and may have the following values: 'no' (research only in current path); 'yes' (research recursively starting from current path)",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, level, path, cwd, container_filter, pid, host_filter, dbms_filter, measure_filter, ntransform, src_filter, db_filter, recursive]
        outputs = [jobid, response, error]

        super(oph_list, self).__init__(
            self._handler,
            identifier="oph_list",
            title="Ophidia list",
            version=_version,
            abstract="Show information about folders, container and datacubes fragmentation (file system)",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_list '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['path'][0].data is not None:
            query += 'path=' + str(request.inputs['path'][0].data) + ';'
        if request.inputs['container_filter'][0].data is not None:
            query += 'container_filter=' + str(request.inputs['container_filter'][0].data) + ';'
        if request.inputs['cube'][0].data is not None:
            query += 'cube=' + str(request.inputs['cube'][0].data) + ';'
        if request.inputs['host_filter'][0].data is not None:
            query += 'host_filter=' + str(request.inputs['host_filter'][0].data) + ';'
        if request.inputs['dbms_filter'][0].data is not None:
            query += 'dbms_filter=' + str(request.inputs['dbms_filter'][0].data) + ';'
        if request.inputs['measure_filter'][0].data is not None:
            query += 'measure_filter=' + str(request.inputs['measure_filter'][0].data) + ';'
        if request.inputs['ntransform'][0].data is not None:
            query += 'ntransform=' + str(request.inputs['ntransform'][0].data) + ';'
        if request.inputs['src_filter'][0].data is not None:
            query += 'src_filter=' + str(request.inputs['src_filter'][0].data) + ';'
        if request.inputs['db_filter'][0].data is not None:
            query += 'db_filter=' + str(request.inputs['db_filter'][0].data) + ';'
        if request.inputs['recursive'][0].data is not None:
            query += 'recursive=' + str(request.inputs['recursive'][0].data) + ';'
        if request.inputs['level'][0].data is not None:
            query += 'level=' + str(request.inputs['level'][0].data) + ';'

        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_log_info(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="sync",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        log_type = LiteralInput(
            identifier="log_type",
            title="Log type",
            abstract="Type of log to be read. Possible values are 'server', 'container' and 'ioserver'. If not specified, it will be used its default value 'server'",
            min_occurs=0,
            max_occurs=1,
            default="server",
            data_type='string')

        container_id = LiteralInput(
            identifier="container_id",
            title="Container id",
            abstract="Optional filter on host name. Used only with level 2",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        ioserver = LiteralInput(
            identifier="ioserver",
            title="Ioserver",
            abstract="Type of the ioserver related to the requested log, valid only when requested log type is 'ioserver'",
            min_occurs=0,
            max_occurs=1,
            default="mysql",
            data_type='string')

        nlines = LiteralInput(
            identifier="nlines",
            title="Nlines",
            abstract="Maximum number of lines to be displayed, starting from the end of the log. Default value is '10'",
            min_occurs=0,
            max_occurs=1,
            default=10,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, log_type, container_id, ioserver, nlines]
        outputs = [jobid, response, error]

        super(oph_log_info, self).__init__(
            self._handler,
            identifier="oph_log_info",
            title="Ophidia log_info",
            version=_version,
            abstract="Read the last lines from the server log or from a specific container log; this operator requires administrator privileges",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_log_info '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['log_type'][0].data is not None:
            query += 'log_type=' + str(request.inputs['log_type'][0].data) + ';'
        if request.inputs['container_id'][0].data is not None:
            query += 'container_id=' + str(request.inputs['container_id'][0].data) + ';'
        if request.inputs['ioserver'][0].data is not None:
            query += 'ioserver=' + str(request.inputs['ioserver'][0].data) + ';'
        if request.inputs['nlines'][0].data is not None:
            query += 'nlines=' + str(request.inputs['nlines'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_loggingbk(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        session_level = LiteralInput(
            identifier="session_level",
            title="Session level",
            abstract="0 (session id (+ session label) (default)) or 1 (sessionid (+ session label) + session creation date)",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        job_level = LiteralInput(
            identifier="job_level",
            title="Job level",
            abstract="0 (nothing (default)) or 1 (job id (+ parent job id) + workflow id + marker id) or 2 (job id (+ parent job id) + workflow id + marker id + job submission date)",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        mask = LiteralInput(
            identifier="mask",
            title="Mask",
            abstract="3-digit mask, considered if job_level is bigger than 0",
            min_occurs=0,
            max_occurs=1,
            default="000",
            data_type='string')

        session_filter = LiteralInput(
            identifier="session_filter",
            title="Session filter",
            abstract="Filter on a particular sessionID",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        session_label_filter = LiteralInput(
            identifier="session_label_filter",
            title="Session label filter",
            abstract="Filter on a particular session label",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        session_creation_filter = LiteralInput(
            identifier="session_creation_filter",
            title="Session creation filter",
            abstract="Filter on session's creation date (yyyy-mm-dd hh:mm:ss <= date <= yyyy:mm:dd hh:mm:ss)",
            min_occurs=0,
            max_occurs=1,
            default="1900-01-01 00:00:00,2100-01-01 00:00:00",
            data_type='string')

        workflowid_filter = LiteralInput(
            identifier="workflowid_filter",
            title="Workflowid filter",
            abstract="Filter on a particular workflow ID",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        markerid_filter = LiteralInput(
            identifier="markerid_filter",
            title="Markerid filter",
            abstract="Filter on a particular marker ID",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        parent_job_filter = LiteralInput(
            identifier="parent_job_filter",
            title="Parent job filter",
            abstract="Filter on a particular parent job ID. If wildcard % is used, then only jobs with a parent will be shown",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        job_creation_filter = LiteralInput(
            identifier="job_creation_filter",
            title="Job creation filter",
            abstract="Filter on a particular parent job ID. If wildcard % is used, then only jobs with a parent will be shown",
            min_occurs=0,
            max_occurs=1,
            default="1900-01-01 00:00:00,2100-01-01 00:00:00",
            data_type='string')

        job_status_filter = LiteralInput(
            identifier="job_status_filter",
            title="Job status filter",
            abstract="Filter on job status",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        submission_string_filter = LiteralInput(
            identifier="submission_string_filter",
            title="Submission string filter",
            abstract="Filter on submission string",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        job_start_filter = LiteralInput(
            identifier="job_start_filter",
            title="Job start filter",
            abstract="Filter on job's start date as with session_creation_filter",
            min_occurs=0,
            max_occurs=1,
            default="1900-01-01 00:00:00,2100-01-01 00:00:00",
            data_type='string')

        job_end_filter = LiteralInput(
            identifier="job_end_filter",
            title="Job end filter",
            abstract="Filter on job's end date as with session_creation_filter",
            min_occurs=0,
            max_occurs=1,
            default="1900-01-01 00:00:00,2100-01-01 00:00:00",
            data_type='string')

        nlines = LiteralInput(
            identifier="nlines",
            title="Nlines",
            abstract="Maximum number of lines to be displayed, starting from the end of the log. Default value is '100'",
            min_occurs=0,
            max_occurs=1,
            default=100,
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, session_level, job_level, mask, session_filter, session_label_filter, session_creation_filter,
            workflowid_filter, markerid_filter, parent_job_filter, job_creation_filter, job_status_filter, submission_string_filter, job_start_filter, job_end_filter, nlines]
        outputs = [jobid, response, error]

        super(oph_loggingbk, self).__init__(
            self._handler,
            identifier="oph_loggingbk",
            title="Ophidia loggingbk",
            version=_version,
            abstract="Show info about sumbitted jobs",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_loggingbk '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['session_level'][0].data is not None:
            query += 'session_level=' + str(request.inputs['session_level'][0].data) + ';'
        if request.inputs['job_level'][0].data is not None:
            query += 'job_level=' + str(request.inputs['job_level'][0].data) + ';'
        if request.inputs['mask'][0].data is not None:
            query += 'mask=' + str(request.inputs['mask'][0].data) + ';'
        if request.inputs['session_filter'][0].data is not None:
            query += 'session_filter=' + str(request.inputs['session_filter'][0].data) + ';'
        if request.inputs['session_label_filter'][0].data is not None:
            query += 'session_label_filter=' + str(request.inputs['session_label_filter'][0].data) + ';'
        if request.inputs['session_creation_filter'][0].data is not None:
            query += 'session_creation_filter=' + str(request.inputs['session_creation_filter'][0].data) + ';'
        if request.inputs['workflowid_filter'][0].data is not None:
            query += 'workflowid_filter=' + str(request.inputs['workflowid_filter'][0].data) + ';'
        if request.inputs['markerid_filter'][0].data is not None:
            query += 'markerid_filter=' + str(request.inputs['markerid_filter'][0].data) + ';'
        if request.inputs['parent_job_filter'][0].data is not None:
            query += 'parent_job_filter=' + str(request.inputs['parent_job_filter'][0].data) + ';'
        if request.inputs['job_creation_filter'][0].data is not None:
            query += 'job_creation_filter=' + str(request.inputs['job_creation_filter'][0].data) + ';'
        if request.inputs['job_status_filter'][0].data is not None:
            query += 'job_status_filter=' + str(request.inputs['job_status_filter'][0].data) + ';'
        if request.inputs['submission_string_filter'][0].data is not None:
            query += 'submission_string_filter=' + str(request.inputs['submission_string_filter'][0].data) + ';'
        if request.inputs['job_start_filter'][0].data is not None:
            query += 'job_start_filter=' + str(request.inputs['job_start_filter'][0].data) + ';'
        if request.inputs['job_end_filter'][0].data is not None:
            query += 'job_end_filter=' + str(request.inputs['job_end_filter'][0].data) + ';'
        if request.inputs['nlines'][0].data is not None:
            query += 'nlines=' + str(request.inputs['nlines'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_man(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        function = LiteralInput(
            identifier="function",
            title="Function",
            abstract="Name of the requested operator/primitive",
            data_type='string')

        function_version = LiteralInput(
            identifier="function_version",
            title="Function version",
            abstract="Version of the requested operator/primitive. If not specified, it will be used its default value 'latest' in order to get info about the latest version of the operator",
            min_occurs=0,
            max_occurs=1,
            default="latest",
            data_type='string')

        function_type = LiteralInput(
            identifier="function_type",
            title="Function type",
            abstract="Type of function to describe; it can be operator or primitive. If not specified, it will be used its default value 'operator'",
            min_occurs=0,
            max_occurs=1,
            default="operator",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, function, function_version, function_type]
        outputs = [jobid, response, error]

        super(oph_man, self).__init__(
            self._handler,
            identifier="oph_man",
            title="Ophidia man",
            version=_version,
            abstract="Show a description of the behaviour of an operator/primitive",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_man '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['function_version'][0].data is not None:
            query += 'function_version=' + str(request.inputs['function_version'][0].data) + ';'
        if request.inputs['function_type'][0].data is not None:
            query += 'function_type=' + str(request.inputs['function_type'][0].data) + ';'

        query += 'function=' + str(request.inputs['function'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_manage_session(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        action = LiteralInput(
            identifier="action",
            title="Action",
            abstract="Name of the action to be applied to session parameter",
            data_type='string')

        session = LiteralInput(
            identifier="session",
            title="Session",
            abstract="Link to intended session, by default it is the working session",
            min_occurs=0,
            max_occurs=1,
            default="this",
            data_type='string')

        key = LiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the parameter to be get/set",
            min_occurs=0,
            max_occurs=1,
            default="user",
            data_type='string')

        value = LiteralInput(
            identifier="value",
            title="Value",
            abstract="Value of the key set with the argument 'key'",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, action, session, key, value]
        outputs = [jobid, response, error]

        super(oph_manage_session, self).__init__(
            self._handler,
            identifier="oph_manage_session",
            title="Ophidia manage_session",
            version=_version,
            abstract="Request or set session data: session list, session creation date, authorized users, etc. Only session owner and administrators can submit the command",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_manage_session '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['session'][0].data is not None:
            query += 'session=' + str(request.inputs['session'][0].data) + ';'
        if request.inputs['key'][0].data is not None:
            query += 'key=' + str(request.inputs['key'][0].data) + ';'
        if request.inputs['value'][0].data is not None:
            query += 'value=' + str(request.inputs['value'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'

        query += 'action=' + str(request.inputs['action'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_merge(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        nmerge = LiteralInput(
            identifier="nmerge",
            title="Number of Input Fragments",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, schedule, nmerge, container, description]
        outputs = [jobid, response, error]

        super(oph_merge, self).__init__(
            self._handler,
            identifier="oph_merge",
            title="Ophidia merge",
            version=_version,
            abstract="Create a new datacube grouping nmerge input fragments in a new output fragment",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_merge '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['nmerge'][0].data is not None:
            query += 'nmerge=' + str(request.inputs['nmerge'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_mergecubes(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pids = LiteralInput(
            identifier="cubes",
            title="Input cubes",
            abstract="Name of the input datacubes, in PID format, to merge. Multiple-values field: list of cubes separated by '|' can be provided",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        mode = LiteralInput(
            identifier="mode",
            title="Mode",
            abstract="Possible values are 'i' (default) to interlace, 'a' to append input measures",
            min_occurs=0,
            max_occurs=1,
            default="i",
            data_type='string')

        hold_values = LiteralInput(
            identifier="hold_values",
            title="Hold Values",
            abstract="Possible values are 'yes' and 'no' (default). Enables the copy of the original values of implicit dimension; by defaylt new values are incremental integer",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        number = LiteralInput(
            identifier="number",
            title="Number",
            abstract="Number of replies of the first cube; by default the first cube is considered only once",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pids, schedule, mode, hold_values, number, container, description]
        outputs = [jobid, response, error]

        super(oph_mergecubes, self).__init__(
            self._handler,
            identifier="oph_mergecubes",
            title="Ophidia mergecubes",
            version=_version,
            abstract="Merge the measures of n input datacubes with the same fragmentation structure and creates a new datacube with the union of the n measures; only single measure data cubes can be merged",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_mergecubes '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['mode'][0].data is not None:
            query += 'mode=' + str(request.inputs['mode'][0].data) + ';'
        if request.inputs['hold_values'][0].data is not None:
            query += 'hold_values=' + str(request.inputs['hold_values'][0].data) + ';'
        if request.inputs['number'][0].data is not None:
            query += 'number=' + str(request.inputs['number'][0].data) + ';'

        query += 'cubes=' + str(request.inputs['cubes'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_mergecubes2(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pids = LiteralInput(
            identifier="cubes",
            title="Input cubes",
            abstract="Name of the input datacubes, in PID format, to merge. Multiple-values field: list of cubes separated by '|' can be provided",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        dim = LiteralInput(
            identifier="dim",
            title="Dimension name",
            abstract="Name of the new dimension to be created. By default a unique random name is chosen",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        dim_type = LiteralInput(
            identifier="dim_type",
            title="Dimension type",
            abstract="Data type associated with the new dimension",
            min_occurs=0,
            max_occurs=1,
            default="long",
            data_type='string')

        number = LiteralInput(
            identifier="number",
            title="Number",
            abstract="Number of replies of the first cube; by default the first cube is considered only once",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pids, schedule, dim, dim_type, number, container, description]
        outputs = [jobid, response, error]

        super(oph_mergecubes2, self).__init__(
            self._handler,
            identifier="oph_mergecubes2",
            title="Ophidia mergecubes2",
            version=_version,
            abstract="Merge the measures of n input datacubes with the same fragmentation structure and creates a new datacube with the union of the n measures; only single measure data cubes can be merged and a new implicit dimension will be created",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_mergecubes2 '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['dim'][0].data is not None:
            query += 'dim=' + str(request.inputs['dim'][0].data) + ';'
        if request.inputs['dim_type'][0].data is not None:
            query += 'dim_type=' + str(request.inputs['dim_type'][0].data) + ';'
        if request.inputs['number'][0].data is not None:
            query += 'number=' + str(request.inputs['number'][0].data) + ';'

        query += 'cubes=' + str(request.inputs['cubes'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_metadata(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        mode = LiteralInput(
            identifier="mode",
            title="Mode",
            abstract="Set the appropiate operation among: insert, read, update, delete",
            min_occurs=0,
            max_occurs=1,
            default="read",
            data_type='string')

        metadata_key = LiteralInput(
            identifier="metadata_key",
            title="Metadata key",
            abstract="Name of the key identifying requested metadata. It can be used always byt not n update mode, where it necessary the id of the to-be-updated metadata",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        variable = LiteralInput(
            identifier="variable",
            title="Variable",
            abstract="Name of the variable to which we can associate a new metadata key; its default value ('global') can be used to refer to a global metadata",
            min_occurs=0,
            max_occurs=1,
            default="global",
            data_type='string')

        metadata_id = LiteralInput(
            identifier="metadata_id",
            title="Metadata id",
            abstract="Id of the particular metadata instance to interact with. It cannot be used in insert mode. It is mandatory in update mode. It can be used in read pr delete mode to specify a particuar instance to be read or deleted. In read or delete modes, if specifed, it will mute the values of the parameter metadata_key; if not specified, it will be used its default value (0) in order to use metadata_key to select appropriate content",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        metadata_type = LiteralInput(
            identifier="metadata_type",
            title="Metadata type",
            abstract="Name of the type of the to-be-inserted metadata. To change the type of already-inserted metadata, use a combination of a deletion and a insertion. default value is 'text', but other values include 'image', 'video', 'audio' and 'url', even if all contents will be saved as strings. Numerical data types are also available as well",
            min_occurs=0,
            max_occurs=1,
            default="text",
            data_type='string')

        metadata_value = LiteralInput(
            identifier="metadata_value",
            title="Metadata value",
            abstract="String value to be assigned to specified metadata. Valid only in insert or update nodes. In insert mode, more values ca be listed by using '|' as separator. Default value is 'null'",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        variable_filter = LiteralInput(
            identifier="variable_filter",
            title="Variable filter",
            abstract="Optional filter on variable name, valid in read/delete mode only",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        metadata_type_filter = LiteralInput(
            identifier="metadata_type_filter",
            title="Metadata type filter",
            abstract="Optional filter on the type of returned metadata valid in read mode only",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        metadata_value_filter = LiteralInput(
            identifier="metadata_value_filter",
            title="Metadata value filter",
            abstract="Optional filter on the value of returned metadata valid in read mode only",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        force = LiteralInput(
            identifier="force",
            title="Force",
            abstract="Force update or deletion of a functional metadata associated to a vocabulary. By defaylt, update or deletion of functional metadata is not allowed ('n'). Set to 'yes' to allow modification of functional metadata",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, mode, metadata_key, variable, metadata_id,
            metadata_type, metadata_value, variable_filter, metadata_type_filter, metadata_value_filter, force]
        outputs = [jobid, response, error]

        super(oph_metadata, self).__init__(
            self._handler,
            identifier="oph_metadata",
            title="Ophidia metadata",
            version=_version,
            abstract="Provide CRUD operations (Create, Read, Update and Delete) on OphidiaDB metadata",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_metadata '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['mode'][0].data is not None:
            query += 'mode=' + str(request.inputs['mode'][0].data) + ';'
        if request.inputs['metadata_key'][0].data is not None:
            query += 'metadata_key=' + str(request.inputs['metadata_key'][0].data) + ';'
        if request.inputs['variable'][0].data is not None:
            query += 'variable=' + str(request.inputs['variable'][0].data) + ';'
        if request.inputs['metadata_id'][0].data is not None:
            query += 'metadata_id=' + str(request.inputs['metadata_id'][0].data) + ';'
        if request.inputs['metadata_type'][0].data is not None:
            query += 'metadata_type=' + str(request.inputs['metadata_type'][0].data) + ';'
        if request.inputs['metadata_value'][0].data is not None:
            query += 'metadata_value=' + str(request.inputs['metadata_value'][0].data) + ';'
        if request.inputs['variable_filter'][0].data is not None:
            query += 'variable_filter=' + str(request.inputs['variable_filter'][0].data) + ';'
        if request.inputs['metadata_type_filter'][0].data is not None:
            query += 'metadata_type_filter=' + str(request.inputs['metadata_type_filter'][0].data) + ';'
        if request.inputs['metadata_value_filter'][0].data is not None:
            query += 'metadata_value_filter=' + str(request.inputs['metadata_value_filter'][0].data) + ';'
        if request.inputs['force'][0].data is not None:
            query += 'force=' + str(request.inputs['force'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_movecontainer(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Container",
            abstract="Exactly 2 paths (separated by |) for the input and the ouput containers (with his ordering) must be specified",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, container, cwd]
        outputs = [jobid, response, error]

        super(oph_movecontainer, self).__init__(
            self._handler,
            identifier="oph_movecontainer",
            title="Ophidia movecontainer",
            version=_version,
            abstract="Move/rename a visible container",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_movecontainer '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'

        query += 'container=' + str(request.inputs['container'][0].data) + ';'
        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_operators_list(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        operator_filter = LiteralInput(
            identifier="operator_filter",
            title="Operator filter",
            abstract="Optional filter on the name of the displayed operators, with pattern 'filter'",
            min_occurs=0,
            max_occurs=1,
            default="operator",
            data_type='string')

        limit_filter = LiteralInput(
            identifier="limit_filter",
            title="Limit filter",
            abstract="Optional filter on the maximum number of displayed operators. Default value is 0, used to show all operators",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, operator_filter, limit_filter]
        outputs = [jobid, response, error]

        super(oph_operators_list, self).__init__(
            self._handler,
            identifier="oph_operators_list",
            title="Ophidia operators_list",
            version=_version,
            abstract="Show the list of all active operators",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_operators_list '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['operator_filter'][0].data is not None:
            query += 'operator_filter=' + str(request.inputs['operator_filter'][0].data) + ';'
        if request.inputs['limit_filter'][0].data is not None:
            query += 'limit_filter=' + str(request.inputs['limit_filter'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_permute(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        dim_pos = LiteralInput(
            identifier="dim_pos",
            title="Dim pos",
            abstract="Permutation of implicit dimensions as a comma-separated list of dimension levels. Number of elements in the list must be equal to the number of implicit dimensions of input datacube. Each element indicates the new level of the implicit dimension, drom the outermost to the innermost, in the output datacube",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, schedule, dim_pos, container, description]
        outputs = [jobid, response, error]

        super(oph_permute, self).__init__(
            self._handler,
            identifier="oph_permute",
            title="Ophidia permute",
            version=_version,
            abstract="Perform a permutation of the dimension of a datacube; this version operates only on implicit dimensions",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_permute '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'dim_pos=' + str(request.inputs['dim_pos'][0].data) + ';'
        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_primitives_list(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        level = LiteralInput(
            identifier="level",
            title="Level",
            abstract="Level of verbosity. '1': shows the primitive's name; '2': shows the type of the returned value, array or number; '3': shows also the name of the related dynamic library; '4': shows also the type of the primitive, simple or aggregate; '5': shows also the related DBMS id",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        dbms_filter = LiteralInput(
            identifier="dbms_filter",
            title="Dbms filter",
            abstract="Id of the specific DBMS instance look up. If no values is specified, then DBMS used will be the first available",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='integer')

        return_type = LiteralInput(
            identifier="return_type",
            title="Return type",
            abstract="Optional filter on the type of the returned value. Possible values are 'array' for a set of data and 'number' for a singleton. Mute this filter with the default value 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        primitive_type = LiteralInput(
            identifier="primitive_type",
            title="Primitive type",
            abstract="Optional filter on the type of the primitive. Possible values are 'simple' for row-based functions and 'aggregate' for column-based aggregate functions. Mute this filter with 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        primitive_filter = LiteralInput(
            identifier="primitive_filter",
            title="Primitive filter",
            abstract="Optional filter on the name of the displayed primitives, with pattern 'filter'",
            min_occurs=0,
            max_occurs=1,
            default="",
            data_type='string')

        limit_filter = LiteralInput(
            identifier="limit_filter",
            title="Limit filter",
            abstract="Optional filter on the maximum number of displayed operators. Default value is 0, used to show all operators",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, level, dbms_filter, return_type, primitive_type, primitive_filter, limit_filter]
        outputs = [jobid, response, error]

        super(oph_primitives_list, self).__init__(
            self._handler,
            identifier="oph_primitives_list",
            title="Ophidia primitives_list",
            version=_version,
            abstract="Show a list with info about active Ophidia Primitives loaded into a specifiv DBMS instance",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_primitives_list '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['level'][0].data is not None:
            query += 'level=' + str(request.inputs['level'][0].data) + ';'
        if request.inputs['dbms_filter'][0].data is not None:
            query += 'dbms_filter=' + str(request.inputs['dbms_filter'][0].data) + ';'
        if request.inputs['return_type'][0].data is not None:
            query += 'return_type=' + str(request.inputs['return_type'][0].data) + ';'
        if request.inputs['primitive_type'][0].data is not None:
            query += 'primitive_type=' + str(request.inputs['primitive_type'][0].data) + ';'
        if request.inputs['primitive_filter'][0].data is not None:
            query += 'primitive_filter=' + str(request.inputs['primitive_filter'][0].data) + ';'
        if request.inputs['limit_filter'][0].data is not None:
            query += 'limit_filter=' + str(request.inputs['limit_filter'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_publish(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        show_index = LiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimensions ids. With 'yes', it will also show the dimension id next to the value",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        show_id = LiteralInput(
            identifier="show_id",
            title="Show id",
            abstract="If 'no' (default), it won't show fragment row ID. With 'yes', it will also show the fragment row ID",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        show_time = LiteralInput(
            identifier="show_time",
            title="Show time",
            abstract="If 'no' (default), the values of time dimension are shown as numbers. With 'yes', the values are converted as a string with date and time",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        content = LiteralInput(
            identifier="content",
            title="Content",
            abstract="Optional argument identifying the type of the content to be published: 'all' allows to publish data and metadata (default); 'data' allows to publish only data; 'metadata' allows to publish only metadata",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, show_index, show_id, show_time, content, schedule]
        outputs = [jobid, response, error]

        super(oph_publish, self).__init__(
            self._handler,
            identifier="oph_publish",
            title="Ophidia publish",
            version=_version,
            abstract="Create HTML pages with data and other information from a datacube",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_publish '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['show_index'][0].data is not None:
            query += 'show_index=' + str(request.inputs['show_index'][0].data) + ';'
        if request.inputs['show_id'][0].data is not None:
            query += 'show_id=' + str(request.inputs['show_id'][0].data) + ';'
        if request.inputs['show_time'][0].data is not None:
            query += 'show_time=' + str(request.inputs['show_time'][0].data) + ';'
        if request.inputs['content'][0].data is not None:
            query += 'content=' + str(request.inputs['content'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_randcube(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            data_type='string')

        host_partition = LiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="Name of I/O host partition used to store data. By default the first available host partition will be used",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        ioserver = LiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data. Possible values are: 'mysql_table' (default) or 'ophidiaio_memory'",
            min_occurs=0,
            max_occurs=1,
            default="mysql_table",
            data_type='string')

        nhost = LiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        nfrag = LiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database",
            data_type='integer')

        ntuple = LiteralInput(
            identifier="ntuple",
            title="Number of tuples per fragment",
            abstract="Number of tuples per fragment",
            data_type='integer')

        measure = LiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure used in the datacube",
            data_type='string')

        measure_type = LiteralInput(
            identifier="measure_type",
            title="Measure type",
            abstract="Type of measures. Possible values are 'double', 'float' or 'int'",
            data_type='string')

        exp_ndim = LiteralInput(
            identifier="exp_ndim",
            title="Exp ndim",
            abstract="Used to specify how many dimensions in dim argument, starting from the first one, must be considered as explicit dimensions",
            data_type='integer')

        dim = LiteralInput(
            identifier="dim",
            title="Dim",
            abstract="Name of the dimension. Multi-value field: list of dimensions separated by '|' can be provided",
            data_type='string')

        concept_level = LiteralInput(
            identifier="concept_level",
            title="Concept Level",
            abstract="Concept level short name (must be a singe char). Default value is 'c'. Multi-value field: list of concept levels separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="c",
            data_type='string')

        dim_size = LiteralInput(
            identifier="dim_size",
            title="Dim size",
            abstract="Size of random dimension. Multi-value field: list of dimensions separated by '|' can be provided",
            data_type='string')

        run = LiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the creation and computes the fragmentation parameters that would be used else. If set to 'yes', the actual cube creation is executed",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        compressed = LiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        algorithm = LiteralInput(
            identifier="algorithm",
            title="Algorithm adopted to generate pseudo-random values",
            abstract="It can be used to specify the type of emulation schema used to generate data. By default values are sampled indipendently from a uniform distribution in the range [0, 1000]. If 'temperatures' is used, then values are generated with a first order auto-regressive model to be consistent with temperature values (in Celsius).",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, cwd, container, host_partition, ioserver, nhost, nfrag, ntuple,
            measure, measure_type, exp_ndim, dim, concept_level, dim_size, run, schedule, compressed, grid, description, algorithm]
        outputs = [jobid, response, error]

        super(oph_randcube, self).__init__(
            self._handler,
            identifier="oph_randcube",
            title="Ophidia randcube",
            version=_version,
            abstract="Create a new datacube with random data and dimensions",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_randcube '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['host_partition'][0].data is not None:
            query += 'host_partition=' + str(request.inputs['host_partition'][0].data) + ';'
        if request.inputs['ioserver'][0].data is not None:
            query += 'ioserver=' + str(request.inputs['ioserver'][0].data) + ';'
        if request.inputs['nhost'][0].data is not None:
            query += 'nhost=' + str(request.inputs['nhost'][0].data) + ';'
        if request.inputs['run'][0].data is not None:
            query += 'run=' + str(request.inputs['run'][0].data) + ';'
        if request.inputs['concept_level'][0].data is not None:
            query += 'concept_level=' + str(request.inputs['concept_level'][0].data) + ';'
        if request.inputs['compressed'][0].data is not None:
            query += 'compressed=' + str(request.inputs['compressed'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['algorithm'][0].data is not None:
            query += 'algorithm=' + str(request.inputs['algorithm'][0].data) + ';'

        query += 'container=' + str(request.inputs['container'][0].data) + ';'
        query += 'nfrag=' + str(request.inputs['nfrag'][0].data) + ';'
        query += 'ntuple=' + str(request.inputs['ntuple'][0].data) + ';'
        query += 'measure=' + str(request.inputs['measure'][0].data) + ';'
        query += 'measure_type=' + str(request.inputs['measure_type'][0].data) + ';'
        query += 'dim=' + str(request.inputs['dim'][0].data) + ';'
        query += 'exp_ndim=' + str(request.inputs['exp_ndim'][0].data) + ';'
        query += 'dim_size=' + str(request.inputs['dim_size'][0].data) + ';'
        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_randcube2(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, used to select the folder where the container is located",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            data_type='string')

        host_partition = LiteralInput(
            identifier="host_partition",
            title="Host Partition",
            abstract="Name of I/O host partition used to store data. By default the first available host partition will be used",
            min_occurs=0,
            max_occurs=1,
            default="auto",
            data_type='string')

        ioserver = LiteralInput(
            identifier="ioserver",
            title="I/O Server",
            abstract="Type of I/O server used to store data. Possible values are: 'mysql_table' (default) or 'ophidiaio_memory'",
            min_occurs=0,
            max_occurs=1,
            default="mysql_table",
            data_type='string')

        nhost = LiteralInput(
            identifier="nhost",
            title="Number of output hosts",
            abstract="Number of output hosts. With defaylt value '0', all host available in the host partition are used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        nfrag = LiteralInput(
            identifier="nfrag",
            title="Number of fragments per database",
            abstract="Number of fragments per database",
            data_type='integer')

        ntuple = LiteralInput(
            identifier="ntuple",
            title="Number of tuples per fragment",
            abstract="Number of tuples per fragment",
            data_type='integer')

        measure = LiteralInput(
            identifier="measure",
            title="Measure",
            abstract="Name of the measure used in the datacube",
            data_type='string')

        measure_type = LiteralInput(
            identifier="measure_type",
            title="Measure type",
            abstract="Type of measures. Possible values are 'double', 'float' or 'int'",
            data_type='string')

        exp_ndim = LiteralInput(
            identifier="exp_ndim",
            title="Exp ndim",
            abstract="Used to specify how many dimensions in dim argument, starting from the first one, must be considered as explicit dimensions",
            data_type='integer')

        dim = LiteralInput(
            identifier="dim",
            title="Dim",
            abstract="Name of the dimension. Multi-value field: list of dimensions separated by '|' can be provided",
            data_type='string')

        concept_level = LiteralInput(
            identifier="concept_level",
            title="Concept Level",
            abstract="Concept level short name (must be a singe char). Default value is 'c'. Multi-value field: list of concept levels separated by '|' can be provided",
            min_occurs=0,
            max_occurs=1,
            default="c",
            data_type='string')

        dim_size = LiteralInput(
            identifier="dim_size",
            title="Dim size",
            abstract="Size of random dimension. Multi-value field: list of dimensions separated by '|' can be provided",
            data_type='string')

        run = LiteralInput(
            identifier="run",
            title="Run",
            abstract="If set to 'no', the operator simulates the creation and computes the fragmentation parameters that would be used else. If set to 'yes', the actual cube creation is executed",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        compressed = LiteralInput(
            identifier="compressed",
            title="Compressed",
            abstract="Two possible values: 'yes' and 'no'.If 'yes', it will save compressed data; if 'no', it will save original data",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Optional argument used to identify the grid of dimensions to be used or the one to be created",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        algorithm = LiteralInput(
            identifier="algorithm",
            title="Algorithm adopted to generate pseudo-random values",
            abstract="It can be used to specify the type of emulation schema used to generate data. By default values are sampled indipendently from a uniform distribution in the range [0, 1000]. If 'temperatures' is used, then values are generated with a first order auto-regressive model to be consistent with temperature values (in Celsius).",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, cwd, container, host_partition, ioserver, nhost, nfrag, ntuple,
            measure, measure_type, exp_ndim, dim, concept_level, dim_size, run, schedule, compressed, grid, description, algorithm]
        outputs = [jobid, response, error]

        super(oph_randcube2, self).__init__(
            self._handler,
            identifier="oph_randcube2",
            title="Ophidia randcube2",
            version=_version,
            abstract="Create a new datacube with random data and dimensions",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_randcube2 '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['host_partition'][0].data is not None:
            query += 'host_partition=' + str(request.inputs['host_partition'][0].data) + ';'
        if request.inputs['ioserver'][0].data is not None:
            query += 'ioserver=' + str(request.inputs['ioserver'][0].data) + ';'
        if request.inputs['nhost'][0].data is not None:
            query += 'nhost=' + str(request.inputs['nhost'][0].data) + ';'
        if request.inputs['run'][0].data is not None:
            query += 'run=' + str(request.inputs['run'][0].data) + ';'
        if request.inputs['concept_level'][0].data is not None:
            query += 'concept_level=' + str(request.inputs['concept_level'][0].data) + ';'
        if request.inputs['compressed'][0].data is not None:
            query += 'compressed=' + str(request.inputs['compressed'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['algorithm'][0].data is not None:
            query += 'algorithm=' + str(request.inputs['algorithm'][0].data) + ';'

        query += 'container=' + str(request.inputs['container'][0].data) + ';'
        query += 'nfrag=' + str(request.inputs['nfrag'][0].data) + ';'
        query += 'ntuple=' + str(request.inputs['ntuple'][0].data) + ';'
        query += 'measure=' + str(request.inputs['measure'][0].data) + ';'
        query += 'measure_type=' + str(request.inputs['measure_type'][0].data) + ';'
        query += 'dim=' + str(request.inputs['dim'][0].data) + ';'
        query += 'exp_ndim=' + str(request.inputs['exp_ndim'][0].data) + ';'
        query += 'dim_size=' + str(request.inputs['dim_size'][0].data) + ';'
        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_reduce(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Grid of dimensions to be used (if the grid already exists) or the one to be created (if the grid has a new name). If it isn't specified, no grid will be used",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        group_size = LiteralInput(
            identifier="group_size",
            title="Group size",
            abstract="Size of the aggregation set. If set to 'all', the reduction will occur on all elements of each tuple",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        operation = LiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the reduction operation. Possible values are count, max, min, avg, sum, std, var, cmoment, acmoment, rmoment, armoment, quantile, arg_max, arg_min",
            data_type='string')

        order = LiteralInput(
            identifier="order",
            title="Order",
            min_occurs=0,
            max_occurs=1,
            default=2,
            data_type='float')

        missingvalue = LiteralInput(
            identifier="missingvalue",
            title="Missing value",
            min_occurs=0,
            max_occurs=1,
            default="NAN",
            data_type='float')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, container, grid, description, schedule, group_size, operation, order, missingvalue]
        outputs = [jobid, response, error]

        super(oph_reduce, self).__init__(
            self._handler,
            identifier="oph_reduce",
            title="Ophidia reduce",
            version=_version,
            abstract="Perform a reduction operation on a datacube with respect to implicit dimensions",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_reduce '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['group_size'][0].data is not None:
            query += 'group_size=' + str(request.inputs['group_size'][0].data) + ';'
        if request.inputs['order'][0].data is not None:
            query += 'order=' + str(request.inputs['order'][0].data) + ';'
        if request.inputs['missingvalue'][0].data is not None:
            query += 'missingvalue=' + str(request.inputs['missingvalue'][0].data) + ';'

        query += 'operation=' + str(request.inputs['operation'][0].data) + ';'
        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_reduce2(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Grid of dimensions to be used (if the grid already exists) or the one to be created (if the grid has a new name). If it isn't specified, no grid will be used",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        dim = LiteralInput(
            identifier="dim",
            title="Dim",
            abstract="Name of dimension on which the operation will be applied",
            data_type='string')

        concept_level = LiteralInput(
            identifier="concept_level",
            title="Concept Level",
            abstract="Concept level inside the hierarchy used for the operation",
            min_occurs=0,
            max_occurs=1,
            default="A",
            data_type='string')

        midnight = LiteralInput(
            identifier="midnight",
            title="Midnight",
            abstract="Possible values are: 00, 24. If 00, the edge point of two consecutive aggregate time sets will be aggregated into the right set; if 24 to the left set",
            min_occurs=0,
            max_occurs=1,
            default="24",
            data_type='string')

        order = LiteralInput(
            identifier="order",
            title="Order",
            abstract="Order used in evaluation of the moments or value of the quantile in range [0,1]",
            min_occurs=0,
            max_occurs=1,
            default=2,
            data_type='float')

        missingvalue = LiteralInput(
            identifier="missingvalue",
            title="Missing value",
            min_occurs=0,
            max_occurs=1,
            default="NAN",
            data_type='float')

        operation = LiteralInput(
            identifier="operation",
            title="Operation",
            abstract="Indicates the reduction operation. Possible values are count, max, min, avg, sum, std, var, cmoment, acmoment, rmoment, armoment, quantile, arg_max, arg_min",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, container, grid, description, schedule, dim, concept_level, midnight, order, missingvalue, operation]
        outputs = [jobid, response, error]

        super(oph_reduce2, self).__init__(
            self._handler,
            identifier="oph_reduce2",
            title="Ophidia reduce2",
            version=_version,
            abstract="Perform a reduction operation based on hierarchy on a datacube",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_reduce2 '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['concept_level'][0].data is not None:
            query += 'concept_level=' + str(request.inputs['concept_level'][0].data) + ';'
        if request.inputs['midnight'][0].data is not None:
            query += 'midnight=' + str(request.inputs['midnight'][0].data) + ';'
        if request.inputs['order'][0].data is not None:
            query += 'order=' + str(request.inputs['order'][0].data) + ';'
        if request.inputs['missingvalue'][0].data is not None:
            query += 'missingvalue=' + str(request.inputs['missingvalue'][0].data) + ';'

        query += 'dim=' + str(request.inputs['dim'][0].data) + ';'
        query += 'operation=' + str(request.inputs['operation'][0].data) + ';'
        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_resume(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        session = LiteralInput(
            identifier="session",
            title="Session",
            abstract="Identifier of the intended session; by default, it is the working session",
            min_occurs=0,
            max_occurs=1,
            default="this",
            data_type='string')

        id = LiteralInput(
            identifier="id",
            title="Id",
            abstract="Identifier of the intended workflow or marker; by default, no filter is applied",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        id_type = LiteralInput(
            identifier="id_type",
            title="Id type",
            abstract="Use 'workflow' (default) or 'marker' to set the filter 'id'",
            min_occurs=0,
            max_occurs=1,
            default="workflow",
            data_type='string')

        document_type = LiteralInput(
            identifier="document_type",
            title="Document type",
            abstract="Document type, 'request' or 'response'",
            min_occurs=0,
            max_occurs=1,
            default="response",
            data_type='string')

        level = LiteralInput(
            identifier="level",
            title="Level",
            abstract="Use level '0' to ask for submitted commands (short version) or workflow progress ratio; Use level '1' to ask for submitted commands (short version) or workflow output; use level '2' to ask for submitted commands (extendend version) or the list of workflow tasks; use level '3' to ask for JSON Requests or the list of workflow task outputs; use level '4' to ask for the list of commands associated to tasks of a workflow (valid only for a specific workflow); use level '5' to ask for original JSON Request (valid only for a specufuc workflow)",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        user = LiteralInput(
            identifier="user",
            title="User",
            abstract="Filter by name of the submitter; by default, no filter is applied. Valid only for workflow list ('id'=0)",
            min_occurs=0,
            max_occurs=1,
            default="",
            data_type='string')

        status_filter = LiteralInput(
            identifier="status_filter",
            title="Status filter",
            abstract="In case of running workflows, filter by job status according some bitmaps",
            min_occurs=0,
            max_occurs=1,
            default=11111111,
            data_type='integer')

        save = LiteralInput(
            identifier="save",
            title="Save",
            abstract="Used to save session identifier on server",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, session, id, id_type, document_type, level, user, status_filter, save]
        outputs = [jobid, response, error]

        super(oph_resume, self).__init__(
            self._handler,
            identifier="oph_resume",
            title="Ophidia resume",
            version=_version,
            abstract="Request the list of the commands submitted within a session or the output of a command",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_resume '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['session'][0].data is not None:
            query += 'session=' + str(request.inputs['session'][0].data) + ';'
        if request.inputs['id'][0].data is not None:
            query += 'id=' + str(request.inputs['id'][0].data) + ';'
        if request.inputs['id_type'][0].data is not None:
            query += 'id_type=' + str(request.inputs['id_type'][0].data) + ';'
        if request.inputs['document_type'][0].data is not None:
            query += 'document_type=' + str(request.inputs['document_type'][0].data) + ';'
        if request.inputs['level'][0].data is not None:
            query += 'level=' + str(request.inputs['level'][0].data) + ';'
        if request.inputs['user'][0].data is not None:
            query += 'user=' + str(request.inputs['user'][0].data) + ';'
        if request.inputs['status_filter'][0].data is not None:
            query += 'status_filter=' + str(request.inputs['status_filter'][0].data) + ';'
        if request.inputs['save'][0].data is not None:
            query += 'save=' + str(request.inputs['save'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_rollup(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        ndim = LiteralInput(
            identifier="ndim",
            title="Number of Implicit Dimensions",
            abstract="Number of explicit dimensions that will be transformed in implicit dimensions",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, schedule, container, description, ndim]
        outputs = [jobid, response, error]

        super(oph_rollup, self).__init__(
            self._handler,
            identifier="oph_rollup",
            title="Ophidia rollup",
            version=_version,
            abstract="Perform a roll-up on a datacube, i.e. it transform dimensions from explicit to implicit",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_rollup '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['ndim'][0].data is not None:
            query += 'ndim=' + str(request.inputs['ndim'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_script(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        script = LiteralInput(
            identifier="script",
            title="Script",
            abstract="Name of the script to be executed; by default no operation is performed. The script has to be registered at server side",
            min_occurs=0,
            max_occurs=1,
            default=":",
            data_type='string')

        args = LiteralInput(
            identifier="args",
            title="Input arguments",
            abstract="List of pipe-separated arguments to be passed to te script",
            min_occurs=0,
            max_occurs=1,
            default="",
            data_type='string')

        stdout = LiteralInput(
            identifier="stdout",
            title="Stdout",
            abstract="File where screen output (stdout) wil be redirected (appended); set to 'stdout' for no redirection",
            min_occurs=0,
            max_occurs=1,
            default="stdout",
            data_type='string')

        stderr = LiteralInput(
            identifier="stderr",
            title="Stderr",
            abstract="File where errors (stderr) will be redirected (appended); set to 'stderr' for no diredirection",
            min_occurs=0,
            max_occurs=1,
            default="stderr",
            data_type='string')

        list = LiteralInput(
            identifier="list",
            title="List",
            abstract="Get the available scripts. You can choose 'yes' or 'no'",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, script, args, stdout, stderr, list]
        outputs = [jobid, response, error]

        super(oph_script, self).__init__(
            self._handler,
            identifier="oph_script",
            title="Ophidia script",
            version=_version,
            abstract="Execute a bash script",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_script '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['script'][0].data is not None:
            query += 'script=' + str(request.inputs['script'][0].data) + ';'
        if request.inputs['args'][0].data is not None:
            query += 'args=' + str(request.inputs['args'][0].data) + ';'
        if request.inputs['stdout'][0].data is not None:
            query += 'stdout=' + str(request.inputs['stdout'][0].data) + ';'
        if request.inputs['stderr'][0].data is not None:
            query += 'stderr=' + str(request.inputs['stderr'][0].data) + ';'
        if request.inputs['list'][0].data is not None:
            query += 'list=' + str(request.inputs['list'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query")
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_search(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        container_filter = LiteralInput(
            identifier="container_filter",
            title="Container filter",
            abstract="Zero, one or more filters on container's names. Filters separated by '|'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        metadata_key_filter = LiteralInput(
            identifier="metadata_key_filter",
            title="Metadata key filter",
            abstract="Zero, one or more filters on metadata keys. Filters separated by '|'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        metadata_value_filter = LiteralInput(
            identifier="metadata_value_filter",
            title="Metadata value filter",
            abstract="Zero, one or more filters on metadata values. Filters separated by '|'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        path = LiteralInput(
            identifier="pathr",
            title="Path",
            abstract="Abslolute/relative path used as the starting point of the recursive search. If not specified or in case of '-' (default), the recursive search will start at the cwd",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, necessary to correctly parse paths. ALl resolved paths must be associated to the calling session",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, container_filter, metadata_key_filter, metadata_value_filter, path, cwd]
        outputs = [jobid, response, error]

        super(oph_search, self).__init__(
            self._handler,
            identifier="oph_search",
            title="Ophidia search",
            version=_version,
            abstract="Provide enhanced searching on metadata",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_search '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['container_filter'][0].data is not None:
            query += 'container_filter=' + str(request.inputs['container_filter'][0].data) + ';'
        if request.inputs['metadata_key_filter'][0].data is not None:
            query += 'metadata_key_filter=' + str(request.inputs['metadata_key_filter'][0].data) + ';'
        if request.inputs['metadata_value_filter'][0].data is not None:
            query += 'metadata_value_filter=' + str(request.inputs['metadata_value_filter'][0].data) + ';'
        if request.inputs['path'][0].data is not None:
            query += 'path=' + str(request.inputs['path'][0].data) + ';'

        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_service(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        state = LiteralInput(
            identifier="status",
            title="Status",
            abstract="New service status, 'up' or 'down'",
            min_occurs=0,
            max_occurs=1,
            default="",
            data_type='string')

        level = LiteralInput(
            identifier="level",
            title="Level",
            abstract="Use level '1' (default) to ask for service status only; use level '2' to ask for job list",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, state, level]
        outputs = [jobid, response, error]

        super(oph_service, self).__init__(
            self._handler,
            identifier="oph_service",
            title="Ophidia service",
            version=_version,
            abstract="Request or set the service status",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_service '
        if request.inputs['state'][0].data is not None:
            query += 'status=' + str(request.inputs['state'][0].data) + ';'
        if request.inputs['level'][0].data is not None:
            query += 'level=' + str(request.inputs['level'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_set(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Set to 'yes' in case 'value' is an index array and subset string has to be stored on behalf of the list of numbers; use 'real' in case 'value' contains real numbers",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        offset = LiteralInput(
            identifier="offset",
            title="Offset",
            abstract="Expected difference between two consecutive items of input array in case subset strings have to be evaluated; by default, it will se to '1'",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='float')

        id = LiteralInput(
            identifier="id",
            title="Id",
            abstract="Workflow identifier. By default the hosting workflow is selected. The target workflow must have been subitted the same session. Default value is @OPH_WORKFLOW_ID",
            min_occurs=0,
            max_occurs=1,
            default='@OPH_WORKFLOW_ID',
            data_type='integer')

        key = LiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the parameter",
            data_type='string')

        value = LiteralInput(
            identifier="value",
            title="Value",
            abstract="Value of the parameter. By default it will set to 1",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, subset_filter, offset, id, key, value]
        outputs = [jobid, response, error]

        super(oph_set, self).__init__(
            self._handler,
            identifier="oph_set",
            title="Ophidia set",
            version=_version,
            abstract="Set parameters in the workflow environment",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_set '
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['id'][0].data is not None:
            query += 'id=' + str(request.inputs['id'][0].data) + ';'
        if request.inputs['value'][0].data is not None:
            query += 'value=' + str(request.inputs['value'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['offset'][0].data is not None:
            query += 'offset=' + str(request.inputs['offset'][0].data) + ';'

        query += 'key=' + str(request.inputs['key'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_showgrid(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Input container",
            abstract="Name of the input container",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Name of the grid to visualize. With no name, all grids are shown",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        dim = LiteralInput(
            identifier="dim",
            title="Dimension name",
            abstract="Name of dimension to visualize. Multiple-value field: list of dimensions separated by '|' can be provided. If not specified, all dimensions are shown",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        show_index = LiteralInput(
            identifier="show_index",
            title="Show index",
            abstract="If 'no' (default), it won't show dimension ids. With 'yes', it will also show the dimension id next to the value",
            min_occurs=0,
            max_occurs=1,
            default="no",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, necessary to correctly parse paths. ALl resolved paths must be associated to the calling session",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, container, grid, dim, show_index, cwd]
        outputs = [jobid, response, error]

        super(oph_showgrid, self).__init__(
            self._handler,
            identifier="oph_showgrid",
            title="Ophidia showgrid",
            version=_version,
            abstract="Show information about one or more grids related to the specified container",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_showgrid '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['dim'][0].data is not None:
            query += 'dim=' + str(request.inputs['dim'][0].data) + ';'
        if request.inputs['show_index'][0].data is not None:
            query += 'show_index=' + str(request.inputs['show_index'][0].data) + ';'

        query += 'container=' + str(request.inputs['container'][0].data) + ';'
        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_split(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        nthreads = LiteralInput(
            identifier="nthreads",
            title="Number of threads",
            abstract="Number of parallel threads per process to be used",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        nsplit = LiteralInput(
            identifier="nsplit",
            title="Nsplit",
            abstract="Number of output fragments per input fragment",
            data_type='integer')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, nthreads, exec_mode, sessionid, pid, container, nsplit, description, schedule]
        outputs = [jobid, response, error]

        super(oph_split, self).__init__(
            self._handler,
            identifier="oph_split",
            title="Ophidia split",
            version=_version,
            abstract="Create a new datacube by splitting input fragments in nsplit output fragments in the same origin database",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_split '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['nthreads'][0].data is not None:
            query += 'nthreads=' + str(request.inputs['nthreads'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['nsplit'][0].data is not None:
            query += 'nsplit=' + str(request.inputs['nsplit'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_subset(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Grid of dimensions to be used (if the grid already exists) or the one to be created (if the grid has a new name). If it isn't specified, no grid will be used",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        subset_type = LiteralInput(
            identifier="subset_type",
            title="Subset Type",
            abstract="Possibile values are: index, coord",
            min_occurs=0,
            max_occurs=1,
            default="index",
            data_type='string')

        time_filter = LiteralInput(
            identifier="time_filter",
            title="Time Filter",
            abstract="Possibile values are: yes, no",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        offset = LiteralInput(
            identifier="offset",
            title="Offset",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, container, grid, subset_dims, subset_filter, description, schedule, subset_type, time_filter, offset]
        outputs = [jobid, response, error]

        super(oph_subset, self).__init__(
            self._handler,
            identifier="oph_subset",
            title="Ophidia subset",
            version=_version,
            abstract="Subset a cube",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_subset '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['subset_type'][0].data is not None:
            query += 'subset_type=' + str(request.inputs['subset_type'][0].data) + ';'
        if request.inputs['time_filter'][0].data is not None:
            query += 'time_filter=' + str(request.inputs['time_filter'][0].data) + ';'
        if request.inputs['offset'][0].data is not None:
            query += 'offset=' + str(request.inputs['offset'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_subset2(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Output container",
            abstract="PID of the container to be used to store the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        grid = LiteralInput(
            identifier="grid",
            title="Grid name",
            abstract="Grid of dimensions to be used (if the grid already exists) or the one to be created (if the grid has a new name). If it isn't specified, no grid will be used",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        subset_dims = LiteralInput(
            identifier="subset_dims",
            title="Dimension names",
            abstract="Dimension names of the cube used for the subsetting",
            min_occurs=0,
            max_occurs=1,
            default="none",
            data_type='string')

        subset_filter = LiteralInput(
            identifier="subset_filter",
            title="Subsetting filter",
            abstract="Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        description = LiteralInput(
            identifier="description",
            title="Output description",
            abstract="Additional description to be associated with the output cube",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        schedule = LiteralInput(
            identifier="schedule",
            title="Schedule",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='integer')

        time_filter = LiteralInput(
            identifier="time_filter",
            title="Time Filter",
            abstract="Possibile values are: yes, no",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        offset = LiteralInput(
            identifier="offset",
            title="Offset",
            abstract="It is added to the bounds of subset intervals defined with 'subset_filter' in case of 'coord' filter type is used",
            min_occurs=0,
            max_occurs=1,
            default=0,
            data_type='float')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid, container, grid, subset_dims, subset_filter, description, schedule, time_filter, offset]
        outputs = [jobid, response, error]

        super(oph_subset2, self).__init__(
            self._handler,
            identifier="oph_subset2",
            title="Ophidia subset2",
            version=_version,
            abstract="Perform a subsetting along dimensions of a datacube; dimension values are used as input filters",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_subset2 '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['schedule'][0].data is not None:
            query += 'schedule=' + str(request.inputs['schedule'][0].data) + ';'
        if request.inputs['subset_dims'][0].data is not None:
            query += 'subset_dims=' + str(request.inputs['subset_dims'][0].data) + ';'
        if request.inputs['subset_filter'][0].data is not None:
            query += 'subset_filter=' + str(request.inputs['subset_filter'][0].data) + ';'
        if request.inputs['grid'][0].data is not None:
            query += 'grid=' + str(request.inputs['grid'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['description'][0].data is not None:
            query += 'description=' + str(request.inputs['description'][0].data) + ';'
        if request.inputs['time_filter'][0].data is not None:
            query += 'time_filter=' + str(request.inputs['time_filter'][0].data) + ';'
        if request.inputs['offset'][0].data is not None:
            query += 'offset=' + str(request.inputs['offset'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_tasks(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        cube_filter = LiteralInput(
            identifier="cube_filter",
            title="Cube filter",
            abstract="Optional filter on the name of input/output datacubes. The name must be in PID format. Default value is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        operator_filter = LiteralInput(
            identifier="operator_filter",
            title="Operator filter",
            abstract="Optional filter on the name of the operators implied in tasks. Default value is 'all'",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        path = LiteralInput(
            identifier="pathr",
            title="Path",
            abstract="Optional filter of abslolute/relative path. Path is expanded so it can also contain '.' and '..'. It is only cnsidered when container_filter is specified",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        cwd = LiteralInput(
            identifier="cwd",
            title="Absolute path of the current working directory",
            abstract="Absolute path corresponding to the current working directory, necessary to correctly parse paths. ALl resolved paths must be associated to the calling session",
            data_type='string')

        container = LiteralInput(
            identifier="container",
            title="Input container",
            abstract="Name of the input container",
            min_occurs=0,
            max_occurs=1,
            default="all",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, cube_filter, operator_filter, path, cwd, container]
        outputs = [jobid, response, error]

        super(oph_tasks, self).__init__(
            self._handler,
            identifier="oph_tasks",
            title="Ophidia tasks",
            version=_version,
            abstract="Show information about executed tasks; default arguments allow to show all the tasks executed; if a container is given, then only tasks that involve the container as shown",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_tasks '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['container'][0].data is not None:
            query += 'container=' + str(request.inputs['container'][0].data) + ';'
        if request.inputs['cube_filter'][0].data is not None:
            query += 'cube_filter=' + str(request.inputs['cube_filter'][0].data) + ';'
        if request.inputs['operator_filter'][0].data is not None:
            query += 'operator_filter=' + str(request.inputs['operator_filter'][0].data) + ';'
        if request.inputs['path'][0].data is not None:
            query += 'path=' + str(request.inputs['path'][0].data) + ';'

        query += 'cwd=' + str(request.inputs['cwd'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_unpublish(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        sessionid = LiteralInput(
            identifier="sessionid",
            title="Session identifier",
            min_occurs=0,
            max_occurs=1,
            default="null",
            data_type='string')

        pid = LiteralInput(
            identifier="cube",
            title="Input cube",
            abstract="Name of the input datacube in PID format",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, sessionid, pid]
        outputs = [jobid, response, error]

        super(oph_unpublish, self).__init__(
            self._handler,
            identifier="oph_unpublish",
            title="Ophidia unpublish",
            version=_version,
            abstract="Remove the HTML pages created by the PUBLISH2 operator; note that it doesn't remove the container folder",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_unpublish '
        if request.inputs['sessionid'][0].data is not None:
            query += 'sessionid=' + str(request.inputs['sessionid'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'

        query += 'cube=' + str(request.inputs['cube'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response


class oph_wait(Process):

    def __init__(self):

        inputs = []
        outputs = []

        userid = LiteralInput(
            identifier="userid",
            title="Username",
            abstract="User identifier for Ophidia system",
            data_type='string')

        passwd = LiteralInput(
            identifier="passwd",
            title="Password",
            abstract="Password to access Ophidia",
            data_type='string')

        ncores = LiteralInput(
            identifier="ncores",
            title="Number of cores",
            min_occurs=0,
            max_occurs=1,
            default=1,
            data_type='integer')

        exec_mode = LiteralInput(
            identifier="exec_mode",
            title="Execution mode",
            abstract="Possible values are async (default) for asynchronous mode, sync for synchronous mode",
            min_occurs=0,
            max_occurs=1,
            default="async",
            data_type='string')

        type = LiteralInput(
            identifier="type",
            title="Type",
            abstract="Waiting type. Use: 'clock' for fixed time; 'inpit' to ask to input data and set a new 'value' for 'key'; 'file' to check the existence of a file",
            min_occurs=0,
            max_occurs=1,
            default="clock",
            data_type='string')

        timeout = LiteralInput(
            identifier="timeout",
            title="Timeout",
            abstract="According to the value of parameter 'timeout_type', it is the duration (in seconds) or the end instant of the waiting interval",
            min_occurs=0,
            max_occurs=1,
            default=-1,
            data_type='integer')

        timeout_type = LiteralInput(
            identifier="timeout_type",
            title="Timeout type",
            abstract="Meaning the value of 'timeout'. Use 'duration' to set the duration of waiting interval; 'deadline' to set the end time instant of waiting interval",
            min_occurs=0,
            max_occurs=1,
            default="duration",
            data_type='string')

        key = LiteralInput(
            identifier="key",
            title="Key",
            abstract="Name of the parameter",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        value = LiteralInput(
            identifier="value",
            title="Value",
            abstract="Value of the parameter. By default it will set to 1",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        filename = LiteralInput(
            identifier="filename",
            title="Filename",
            abstract="Name of the file to be checked (only for type 'file'); base folder to refer files in BASE_SRC_PATH",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        message = LiteralInput(
            identifier="message",
            title="Message",
            abstract="This user-defined message is appended to response in order to notify the waiting reason",
            min_occurs=0,
            max_occurs=1,
            default="-",
            data_type='string')

        run = LiteralInput(
            identifier="run",
            title="Run",
            abstract="Set to 'yes' (default) to wait effectively",
            min_occurs=0,
            max_occurs=1,
            default="yes",
            data_type='string')

        jobid = LiteralOutput(
            identifier="jobid",
            title="Ophidia JobID",
            data_type='string')

        response = ComplexOutput(
            identifier="response",
            title="JSON Response",
            supported_formats=[Format('text/json', encoding='base64'), Format('text/plain', encoding='utf-8')])

        error = LiteralOutput(
            identifier="return",
            title="Return code",
            data_type='integer')

        inputs = [userid, passwd, ncores, exec_mode, type, timeout, timeout_type, key, value, filename, message, run]
        outputs = [jobid, response, error]

        super(oph_wait, self).__init__(
            self._handler,
            identifier="oph_wait",
            title="Ophidia wait",
            version=_version,
            abstract="Wait until an event occurs; the task can be unlocked by means of the command 'OPH_INPUT'",
            inputs=inputs,
            outputs=outputs,
            store_supported=True,
            status_supported=True
        )

    def _handler(self, request, response):

        response.update_status("Pre-processing", 1)

        response.outputs['jobid'].data = ""
        response.outputs['response'].data = ""
        response.outputs['return'].data = 1

        response.update_status("Running", 2)

        LOGGER.debug("Build the query")
        query = 'oph_wait '
        if request.inputs['type'][0].data is not None:
            query += 'type=' + str(request.inputs['type'][0].data) + ';'
        if request.inputs['exec_mode'][0].data is not None:
            query += 'exec_mode=' + str(request.inputs['exec_mode'][0].data) + ';'
        if request.inputs['timeout'][0].data is not None:
            query += 'timeout=' + str(request.inputs['timeout'][0].data) + ';'
        if request.inputs['timeout_type'][0].data is not None:
            query += 'timeout_type=' + str(request.inputs['timeout_type'][0].data) + ';'
        if request.inputs['key'][0].data is not None:
            query += 'key=' + str(request.inputs['key'][0].data) + ';'
        if request.inputs['value'][0].data is not None:
            query += 'value=' + str(request.inputs['value'][0].data) + ';'
        if request.inputs['filename'][0].data is not None:
            query += 'filename=' + str(request.inputs['filename'][0].data) + ';'
        if request.inputs['message'][0].data is not None:
            query += 'message=' + str(request.inputs['message'][0].data) + ';'
        if request.inputs['run'][0].data is not None:
            query += 'run=' + str(request.inputs['run'][0].data) + ';'
        if request.inputs['ncores'][0].data is not None:
            query += 'ncores=' + str(request.inputs['ncores'][0].data) + ';'

        LOGGER.debug("Create Ophidia client")
        oph_client = _client.Client(request.inputs['userid'][0].data, request.inputs['passwd'][0].data, _host, _port)
        oph_client.api_mode = False

        LOGGER.debug("Submit the query: " + query)
        oph_client.submit(query)

        LOGGER.debug("Get the return values")
        response = oph_client.last_response
        jobid = oph_client.last_jobid
        return_value = oph_client.last_return_value
        error = oph_client.last_error

        LOGGER.debug("Return value: %s" % return_value)
        LOGGER.debug("JobID: %s" % jobid)
        LOGGER.debug("Response: %s" % response)
        LOGGER.debug("Error message: %s" % error)

        response.update_status("Post-processing", 99)

        response.outputs['return'].data = return_value
        if return_value == 0:
            if jobid is not None:
                response.outputs['jobid'].data = jobid
            if request.inputs['exec_mode'][0].data == "sync" and len(buffer) > 0:
                response.outputs['response'].data = buffer

        response.update_status("Succeded", 100)

        return response
