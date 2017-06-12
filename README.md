# Ophidia WPS Module

### Description

WPS module is a Python package enabling a WPS interface for Ophidia Server.

It implements a process for PyWPS - Python Web Processing Service (http://pywps.org/), which translates WPS Requests into JSON Requests for Ophidia Web Service and, vice versa, replies to WPS clients with WPS Responses encapsulating the releted JSON Responses.

### Requirements

This software requires Python 2.6 and PyWPS 3.2.4 - Python Web Processing Service (http://pywps.org/), which can be built from sources provided that the following packages are installed:

- limxml2-devel
- libxslt-devel

It is recommended to start the service as module of Apache web server (https://www.apache.org/), so that TLS could be exploited to encrypt Ophidia credentials coded in WPS Requests. In this case, the following packages are required

- python-lxml
- python-setuptools
- mod_ssl

and *mod_python* from http://modpython.org/. This module requires

- python-devel
- httpd-devel

### How to install

Download PyWPS 3.2.4 from https://github.com/geopython/pywps/archive/pywps-3.2.4.tar.gz into */usr/local/ophidia/extra/src/pywps/* and install it.

```
$ mkdir -p /usr/local/ophidia/extra/src/
$ cd /usr/local/ophidia/extra/src/
$ wget https://github.com/geopython/pywps/archive/pywps-3.2.4.tar.gz
$ tar xzf pywps-3.2.4.tar.gz
$ mv pywps-pywps-3.2.4 pywps
$ cd pywps
$ cp /usr/local/ophidia/extra/src/pywps/webservices/mod_python/wps.py .
$ sudo python setup.py install
```

Create a folder */usr/local/ophidia/extra/wps* and copy both the folders *processes* and *etc* inside:

```
$ mkdir -p /usr/local/ophidia/extra/wps
$ cp -R processes /usr/local/ophidia/extra/wps/
$ cp -R etc /usr/local/ophidia/extra/wps/
```

Install and configure mod_python by cloning it from https://github.com/grisha/mod_python.git. The following command list should be enough:

```
$ ./configure
$ make
$ sudo make install

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
$ mkdir -p /var/www/html/wpsoutputs
$ mkdir -p /var/log/wps
$ chown root:apache /var/www/html/wpsoutputs
$ chmod 775 /var/www/html/wpsoutputs
$ chown root:apache /var/log/wps
$ chmod 775 /var/log/wps
```

Finally, enable Apache to open new connections in case SELinux is enabled as follows:

```
$ sudo setsebool -P httpd_can_network_connect on
```

and restart the web server.

Further information can be found at [http://ophidia.cmcc.it/documentation](http://ophidia.cmcc.it/documentation).

### Known problems

In case Apache returns the following error:

	Traceback (most recent call last):
	  File "/usr/local/ophidia/extra/src/pywps/wps.py", line 75, in handler
	    wps.parser.isSoap, self.wps.parser.isSoapExecute,contentType = wps.request.contentType)
	NameError: global name 'self' is not defined

delete the prefix *self.* in */usr/local/ophidia/extra/src/pywps/wps.py*.

