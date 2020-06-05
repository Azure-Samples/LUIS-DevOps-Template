# 1. Project Setup

This document shows how to create the GitHub repository, Azure resources and configuration of [GitHub Actions](https://help.github.com/en/actions) workflows necessary to begin developing LUIS models. The setup instructions here are the quickest and the recommended path to getting started.

This template is pre-configured with a sample LUIS project ***vacation_requests***, defined in this repo in the [model.lu file](../luis-app/model.lu). The sample LUIS project defines a language understanding model to handle requests for vacation from employees. After running through the setup steps described in this document and the run through of the ["dev inner loop"](https://mitchdenny.com/the-inner-loop/) activities described in [2. Making updates to a LUIS app in a feature branch](2-feature-branches-and-running-pipelines.md), read [3. Customizing the Repository for your own project](3-customizing-own-project.md) for instructions on how to adapt this repository for use with your own solution.

## Table of Contents

In order to use this template to setup a repo for your own use, you will:

- [Create your repo](#create-your-repo) - Create your own GitHub repository from this template
- [Clone the repository](#clone-your-repository) to your own machine
- [Register in the LUIS Authoring portal](#register-in-the-luis-authoring-portal)
- [Provision Azure resources](#provisioning-azure-resources)
- [Setup the CI/CD workflows](#setup-the-cicd-workflows)
  - [Set environment variables in the workflow yaml](#set-environment-variables-for-resource-names-in-the-workflow-yaml)
  - [Create the Azure Service Principal](#create-the-azure-service-principal)
- [Protect the master branch](#protecting-the-master-branch)

## Create your repo

You'll use a GitHub repository and [GitHub Actions](https://help.github.com/en/actions) for running the workflows with build, LUIS quality testing, and release stages.

To create your repository:

- If you don't already have a GitHub account, create one by following the instructions at [Join GitHub: Create your account](https://github.com/join).
- Click the green **Use this template** button near the top of the [LUIS-DevOps-Samples](https://github.com/Azure-Samples/LUIS-DevOps-Samples) home page for this GitHub repo. This will copy this repository to a GitHub repository of your own that it will create.

   ![Use this template](./images/template_button.png?raw=true "Cloning the template repo")

  - Enter your own repository name where prompted.
  - Leave **Include all branches** unchecked as you only need the master branch of the source repo copied.
  - Click **Create repository from template** to create your copy of this repository.
- You can use the resulting repository for this guide and for your own experimentation.

## Clone your repository

After your repository is created, clone it to your own machine.

- Follow these steps to [clone your repository](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository) to your own machine.

## Register in the LUIS Authoring portal

Ensure that you have logged into the [LUIS authoring portal](https://docs.microsoft.com/azure/cognitive-services/luis/luis-reference-regions) for your chosen region using the same credentials you use to sign into Azure.

Choose the LUIS authoring portal most appropriate to your location, one of:

- [LUIS authoring portal](https://www.luis.ai/home) - <https://www.luis.ai>
- [LUIS authoring portal (Europe)](https://eu.luis.ai/home) - <https://eu.luis.ai>
- [LUIS authoring portal (Australia)](https://au.luis.ai/home) - <https://au.luis.ai>

> **Important:** If you are an existing LUIS user and have not yet migrated your account to use an Azure resource authoring key rather than an email, you should consider doing this now. If you do not migrate your account, you will not be able to select LUIS Authoring resources in the portal and it will not be possible to follow all the steps described in this solution walkthrough. See [Migrate to an Azure resource authoring key](https://docs.microsoft.com/azure/cognitive-services/luis/luis-migration-authoring) for more information.

## Provisioning Azure resources

The CI/CD workflows and the LUIS apps require some resources in Azure to be configured:

| Resource                                  | Description                                               |
|-------------------------------------------|-----------------------------------------------------------|
|Language Understanding Authoring resource  | Used by the workflows to author LUIS apps                 |
|Language Understanding Prediction resource | Used by the workflows to query the LUIS app during testing |
|Azure Storage account                      | Stores F-measure LUIS app quality testing results         |

To set up these resources, click the following button:

[![Deploy to Azure](https://aka.ms/deploytoazurebutton)](https://portal.azure.com/#create/Microsoft.Template/uri/https%3A%2F%2Fraw.githubusercontent.com%2FAzure-Samples%2FLUIS-DevOps-Template%2Fmaster%2Fazuredeploy.json)

When you click the button, you will be directed to the Azure Portal where you will need to provide unique names for the resources to be created by the template. Take a note of the names you enter for the following resources, as you will need them in the next step when we configure the CI/CD workflow:

- **Resource Group**
- **LUIS Authoring resource name** - must be unique across Azure
- **LUIS Prediction resource name** - must be unique across Azure
- **Storage account name** - 8-24 characters, lowercase letters and numbers, and must be unique across Azure

## Setup the CI/CD workflows

*If you are unfamiliar with GiHub actions then you may wish to review the [GitHub Actions documentation](https://help.github.com/actions).*

The GitHub Actions CI/CD workflows require a few setup steps to prepare for use. You will:

- Set [GitHub secrets](https://help.github.com/en/actions/configuring-and-managing-workflows/creating-and-storing-encrypted-secrets) for each of the resource names you created in Azure
- Get a token for an Azure Service Principal that you will configure and which you will store in **GitHub secrets**.

### Set GitHub Secrets

GitHub Secrets serve as parameters to the workflow, while also hiding secret values. When viewing the logs for a workflow on GitHub, secrets will appear as `***`.

You access GitHub Secrets by clicking on the **Settings** tab on the home page of your repository, or by going to `https://github.com/{your-GitHub-Id}/{your-repository}/settings`. Then click on **Secrets** in the **Options** menu, which brings up the UI for entering Secrets, like this:

![GitHub Secrets](./images/gitHubSecretsAzure.png?raw=true "Saving in GitHub Secrets")

Ensure each of the following secrets have been set, using the values you entered when you went through the **Deploy to Azure** dialog:

| Secret Name | Value |
|-------------|-------|
| **AZURE_RESOURCE_GROUP** | Azure resource group name |
| **AZURE_LUIS_AUTHORING_RESOURCE_NAME** | Azure LUIS authoring resource name |
| **AZURE_LUIS_PREDICTION_RESOURCE_NAME** | Azure LUIS prediction resource name |
| **AZURE_STORAGE_ACCOUNT_NAME** | Azure storage account name |

### Create the Azure Service Principal

You need to configure an [Azure Service Principal](https://docs.microsoft.com/cli/azure/create-an-azure-service-principal-azure-cli) to allow the workflow to login using your identity and to work with Azure resources on your behalf. You will save the access token for the service principal in the GitHub Secrets for your repository.

A Powershell script [./setup/create_sp.ps1](./setup/create_sp.ps1) is provided in this repo to make this simple and the easiest way to run the script is to use [Azure Cloud Shell](https://shell.azure.com).

To launch Azure Cloud Shell:

- Click  this button to open Cloud Shell in your browser: [![Launch Cloud Shell in a new window](./images/hdi-launch-cloud-shell.png)](https://shell.azure.com)
- Or select the **Cloud Shell** button on the menu bar at the upper right in the [Azure portal](https://portal.azure.com).

When Cloud shell launches, select the Azure subscription you used before to create the Azure resources, and if this is the first time of use, complete the initialization procedure.

To run the script:

1. Select **Powershell** at the top left of the terminal taskbar.

1. Click the **Upload/Download** button on the taskbar.

   ![Azure CloudShell Upload button](./images/cloudshell.png?raw=true "Uploading in Azure Cloud Shell")

1. Click **Upload** and navigate to the **/setup/create_sp.ps1** file in the cloned copy of this repo on your computer.

1. After the file has finished uploading, execute it:

   ```powershell
   ./create_sp.ps1
   ```

1. Enter the  requested input as prompted.

   > **IMPORTANT:** The Service Principal name you use must be unique within your Active Directory. When prompted enter your own unique name or hit *Enter* to use an auto-generated unique name. Also enter the **Resource Group** name you created when you configured the Azure resources:

   ![Azure create-for-rbac](./images/rbac.png?raw=true "Saving output from az ad sp create-for-rbac")

1. As prompted, copy the JSON that is returned, then in your repository, create a **GitHub secret** named **AZURE_CREDENTIALS** and paste the JSON in as the value.

![GitHub Secrets](./images/githubsecretsall.png?raw=true "Saving variables in GitHub Secrets")

## Protecting the master branch

It is recommended (and a software engineering best practice) to protect the master branch from direct check-ins. By protecting the master branch in this way, you require all developers to check-in changes by raising a Pull Request and you may enforce certain workflows such as requiring more than one pull request review or requiring certain status checks to pass before allowing a pull request to merge. Read [Configuring protected branches](https://help.github.com/en/github/administering-a-repository/configuring-protected-branches) to learn more about protecting branches in GitHub.

Note that the CI/CD workflow in this repository is configured to run when either of two GitHub events occur:

- When a developer raises a pull request to merge to the master branch
- When a merge to master occurs, for example after a PR is merged.

Branch Protections are not required for either of these events to occur, so setting them can be considered optional for enabling the operation of the CI/CD workflow. However, by setting branch protections as described in the rest of this section, you require developers to raise a PR in order to propose changes to master, which will trigger the CI/CD workflow to execute. The branch protections can be set to enforce the requirement that the PR cannot be merged until the workflow has completed successfully, so in this way the workflow acts as a quality gate, working to maintain the quality of the code being checked in.

> **Important:** Branch protections are supported on public GitHub repositories, or if you have a GitHub Pro subscription. If you are using a personal GitHub account and you created your repository as a private repository, you will have to change it to be **public** if you want to configure Branch protection policies. You can change your repository to be public in repository settings.

You should configure the specific workflows that you require for your software engineering organization. In order to support the solution walkthrough described in this documentation, you can configure branch protections as follows:

- **master** branch is protected from direct check-ins
- Pull request requires **1** review approval
- Status check configured so that the automation workflow when triggered by a Pull Request must complete successfully before the PR can be merged.

To configure these protections:

1. In the home page for your repository on **GitHub.com**, click on **Settings**
1. On the Settings page, click on **Branches** in the Options menu

   ![Branch protection settings](./images/branch_protection_settings.png?raw=true "Accessing branch protection settings")

1. Under **Branch protection rules**, click the **Add rule** button
1. Configure the rule:
   1. In the **Branch name pattern** box, enter **master**
   1. Check **Require pull request reviews before merging**
   1. Check **Require status checks to pass before merging**
   1. **Do not** check **Include administrators** as we will use the fact that you are an administrator of this repository to bypass restrictions on merging later on in this [developer solution walkthrough](2-feature-branches-and-running-pipelines.md#raising-the-pull-request). When you configure this repository to support your own project, consider checking this to enforce all the configured restrictions for administrators as well.

      ![Branch protection add rule](./images/branch_protection_rule.png?raw=true "Configuring branch protection rule")

   1. Click the **Create** button at the bottom of the page

> **Note:** Although you have checked **Require status checks to pass before merging** and the *luis_pr.yaml* workflow will run in response to the raising of a PR, it is not possible at this time to make it a hard requirement that the workflow should complete successfully before the PR can be merged. To make it a hard requirement, return to this configuration after the *luis_pr* workflow has run at least once and then you will be able to check the *Build and Test LUIS model (PR)* status check which will make successful completion a hard requirement.

## Next Steps

For the next steps, find out how to create a feature branch, make updates to your LUIS app, and to execute the CI/CD workflows:

- **Next:** [Creating a Feature branch, updating your LUIS app, and executing the CI/CD workflows](2-feature-branches-and-running-pipelines.md).

#### Further Reading

See the following documents for more information on this template and the engineering practices it demonstrates:

- [Creating a Feature branch, updating your LUIS app, and executing the CI/CD workflows](2-feature-branches-and-running-pipelines.md)

- [Adapting this repository to your own project](3-customizing-own-project.md#starting-a-new-project-from-scratch)

- [GitHub Actions workflow operation](4-pipeline.md#the-workflows)

- [Learn more about GitHub Actions](https://help.github.com/en/articles/about-github-actions)
