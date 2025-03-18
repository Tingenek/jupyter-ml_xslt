import requests
from requests.auth import HTTPDigestAuth
from requests_toolbelt.multipart import decoder
from IPython.core.magic import needs_local_scope
import json

def dispatcher(line,cell):
    #Split the URI up
    r = requests.utils.urlparse(line)
    session = requests.session()
    session.auth = HTTPDigestAuth(r.username,r.password)
    payload = {r.scheme: cell}
    uri = 'http://%s:%s/v1/eval' % (r.hostname,r.port)
    r = session.post(uri, data=payload)
    # Output is a list of dict
    out = []
    if r.status_code == 200 and 'content-type' in r.headers:
        if r.headers['content-type'].startswith("multipart/mixed"):
            multipart_data = decoder.MultipartDecoder.from_response(r)
            for part in multipart_data.parts:
                ctype = part.headers['Content-Type']
                data = json.loads(part.content) if (ctype == 'application/json') else part.content
                out.append({'data' : data, 'type' : ctype})
    return out 
 
 
def load_ipython_extension(ipython, *args):
    ipython.register_magic_function(dispatcher, 'cell', magic_name="marklogic")

def unload_ipython_extension(ipython):
    pass
