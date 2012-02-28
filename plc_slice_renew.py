#!/bin/env python

"""Simple script to renew a slice using the PLCAPI python library.

Tested with Python 2.7 and PLCAPI version HEAD on Feb 28, 2012 on OS X.
"""

##############################################################################
##############################################################################

import sys, optparse, getpass, datetime, time

import PLC.Shell

##############################################################################
##############################################################################

# if our local time is too different from PLC time, this will raise a Fault
# so to avoid this we will renew for less than the maximum (8 weeks)
RENEW_DAYS_DEFAULT = 54

PLCAPI_URL = 'https://www.planet-lab.org/PLCAPI/'

USAGE = "%prog [options] USER"
DESCRIPTION = """Renews a PlanetLab slice using the PLCAPI.
Required argument USER: PLC user or file containing PLC user.
Prompts for the password if not given on the command line.
Will renew some slice if no slice is specified.
"""

##############################################################################
##############################################################################

def renew(url, user, password, slice, days):
    shell = PLC.Shell.Shell(globals = globals(),
                            url = url, 
                            xmlrpc = True,
                            method = 'password',
                            user = user, 
                            password = password)
    if slice is not None:
        slice = GetSlices(slice)[0]
    else: # if slice is not specified, use the first slice returned
        slice = GetSlices()[0]
    
    renew = datetime.timedelta(days=days)
    now = datetime.datetime.now()
    then = now + renew
    args = { 'expires' : int(time.mktime(then.timetuple())), }
    
    if UpdateSlice(slice['name'], args) != 1:
        raise RuntimeError('Unable to update slice %s' % slice)

    slice = GetSlices(slice['name'])[0]
    return slice

##############################################################################
##############################################################################

def main(argv=None):
    
    #
    # Parse arguments
    #
    
    if argv is None:
        argv = sys.argv
    parser = optparse.OptionParser(usage=USAGE, description=DESCRIPTION)
    parser.add_option("-u", "--url", help="PLCAPI URL (default: %s)" % PLCAPI_URL, 
                      default=PLCAPI_URL)
    parser.add_option("-p", "--password", 
                      help = "PLC password or file containing PLC password (default: prompt)")
    parser.add_option("-s", "--slice", 
                      help = "Slice name (default: some slice)")
    parser.add_option("-d", "--days", 
                      help = "Days to renew (default: %d)" % RENEW_DAYS_DEFAULT,
                      default=RENEW_DAYS_DEFAULT)
    
    opts, args = parser.parse_args()
    if len(args) < 1:
        parser.error("Missing required argument (USER)")
    opts.user = args[0]
    try:
        opts.user = open(opts.user).read().strip()
    except IOError:
        pass
    if opts.password is None:
        try:
            opts.password = getpass.getpass()
        except (EOFError, KeyboardInterrupt):
            return 0
    else:
        try:
            opts.password = open(opts.password).read().strip()
        except IOError:
            pass

    slice = renew(**(opts.__dict__))
    expires = time.strftime("%d %B %Y %H:%M:%S", 
                            time.localtime(slice['expires']))
    # Print result
    print "Slice %s renewed until %s" % (slice['name'], expires)
    return 0

##############################################################################
##############################################################################

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    
##############################################################################
##############################################################################
