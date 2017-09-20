# Ophidia WPS Module

### Description

WPS module is a Python package enabling a WPS interface for Ophidia Server.

It implements a process for PyWPS - Python Web Processing Service (http://pywps.org/), which translates WPS Requests into JSON Requests for Ophidia Web Service and, vice versa, replies to WPS clients with WPS Responses encapsulating the releted JSON Responses.

### Requirements

This software requires Python 2.6, PyOphidia and PyWPS 3.2.4 - Python Web Processing Service (http://pywps.org/), which can be built from sources provided that the following packages are installed:

- libxml2-devel
- libxslt-devel

It is recommended to start the service as module of Apache web server (https://www.apache.org/), so that TLS could be exploited to encrypt Ophidia credentials coded in WPS Requests. In this case, the following packages are required

- python-lxml
- python-setuptools
- mod_ssl

and *mod_python* from http://modpython.org/. This module requires

- python-devel
- httpd-devel

### How to install

Download PyWPS 3.2.4 from https://github.com/geopython/pywps/archive/pywps-3.2.4.tar.gz into */usr/local/ophidia/extra/src/pywps/*.

```
$ mkdir -p /usr/local/ophidia/extra/src
$ cd /usr/local/ophidia/extra/src
$ wget https://github.com/geopython/pywps/archive/pywps-3.2.4.tar.gz
$ tar xzf /usr/local/ophidia/extra/src/pywps-3.2.4.tar.gz
$ mv /usr/local/ophidia/extra/src/pywps-pywps-3.2.4 /usr/local/ophidia/extra/src/pywps
```

Replace the main Python script */usr/local/ophidia/extra/src/pywps/wps.py* with the script */usr/local/ophidia/extra/src/pywps/webservices/mod_python/wps.py* adapted for mod_python and, then, install PyWPS (see section below for known issues).

```
$ cd /usr/local/ophidia/extra/src/pywps
$ cp -f /usr/local/ophidia/extra/src/pywps/webservices/mod_python/wps.py /usr/local/ophidia/extra/src/pywps
$ sudo python setup.py install
```

Create a folder */usr/local/ophidia/extra/wps* and copy both the folders *processes* and *etc* inside:

```
$ mkdir -p /usr/local/ophidia/extra/src
$ cd /usr/local/ophidia/extra/src
$ git clone https://github.com/OphidiaBigData/ophidia-wps-module.git
$ mkdir -p /usr/local/ophidia/extra/wps
$ cp -R /usr/local/ophidia/extra/src/ophidia-wps-module/processes /usr/local/ophidia/extra/wps/
$ cp -R /usr/local/ophidia/extra/src/ophidia-wps-module/etc /usr/local/ophidia/extra/wps/
```

Install and configure mod_python by cloning it from https://github.com/grisha/mod_python.git. The following command list should be enough:

```
$ mkdir -p /usr/local/ophidia/extra/src
$ git clone https://github.com/grisha/mod_python.git
$ cd /usr/local/ophidia/extra/src/mod_python
$ ./configure
$ make
$ sudo make install
```

Create the folder */var/www/wps*, configure mod_python for Apache, by saving the following specification in */etc/httpd/conf.d/python.conf*, and restart the service:

	LoadModule python_module modules/mod_python.so
	Alias /wps "/var/www/wps"
	<Directory "/var/www/wps">
		AllowOverride None
		Order allow,deny
		Allow from all
		SetEnv PYWPS_PROCESSES /usr/local/ophidia/extra/wps/processes/
		SetEnv PYWPS_CFG /usr/local/ophidia/extra/wps/etc/pywps.cfg
		SetHandler python-program
		PythonHandler wps
		PythonAuthenHandler wps
		PythonDebug On
		PythonPath "sys.path+['/usr/local/ophidia/extra/src/pywps/']"
		PythonAutoReload On
	</Directory>

By default it is assumed that Ophidia Server is running on the same node where PyWPS works and listening to port 11732. Otherwise, change service address (IP address and port number) by editing */usr/local/ophidia/extra/wps/processes/ophidia.py*.

Create the folders for PyWPS log file and WPS Responses (based on parameters set in */usr/local/ophidia/extra/wps/etc/pywps.cfg*):

```
$ sudo mkdir -p /var/www/html/wpsoutputs
$ sudo mkdir -p /var/log/wps
$ sudo chown root:apache /var/www/html/wpsoutputs
$ sudo chmod 775 /var/www/html/wpsoutputs
$ sudo chown root:apache /var/log/wps
$ sudo chmod 775 /var/log/wps
```

Install PyOphidia as follows:

```
$ sudo pip install PyOphidia
```

Finally, enable Apache to open new connections in case SELinux is enabled as follows:

```
$ sudo setsebool -P httpd_can_network_connect on
```

and restart the web server.

If PyWPS runs as an extension of Apache, default port to access Ophidia WPS is 443.

Further information can be found at [http://ophidia.cmcc.it/documentation](http://ophidia.cmcc.it/documentation).

### Test

Check the WPS interface by sending the requests "GetCababilities" and "DescribeProcess" as follows:

```
curl -k https://server.hostname/wps/?service=WPS&version=1.0.0&request=getcapabilities
curl -k https://server.hostname/wps/?service=WPS&version=1.0.0&request=describeprocess&identifier=ophexecutemain
```

Requested resources are XML documents with a number of details about the service and the process *ophexecutemain*.

### Known problems

In case Apache returns the following error:

	Traceback (most recent call last):
	  File "/usr/local/ophidia/extra/src/pywps/wps.py", line 75, in handler
	    wps.parser.isSoap, self.wps.parser.isSoapExecute,contentType = wps.request.contentType)
	NameError: global name 'self' is not defined

delete the prefix *self.* in */usr/local/ophidia/extra/src/pywps/wps.py*.

