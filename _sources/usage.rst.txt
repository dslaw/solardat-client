Usage
=====


Searching
---------

Archival data files contain observations across multiple variables and
instruments, for a single month and station. An open interval can be used to
search across months, and one or more stations can be queried for directly.

.. code-block:: python

   from datetime import date
   from solardat import find_files

   # Search for archival data from January thru February, 2018 at
   # the Eugene, Oregon station.
   start = date(2018, 1, 1)
   end = date(2018, 2, 1)
   stations = ["Eugene"]
   search_results = find_files(start, end, stations)

The returned search results are the paths to archival data files on the server,
organized by station. Note that the station names returned by ``find_files``
differ slightly from those passed to the search query.

If you don't know the names of the different stations, you can visit the
`monitoring stations web page
<http://solardat.uoregon.edu/MonitoringStations.html>`_ or use the
:func:`~solardat.search.fetch_stations` function.

.. code-block:: python
   
   from solardat import fetch_stations

   all_stations = fetch_stations()


Filtering
---------

Even for a single month and station, there will often be multiple files. These
differ in the granularity of the measurements - the data can be given in
one-minute, five-minute, fifteen-minute and hourly intervals, which is denoted
by the fourth character in the filename. It is not possible to search by
the interval length, but the results can easily be filtered.

.. code-block:: python

   from pathlib import Path

   # Select only data files with five-minute intervals, denoted
   # by "F".
   filepaths = []
   for station_name, files in search_results.items():
       for file in files:
           filestem = Path(file).stem
           interval_code = filestem[3]
           if interval_code == "F":
               filepaths.append(file)


Downloading
-----------

The dataset(s) can be pulled directly into memory, one at a time

.. code-block:: python

   from solardat import fetch_file

   datasets = []
   for filepath in filepaths:
       filestem = Path(filename).stem
       station_id, rows = fetch_file(filepath)
       datasets.append((filestem, rows))

or asynchronously

.. code-block:: python

   from solardat import fetch_many
   import aiohttp
   import asyncio

   async def main():
       async with aiohttp.ClientSession() as session:
           return await fetch_file(session, filepaths)

    loop = asyncio.get_event_loop()
    results = loop.run_until_complete(main())

The returned data is marshalled into dictionaries.


Compressed Files
----------------

A zipfile of the compressed data can also be downloaded and unpacked, instead
downloading multiple files separately.

.. code-block:: python

   from solardat import fetch_compressed, find_compressed

   # Get download link to a zipfile of compressed search results.
   download_path = find_compressed(start, end, ["Eugene"])

   # Download and decompress.
   datasets = []
   for filestem, station_id, rows in fetch_compressed(download_path):
       datasets.append((filestem, rows))

Note that this is a synchronous operation, and may take some time depending on
how much data was requested.
