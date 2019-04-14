# Ophidia WPS Module

### Description

WPS module is a Python package enabling a WPS interface for Ophidia Server. This version is compatible with Ophidia Server v1.5.0.

It implements a process for PyWPS - Python Web Processing Service (http://pywps.org/), which translates WPS Requests into JSON Requests for Ophidia Web Service and, vice versa, replies to WPS clients with WPS Responses encapsulating the releted JSON Responses.

### Requirements

This software requires Python 2.7, PyOphidia and PyWPS 4.2 - Python Web Processing Service (http://pywps.org/), which can be built from sources provided that requirements are met as reported in PyWPS official documentation (https://pywps.readthedocs.io/en/latest/install.html). In particulat, install the following modules:

- gdal-python

It is recommended to start the service as module of Apache web server (https://www.apache.org/), so that TLS could be exploited to encrypt Ophidia credentials coded in WPS Requests. In this case, the following packages are required

- python-lxml
- python-setuptools
- mod_ssl
- mod_wsgi

### How to install

Download PyWPS sources and copy them in */usr/local/ophidia/extra/src/pywps/*.

```
mkdir -p /usr/local/ophidia/extra/src
cd /usr/local/ophidia/extra/src
git clone https://github.com/geopython/pywps.git
```

Install the requirements (skipping possible errors) and the package as follows:

```
cd /usr/local/ophidia/extra/src/pywps
sudo pip install -r requirements.txt
sudo pip install -r requirements-gdal.txt # Skip in case of errors
sudo pip install -r requirements-dev.txt # Skip in case of errors
sudo python setup.py install
```

Download Ophidia WPS sources in /usr/local/ophidia/extra/src, create a folder */usr/local/ophidia/extra/wps* and copy the sources inside:

```
mkdir -p /usr/local/ophidia/extra/src
cd /usr/local/ophidia/extra/src
git clone https://github.com/OphidiaBigData/ophidia-wps-module.git
mkdir -p /usr/local/ophidia/extra/wps
cp -R /usr/local/ophidia/extra/src/ophidia-wps-module/processes /usr/local/ophidia/extra/wps/
cp -R /usr/local/ophidia/extra/src/ophidia-wps-module/etc /usr/local/ophidia/extra/wps/
```

Configure Apache by saving the following specification in */etc/httpd/conf.d/python.conf*.

	WSGIDaemonProcess pywps home=/usr/local/ophidia/extra/wps/ user=apache group=apache processes=2 threads=5
	WSGIScriptAlias /wps /usr/local/ophidia/extra/wps/etc/pywps.wsgi process-group=pywps
	<Directory /usr/local/ophidia/extra/wps/>
		WSGIScriptReloading On
		WSGIProcessGroup pywps
		WSGIApplicationGroup %{GLOBAL}
		Require all granted
	</Directory>

By default it is assumed that Ophidia Server is running on the same node where PyWPS works and listening to port 11732. Otherwise, change service address (IP address and port number) by editing */usr/local/ophidia/extra/wps/processes/ophidia.py*.

Create the folders for PyWPS log file and WPS Responses (based on parameters set in */usr/local/ophidia/extra/wps/etc/pywps.cfg*):

```
sudo mkdir -p /var/www/html/wpsoutputs
sudo mkdir -p /var/log/wps
sudo chown root:apache /var/www/html/wpsoutputs
sudo chown root:apache /var/log/wps
sudo chmod 775 /var/www/html/wpsoutputs
sudo chmod 775 /var/log/wps
```

Install PyOphidia as follows:

```
sudo pip install PyOphidia
```

Finally, enable Apache to open new connections in case SELinux is enabled as follows:

```
sudo setsebool -P httpd_can_network_connect on
```

and restart the web server as follows.

```
sudo service httpd restart
```

If PyWPS runs as an extension of Apache, default port to access Ophidia WPS is 443.

Further information can be found at [http://ophidia.cmcc.it/documentation](http://ophidia.cmcc.it/documentation).

### Test

Check the WPS interface by sending the requests "GetCababilities" and "DescribeProcess" as follows:

```
curl -k https://localhost/wps/?service=WPS&version=1.0.0&request=getcapabilities
curl -k https://localhost/wps/?service=WPS&version=1.0.0&request=describeprocess&identifier=ophexecutemain
```

Requested resources are XML documents with a number of details about the service and the process *ophexecutemain*.

