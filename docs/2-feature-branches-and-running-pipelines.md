# 2. Making updates to a LUIS app in a feature branch

This document explains how to create a feature branch in your GitHub repository, how to make updates to your LUIS app and to save changes in source control, how to raise a pull request (PR) to merge the updates back into the master branch and how to execute continuous integration workflows.

In this example, we follow the [GitHub flow branching strategy](https://guides.github.com/introduction/flow/index.html) which is a simple and effective branching strategy. Broadly you will follow this flow:

* Developer creates a feature branch and does the feature/work in that branch.
* When done, the developer does a push of their changes and raises a pull request from their feature branch to master. The developer works on the updates using a LUIS app that they create solely to support the work in the feature branch.
* The continuous integration workflow is triggered automatically by the pull request and runs as a quality gate check. It builds a temporary LUIS app from the source in the PR, runs unit tests against it and then deletes it at the end of the run.
* If the workflow completes successfully, and reviewers approve the pull request, the developer merges the PR into master.
* The merge to master automatically triggers the full CI/CD workflow which:
  * Creates a new LUIS app version in the *master* LUIS app from the merged source. This LUIS app will be created if it does not already exist, such as on first run of the CI/CD workflow.
  * Runs unit test against it. If the tests fail, GitHub fails the workflow and notifies repository members by email.
  * If unit tests pass, creates a [GitHub Release](https://help.github.com/en/github/administering-a-repository/managing-releases-in-a-repository) of the repository.
  * Runs LUIS quality tests to determine and publish the F-measure of the new LUIS app version.

![GitFlow](images/GitFlow.png?raw=true "GitFlow")

This document explains how to run through these steps. Note that all steps involving `git` operations are shown using the **Git Bash shell**. Developers may have their own preference for using GUI tools or tooling built into developer tools such as Visual Studio Code to achieve the same result.

You will be performing the following steps to make updates to the LUIS app:

* [Making updates to a LUIS app in a feature branch](#2-making-updates-to-a-luis-app-in-a-feature-branch)
  * [Installing the required command line tools](#installing-the-required-command-line-tools)
  * [Creating a feature branch](#creating-a-feature-branch)
  * [Make your LUIS app updates](#make-your-luis-app-updates)
    * [Update the LUIS app using the LUIS Portal](#update-the-luis-app-using-the-luis-portal)
  * [Testing the new LUIS model](#testing-the-new-luis-model)
    * [Setting up for testing](#setting-up-for-testing)
    * [Testing the LUIS app](#testing-the-luis-app)
  * [Raising the pull request](#raising-the-pull-request)
  * [Running the CI/CD workflow](#running-the-cicd-workflow)
    * [Verifying the new LUIS master app version](#verifying-the-new-luis-master-app-version)
    * [Executing predictions against the LUIS app version endpoint](#executing-predictions-against-the-luis-app-version-endpoint)

## Installing the required command line tools

You will need to install the following tools:

1. **Bot Framework CLI** - this includes tools for working with LUIS apps. Follow these instructions to [install the Bot Framework CLI tools](https://github.com/microsoft/botframework-cli#installation).

1. **NLU.DevOps** - you use these tools for running tests against a LUIS model. Follow these instructions to [install the NLU.DevOps tools](https://github.com/microsoft/NLU.DevOps#getting-started-with-the-nludevops-cli).

## Creating a feature branch

If you followed the [setup instruction for this sample](../README.md) you will have cloned your repository from GitHub to your own machine. To set up a feature branch:

1. After the GitHub repository is cloned, navigate to the project directory:  
`$ cd my-LUIS-DevOps-sample`

1. Create a feature branch and check it out:  
`$ git checkout -B update-luis-sample`

## Make your LUIS app updates

Now that you are working inside the feature branch, you can make your updates to the LUIS app source, unit tests, and model verification tests. If this was a brand new project, you would need to create the LUDown representation of the first version of your LUIS app and the JSON files for testing and check them in. We use the [LUDown format](https://docs.microsoft.com/azure/bot-service/file-format/bot-builder-lu-file-format?view=azure-bot-service-4.0) to define a LUIS app since it can be maintained in a source control system and is human readable which enables the reviewing process because of its legibility.

In this sample, the LUDown for a sample application and the test files are provided:

* **luis-app/model.lu** - the LUDown encoding of the LUIS app
* **luis-app/tests/unittests.json** - the unit tests
* **luis-app/tests/verificationtests.json** - the verification tests

### Update the LUIS app using the LUIS Portal

For minor updates to a LUIS app, it is possible to edit the **model.lu** file directly. However, for most feature branch development, it is easier and more practical to make updates using the LUIS Portal.

To make updates using the LUIS Portal:

1. Sign into the LUIS portal for [your authoring and publishing region](https://docs.microsoft.com/azure/cognitive-services/luis/luis-reference-regions):
   * LUIS authoring portal - [https://www.luis.ai](https://www.luis.ai/home)
   * LUIS authoring portal (Europe) - [https://eu.luis.ai](https://eu.luis.ai/home)
   * LUIS authoring portal (Asia) - [https://au.luis.ai](https://au.luis.ai/home)  

   > **Important:** If you are an existing LUIS user and have not yet migrated your account to use an Azure resource authoring key rather than an email, you should consider doing this now. If you do not migrate your account, you will not be able to select LUIS Authoring resources in the portal and it will not be possible to follow all the steps described in this solution walkthrough. See [Migrate to an Azure resource authoring key](https://docs.microsoft.com/azure/cognitive-services/luis/luis-migration-authoring) for more information.

1. Select the Azure subscription and the authoring resource you want to use while you are working in the feature branch (note that this does not have to be the same subscription and/or authoring resource that you configured for the GitHub Actions workflows):

   ![Select Authoring Resource](images/LUIS_portal_authoring_resource.png?raw=true "Select authoring resource")

1. You will now create a LUIS app that you will use just for the work in this feature branch:

   1. Click **New app for conversation**. In the dropdown, click **Import as LU**.

   ![Import as LU](images/importaslu.png?raw=true "Import as LU")

   1. Select the **/luis-app/model.lu** file in this repo in the *Import new app* dialog, set a suitable name for the app such as **DEV-update-luis-sample** and click **Done**.

1. Now you can make your changes to the app. For the purposes of this sample, you will add a new training utterance to the **None** intent.
   1. From the **Intents** editor, click on the **None** intent.

   2. Enter a new example utterance, for example: **Great that we can do DevOps with LUIS** and hit **Enter**.

   ![Updating the None intent](images/noneintent.png?raw=true "Updating the None intent")

   1. Click **Train** at the top of the page.

   2. When training is complete, then click **Publish**, select **Staging Slot** and then click **Done**.

## Testing the new LUIS model

The CI workflows are setup to perform automated unit testing of the LUIS model when you raise your PR, and again when your changes are merged to master. The test utterances and the expected responses are defined in the **luis-app/tests/unittests.json** file.

It is good development practice for the developer to run all the unit tests manually during feature development to make sure that no problems have been introduced before checking in changes. For this, we use the **NLU.DevOps** tool, <https://github.com/NLU.DevOps/.>

### Setting up for testing

You need to enter settings for the test target LUIS app - the app you have just created - in an **appsettings.local.json** file. In the **luis-app** folder, a sample **appsettings.sample.json** has been provided. Rename this file to **appsettings.local.json** and then enter the required values:

```json
{
  "luisAppId": "***your LUIS App Id***",
  "luisEndpointKey": "****your LUIS endpoint key***",
  "luisPredictionResourceName": "***your LUIS prediction resource name***",
  "luisIsStaging": true
}
```

* You can find the **LUIS App Id** for your app by clicking the **Manage** tab in the LUIS Portal. The App ID is shown on the **Application Information** page.

* To get the **luisEndpointKey** value, go to the **Azure Resources** page on the **Manage** tab in the LUIS Portal, click on the **Prediction resources** tab and copy the **Primary Key** of your Azure *prediction resource*.

* To get the **luisPredictionResourceName**, enter the name of your prediction resource, for example **LUISDevOpsResource-Prediction**.

* Save this file.

### Testing the LUIS app

1. In your console terminal, set your current working directory to the *luis-app* folder.

1. Run the unit tests defined in /tests/unittests.json against the LUIS app you just published:  

   `dotnet nlu test -s luisV3 -u .\tests\unittests.json -o results.json`

1. The `nlu test` command runs your test utterances against the LUIS app endpoint and returns the results in the *results.json* file. In order to compare these new results with the expected results (defined in the *tests/unittests.json* file), use the `nlu compare` command:  

   `dotnet nlu compare -e .\tests\unittests.json -a results.json --unit-test`

1. This reports which tests have passed and failed:

![unit testing](images/nlucompare.png?raw=true "Unit Testing")

To find out more about unit testing with NLU.DevOps, read [Testing an NLU model](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Test.md) and [Analyzing NLU model results](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Analyze.md).

## Raising the pull request

Now that the changes have been applied to the LUIS app and you have tested it, you must download the updated LUIS app from the LUIS Portal and check in your changes and raise the PR.

1. Download the LUIS app version and convert to LUDown either at the command line or using the LUIS portal:

    * To download the app version at the command line:
       1. Use the following command:  
       <code>$ bf luis:version:export --appId <i>{your-appId}</i> --versionId "0.1" --endpoint <i>{your-authoring-endpoint}</i> --subscriptionKey <i>{your-authoring-key}</i> --out model.json</code>
          > Note: The App ID and Authoring Key are the same values you entered in the *appsettings.local.json* file. You can get the Authoring Endpoint from the **Manage** tab, **Azure Resources** page for your app in the Azure portal.

       1. Convert the JSON file to LUDown:  
       <code>$ bf luis:convert -i model.json -o model.lu</code>

    * Alternatively, to export the app from the LUIS portal:
       1. In the LUIS Portal, click the **Manage** tab at the top of the page, and then go to the **Versions** page.
       1. Select the latest version (there will only be one, version 0.1, if you have been following this solution walkthrough), click **Export** and then click **Export as LU**.
       1. Take the downloaded file (currently named as *{LUIS App Id}*_v0.1.lu) and rename it to **model.lu**

1. Copy the new **model.lu** file to **luis-app/model.lu** in your project, replacing the existing version of that file.

1. Add your changed file(s) to the commit and commit the changes:  
`$ git add -A`  
`$ git commit -m 'Updated the none intent'`

1. Push the changes up to the remote - the GitHub repository:  
`$ git push --set-upstream origin update-luis-sample`

1. In order to raise the Pull Request for these changes, we switch to the GitHub portal.
   * Go to your repository on github.com. Click on the **Pull requests** tab.
   * You should see a notification that you recently pushed the **update-luis-sample** branch. Click on the green Compare & pull request button.

   ![pull requests](images/compareandpullrequest.png?raw=true "Pull Requests")

   * In the **Open a pull request** page, click the green **Create pull request** button near the bottom of the page.

   * You will see that after the pull request is raised, the status screen shows that completion of the pull request is blocked because of **Review required**. In addition, after a few seconds, you will see an additional status display **Some checks haven't completed yet** and underneath that the status of the **LUIS-CI /Build and Test LUIS model (pull_request)** CI workflow as it runs, triggered by the raising of the pull request.

   ![pull request status](images/prstatuschecks.png?raw=true "Pull Request Status")

    * You can click on the **Details** link next to the Build workflow status to see the workflow stages as they execute.
    * Read more about the internals and operation of the workflow in the document [GitHub Actions workflow with NLU.DevOps](4-pipeline.md).

1. When the workflow has completed, the **All checks have passed** status shows as green since the CI workflow ran and the unit tests passed. The workflow has performed its function of a quality gate on the changes in the pull request. However, merging of the pull request is still blocked since at least 1 approving review is required by reviewers.

![merging is blocked](images/mergingblocked.png?raw=true "Merging is blocked")

1. On a real project, the changes should be reviewed and approved. However, for this sample, you can override this requirement since you are the Administrator of this repository.
   * Click on the **Merge pull request** button.
   * On the next page, check **Use your administrator privileges to merge this pull request.**
   * Click **Confirm merge**.

## Running the CI/CD workflow

If you click on the **Actions** tab immediately after you merge your pull request, you will see that the full CI/CD workflow has already been triggered and is executing by the push to master. The first job of this workflow is similar to the one that executed for the pull request, but it has some important differences in operation:

* It builds a new LUIS app version from the source that has been merged. It uses the LUIS app that is dedicated to the master branch, the name of which is set in the environment variables at the top of the **.github/workflows/luis_ci.yaml** file. The app is created if it does not already exist, such as on first run of the workflow.
* It runs the job **LUIS Build and Test** which builds the new LUIS master app version and runs unit tests against it and if the tests pass it creates a GitHub release for the new version.
* If the *LUIS Build and Test* job completes successfully, it runs the **LUIS CD** job . This job publishes the app version to the [Production endpoint](https://docs.microsoft.com/azure/cognitive-services/luis/luis-how-to-publish-app). It is a simple example of a CD (Continuous Delivery) workflow.
* It also runs the **LUIS F-measure testing** job which runs LUIS verification tests (equivalent to using the [batch testing](https://docs.microsoft.com/azure/cognitive-services/luis/luis-how-to-batch-test) capability in the LUIS portal).  
The **LUIS F-measure testing** job is currently configured to run concurrently with the **Create LUIS Release** job and runs purely as an advisory and does not block the **LUIS CD** job from running should it fail. It is provided as an example of how to perform model quality testing within the workflow. See  [Enabling the F-measure testing capability](3-customizing-own-project.md#enabling-the-f-measure-testing-capability) for details of how to enable this feature.
* If the workflow fails, the repository contributors and the author of the pull request are notified by email and must determine the failing tests and resolve the code failures that caused the workflow failure.

![CI/CD workflow completed](images/cicdpipelinecompleted.png?raw=true "CI/CD workflow completed")

### Verifying the new LUIS master app version

> **Note:** This solution uses [GitVersion](https://gitversion.net/docs/why) to increment the version number on every build. It looks at your git history on every commit to calculate what the version currently is, and calculates the new version number automatically using semantic versioning. You can instruct GitVersion to manually increment the major, minor or patch version using commit messages, or by setting the next-version property in the GitVersion.yml file in the root of your repository. Read more about [GitVersion Version Incrementing](https://gitversion.net/docs/more-info/version-increments) in the GitVersion documentation.

After the workflow has completed successfully, if you look on the home page of your repository, you can see that a new release has been created:

![GitHub Release](images/release.png?raw=true "GitHub Release")

When you click on this release flag, you can see the details of the new release, which is the zipped source code from the repository and a file called **luis_latest_version.json**.If you click on **luis_latest_version.json** you can download it and open it in a text editor. This gives you data about the new LUIS app version the workflow has created.

![GitHub Release Details](images/releasedetails.png?raw=true "GitHub Release Details")

To view the LUIS app version that the workflow has created:

1. Go to the LUIS Portal to the **My apps** page, select your Azure subscription and the LUIS authoring resource you configured for the workflow during [Provisioning Azure resources](1-project-setup.md#provisioning-azure-resources) while setting up this solution.
1. You will see the **LUISDevOps-master** app that the workflow has created. This name of this app is defined in the [Environment variables](4-pipeline.md#environment-variables) at the top of *luis_ci.yaml*.
1. Select the **LUISDevOps-master** app and go to the **Manage** tab, and then to **Versions**, you can see the LUIS app version that the workflow has built and tested.

![LUIS portal master app](images/luismasterapp.png?raw=true "LUIS portal master app")

> **Important:** If you are an existing LUIS user and have not yet migrated your account to use an Azure resource authoring key rather than an email, you should consider doing this now. If you do not migrate your account, you will not be able to select LUIS Authoring resources in the portal and it will not be possible to find apps in the portal that have been created using Azure LUIS Authoring resources, such as the app created by this workflow. See [Migrate to an Azure resource authoring key](https://docs.microsoft.com/azure/cognitive-services/luis/luis-migration-authoring) for more information.

### Executing predictions against the LUIS app version endpoint

You can test out the new LUIS app version by sending a prediction request from the LUIS portal using the **Test** button on the task bar:

1. In the LUIS portal, ensure that the **LUISDevOps-master** app is open.
1. Click the **Test** button on the taskbar.
1. Enter a test utterance, for example: *great now i can do devops with my luis apps*. Press **Enter**.
1. Click the **Inspect** link to view the response from the authoring endpoint.
1. Click **Compare with published** to send the request to the published endpoint. If you see the message *Please publish your model first*, click **Additional Settings** underneath the **Published** heading and select **Production** in the **Publish slot** dropdown.
1. You will see the prediction response returned from the LUIS service for the Production slot for this app. You can click **Show JSON view** if you want to view the JSON response from the service:

   ![Prediction request](images/testquery.png?raw=true "Prediction request")

1. Try other utterances, such as: *i want my vacation to start on july 4th and last for 10 days*.

## Next Steps

For the next steps, find out how to adapt this repository to your own project:

*-* **Next:** [Adapting this repository to your own project](3-customizing-own-project.md#starting-a-new-project-from-scratch).

#### Further Reading

See the following documents for more information on this template and the engineering practices it demonstrates:

* [Project Setup and configuration](1-project-setup.md)

* [Adapting this repository to your own project](3-customizing-own-project.md#starting-a-new-project-from-scratch)

* [GitHub Actions workflows](4-pipeline.md#workflow-steps)
