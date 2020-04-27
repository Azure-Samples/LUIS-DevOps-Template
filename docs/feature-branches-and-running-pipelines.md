# Updating a LUIS app in a feature branch and running the pipelines on check in

This document explains how to create a feature branch in your GitHub repository, how to make updates to your LUIS app and how to raise a pull request (PR) to merge the updates back into the master branch. 

In this sample, we follow the [GitHubFlow branching strategy](https://guides.github.com/introduction/flow/index.html) which is a simple and effective branching strategy. When using this strategy:

1. The master branch is always deployable
1. The developer creates a feature branch to work on changes
1. Developer does the feature/work in the feature branch
1. When done, the developer does a Push of their changes and raises a pull request from their feature branch to master
1. The continuous integration pipeline is triggered by the pull request and runs as a quality gate check, building a transient LUIS app from the source in the PR and runs unit tests against it
1. If the pipeline completes successfully, and reviewers approve the pull request, the developer merges the PR into master
1. The merge to master triggers the full CI/CD pipeline which:
   * Creates a new LUIS app version from the merged source
   * Runs unit test against it
   * If tests pass, creates a [GitHub Release](https://help.github.com/en/github/administering-a-repository/managing-releases-in-a-repository) of the repository
   * Runs LUIS quality tests to determine and publish the F-measure of the new LUIS app version

![GitFlow](images/GitFlow.png?raw=true "GitFlow")

The rest of this document explains how to run through these steps with the sample. Note that all steps involving `git` operations are shown using the **Git Bash shell**. Developers may have their own preference for using GUI tools or tooling built into developer tools such as Visual Studio Code to achieve the same result.

## Installing the required command line tools

You will need to install the following tools:

* **Bot Framework CLI** - this includes tools for working with LUIS apps. Follow these instructions to [install the Bot Framework CLI tools](https://github.com/microsoft/botframework-cli#installation).

* **NLU.DevOps** - you use these tools for running tests against a LUIS model. Follow these instructions to [install the NLU.DevOps tools](https://github.com/microsoft/NLU.DevOps#getting-started-with-the-nludevops-cli).

## Creating a feature branch

If you followed the [setup instruction for this sample](../README.md) you will have cloned your repository from GitHub to your own machine. To set up a feature branch:

1. After the GitHub repoitory is cloned, navigate to the project directory:   
`$ cd my-LUIS-DevOps-sample`

1. Create a feature branch:   
`$ git branch update-luis-sample`

1. Checkout the branch   
`$ git checkout update-luis-sample`

## Make your LUIS app updates

Now that you are working inside the feature branch, you can make your updates to the LUIS app, unit tests and model verification tests. If this was a brand new project, you would need to create the LUDown representation of the first version of your LUIS app and the JSON files for testing and check them in. However, in this sample, these files are provided:

* **luis-app/model.lu** - the LUDown encoding of the LUIS app
* **luis-app/tests/unittests.json** - the unit tests
* **luis-app/tests/verificationtests.json** - the verification tests

### Working with your LUIS app using the LUIS Portal

For minor updates to a LUIS app, an experienced developer can make updates directly to the **model.lu** file, can import the updated LUDown into a development LUIS app, train and publish it, and then run unit tests all at the command line. However, for most feature branch development, it is easier and more practical to make updates using the LUIS Portal.

To make updates using the LUIS Portal:

1. Sign into your preferred LUIS portal:
   * LUIS authoring portal - [https://preview.luis.ai](https://preview.luis.ai/home)
   * LUIS authoring portal (Europe) - [https://preview.eu.luis.ai](https://preview.eu.luis.ai/home)
   * LUIS authoring portal (Asia) - [https://preview.au.luis.ai](https://preview.au.luis.ai/home)

1. Select your Azure Subscription and your LUIS Authoring resource, and then you will create a LUIS app that you will use just for the work in this feature branch:

   1. First convert the **model.lu** file to JSON format using the Bot Framework CLI and save it to the same folder (**Note:** *luis-app/model.json* has already been added to the .gitignore file for this repository so that it will be considered as a transient file and will not be tracked by git):   
   `$ bf luis:convert -i luis-app/model.lu -o luis-app/model.json`

   1. Click **New app for conversation**. In the dropdown, click **Import as JSON**.
   ![Import as LU](images/importaslu.png?raw=true "Import as LU")

   1. Select the **model.json** file in the *Import new app* dialog, set a suitable  name for the app such as **DEV-update-luis-sample** and click **Done**.

1. Now you can make your changes to the app. For the purposes of this sample, you will add a new training utterance to the **None** intent.
   1. From the **Intents** editor, click on the **None** intent.

   1. Enter a new example utterance, for example: **Great that we can do DevOps with LUIS** and hit ***Enter**.

   ![Updating the None intent](images/noneintent.png?raw=true "Updating the None intent")

   1. Click **Train** at the top of the page.

   1. When training is complete, then click **Publish**, select **Staging Slot** and then click **Done**.

## Testing the new LUIS model (Optional)

A developer can use the single testing features in the LUIS portal to test single utterances against the LUIS model, and can run a test set using the batch testing capability in the portal but that is intended more for quality testing and for determining the F-measure score for your LUIS app than for executing a suite of unit tests and making sure that they all pass. The CI pipelines perform automated unit testing of the LUIS model when you raise your PR, and again when your changes are merged to master. 

However, it is good development practice for the developer to run all the unit tests during feature development to make sure that no problems have been introduced before checking in changes. For this, we use the **NLU.DevOps** tool, https://github.com/NLU.DevOps/.

### Setting up for testing

You need to enter settings for the test target LUIS app - the app you have just created - in an **appSettings.local.json** file. In the **luis-app** folder, a sample **appSettings.sample.json** has been provided. Copy this file to **appSettings.local.json** in the same folder and then enter the required values:

```json
{
  "luisAppId": "***your LUIS App Id***",
  "luisEndpointKey": "****your LUIS endpoint key***",
  "luisEndpointRegion": "***region***",
  "luisIsStaging": true
}
```

* You can find the **LUIS App Id** for your app by clicking the **Manage** tab in the LUIS Portal. The App ID is shown on the **Application Settings** page.

* To get the **luisEndpointKey** value, go to the **Azure Resources** page and copy the **Primary Key**.

* To get the **luisEndpointRegion**, take the first part of the Endpoint URL, one of *westus*, *westeurope* or *australiaeast*.

* Save this file.

### Testing the LUIS app

1. In your console terminal, set your current working directory to the *luis-app* folder.

1. Run the unit tests defined in /tests/unittests.json against the LUIS app you just published:   

`..\luis-app> dotnet nlu test -s luisV3 -u .\tests\unittests.json -o results.json`

1. The `nlu test` command runs your test utterances against the LUIS app endpoint and returns the results in the *results.json* file. In order to compare these new results with the expected results (defined in the *tests/unittests.json* file), use the `nlu compare` command:   

`..\luis-app> dotnet nlu compare -e .\tests\unittests.json -a results.json --unit-test`

1. This reports which tests have passed and failed:

![unit testing](images/nlucompare.png?raw=true "Unit Testing")

To find out more about unit testing with NLU.DevOps, read [Testing an NLU model](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Test.md) and [Analyzing NLU model results](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Analyze.md).

## Raising the pull request

Now that the changes have been applied to the LUIS app, you must download the updated LUIS app from the LUIS Portal and check in your changes and raise the PR.

1. In the LUIS Portal, click the **Manage** tab at the top of the page, and then go to the **Versions** page.

1. Select the latest version (there will only be one, version 0.1, if you have been following this tutorial) and then click **Export**. In the dropdown menu, click **Export as JSON**. [**IMPORTANT:** Do *not* use the *Export as LU* option at this time as it has a bug.]

1. Take the downloaded file (currently named as ***{LUIS App Id}*_v0.1.json**) and convert it to **LU**:   
   `$ bf luis:convert -i <i>{downloaded file}</i>.json -o luis-app/model.json`

1. save it as **model.lu** in the luis-app folder in your project, replacing the existing version of that file.

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

   * You will see that after the pull request is raised, the status screen shows that completion of the pull request is blocked because of **Review required**. In additon, after a few seconds, you will see an additonal status display **Some checks haven't completed yet** and underneath that the status of the **LUIS-CI /Build and Test LUIS model (pull_request)** CI pipeline as it runs, triggered by the raising of the pull request.

   ![pull request status](images/prstatuschecks.png?raw=true "Pull Request Status")

    * You can click on the **Details** link next to the Build pipeline status to see the pipeline stages as they execute.

1. When the pipeline has completed, the **All checks have passed** status shows as green since the CI pipeline ran and the unit tests passed. The pipeline has performed its function of a quality gate on the changes in the pull request. However, merging of the pull request is still blocked since at least 1 approving review is required by reviewers.

![merging is blocked](images/mergingblocked.png?raw=true "Merging is blocked")

1. On a real project, the changes should be reviewed and approved. However, for this sample, you can override this requirement since you are the Administrator of this repository. 
   * Click on the **Merge pull request** button.
   * On the next page, check **Use your administrator privileges to merge this pull request.**
   * Click **Confirm merge**.

## Running the CI/CD pipeline

If you click on the **Actions** tab immediately after you merge your pull request, you will see that the full CI/CD pipeline has already been triggered and is executing by the push to master. This pipeline is the same as the one that executed for the pull request but has some important differences in operation:

* It builds a new LUIS app version from the source that has been merged. It uses the LUIS app that is dedicated to the master branch, the name of which is set in the environment variables at the top of the **.github/workflows/luis_ci.yaml** file.
* It runs the unit tests again against the new LUIS app version.
* If the tests pass, it creates a GitHub release for the new version.
* It also runs the LUIS verification tests (equivalent to using the batch testing capability in the LUIS portal).

![CI/CD pipeline completed](images/cicdpipelinecompleted.png?raw=true "CI/CD pipeline completed")

### Verifying the new LUIS master app version

After the pipeline has completed successfully, if you look on the home page of your repository, you can see that a new release has been created: 

![GitHub Release](images/release.png?raw=true "GitHub Release")

When you click on this release flag, you can see the details of the new release, which is the zipped source code from the repository and a file called **luis_latest_version.json**:

![GitHub Release Details](images/releasedetails.png?raw=true "GitHub Release Details")

If you click on **luis_latest_version.json** you can download it and open it in a text editor. This gives you data about the new LUIS app version the pipeline has created.

### Executing predictions against the LUIS app version endpoint

The URI format for the endpoint is as follows:

<code>
https://<i>{AzureRegion}</i>.api.cognitive.microsoft.com/luis/prediction/v3.0/apps/<i>{AppId}</i>/versions/<i>{VersionId}</i>/predict?verbose=true&timezoneOffset=0&subscription-key=<i>{LUISSubscriptionKey}</i>&query=<i>yourQuery</i>
</code>

In this:
* **AzureRegion** - Use the region where you created all the LUIS resources, one of *westus*, *westeurope* or *australiaeast*
* **AppId** - the LUIS application ID. Get this by signing into the LUIS portal, finding your LUIS app for the master branch and goto the **Manage** tab
* **VersionId** - the version ID of the new version in the GitHub release.
* **LUISSubscriptionKey** - the LUIS Prediction resource key. Get this from the Manage tab for your master LUIS app in the LUIS portal, and then go to Azure Resources. Copy the **Primary Key** shown for the Prediction Resource.

When you have all the information, open a browser and paste in the complete URL with a query such as *I want my vacation to start on July 4th and to last for 10 days*. You will see the prediction response returned from the LUIS service:

![Prediction request](images/prediction.png?raw=true "Prediction request")
