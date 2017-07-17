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
import ophsubmit as _ophsubmit

_host = "127.0.0.1"
_port = 11732

class OphExecuteMainProcess(WPSProcess):

	def __init__(self):
		WPSProcess.__init__(
			self,
			identifier="ophexecutemain", 
			title="Ophidia",
			version = "1.0.0",
			metadata = [],
			abstract = "Submit a generic workflow",
			storeSupported = True,
			statusSupported = True)

		self.userid = self.addLiteralInput(
			identifier = "userid",
			title = "Username",
			abstract = "User identifier for Ophidia system",
			type = type(''))

		self.passwd = self.addLiteralInput(
			identifier = "passwd",
			title = "Password",
			abstract = "Password to access Ophidia",
			type = type(''))

		self.request = self.addComplexInput(
			identifier = "request",
			title = "JSON Request",
			formats = [{"mimeType":"text/json", "encoding": "base64"}, {"mimeType":"text/plain", "encoding": "utf-8"}],
			metadata = [],
			maxmegabites = 1)

		self.jobid = self.addLiteralOutput(
			identifier = "jobid",
			title = "Ophidia JobID",
			type = type(''))

		self.response = self.addComplexOutput(
			identifier = "response",
			title = "JSON Response",
			metadata = [],
			formats = [{"mimeType":"text/json", "encoding": "base64"}, {"mimeType":"text/plain", "encoding": "utf-8"}])

		self.error = self.addLiteralOutput(
            identifier = "return",
            title = "Return code",
            type = type(1))

	def execute(self):
		self.status.set("Pre-processing",1)
		logging.debug("Incoming a request with format %s" % self.request.format)

		self.error.setValue(1)
		self.jobid.setValue("")
		self.response.format = self.request.format

		logging.debug("Building request for oph_server")
		file = open(self.request.getValue(),'r')
		buffer = file.read()
		file.close()

		if self.request.format["encoding"] == "base64":
			logging.debug("Decoding request")
			buffer = buffer.decode("base64")

		logging.debug("Request: %s" % buffer)

		self.status.set("Running",2)
		logging.debug("Execute the job")
		buffer, jobid, return_value, error = _ophsubmit.submit(self.userid.getValue(), self.passwd.getValue(), _host, _port, buffer)

		logging.debug("Return value: %s" % return_value)
		logging.debug("JobID: %s" % jobid)
		logging.debug("Response: %s" % buffer)
		logging.debug("Error message: %s" % error)

		self.status.set("Post-processing",98)
		if return_value == 0 and len(buffer) > 0 and self.request.format["encoding"] == "base64":
			logging.debug("Encoding response")
			buffer = buffer.encode("base64")

		self.status.set("Outputting",99)
		output = StringIO.StringIO()
		self.error.setValue(return_value)
		if return_value == 0:
			if jobid is not None:
				self.jobid.setValue(jobid)
			if len(buffer) > 0:
				output.write(buffer)
		self.response.setValue(output)

		self.status.set("Succeded",100)


