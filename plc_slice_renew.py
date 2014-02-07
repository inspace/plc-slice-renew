#!/usr/bin/env python

"""Simple script to renew a slice using the PLCAPI python library.

Tested with Python 2.7 and PLCAPI version HEAD on Feb 28, 2012 on OS X.
"""

##############################################################################
##############################################################################

import sys, optparse, getpass, datetime, time, xmlrpclib, os

##############################################################################
##############################################################################

# if our local time is too different from PLC time, this will raise a Fault
# so to avoid this we will renew for less than the maximum (8 weeks)
RENEW_DAYS_DEFAULT = 54

PLCAPI_URL = 'https://www.planet-lab.org/PLCAPI/'

AUTH_FILE = '~/.pl_auth'

USAGE = "%prog [options] USER"
DESCRIPTION = """Renews a PlanetLab slice using the PLCAPI.
First looks for credentials file at ~/.pl_auth formatted as
"user password slice". If no file is found then USER is required.

Required argument USER: PLC user or file containing PLC user.
Prompts for the password if not given on the command line.
Will renew some slice if no slice is specified.
"""

##############################################################################
##############################################################################

def renew(url, user, password, slice, days):
    
    server = xmlrpclib.ServerProxy(PLCAPI_URL)

    auth = {'Username': user, 'AuthString': password, 'AuthMethod': 'password'}

    if slice is not None:
        slice = server.GetSlices(auth, slice)[0]
    else: # if slice is not specified, use the first slice returned
        slice = server.GetSlices(auth)[0]
    
    renew = datetime.timedelta(days=days)
    now = datetime.datetime.now()
    then = now + renew
    args = { 'expires' : int(time.mktime(then.timetuple())), }
    
    if server.UpdateSlice(auth, slice['name'], args) != 1:
        raise RuntimeError('Unable to update slice %s' % slice)

    slice = server.GetSlices(auth, slice['name'])[0]
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
                      help="PLC password or file containing PLC password (default: prompt)")
    parser.add_option("-s", "--slice", 
                      help="Slice name (default: some slice)")
    parser.add_option("-d", "--days",
                      type='int',
                      help="Days to renew (default: %d)" % RENEW_DAYS_DEFAULT,
                      default=RENEW_DAYS_DEFAULT)    
    parser.add_option("-f", "--file", default=AUTH_FILE, 
                      help="Path to credentials file (default: %s)" % AUTH_FILE)

    opts, args = parser.parse_args()
    if len(args) == 0:          #should have AUTH_FILE configured
        try:
            auth_file_path = os.path.expanduser(opts.file)
            credentials = open(auth_file_path).read().strip().split()
            opts.user = credentials[0]
            opts.password = credentials[1]
            opts.slice = credentials[2]
        except IOError:
            parser.error('Missing required argument (USER) or no %s file configured' % AUTH_FILE)
        except IndexError:
            parser.error('Format of %s file is "user password slice"' % AUTH_FILE)
    elif len(args) == 1:
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
    else:
        parser.error('Missing required argument (USER) or no %s file configured' % AUTH_FILE)

    #slice = renew(**(opts.__dict__))
    slice = renew(opts.url, opts.user, opts.password, opts.slice, opts.days)
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
