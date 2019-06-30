solardat: A Python client for solar irradiance data
===================================================

solardat-client provides programmatic access to solar radiation data collected
and maintained by the `University of Oregon Solar Radiation Monitoring
Laboratory <http://solardat.uoregon.edu>`_, specifically their `archival data
<http://solardat.uoregon.edu/ArchivalFiles.html>`_, as well as utilities for
reading the data.

Python versions 3.6+ are supported.


Motivation
----------

The UO Solar Radiation Monitoring Laboratory hosts a `web interface
<http://solardat.uoregon.edu/SelectArchival.html>`_ which can be used to search
for archival data files and perform a bulk download. If you are interested in
generating a single, static data dump, then you should use the provided web
interface. If, however, you want to perform a finer grained search, filter the
results or programmatically fetch new datasets, the web interface may be
lacking.


Features
--------

.. TODO: mention printing of column descriptions

solardat-client provides utilities for searching, downloading and parsing
archival data files. Requests are cached in-memory.


Contents
--------

.. toctree::
   :maxdepth: 2

   usage.rst
   api.rst