class oph_subset(WPSProcess):

	def __init__(self):
		WPSProcess.__init__(
			self,
			identifier="oph_subset", 
			title="Ophidia",
			version = "1.0.0",
			metadata = [],
			abstract = "Subset a cube",
			storeSupported = True,
			statusSupported = True)

		self.userid = self.addLiteralInput(
			identifier = "userid",
			title = "Username",
			abstract = "User identifier for Ophidia system",
			type = type(''))

		self.passwd = self.addLiteralInput(
			identifier = "passwd",
			title = "Password",
			abstract = "Password to access Ophidia",
			type = type(''))

		self.ncores = self.addLiteralInput(
            identifier = "ncores",
            title = "Number of cores",
			minOccurs = 0,
			maxOccurs = 1,
			default = 1,
            type = type(1))

		self.exec_mode = self.addLiteralInput(
			identifier = "exec_mode",
			title = "Execution mode",
			abstract = "Possible values are async (default) for asynchronous mode, sync for synchronous mode",
			minOccurs = 0,
			maxOccurs = 1,
			default = "async",
			type = type(''))

		self.sessionid = self.addLiteralInput(
			identifier = "sessionid",
			title = "Session identifier",
			type = type(''))

		self.cwd = self.addLiteralInput(
			identifier = "cwd",
			title = "Current working directory",
			minOccurs = 0,
			maxOccurs = 1,
			default = "/",
			type = type(''))

		self.cube = self.addLiteralInput(
			identifier = "cube",
			title = "Input cube",
			abstract = "Name of the input datacube in PID format",
			type = type(''))

		self.container = self.addLiteralInput(
			identifier = "container",
			title = "Output container",
			abstract = "PID of the container to be used to store the output cube",
			minOccurs = 0,
			maxOccurs = 1,
			default = "-",
			type = type(''))

		self.grid = self.addLiteralInput(
			identifier = "grid",
			title = "Grid name",
			abstract = "Grid of dimensions to be used (if the grid already exists) or the one to be created (if the grid has a new name). If it isn't specified, no grid will be used",
			minOccurs = 0,
			maxOccurs = 1,
			default = "-",
			type = type(''))

		self.subset_dims = self.addLiteralInput(
			identifier = "subset_dims",
			title = "Dimension names",
			abstract = "Dimension names of the datacube used for the subsetting",
			minOccurs = 0,
			maxOccurs = 1,
			default = "none",
			type = type(''))

		self.subset_filter = self.addLiteralInput(
			identifier = "subset_filter",
			title = "Subsetting filter",
			abstract = "Enumeration of comma-separated elementary filters (1 series of filters for each dimension)",
			minOccurs = 0,
			maxOccurs = 1,
			default = "all",
			type = type(''))

		self.description = self.addLiteralInput(
			identifier = "description",
			title = "Output description",
			abstract = "Additional description to be associated with the output cube",
			minOccurs = 0,
			maxOccurs = 1,
			default = "-",
			type = type(''))

		self.schedule = self.addLiteralInput(
            identifier = "schedule",
            title = "Schedule",
			minOccurs = 0,
			maxOccurs = 1,
			default = "0",
            type = type(1))

		self.jobid = self.addLiteralOutput(
			identifier = "jobid",
			title = "Ophidia JobID",
			type = type(''))

		self.response = self.addComplexOutput(
			identifier = "response",
			title = "JSON Response",
			metadata = [],
			formats = [{"mimeType":"text/json", "encoding": "base64"}])

		self.error = self.addLiteralOutput(
            identifier = "return",
            title = "Return code",
            type = type(1))

	def execute(self):

		operator = self.identifier

		self.status.set("Pre-processing",1)

		self.error.setValue(1)
		self.jobid.setValue("")

		logging.debug("Building request for oph_server")

		buffer = '{'
		buffer += '"name": "' + operator + '",'
		buffer += '"author": "' + self.userid.getValue() +  '",'
		buffer += '"abstract": "Workflow generated by Ophidia WPS module to wrap a command",'
		buffer += '"command": "' + operator + '",'
		buffer += '"ncores": "' + str(self.ncores.getValue()) + '",'
		buffer += '"exec_mode": "' + self.exec_mode.getValue() + '",'
		buffer += '"sessionid": "' + self.sessionid.getValue() +  '",'
		buffer += '"cwd": "' + self.cwd.getValue() +  '",'
		buffer += '"cube": "' + self.cube.getValue() + '",'
		buffer += '"tasks": ['
		buffer += '{'
		buffer += '"name": "Task 0",'
		buffer += '"operator": "' + operator + '",'
		buffer += '"arguments": ['
		buffer += '"container=' + self.container.getValue() + '",'
		buffer += '"grid=' + self.container.getValue() + '",'
		buffer += '"subset_dims=' + self.subset_dims.getValue() + '",'
		buffer += '"subset_filter=' + self.subset_filter.getValue() + '",'
		buffer += '"description=' + self.description.getValue() + '",'
		buffer += '"schedule=' + str(self.schedule.getValue()) + '"'
		buffer += ']'
		buffer += '}'
		buffer += ']'
		buffer += '}'

		logging.debug("Request: %s" % buffer)

		self.status.set("Running",2)
		logging.debug("Execute the job")
		buffer, jobid, return_value, error = _ophsubmit.submit(self.userid.getValue(), self.passwd.getValue(), _host, _port, buffer)

		logging.debug("Return value: %s" % return_value)
		logging.debug("JobID: %s" % jobid)
		logging.debug("Response: %s" % buffer)
		logging.debug("Error message: %s" % error)

		self.status.set("Post-processing",98)
		if return_value == 0 and self.exec_mode.getValue() == "sync" and len(buffer) > 0:
			logging.debug("Encoding response")
			buffer = buffer.encode("base64")

		self.status.set("Outputting",99)
		output = StringIO.StringIO()
		self.error.setValue(return_value)
		if return_value == 0:
			if jobid is not None:
				self.jobid.setValue(jobid)
			if self.exec_mode.getValue() == "sync" and len(buffer) > 0:
				output.write(buffer)
		self.response.setValue(output)

		self.status.set("Succeded",100)

