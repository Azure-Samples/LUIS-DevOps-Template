---
page_type: sample
languages:
- yaml
products:
- azure-language-understanding
- azure-cognitive-services
description: |
  DevOps practices for LUIS app development
urlFragment: luis-devops-sample
---

# Developing a LUIS app using DevOps practices

![Flask sample MIT license badge](https://img.shields.io/badge/license-MIT-green.svg)

<!-- 
Guidelines on README format: https://review.docs.microsoft.com/help/onboard/admin/samples/concepts/readme-template?branch=master

Guidance on onboarding samples to docs.microsoft.com/samples: https://review.docs.microsoft.com/help/onboard/admin/samples/process/onboarding?branch=master

Taxonomies for products and languages: https://review.docs.microsoft.com/new-hope/information-architecture/metadata/taxonomies?branch=master
-->

Sample demonstrating how to develop a LUIS application while following engineering practices that adhere to software engineering fundamentals around source control, testing, CI/CD and release management.

This sample shows how to get GitHub Actions working with a sample LUIS project ***vacation_requests***, defined in this repo in the [model.lu file](luis-app/model.lu). The project creates a language understanding model to handle requests for vacation from employees. You can [adapt this example](docs/customizing-own-project.md) to use with your own project.

## Contents

Outline the file contents of the repository. It helps users navigate the codebase, build configuration and any related assets.

| File/folder        | Description                                |
|--------------------|--------------------------------------------|
| `.github\workflows`| Sample GitHub Actions pipeline.            |
| `.gitignore`       | Define what to ignore at commit time.      |
| `azuredeploy.json` | ARM template used by **Deploy to Azure**.  |
| `CHANGELOG.md`     | List of changes to the sample.             |
| `CONTRIBUTING.md`  | Guidelines for contributing to the sample. |
| `docs`             | Documentation                              |
| `luis-app`         | Sample LUIS app and test files             |
| `setup`            | Setup scripts                              |
| `README.md`        | This README file.                          |
| `LICENSE`          | The license for the sample.                |

## Prerequisites

- [GitHub account](https://github.com/join)
- [Azure subscription](https://azure.microsoft.com/free/)
- LUIS authoring account, one of:
  - [LUIS authoring account](https://www.luis.ai/home)
  - [LUIS authoring account (Europe)](https://eu.luis.ai/home)
  - [LUIS authoring account (Australia)](https://au.luis.ai/home)
- [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest)

## Setup

You'll use a GitHub repository and GitHub Actions for running the multi-stage pipeline with build, LUIS quality testing, and release stages.

### Get the code

You'll use a GitHub repository and GitHub Actions for running the multi-stage pipeline with build, LUIS quality testing, and release stages. If you don't already have a GitHub account, create one by following the instructions at [Join GitHub: Create your account](https://github.com/join).

Next you must create a new repository to hold the code and the GitHub Actions pipelines. To create your repository:

- Click the green **Use this template** button near the top of the [LUISDevOpsSample](https://github.com/andycw/LUISDevOpsSample) home page for this GitHub repo, or click [this link](https://github.com/andycw/LUISDevOpsSample/generate). This will copy this repository to your own GitHub repository and squashes the history.
   ![Use this template](docs/images/template_button.png?raw=true "Cloning the template repo")
  - Enter your own repository name where prompted.
  - Leave **Include all branches** unchecked as you only need the master branch of the source repo copied.
  - Click **Create repository from template** to create your copy of this repository.
- You can use the resulting repository for this guide and for your own experimentation.

### Clone your repository

After your repository is created, clone it to your own machine. You can follow these steps to [clone your repository](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) to your own machine.

### Provisioning Azure resources

The CI/CD pipeline and the LUIS apps require some resources in Azure to be configured:

| Resource                                  | Description                                               |
|-------------------------------------------|-----------------------------------------------------------|
|Language Understanding Authoring resource  | Used by the pipeline to author LUIS apps                  |
|Language Understanding Prediction resource | Used by the pipeline to query the LUIS app during testing |
|Azure Storage account                      | Stores F-measure LUIS app quality testing results         |

To set up these resources, click the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FAndyCW%2FLUISDevOpsSample%2Fmaster%2Fazuredeploy.json)

When you click the button, it takes you to a web page in the Azure Portal where you can enter the names of the resources. Enter your own values on this page, bearing in mind that your names must be unique across Azure:

- **Resource Group**
- **LUIS Authoring resource name**
- **LUIS Prediction resource name**
- **Storage account name**

Take a note of the names you enter, as you will need them in the next step when we configure the CI/CD pipeline.

### Setup the CI/CD pipeline

The CI/CD pipeline requires a few setup steps to prepare it for use. You will:

- Set environment variables in the pipeline YAML file to match the resource names you created in Azure
- Get a token for an Azure Service Principal that you will configure and which you will store in GitHub secrets

#### Set Environment Variables for Resource names in the pipeline YAML

The CI/CD pipeline is defined in the **luis_ci.yaml** file in the **/.github/workflows** folder in your cloned repository. At the top of this file, a number of environment variables are defined:

- variables for the names of the Azure resources
- **LUIS_MASTER_APP_NAME** environment variable defines the name of the LUIS app that is built from the source checked into the master branch, and which the pipeline will create when it first runs.

Edit the **luis_ci.yaml** file and change the environment variables to match the names of the Azure resources you defined earlier. You can also change the name of the master LUIS app specified in the **LUIS_MASTER_APP_NAME** variable, if you wish. Also, set the **IS_PRIVATE_REPOSITORY** value to `true` if your repository is private. For example:

```yml
env:
  # Set the Azure Resource Group name
  AzureResourceGroup: YOUR_RESOURCE_GROUP_NAME
  # Set the Azure LUIS Authoring Resource name
  AzureLuisAuthoringResourceName: YOUR_LUIS_AUTHORING_RESOURCE_NAME
  # Set the Azure LUIS Prediction Resource name
  AzureLuisPredictionResourceName: YOUR_LUIS_PREDICTION_RESOURCE_NAME
  # Set the Azure Storage Account name
  AzureStorageAccountName: yourstorageaccountname
  
  # Set the name of the master LUIS app
  LUIS_MASTER_APP_NAME: LUISDevOps-master
  # If your repository is Private, set this to true
  IS_PRIVATE_REPOSITORY: false
```

When you have made your edits, save them, commit the changes and push the changes up to update the repository:

   ```bash
   git add .
   git commit -m "Updated parameters"
   git push
   ```

#### Create the Azure Service Principal

You need to configure an Azure Service Principal to allow the pipeline to login using your identity and to work with Azure resources on your behalf. You will save the access token for the service principal in the GitHub Secrets for your repository.

1. Install the Azure CLI on your machine, if not already installed. Follow these steps to [install the Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli?view=azure-cli-latest) on your system.

1. Open a terminal window and log into Azure:

    ```bash
    az login
    ```

   If the CLI can open your default browser, it will do so and load an Azure sign-in page. Sign in with your account credentials in the browser.

   Otherwise, open a browser page at https://aka.ms/devicelogin and enter the authorization code displayed in your terminal.

1. Execute the following command to confirm the selected azure subscription:

   ```bash
   az account show
   ```

1. If you have more than one subscription and do not have the correct subscription selected, select the right subscription with:

   ```bash
   az account set -s {Name or ID of subscription}
   ```

1. Go to the root folder of your cloned repository. Then execute the following script to create an Azure Service Principal:   
**IMPORTANT:** The Service Principal name you use must be unique within your Active Directory, so enter your own unique name for this service principal when prompted. Also enter the **Resource Group** name and the **Azure Key Vault** name you created when you configured the Azure resources:

   If you are using `bash`:

   ```bash
   ./setup/create_sp.sh
   ```
    
   If you are using `Powershell`:
    
   ```powershell
   ./setup/create_sp.ps1
   ```

   ![Azure create-for-rbac](docs/images/rbac.png?raw=true "Saving output from az ad sp create-for-rbac")

1. As prompted, copy the JSON that is returned, then in your repository, create a **GitHub secret** named **AZURE_CREDENTIALS** and paste the JSON in as the value.

   You access GitHub Secrets by clicking on the **Settings** tab on the home page of your repository, or by going to https://github.com/*your-GitHub-Id*/*your-repository*/settings. Then click on **Secrets** in the **Options** menu, which brings up the UI for entering Secrets, like this:

   ![GitHub Secrets](docs/images/gitHubSecretsAzure.png?raw=true "Saving in GitHub Secrets")

#### Store LUIS Keys in GitHub Secrets

You must also save the LUIS Authoring and Prediction resource keys in GitHub Secrets so that the pipeline can use them. You can get the keys for these resources from the Azure Portal.

![LUIS resource keys in Azure Portal](docs/images/azureLUISkey.png?raw=true "Getting the LUIS resource keys")

Alternatively, you can retrieve them using the Azure CLI, using the Azure Resource Group name and the LUIS Prediction resource names you entered when you configured the resources in Azure:

<code>
az cognitiveservices account keys list --name *LUISAuthoringResourceName* --resource-group *ResourceGroup*
</code>

Repeat this for both your **LUIS Authoring** and **Prediction** resources.

Save these keys in **GitHub Secrets** in your repository, using the following key names:


| Key                      |         value            |
|--------------------------|--------------------------|
| **LUISAuthoringKey**     |  The LUIS Authoring resource key  |
| **LUISPredictionKey**    |  The LUIS Prediction resource key |  

![LUIS resource keys saved in GitHub Secrets](docs/images/saveGitHubSecretsLUIS.png?raw=true "Saving the LUIS resource keys in GitHub Secrets")

### Protecting the master branch

It is software engineering best practices to protect the master branch from direct check-ins. By protecting the master branch, you require all developers to check-in changes by raising a Pull Request and you may enforce certain workflows such as requiring more than one pull request review or requiring certain status checks to pass before allowing a pull request to merge. You can learn more about Configuring protected branches in GitHub [here](https://help.github.com/en/github/administering-a-repository/configuring-protected-branches).

> **Important:** Branch protections are supported on public GitHub repositories, or if you have a GitHub Pro subscription. If you are using a personal GitHub account and you created your repository as a private repository, you will have to change it to be **public** if you want to configure Branch protection policies. You can change your repository to be public in repository settings.

You configure the specific workflows you require in your own software engineering organization. For the purposes of this sample, you will configure branch protections as follows:

- **master** branch is protected from direct check-ins
- Pull request requires **1** review approval (1 reviewer is suggested for this sample for simplicity, but it is considered best practice to require at least 2 reviewers on a real project)
- Status check configured so that the automation pipeline when triggered by a Pull Request must complete successfully before the PR can be merged.

To configure these protections:

1. In the home page for your repository on **GitHub.com**, click on **Settings**
1. On the Settings page, click on **Branches*** in the Options menu

   ![Branch protection settings](docs/images/branch_protection_settings.png?raw=true "Accessing branch protection settings")
1. Under **Branch protection rules**, click the **Add rule** button
1. Configure the rule:
   1. In the **Branch name pattern** box, enter **master**
   1. Check **Require pull request reviews before merging**
   1. Check **Require status checks to pass before merging**
   1. It is **not** recommended for the purposes of this sample to also check **Include administrators** as we will use the fact that you are an administrator of this repository to bypass restrictions on merging later on in this tutorial. However for a real project, consider checking this to enforce all the configured restrictions for administrators as well.

   ![Branch protection add rule](docs/images/branch_protection_rule.png?raw=true "Configuring branch protection rule")
   1. Click the **Create** button at the bottom of the page

## Running the sample

For the next steps, find out how to create a feature branch, make updates to your LUIS app, and to execute the CI/CD pipelines:

- **Next:** [Creating a Feature branch, updating your LUIS app, and executing the CI/CD pipelines](docs/feature-branches-and-running-pipelines.md).

## Further Reading

See the following documents for more information on this sample and the engineering practices it demonstrates:

- [Creating a Feature branch, updating your LUIS app, and executing the CI/CD pipelines](docs/feature-branches-and-running-pipelines.md)

- [Adapting this sample to your own project](docs/customizing-own-project.md)

- [CI/CD pipeline operation](docs/pipeline.md)

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit https://cla.opensource.microsoft.com.

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
