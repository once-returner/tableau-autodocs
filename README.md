# Tableau Server AutoDocs for Data Sources

This repository is designed to create automatic documentation for all [self-service data sources published to a Tableau Server instance](https://onlinehelp.tableau.com/current/pro/desktop/en-us/publish_datasources.htm).

## Basic requirements

This README assumes that you have Python and git installed. You can download Python [here](https://www.python.org/downloads/) and you can download git [here](https://git-scm.com/downloads). It's recommended to add Python and git to the PATH variable to follow along with any commands listed below.

## Understanding the use case

This tool was developed due to our team using Tableau Server as a self-service data warehouse for business users. Since we created 50+ data sources based on a variety of user needs, we found ourselves lacking good documentation.

Our Tableau development team is small, lazy, and automation-oriented. We cannot keep up with ongoing changes to our growing list of data sources, so we developed this tool.

## Recommended data source structure

For every data source in your self-service data warehouse, we recommend that you [rename every field](https://kb.tableau.com/articles/howto/renaming-dimension-column-row-headers) to something user-friendly and hide any fields that would confuse the user. We also recommend that you [group fields by folder](https://onlinehelp.tableau.com/current/pro/desktop/en-us/datafields_dwfeatures.htm).

## Tool capabilities

### datasourceRefresh.py

The datasourceRefresh.py script prompts you to log into a Tableau Server instance and then downloads all data sources into a directory called **Published Extracts**.

### datasourceDocumentation.py

The datasourceDocumentation.py script is the core of the "AutoDocs" functionality, and is intended to be run after the datasourceRefresh.py script. It will document every valid data source (.tds, .tdsx, .hyper) in the **Published Extracts** directory.

**Sample JSON:**

The generated JSON file contains a collection of data source objects, named per each data source. All relevant data points are stored on a per-field basis. This is ***much*** easier to interpret than the base XML that is contained in a .tds file.

```json
{
    "Sample Data Source": {
        "fields": {
            "product_cat": {
                "alias": "Product Category",
                "calculatedField": 0,
                "calculatedFieldName": null,
                "folder": "Products",
                "hidden": 0,
                "hierarchy": "Product Hierarchy",
                "hierarchyOrder": 0
            },
            "product_name": {
                "alias": "Product Name",
                "calculatedField": 0,
                "calculatedFieldName": null,
                "folder": "Products",
                "hidden": 0,
                "hierarchy": "Product Hierarchy",
                "hierarchyOrder": 1
            },
            "Order Volume": {
                "alias": null,
                "calculatedField": 1,
                "calculatedFieldName": null,
                "folder": "Uncategorized",
                "hidden": 0,
                "hierarchy": null,
                "hierarchyOrder": null
            }
        }
    }
}
```

**Sample Markdown:**

Alongside the JSON file, a Markdown file is generated. This functions as the data dictionary and can be saved to a git repository or exported as a business document. There are plenty of tools out there to export Markdown to HTML or PDF for users to read (we use the [Markdown All in One extension for VS Code](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one)  by Yu Zhang).

```markdown
---
## __Sample Data Source__
- __Products__
    - Product Hierarchy
        - Product Category
        - Product Name
- __Uncategorized__
    - Order Volume
---
```

## Executing the Python scripts

Start by opening up git Bash and [cloning our repository](https://git-scm.com/book/en/v2/Git-Basics-Getting-a-Git-Repository). If you don't have the pipenv library installed, go ahead and do that now. You can find the basics of using pipenv [here](https://pipenv.readthedocs.io/en/latest/basics/).

```bash
$ pip install pipenv
```

Once you have pipenv installed, navigate to the project folder and run the following commands to start up a virtual environment with the correct dependencies.

```bash
$ pipenv install

Installing dependencies from Pipfile.lock (6ffcd4)…
  ================================ 7/7 - 00:00:09
To activate this project's virtualenv, run pipenv shell.
Alternatively, run a command inside the virtualenv with pipenv run.

$ pipenv shell

Launching subshell in virtual environment…
```

The behavior depends on the context, but likely you will be kept in the same terminal window and can then run the following commands. Once you enter your Tableau credentials, each data source successfully downloaded will print out and any invalid datasources will be removed (supported filetypes are .tds, .tdsx, and .hyper).

```bash
$ pipenv run python datasourceRefresh.py

Datasources will download to: C:\somewhere\Published Extracts

Server URL: https://something.someplace.com/
Username: yourusername
Password: yourpassword

Sample Datasource 1
Sample Datasource 2
Sample Datasource 3

sampleExcelDatasource.tdsx is invalid, removing from directory.

$ pipenv run python datasourceDocumentation.py

```

## Contribute

Simply branch off of master, make your changes, and submit a pull request. Please check out the [basics of pipenv](https://pipenv.readthedocs.io/en/latest/basics/) so that you can update the **Pipfile** and **Pipfile.lock** files if any package requirements have changed.