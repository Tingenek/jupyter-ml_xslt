import requests
from requests.auth import HTTPDigestAuth
from requests.exceptions import HTTPError
from requests_toolbelt.multipart import decoder
from bs4 import BeautifulSoup 
from io import StringIO
# ----------------------------------------------------------------------

class ConfigStruct:
    def __init__(self, **entries):
        self.__dict__.update(entries)


# ----------------------------------------------------------------------

class MLRESTConnection(object):

    def __init__(self):
        self.cfg = ConfigStruct(host='localhost', port='8000', user='admin', password='admin', scheme='', action='eval', param=None)
        self.search = ConfigStruct(start='1', page='10')

    def call_rest(self, args, code):
        session = requests.session()
        session.auth = HTTPDigestAuth(self.cfg.user, self.cfg.password)
        #TODO Replace defaults with import
        template = '''xdmp:xslt-eval(
            <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                            xmlns:xdmp="http://marklogic.com/xdmp"
                            xmlns:utils="urn:util-lib"
                            xmlns:map="http://marklogic.com/xdmp/map"
                            extension-element-prefixes="xdmp"
                            version="3.0">  
            <!-- Import main converter -->
            $BASE$
            <xsl:param name="context" as="map:map?"/>
            <xsl:param name="params"  as="map:map?"/> 

            <xsl:output method="xml"/>
            <xsl:template match="/">             
                <xsl:apply-templates/>   
            </xsl:template>
            $TRANSFORM$
            <xsl:template match="@* | node()">
                <xsl:copy>            
                    <xsl:apply-templates select="@* | node()"/>
                </xsl:copy>
            </xsl:template>
            </xsl:stylesheet>,
            $DOCUMENT$)
        '''
        if (args.base):
            import_string = f'<xsl:import href="{args.base}"/>'
        else:
            import_string = ""
      
        if (args.file):
            document = f'doc("{args.file}")'
        else:    
            document = '''document{<hello><world>hello world</world></hello>}'''
        transform = template.replace('$TRANSFORM$',code).replace('$DOCUMENT$', document).replace('$BASE$', import_string)  
        payload = {"xquery": transform}
        uri = '%s://%s:%s/v1/eval' % (self.cfg.scheme, self.cfg.host, self.cfg.port)
        #print(transform)
        out = []
        try:
            result = session.post(uri, data=payload)
            # If the response was successful, no Exception will be raised
            result.raise_for_status()
        except HTTPError as http_err:
            error = result.json()["errorResponse"]["message"]
            print(error)
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            if result.status_code == 200 and 'content-type' in result.headers:
                if result.headers['content-type'].startswith("multipart/mixed"):
                    multipart_data = decoder.MultipartDecoder.from_response(result)
                    for part in multipart_data.parts:
                        ctype = part.headers[b'Content-Type'].decode("utf-8")
                        content = part.content.decode("utf-8")
                        
                        data = BeautifulSoup(content, 'xml') if (ctype == 'application/xml') else content
                        out.append(data)
        if len(out) == 1:
            return out[0]
        else:
            return  
       
    def endpoint(self,line):
        try:
            r = requests.utils.urlparse(line)
            self.cfg = ConfigStruct( host=r.hostname, port=r.port, user=r.username, password=r.password, scheme=r.scheme, action='eval', param=None)
        except:
            print('malformed connection' + line)
        return None
