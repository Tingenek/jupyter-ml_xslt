from __future__ import print_function

from IPython.core.magic import (Magics, magics_class, line_magic,
                                cell_magic, line_cell_magic, needs_local_scope)
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

import requests
from requests.auth import HTTPDigestAuth
from requests_toolbelt.multipart import decoder
from IPython.core.display import display

from .connection import MLRESTConnection

# The class MUST call this class decorator at creation time
# print("Full access to the main IPython object:", self.shell)
# print("Variables in the user namespace:", list(self.shell.user_ns.keys()))

@magics_class
class MarkLogicXsltMagic(Magics):

    def __init__(self,shell):
        # You must call the parent constructor
        super(MarkLogicXsltMagic, self).__init__(shell)
        self.connection = MLRESTConnection()
        self.variable = 'ml_xslt'
        self.parser = 'xquery'
        self.file = None
        self.mode = 'server'

    @magic_arguments()
    @cell_magic
    @argument(
        '-v', '--variable',default=None,
        help='output to a var, default is ml_xslt'
    )
    @argument(
        '-f', '--file',default=None,
        help='document to transform'
    )
    @argument(
        '-m', '--mode',default='local',
        help='path to file: local or server. Default is local'
    )
    @argument(
        'connection', default=None,nargs='?',
        help='connection string; can be empty if set previously.'
    )
    def ml_xslt(self, line=None, cell=None,local_ns={}):
        user_ns = self.shell.user_ns.copy()
        user_ns.update(local_ns)
        args = parse_argstring(self.ml_xslt, line)
        args.parser = self.parser

        if args.variable is not None:
            self.variable = args.variable
        else:
            args.variable = self.variable

        if args.file is not None:
            self.file = args.file
        else:
            args.file = self.file

        if args.mode is not None:
            self.mode = args.mode
        else:
            args.mode = self.mode

        result = None
        if cell is None:
            print("No contents")
        else:
            #reset connection if given
            if args.connection is not None:
                self.connection.endpoint(args.connection)
            #expand out {var} in cell body

            #try:
            cell = cell.format(**user_ns)
            result = self.connection.call_rest(args, cell)
            #except Exception as err:
            #    print(f'Other error: {err}')  # Python 3.6
            if result is not None:
                print(args.variable + ' returns:')
                display(result)
            else:
                print('No results')
            self.shell.user_ns.update({args.variable: result})

def load_ipython_extension(ipython, *args):
    ipython.register_magics(MarkLogicXsltMagic)
    print("marklogic xslt magic loaded.")


def unload_ipython_extension(ipython):
    print("marklogic xslt magic unloaded.")
