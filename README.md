This program allows jobs to be sent to a PrintMonkey through CUPS.

*The program listens for signals via D-BUS as to when a new job comes in via CUPS.
*It releases the job, which goes through cups-pdf into a designated folder
*It gets the job details and adds them to the database
*It then copies the file to the PrintMonkey folder which stores the PDFs for viewing. This copying triggers inotify, which is how PrintMonkey is aware of incoming jobs

Installation
============

1. On the PrintMonkey machine, install *cups-pdf*
2. Create a queue named *PDF* in CUPS, with the device URI as *cups-pdf:/* and the *Generic CUPS-PDF Printer* driver. In */etc/cups/cups-pdf.conf* set the Out, AnonDirName, and Spool settings to */var/spool/cups-pdf/* and the Label to *1*. You may also have to set the Grp option.
3. Modify the PDF queue in */etc/cups/printers.conf* adding the following line: *Option job-hold-until indefinite*
4. `sudo /etc/init.d/cups restart`
5. `git clone https://github.com/Userful/printmonkey-cupslistener.git`
6. `cd printmonkey-cupslistener`
7. `sudo make install`
8. Modify the database details in */usr/bin/cups-listener.py*
9. `sudo /etc/init.d/cups-listener start`
10. `sudo update-rc.d cups-listener defaults`

Q & A
=====
Q. How are barcodes sent from Userful Desktop to PrintMonkey?

A. We use the UDIPP filter so that jobs are sent with the barcodes in the "originating-job-user-name" field.

Q. cups-pdf is dying with "failed to open source stream" as an error message in its log.

A. This seems to be a problem with apparmor not liking cups-pdf getting stuff from IPP.

You can see if apparmor has a rule for cups-pdf:

`sudo apparmor_status`

The fix:

`sudo ln -s /etc/apparmor.d/usr.sbin.cupsd /etc/apparmor.d/disable/`
`sudo apparmor_parser -R //etc/apparmor.d/usr.sbin.cupsd`

Notes
=====
Userful Desktop is a trademark of Userful

CUPS is a trademark of Apple Inc.
