import time, urllib, urllib2, hashlib, pprint, re, sys
import urllib, urllib2, socket, httplib

import json

"""
   Being lazy with globals because you probably don't have more than one in your LAN 

   Note that login takes a little time. The _fritz_sid keeps the login token so if you can 
   keep the interpreter running you can get fster fetches


   CONSIDER: fetching things beyond transfers.
"""

_fritz_sid = None
_fritz_lastfetched = 0
_fritz_lastdata = None

IP       = '192.168.178.1'
username = ''
password = 'change_me'


def urlfetch(url, data=None, headers=None, raise_as_none=False, return_reqresp=False):
    """ Returns:
        - if return_reqresp==False (default), returns the data at an URL
        - if return_reqresp==True,  returns the request and response objects (can be useful for streams)

        data:           May be
                        - a dict 
                        - a sequence of tuples (will be encoded), 
                        - a string (not altered - you often want to have used urllib.urlencode)
                        When you use this parameter, the request becomes a POST instead of the default GET
                         (and seems to force <tt>Content-type: application/x-www-form-urlencoded</tt>)
        headers:        dict of additional headers  (each is add_header()'d)
        raise_as_none:  In cases where you want to treat common connection failures as 'try again later',
                         using True here can save a bunch of your own typing in error catching
    """
    try:
        if type(data) in (tuple, dict):
            data=urllib.urlencode(data)
        req  = urllib2.Request(url, data=data)
        if headers!=None: 
            for k in headers:
                vv = headers[k]
                if type(vv) in (list,tuple):
                    for v in vv: 
                        req.add_header(k,v)
                else: # assume single string. TODO: consider unicode
                    req.add_header(k,vv)
        response = urllib2.urlopen(req, timeout=60)
        if return_reqresp:
            return req,response
        else:
            data = response.read()
            return data
    except (socket.timeout), e:
        if raise_as_none:
            sys.stderr.write( 'Timeout fetching %r\n'%url )
            return None
        else:
            raise
    except (socket.error, urllib2.URLError, httplib.HTTPException), e:
        if raise_as_none:
            #print 'Networking problem, %s: %s'%(e.__class__, str(e))
            return None
        else:
            raise



def fritz_login(): 
    data = urlfetch('http://%s/login_sid.lua'%(IP,))
    m = re.search('<Challenge>([0-9a-f]+)</Challenge>', data)
    challenge = m.groups()[0]
    m5h = hashlib.md5()
    hashstr = '%s-%s'%(challenge, password)
    m5h.update(hashstr.encode('utf_16_le'))
    response = m5h.hexdigest()
    data = urlfetch('http://%s/login_sid.lua'%(IP,), {'response':'%s-%s'%(challenge, response)})        
    m = re.search('<SID>([0-9a-f]+)</SID>', data)
    return m.groups()[0]
   

def fritz_fetch():
    " Fetches ul/dl graph data "
    global _fritz_sid, _fritz_lastfetched, _fritz_lastdata

    td = time.time() - _fritz_lastfetched
    if td < 5.0 and _fritz_lastdata!=None: # if our last fetch was less than 5 seconds ago, we're not going to get a new answer
        return _fritz_lastdata
            
    try:
        fetchurl = 'http://%s/internet/inetstat_monitor.lua?sid=%s&myXhr=1&action=get_graphic&useajax=1&xhr=1'%(IP, _fritz_sid)
        data = urlfetch(fetchurl)
    except urllib2.HTTPError, e:
        if e.code==403:
            #print "Forbidden, tryin to log in for new SID"
            _fritz_sid = fritz_login() 
        fetchurl = 'http://%s/internet/inetstat_monitor.lua?sid=%s&myXhr=1&action=get_graphic&useajax=1&xhr=1'%(IP, _fritz_sid)
        #print fetchurl
        data = urlfetch(fetchurl)
        
    jd = json.loads( data )[0]# [0]: assume it's one main interface
    _fritz_lastfetched = time.time()
    _fritz_lastdata = jd
    #pprint.pprint( jd )
    return jd


if __name__ == '__main__':
    import pprint
    pprint.pprint( fritz_fetch() )
