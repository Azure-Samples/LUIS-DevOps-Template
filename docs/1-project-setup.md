# 1. Project Setup

This document shows how to create the GitHub repository, Azure resources and configuration of GitHub Actions pipelines necessary to begin developing LUIS models. The setup instructions here are the quickest and the recommended path to getting started.

This template is pre-configured with a sample LUIS project ***vacation_requests***, defined in this repo in the [model.lu file](../luis-app/model.lu). The sample LUIS project defines a language understanding model to handle requests for vacation from employees. After running through the setup steps described in this document and the run through of the "dev inner loop" activities described in [2. Making updates to a LUIS app in a feature branch](2-feature-branches-and-running-pipelines.md), read [3. Customizing the Repository for your own project](3-customizing-own-project.md) for instructions on how to adapt this repository for use with your own solution.

## Table of Contents

In order to use this template to setup a repo for your own use, you will:

- [Get the code](#get-the-code) - Create your own GitHub repository from this template
- [Clone the repository](#clone-your-repository) to your own machine
- [Provision Azure resources](#provisioning-azure-resources)
- [Setup the CI/CD pipeline](#setup-the-ci/cd-pipeline)
  - [Set environment variables in the pipeline yaml](#set-environment-variables-for-resource-names-in-the-pipeline-yaml))
  - [Create the Azure Service Principal](#create-the-azure-service-principal)
  - [Store LUIS Keys in GitHub Secrets](#store-luis-keys-in-github-secrets)
- [Protect the master branch](#protecting-the-master-branch)

## Get the code

You'll use a GitHub repository and GitHub Actions for running the multi-stage pipeline with build, LUIS quality testing, and release stages.

To create your repository:

- If you don't already have a GitHub account, create one by following the instructions at [Join GitHub: Create your account](https://github.com/join).
- Click the green **Use this template** button near the top of the [LUIS-DevOps-Samples](https://github.com/Azure-Samples/LUIS-DevOps-Samples) home page for this GitHub repo. This will copy this repository to a GitHub repository of your own that it will create.
   ![Use this template](/images/template_button.png?raw=true "Cloning the template repo")
  - Enter your own repository name where prompted.
  - Leave **Include all branches** unchecked as you only need the master branch of the source repo copied.
  - Click **Create repository from template** to create your copy of this repository.
- You can use the resulting repository for this guide and for your own experimentation.

## Clone your repository

After your repository is created, clone it to your own machine.

- Follow these steps to [clone your repository](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) to your own machine.

## Provisioning Azure resources

The CI/CD pipeline and the LUIS apps require some resources in Azure to be configured:

| Resource                                  | Description                                               |
|-------------------------------------------|-----------------------------------------------------------|
|Language Understanding Authoring resource  | Used by the pipeline to author LUIS apps                  |
|Language Understanding Prediction resource | Used by the pipeline to query the LUIS app during testing |
|Azure Storage account                      | Stores F-measure LUIS app quality testing results         |

To set up these resources, click the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FAzure-Samples%2FLUIS-DevOps-Samples%2Fmaster%2Fazuredeploy.json)

When you click the button, it takes you to a web page in the Azure Portal where you can enter the names of the resources. Take a note of the names you enter, as you will need them in the next step when we configure the CI/CD pipeline.:

- **Resource Group**
- **LUIS Authoring resource name** - must be unique across Azure
- **LUIS Prediction resource name** - must be unique across Azure
- **Storage account name** - 8-24 characters, lowercase letters and numbers, and must be unique across Azure

## Setup the CI/CD pipeline

The GitHub Actions CI/CD pipeline requires a few setup steps to prepare it for use. You will:

- Set environment variables in the pipeline YAML file to match the resource names you created in Azure
- Get a token for an Azure Service Principal that you will configure and which you will store in GitHub secrets

### Set Environment Variables for Resource names in the pipeline YAML

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

### Create the Azure Service Principal

You need to configure an Azure Service Principal to allow the pipeline to login using your identity and to work with Azure resources on your behalf. You will save the access token for the service principal in the GitHub Secrets for your repository.

1. Install the Azure CLI on your machine, if not already installed. Follow these steps to [install the Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli?view=azure-cli-latest) on your system.

1. Open a terminal window in the root folder of your cloned repository. and log into Azure:

    ```bash
    az login
    ```

   If the CLI can open your default browser, it will do so and load an Azure sign-in page. Sign in with your account credentials in the browser.

   Otherwise, open a browser page at <https://aka.ms/devicelogin> and enter the authorization code displayed in your terminal.

1. Show the selected azure subscription. If you have more than one subscription and do not have the correct subscription selected, select the right subscription with `az account set`:

   ```bash
   az account show
   az account set -s {Name or ID of subscription}
   ```

1. Execute the following script to create an Azure Service Principal:

   > **IMPORTANT:** The Service Principal name you use must be unique within your Active Directory, so enter your own unique name for this service principal when prompted. Also enter the **Resource Group** name you created when you configured the Azure resources:

   If you are using `bash`:

   ```bash
   ./setup/create_sp.sh
   ```

   If you are using `Powershell`:

   ```powershell
   ./setup/create_sp.ps1
   ```

   ![Azure create-for-rbac](./images/rbac.png?raw=true "Saving output from az ad sp create-for-rbac")

1. As prompted, copy the JSON that is returned, then in your repository, create a **GitHub secret** named **AZURE_CREDENTIALS** and paste the JSON in as the value.

   You access GitHub Secrets by clicking on the **Settings** tab on the home page of your repository, or by going to `https://github.com/{your-GitHub-Id}/{your-repository}/settings`. Then click on **Secrets** in the **Options** menu, which brings up the UI for entering Secrets, like this:

   ![GitHub Secrets](./images/gitHubSecretsAzure.png?raw=true "Saving in GitHub Secrets")

### Store LUIS Keys in GitHub Secrets

You must also save the LUIS Authoring and Prediction resource keys in GitHub Secrets so that the pipeline can use them.

You can get the keys using the Azure CLI, specifying the Azure Resource Group name and the LUIS Prediction resource names you entered when you configured the resources in Azure:

<code>
az cognitiveservices account keys list --name <i>{LUISAuthoringResourceName}</i> --resource-group <i>{ResourceGroup}</i>

</code>

Repeat this for both your **LUIS Authoring** and **Prediction** resources, and save these keys in **GitHub Secrets** in your repository, using the following key names:

| Key                      |         value                     |
|--------------------------|-----------------------------------|
| **LUISAuthoringKey**     |  The LUIS Authoring resource key  |
| **LUISPredictionKey**    |  The LUIS Prediction resource key |  

![LUIS resource keys saved in GitHub Secrets](./images/saveGitHubSecretsLUIS.png?raw=true "Saving the LUIS resource keys in GitHub Secrets")

## Protecting the master branch

It is software engineering best practices to protect the master branch from direct check-ins. By protecting the master branch, you require all developers to check-in changes by raising a Pull Request and you may enforce certain workflows such as requiring more than one pull request review or requiring certain status checks to pass before allowing a pull request to merge. You can learn more about Configuring protected branches in GitHub [here](https://help.github.com/en/github/administering-a-repository/configuring-protected-branches).

> **Important:** Branch protections are supported on public GitHub repositories, or if you have a GitHub Pro subscription. If you are using a personal GitHub account and you created your repository as a private repository, you will have to change it to be **public** if you want to configure Branch protection policies. You can change your repository to be public in repository settings.

You configure the specific workflows you require in your own software engineering organization. For the purposes of this sample, you will configure branch protections as follows:

- **master** branch is protected from direct check-ins
- Pull request requires **1** review approval (1 reviewer is suggested for this sample for simplicity, but it is considered best practice to require at least 2 reviewers on a real project)
- Status check configured so that the automation pipeline when triggered by a Pull Request must complete successfully before the PR can be merged.

To configure these protections:

1. In the home page for your repository on **GitHub.com**, click on **Settings**
1. On the Settings page, click on **Branches** in the Options menu

   ![Branch protection settings](/images/branch_protection_settings.png?raw=true "Accessing branch protection settings")
1. Under **Branch protection rules**, click the **Add rule** button
1. Configure the rule:
   1. In the **Branch name pattern** box, enter **master**
   1. Check **Require pull request reviews before merging**
   1. Check **Require status checks to pass before merging**
   1. It is **not** recommended for the purposes of learning how to use this sample to also check **Include administrators**, as we will use the fact that you are an administrator of this repository to bypass restrictions on merging later on in this tutorial. However for a real project, consider checking this to enforce all the configured restrictions for administrators as well.

   ![Branch protection add rule](./images/branch_protection_rule.png?raw=true "Configuring branch protection rule")
   1. Click the **Create** button at the bottom of the page

## Updating the LUIS app in a feature branch

For the next steps, find out how to create a feature branch, make updates to your LUIS app, and to execute the CI/CD pipelines:

- **Next:** [Creating a Feature branch, updating your LUIS app, and executing the CI/CD pipelines](2-feature-branches-and-running-pipelines.md).

## Further Reading

See the following documents for more information on this template and the engineering practices it demonstrates:

- [Creating a Feature branch, updating your LUIS app, and executing the CI/CD pipelines](2-feature-branches-and-running-pipelines.md)

- [Adapting this repository to your own project](3-customizing-own-project.md#starting-a-new-project-from-scratch)

- [CI/CD pipeline operation](4-pipeline.md#pipeline-steps)
