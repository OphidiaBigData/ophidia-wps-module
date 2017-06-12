#
#    Ophidia WPS Module
#    Copyright (C) 2015-2016 CMCC Foundation
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

class OphExecuteMainProcess(WPSProcess):

    def __init__(self):
        WPSProcess.__init__(
            self,
            identifier="ophexecutemain", 
            title="Ophidia",
            version = "1.0.0",
            metadata = [],
            abstract="Submit a command to Ophidia",
            storeSupported = True,
            statusSupported = True)

	self.request = self.addComplexInput(
            identifier = "request",
            title = "JSON Request",
            formats = [{"mimeType":"text/json", "encoding": "base64"},{"mimeType":"text/plain", "encoding": "utf-8"}],
            metadata = [],
            maxmegabites = 1)

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
        
        self.jobid = self.addLiteralOutput(
            identifier = "jobid",
            title = "Ophidia JobID",
            type = type(''))

	self.response = self.addComplexOutput(
            identifier = "response",
            title = "JSON Response",
            metadata = [],
            formats = [{"mimeType":"text/json", "encoding": "base64"},{"mimeType":"text/plain", "encoding": "utf-8"}])

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
	buffer, jobid, return_value, error = _ophsubmit.submit(self.userid.getValue(), self.passwd.getValue(), "127.0.0.1", 11732, buffer)

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

