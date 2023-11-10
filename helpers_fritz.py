import time, hashlib, re, urllib, json, bs4, pprint
import xml.etree.ElementTree as ET
import requests

"""
   Being lazy with globals because you probably don't have more than one in your LAN 

   Note that login takes a little time. The _fritz_sid keeps the login token so that
   if you can keep the interpreter running you can get faster fetches

   CONSIDER: fetching things beyond transfers.

   So, there are two variants.
     The older one is MD5-based,
     the newer one (?version=2) is SHA256-based

   I'm still confused as to why the older version broke, 
   because it seems requests to login_sid.lua default to the older style
   

   https://avm.de/fileadmin/user_upload/Global/Service/Schnittstellen/AVM_Technical_Note_-_Session_ID_english_2021-05-03.pdf

"""

_fritz_sid         = None
_fritz_lastfetched = 0
_fritz_lastdata    = None

#as str, not bytestr
IP       = '192.168.178.1'
username = 'changeme'   # depending on the fritzbox age, this may be empty, or effectively decided for you and you can fish it out of the regular HTML login page
password = 'changeme'



def fritz_login(version=1, verbose=False):
    ''' TODO: Make version 2 work, 
        TODO: review for clarity with all the encodings
        CONSIDER: fetch username from first request, so we don't have to set it (but check how that worked on older versions)

        Returns
          None      if the fritzbox signals that we're being blocked for a while
          False     if the login seems to be wrong
          a string  as a valid session identifier
    '''
    if version==2:
        url = 'http://%s/login_sid.lua?version=2'%(IP,)
    else:
        url = 'http://%s/login_sid.lua'%(IP,)

    if verbose:
        print( "FIRST" )
    r = requests.get( url )
    if verbose:
        print('  fetched:    ',r.text)
    root = ET.fromstring( r.text )
    challenge = root.find('Challenge').text.encode('ascii')

    blocktime = root.find('BlockTime').text
    if int(blocktime)>0:
        print('Blocktime = %s'%blocktime)
        return None

    if verbose:
        print('  challenge:   %r'%challenge)

    # note: challenge and password are bytestrings, response should be str
    if challenge.startswith( b'2$'):  ## version 2
        # this is not correct, and I don't yet understand why
        _, iter1, salt1, iter2, salt2 = challenge.split(b"$")
        iter1   = int(iter1)
        salt1_b = bytes.fromhex(salt1.decode('ascii')) # apparently fromhex wants str, not bytes.  Maybe there's a slightly cleaner way?
        iter2   = int(iter2)
        salt2_b = bytes.fromhex(salt2.decode('ascii'))
        if verbose:
            print('  iter1=%r, salt1=%r, iter2=%r, salt2=%r'%(iter1, salt1, iter2, salt2) )
        hash1 = hashlib.pbkdf2_hmac(hash_name="sha256", password=password.encode('utf8'), salt=salt1, iterations=iter1)
        hash2 = hashlib.pbkdf2_hmac(hash_name="sha256", password=hash1,                   salt=salt2, iterations=iter2)
        response = '%s$%s'%(salt2.decode('ascii'), hash2.hex())

    else: ## version 1
        m5h = hashlib.md5()
        hashstr = '%s-%s'%(challenge.decode('ascii'), password)
        hashstr = hashstr.encode('utf_16_le') # or maybe decode utf8 if our password contains any?
        m5h.update( hashstr )
        digest = m5h.hexdigest() # a str
        response = '%s-%s'%(challenge.decode('ascii'), digest)

    data = {'response':response, 'username':username} 
    if verbose:
        print('  response request data: %r'%data)
    r = requests.post( url, data=data )

    secondresp = r.text
    if verbose:
        print( 'SECOND' ) 
        print( '  fetched', secondresp )
    m = re.search('<SID>([0-9a-f]+)</SID>', secondresp)
    sid = m.groups()[0]
    #print( "  SID", sid )
    if sid == '0000000000000000':
        return False
        #raise ValueError('Login failed (SID is %r)'%sid)
    else:
        return sid
   


def fritz_fetch(verbose=False):
    " Fetches ul/dl graph data "
    global _fritz_sid, _fritz_lastfetched, _fritz_lastdata
    if verbose:
        print( "FETCH data")

    td = time.time() - _fritz_lastfetched
    if td < 5.0 and _fritz_lastdata!=None: # if our last fetch was less than 5 seconds ago, we're not going to get a new answer
        return _fritz_lastdata


    # Previously this fetch would fail with a 403, now it only redirects you
    if 0:
        fetchurl = 'http://%s/internet/inetstat_monitor.lua?sid=%s&myXhr=1&action=get_graphic&useajax=1&xhr=1'%(IP, _fritz_sid)
        resp = requests.get( fetchurl, allow_redirects = False )
    else:
        fetchurl = 'http://%s/data.lua'%IP
        resp = requests.post(fetchurl, data={
                'xhr':'1',
                'sid':_fritz_sid,
                'lang':'en',
                'page':'netMoni',
                'xhrId':'updateGraphs',
                'useajax':'1',
                'no_sidrenew':'',
            }, allow_redirects=False) # or it'd send a 303 to the front page that we follow


    if resp.status_code != 200:

        if verbose:
            print( "  Status code %r, trying to log in for new SID"%resp.status_code )
        _fritz_sid = fritz_login(verbose=verbose) 

        if _fritz_sid in (None,False):
            raise ValueError( "Could not log in, either wrong auth or being blocked for some reason" )
        else:
            if verbose:
                print("Logged in, SID = %s"%_fritz_sid)

        if 0:
            fetchurl = 'http://%s/internet/inetstat_monitor.lua?sid=%s&myXhr=1&action=get_graphic&useajax=1&xhr=1'%(IP, _fritz_sid)
            if verbose:
                print( "  try 2: %r"% fetchurl )
            resp = requests.get(fetchurl)
        else:
            fetchurl = 'http://%s/data.lua'%IP
            resp = requests.post(fetchurl, data={
                'xhr':'1',
                'sid':_fritz_sid,
                'lang':'en',
                'page':'netMoni',
                'xhrId':'updateGraphs',
                'useajax':'1',
                'no_sidrenew':'',
            }, allow_redirects=False)

            #print( resp.status_code )
            #print( resp.text )
            
    # implied else, or assume the last-minute login worked:   assume  (200 OK, JSON fetched fine)
    # TODO: slightly better testing

    data = resp.text

    if verbose:
        print( repr(data) )


    jd = json.loads( data )   #[0]# [0]: assume it's one main interface
    _fritz_lastfetched = time.time()
    _fritz_lastdata = jd
    if verbose:
        pprint.pprint( jd )
    return jd


if __name__ == '__main__':
    SID = fritz_login()
    #print( 'SID:', SID )

    while True:
        print( 'data', fritz_fetch() )
        time.sleep( 2.5 )
