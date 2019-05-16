import tableauserverclient as tableau
from tableaudocumentapi import Datasource
import json
import csv
import os
import xml.etree.ElementTree as xml
import zipfile # tableau .tdsx parsing
import tableaudocumentapi.xfile as twbx

class datasourceRefresh():
    '''
    A class for downloading all datasources from a Tableau Server instance.
    Optionally set the working directory.
    '''

    def __init__(self, workingDirectory = os.getcwd()):
        '''Initialize the datasourceRefresh class.'''
        
        # initialize class variables
        self.tableau_auth = None
        self.datasourceRepository = None

        # set the working directory
        self.workingDirectory = workingDirectory
        os.chdir(self.workingDirectory)
        print(f'\nDatasources will download to: {os.getcwd()}\n')


    def serverLogin(self, RESTApiVersion = '3.0'):
        '''
        Prompt user for credentials to log into a Tableau Server instance.
        Optionally set the REST API Version (v3.0 recommended).
        '''

        # get server credentials
        self.server = input("Server URL: ")
        self.server = tableau.Server(self.server)
        self.server.version = RESTApiVersion

        # get user credentials
        self.username = input("Username: ")
        self.password = input("Password: ")

        # generate tableau authentication object
        self.tableau_auth = tableau.TableauAuth(self.username, self.password)


    def downloadDatasources(self):
        '''Download all datasources from the specified server instance.'''

        if self.tableau_auth != None:
            try:
                print('\n')
                with self.server.auth.sign_in(self.tableau_auth):
                    for datasource in tableau.Pager(self.server.datasources):
                        self.server.datasources.download(datasource.id, include_extract=False)
                        print(datasource.name)
            except:
                print('Invalid login credentials and/or Tableau Server URL.')


    def parseDataSources(self):
        '''Parse the XML for each datasource (accepts either .tds or .tdsx format).'''
        print('\n')
        # parse datasources differently depending on the file type (.tds or .tdsx)
        for datasource in os.listdir():
            if datasource.endswith('.tds'):
                contents = xml.parse(datasource).getroot()
            elif datasource.endswith('.tdsx'):
                contents = twbx.xml_open(datasource).getroot()

            # if there's no xml to parse (e.g. a static csv datasource), then delete it
            if contents != None:
                if contents.attrib.get('formatted-name').startswith('federated.') == False:
                    pass
                else:
                    print(f'{datasource} is invalid, removing from directory.')
                    os.remove(datasource)

if __name__ == '__main__':

    # download all datasources that the user has permissions to
    datasourceDownload = datasourceRefresh('Published Extracts')
    datasourceDownload.serverLogin()
    datasourceDownload.downloadDatasources()
    datasourceDownload.parseDataSources()