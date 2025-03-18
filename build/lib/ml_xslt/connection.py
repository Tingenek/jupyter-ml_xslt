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
            <xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="3.0">
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
        if (args.file):
            document = f'doc("{args.file}")'
        else:    
            document = '''document{<hello><world>hello world</world></hello>}'''
        transform = template.replace('$TRANSFORM$',code).replace('$DOCUMENT$', document) 
        payload = {"xquery": transform}
        uri = '%s://%s:%s/v1/eval' % (self.cfg.scheme, self.cfg.host, self.cfg.port)
        print(document)
        r = session.post(uri, data=payload)
        r.raise_for_status()
        # Output is a list of dict
        out = []
        if r.status_code == 200 and 'content-type' in r.headers:
            if r.headers['content-type'].startswith("multipart/mixed"):
                multipart_data = decoder.MultipartDecoder.from_response(r)
                for part in multipart_data.parts:
                    ctype = part.headers[b'Content-Type'].decode("utf-8")
                    content = part.content.decode("utf-8")
                    data = BeautifulSoup(content, 'xml') if (ctype == 'application/xml') else content
                    out.append(data)
        return out 


    def _eval_code(self, code,args):
        session = requests.session()
        session.auth = HTTPDigestAuth(self.cfg.user, self.cfg.password)
        # replace result with export
        #scheme = args.parser
        # replace result with export
        if args.parser == 'xquery':
            code = code.replace('result()','export()')
            code = "xquery version '1.0-ml';\nimport module namespace op='http://marklogic.com/xslt' at '/MarkLogic/xslt.xqy';\n\n" + code
        if args.parser == 'javascript':
            code = code.replace('result()','export()')
            code =  "'use strict'\nconst op = require('/MarkLogic/xslt');\n\n" + code

        #(code)
        payload = {args.parser: code}

        #logging.info(code)
        print(payload) 
        uri = '%s://%s:%s/v1/eval' % (self.cfg.scheme, self.cfg.host, self.cfg.port)
        data = None
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
                data = self._get_multi_result(result)
        return data

    def endpoint(self,line):
        try:
            r = requests.utils.urlparse(line)
            self.cfg = ConfigStruct( host=r.hostname, port=r.port, user=r.username, password=r.password, scheme=r.scheme, action='eval', param=None)
        except:
            print('malformed connection' + line)
        return None
