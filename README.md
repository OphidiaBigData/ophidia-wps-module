# Ophidia WPS Module

### Description

WPS module is a Python package enabling a WPS interface for Ophidia Server.

It implements a process for PyWPS - Python Web Processing Service (http://pywps.org/), which translates WPS Requests into JSON Requests for Ophidia Web Service and, vice versa, replies to WPS clients with WPS Responses encapsulating the releted JSON Responses.

### Requirements

This software requires PyWPS - Python Web Processing Service (http://pywps.org/).

It is recommanded to start the service as module of Apache web server (https://www.apache.org/), so that TLS could be exploited to encrypt Ophidia credentials coded in WPS Requests. In this case, the following packages are required:

#. python-lxml
#. python-setuptools
#. mod_python
#. mod_ssl

### How to Install

Download PyWPS from http://pywps.org/download/ and install it into */usr/local/ophidia/extra/pywps/*.

Create a folder */usr/local/ophidia/extra/wps* and copy both the folders *processes* and *etc* inside:

```
$ mkdir -p /usr/local/ophidia/extra/wps
$ cp -r processes /usr/local/ophidia/extra/wps/
$ cp -r etc /usr/local/ophidia/extra/wps/
```

Copy Apache module for PyWPS *wps.py* in a folder accessible from the web server as follows:

```
$ mkdir -p /var/www/wps/
$ cp /usr/local/ophidia/extra/pywps/webservices/mod_python/wps.py /var/www/wps/
```

Configure Apache by adding the specification for the folder */var/www/wps/*:

Alias /wps/ "/var/www/wps/"
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
    PythonPath "sys.path+['/usr/local/ophidia/extra/pywps/']"
    PythonAutoReload On
</Directory>

By default it is assumed that Ophidia Server is running on the same node where PyWPS works and listening to port 11732. Otherwise, change service address (IP address and port number) by editing /usr/local/ophidia/extra/wps/processes/ophidia.py.

Finally, create the folders for PyWPS log file and WPS Responses (based on parameters set in */usr/local/ophidia/extra/wps/etc/pywps.cfg*):

```
$ mkdir -p /var/www/html/wpsoutputs
$ mkdir -p /var/log/wps
$ chown root:apache /var/www/html/wpsoutputs/
$ chmod 775 /var/www/html/wpsoutputs/
$ chown root:apache wps
$ chmod 775 /var/log/wps/
```

Further information can be found at [http://ophidia.cmcc.it/documentation](http://ophidia.cmcc.it/documentation).

