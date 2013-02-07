This program allows jobs to be sent to a PrintMonkey through CUPS.

The program listens for signals via D-BUS as to when a new job comes in via CUPS.
It releases the job, which goes through cups-pdf into a designated folder
It gets the job details and adds them to the database
It then copies the file to the PrintMonkey folder which stores the PDF's for viewing. This copying triggers inotify, which is how PrintMonkey is aware of incoming jobs

## Known Issues
The PrintMonkey database has the 'barcode' data type set to integer on the 'jobs' table. If there's a non-integer username associated with the job, it will not get put into the database.

## Q & A
Q. How are barcodes sent from Userful Desktop to PrintMonkey?
A. We use the UDIPP filter so that jobs are sent with the barcodes in the "originating-job-user-name" field.

## Notes
Userful Desktop is a trademark of Userful
CUPS is a trademark of Apple Inc.
