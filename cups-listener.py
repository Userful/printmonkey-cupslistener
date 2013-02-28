#!/usr/bin/env python
"""
Copyright (c) 2011-2013, Userful Corporation
All rights reserved.
http://www.userful.com

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:
    * Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in the
      documentation and/or other materials provided with the distribution.
    * Neither the name of Userful nor the
      names of its contributors may be used to endorse or promote products
      derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL USERFUL BE LIABLE FOR ANY
DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
(INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import cups
import gobject
import dbus
import os, sys
from pyPdf import PdfFileReader
import MySQLdb
import glob
import time
import logging

logging.basicConfig(filename='/tmp/pmcups.log', level=logging.INFO)

# Database variables
# TODO use configparser and store these in a separate file
DB_HOST = 'host'
DB_USER = 'user'
DB_PASS = 'pass'
DB_DB = 'db'

def get_job_origin(job_id):
    return CONN.getJobAttributes(job_id)['job-originating-host-name']

def get_job_name(job_id):
    return CONN.getJobAttributes(job_id)['job-name']

def job_queued_handler(queue_name, job_id, owner):
    """ A job has entered CUPS """

    logging.info("got JobQueuedLocal: %s, %s, %s" , queue_name, str(job_id), owner)

    # Check that it's come in remotely
    if queue_name != "PDF":
        return

    logging.debug("queue is good")

    # Fork the process so we can adequately handle multiple incoming jobs
    try:
        PID = os.fork()
        if PID == 0:
            logging.debug("in forked process")
            # Get job details
            origin = get_job_origin(job_id)
            name = get_job_name(job_id)
            logging.info("Origin: %s Name: %s" , origin, name)

            # Release to /var/spool/cups-pdf/
            try:
                CONN.setJobHoldUntil(job_id, 'no-hold')
            except cups.IPPError, (status, desc):
                logging.error("IPP setJobHoldUntil error %d: %s", status, desc)
                return

            # Time-out to avoid race condition whilst PDF is created
            logging.debug("going to sleep for 5 seconds")
            time.sleep(5)
            logging.debug("done sleeping")

            # Get the path of the job
            tmp_path = '/var/spool/cups-pdf/job_'+str(job_id)+'*'
            logging.info("tmp_path: %s", tmp_path)
            try:
                orig_file_path = glob.glob(tmp_path)[0]
            except:
                logging.error("Couldn't find PDF file")
                return
            logging.info("Original file path: %s", orig_file_path)

            # Get the size of the job
            orig_file = file(orig_file_path, "rb")
            pdfin = PdfFileReader(orig_file)
            pdflength = pdfin.getNumPages()

            # Create a database connection
            print_db_cursor = PRINT_DB.cursor()

            # Let the database know about the print job
            print_db_cursor.execute("INSERT INTO jobs (name, barcode, ip, length) VALUES ('%s','%s','%s','%d')" % (name, owner, origin, pdflength))

            # Get the jobs printid
            print_db_cursor.execute("SELECT printid FROM jobs WHERE (ip='" + origin + "' AND barcode='" + owner + "') ORDER BY date DESC")
            printid = print_db_cursor.fetchone()[0]

            # Close the database connection
            print_db_cursor.close()

            # Move the job to /var/prints/
            new_file_path = "/var/prints/" + str(printid) + ".pdf"
            logging.info("New file path: %s", new_file_path)

            os.system("cp "+orig_file_path+" "+new_file_path) # We do this to trigger inotify

            # Fix the ownership
            new_file = file(new_file_path)
            fdno = new_file.fileno()
            os.fchown(fdno, 1000, 1000)

            return

    except OSError, e:
        logging.error("fork failed: (%d) %s\n" % (e.errno, e.strerror))
        return

logging.info('starting printMonkey CUPS listener')

# Create a database connection
try:
    PRINT_DB = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_DB)
except MySQLdb.Error, e:
    logging.error("Could not connect to PM database")
    logging.error("Error %d: %s", e.args[0], e.args[1])
    sys.exit(1)

# Create a connection to CUPS
CONN = cups.Connection()

# Create the DBus loop
from dbus.mainloop.glib import DBusGMainLoop

DBusGMainLoop(set_as_default=True)

bus = dbus.SystemBus()

bus.add_signal_receiver(job_queued_handler, "JobQueuedLocal", "com.redhat.PrinterSpooler", None, None)

mainloop = gobject.MainLoop()
mainloop.run()
