
import urllib.request, urllib.parse, json, base64

def couch_webservice_request(request,*args,**kwargs):
    baseurl = 'http://localhost:5984'
    url = baseurl + "/" + request.lstrip('/')
    return webservice_request(url,*args,**kwargs)

def uniprot_webservice_request(request,*args,**kwargs):
    baseurl = 'https://www.ebi.ac.uk/proteins/api'
    url = baseurl + "/" + request.lstrip('/')
    return webservice_request(url,*args,**kwargs)

def webservice_request(request,
                       payload={},
                       method='GET',
                       username=None,
                       password=None):
    headers = {'Content-type': 'application/json',
               'Accept':       'application/json'}
    opener = urllib.request.build_opener(urllib.request.HTTPHandler())
    if username and password:
        b64 = base64.b64encode(('%s:%s'%(username, password)).encode()).decode()
        headers["Authorization"] = "Basic %s"%(b64,)
    url = request
    if method == 'GET':
        if payload != {}:
            url += '?' + urllib.parse.urlencode(payload)
        request = urllib.request.Request(url, headers=headers)
    elif method == 'POST':
        request = urllib.request.Request(url, json.dumps(payload).encode(), headers=headers)
    elif method == 'PUT':
        request = urllib.request.Request(url, json.dumps(payload).encode(), headers=headers)
        request.get_method = lambda: 'PUT'
    elif method == 'DELETE':
        request = urllib.request.Request(url, json.dumps(payload).encode(), headers=headers)
        request.get_method = lambda: 'DELETE'
    else:
        raise RuntimeError('Bad method '+method)
    try:
        return json.loads(opener.open(request).read())
    except urllib.request.HTTPError as e:
        return {u'error': True, u'errorcode': e.code, u'errormsg': e.msg}
    return {u'error': True}
