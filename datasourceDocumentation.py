# tableau libraries
import tableauserverclient as tableau
import tableaudocumentapi.xfile as twbx
import tableaudocumentapi.field as tableauFields
import xml.etree.ElementTree as xml

# generic libraries
import getpass
import json
import csv
import os
import operator


class tableauServerDataDictionary():
    '''
    A class for building a Tableau Server Data Dictionary. 
    Optionally specify a subdirectory where the datasources are located (assumes
    the datasources are located in the current working directory if no subdirectory 
    is provided).
    '''

    def __init__(self, workingDirectory = os.getcwd()):
        '''Instatiate a new Tableau Server Data Dictionary'''

        # set the default working directory. if the user specifies a working directory, navigate to it.
        self.originalWorkingDirectory = os.getcwd()
        os.chdir(workingDirectory)
        self.workingDirectory = os.getcwd()

        # create a blank data dictionary and array of datasources to parse
        self.TableauServerDataDictionary = {}
        self.parsedDatasources = []

        # parse datasources and build the data dictionary
        self.parseDataSources()
        self.buildSelfServiceDataSources()


    def parseDataSources(self):
        '''Parse the XML for each datasource (accepts either .tds or .tdsx format).'''

        # parse datasources differently depending on the file type (.tds or .tdsx)
        for datasource in os.listdir():
            if datasource.endswith('.tds'):
                contents = xml.parse(datasource).getroot()
            elif datasource.endswith('.tdsx'):
                contents = twbx.xml_open(datasource).getroot()

            # if there's no xml to parse (e.g. a static csv datasource), then delete it
            if contents != None:
                if contents.attrib.get('formatted-name').startswith('federated.') == False:
                    self.parsedDatasources.append(contents)
                else:
                    print(f'{datasource} is invalid, removing from directory.')
                    os.remove(datasource)


    def buildSelfServiceDataSources(self):
        '''Identify all of the data sources in Self Service folders.'''

        # for each datasource, build the data catalog (a list of fields and metadata)
        for datasource in self.parsedDatasources:
            print(datasource.get('formatted-name'))
            self.TableauServerDataDictionary[datasource.get('formatted-name')] = self.buildDataCatalog(datasource)


    def buildDataCatalog(self, datasourceXML):
        '''Build out the data catalog for an individual datasource (provided as XML)'''
        
        # instantiate a blank JSON template
        JSON = {'fields':{}}

        # add in the list of fields along with placeholders for hierarchy and datatype
        for node in datasourceXML.iter('metadata-record'):
            JSON['fields'][node.find('remote-name').text] = {
                'alias': None,
                'hierarchy': None,
                'hierarchyOrder': None,
                'hidden': 0,
                'folder': 'Uncategorized',
                'calculatedField': 0,
                'calculatedFieldName': None
                }

        # add calculated fields
        JSON = self.getCalculatedFields(JSON, datasourceXML)

        # add hidden property
        JSON = self.getHiddenFields(JSON, datasourceXML)

        # add aliases
        JSON = self.getAliases(JSON, datasourceXML)

        # add hierarchy attributes
        JSON = self.getHierarchies(JSON, datasourceXML)

        # add folder names for each field (if applicable)
        JSON = self.getFolders(JSON, datasourceXML)

        return JSON


    def getCalculatedFields(self, JSON, datasourceXML):
        '''Identify friendly names for calculated fields.'''

        # Define a dictionary to hold the list of folders and fields
        fieldList = {}
        tempJSON = JSON

        # Determine friendly names for calculated fields
        for node in datasourceXML.iter('column'):
            if '[Calculation_' in node.get('name'):
                fieldList[node.get('caption')] = node.get('name').replace(']','').replace('[','')

        # append calculated fields to the JSON blob
        for field, value in fieldList.items():
            tempJSON['fields'][field.replace(']','').replace('[','')] = {
                'alias': None,
                'hierarchy': None,
                'hierarchyOrder': None,
                'hidden': 0,
                'folder': 'Uncategorized',
                'calculatedField': 1,
                'calculatedFieldName': value
            }

        return tempJSON


    def getHiddenFields(self, JSON, datasourceXML):
        '''Identify hidden fields.'''

        # Define a dictionary to hold the list of folders and fields
        fieldList = {}
        tempJSON = JSON

        # Determine hidden property for calculated fields and normal fields
        for column in datasourceXML.iter('column'):
            if '[Calculation_' in column.get('name') and column.get('hidden') == 'true':
                fieldList[column.get('caption').replace(']','').replace('[','')] = 1
            elif column.get('hidden') == 'true':
                fieldList[column.get('name').replace(']','').replace('[','')] = 1

        # set hidden property for all fields in data catalog
        for field, value in tempJSON['fields'].items():
            if field in fieldList:
                value['hidden'] = 1

        return tempJSON


    def getAliases(self, JSON, datasourceXML):
        '''Identify friendly names for calculated fields.'''

        # Define a dictionary to hold the list of folders and fields
        fieldList = {}
        tempJSON = JSON

        # Determine aliases for calculated fields and normal fields
        for column in datasourceXML.iter('column'):
            if '[Calculation_' in column.get('name'):
                fieldList[column.get('caption').replace(']','').replace('[','')] = column.get('caption').replace(']','').replace('[','')
            elif column.get('caption') != None:
                fieldList[column.get('name').replace(']','').replace('[','')] = column.get('caption').replace(']','').replace('[','')

        # set aliases for all fields in data catalog
        for field, value in tempJSON['fields'].items():
            if field in fieldList:
                value['alias'] = fieldList[field]

        return tempJSON


    def getHierarchies(self, JSON, datasourceXML):
        '''Identify fields that belong in a hierarchy'''
        tempJSON = JSON
        hierarchies = {}

        # get hierarchy names
        for hierarchy in datasourceXML.iter('drill-path'):
            hierarchyName = hierarchy.get('name')
            hierarchies[hierarchyName] = []

            # get hierarchy items and their order
            for hierarchyItem in hierarchy:
                hierarchies[hierarchyName].append(hierarchyItem.text.replace(']','').replace('[',''))

        # for each field in the provided JSON, determine hierarchy (if applicable) and order
        for field, data in tempJSON['fields'].items():
            for hierarchy in hierarchies:
                # ensure that the alias name is used for searching if one exists
                if field in hierarchies[hierarchy]:
                    data['hierarchy'] = hierarchy
                    data['hierarchyOrder'] = hierarchies[hierarchy].index(field)
                elif data['alias'] in hierarchies[hierarchy]:
                    data['hierarchy'] = hierarchy
                    data['hierarchyOrder'] = hierarchies[hierarchy].index(data['alias'])
                elif data['calculatedFieldName'] in hierarchies[hierarchy]:
                    data['hierarchy'] = hierarchy
                    data['hierarchyOrder'] = hierarchies[hierarchy].index(data['calculatedFieldName'])

        return tempJSON


    def getFolders(self, JSON, datasourceXML):
        '''Identify folder names for all fields'''

        # create a placeholder for folder/field structure
        folderList = {}
        tempJSON = JSON

        # get folder names and folder items
        for folder in datasourceXML.iter('folder'):
            folderName = folder.get('name').replace(']','').replace('[','')
            folderList[folderName] = {}
            for folderItem in folder.iter('folder-item'):
                folderItemName = folderItem.get('name').replace(']','').replace('[','')
                folderList[folder.get('name')][folderItemName] = folderItem.get('type')

        # for each field in the provided JSON, determine folder attribute
        for field, data in tempJSON['fields'].items():
            for folder in folderList:
                for folderField in folderList[folder]:
                    if data['calculatedField'] == 1:
                        if data['calculatedFieldName'] == folderField or data['alias'] == folderField:
                            data['folder'] = folder
                    elif data['calculatedField'] == 0:
                        if field == folderField or data['alias'] == folderField:
                            data['folder'] = folder

        # place hierarchies in the correct folder
        for folder in datasourceXML.iter('folder'):
            for folderItem in folder:
                if folderItem.get('type') == 'drillpath':
                    for field, data in tempJSON['fields'].items():
                        if data['hierarchy'] == folderItem.get('name'):
                            data['folder'] = folder.get('name')

        return tempJSON


    def saveToJSON(self):
        '''Dump the data dictionary into TableauServerDataDictionary.json'''

        # return to the original working directory
        os.chdir(self.originalWorkingDirectory)

        # write the JSON file to the original working directory
        with open('TableauServerDataDictionary.json', 'w') as outfile:
            json.dump(self.TableauServerDataDictionary, outfile, sort_keys=True)


    def saveToMarkdown(self):
        '''Dump the data dictionary into TableauServerDataDictionary.md'''

        # return to the original working directory
        os.chdir(self.originalWorkingDirectory)

        # write a markdown file including datasource names and fields
        with open('TableauServerDataDictionary.md', 'w') as f:

            # load data dictionary and create folders placeholder
            dataDictionary = self.TableauServerDataDictionary
            folders = {}

            # reorganize the fields to be grouped by folder and datasource
            for datasource in dataDictionary:
                folders[datasource] = {}

                # add folders
                for field, value in dataDictionary[datasource]['fields'].items():
                    folders[datasource][value['folder']] = {}

                # add folder items and hierarchies
                for field, value in dataDictionary[datasource]['fields'].items():

                    # identify distinct folder items
                    if value['folder'] in folders[datasource] and value['hierarchy'] == None:
                        if value['hidden'] == 0:
                            folders[datasource][value['folder']][(field if value['alias'] == None else value['alias'])] = {'hierarchy': 0, 'fields': None}

                    # identify distinct hierarchies
                    elif value['hidden'] == 0 and value['hierarchy'] != None:
                        folders[datasource][value['folder']][value['hierarchy']] = {'hierarchy': 1, 'fields': None}

                # add fields that are contained within each hierarchy
                for folder, folderAttributes in folders[datasource].items():
                    for item, value in folderAttributes.items():
                        if value['hierarchy'] == 1:
                            x = [[(hierarchyField if data['alias'] == None else data['alias']), data['hierarchyOrder']] for hierarchyField, data in dataDictionary[datasource]['fields'].items() if data['hierarchy'] == item]
                            folderAttributes[item]['fields'] = sorted(x, key=lambda x: x[1])

            # write the results to markdown
            for datasource in sorted(folders):
                f.write(f'## __{datasource}__\n')
                for folder in sorted(folders[datasource]):
                    f.write(f'- __{folder}__\n')
                    for field, value in sorted(folders[datasource][folder].items()):
                        f.write(f'    - {field}\n')
                        if value['hierarchy'] == 1:
                            for i in value['fields']:
                                f.write(f'        - {i[0]}\n')
                f.write('------\n')

if __name__ == '__main__':

    # create a data dictionary from the published extracts folder
    tableauDocumentation = tableauServerDataDictionary('Published Extracts')

    # write the data dictionary to a JSON and Markdown file
    tableauDocumentation.saveToJSON()
    tableauDocumentation.saveToMarkdown()