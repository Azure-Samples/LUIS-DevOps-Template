# 3. Customizing the repository for your own project

This sample uses a sample LUIS project ***vacation_requests***, defined in this repo in the [model.lu file](../luis-app/model.lu). The sample project creates a language understanding model to handle requests for vacation from employees.

If you have the GitHub Actions workflows operating correctly using the supplied sample data, it is very simple to adapt it to support your own project.

## Starting a new project from scratch

1. Create a Feature branch in your repository

1. Define your own app model using [LUDown](https://docs.microsoft.com/azure/bot-service/file-format/bot-builder-lu-file-format?view=azure-bot-service-4.0) by one of the two methods:

   * Write the LUDown directly into the **luis-app/model.lu** file using a text editor, replacing the sample app content.
   * Define your new LUIS app using the [LUIS portal](https://www.luis.ai) and when you have made your changes, export the active version using the **Export as LU** menu. Rename the export file as **model.lu** and save it to the **luis-app** folder replacing the existing file.

   ![Export to LU](images/exportlu.png?raw=true "Exporting to LU")

1. Replace the contents of the **luis-app/tests/unittests.json** file with your own unit tests. Unit testing is performed by the [NLU.DevOps](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Test.md) tool.

1. Replace the contents of the **luis-app/tests/verificationtests.json** file with your own verification tests. The verification tests use the [LUIS batch test](https://docs.microsoft.com/en-us/azure/cognitive-services/LUIS/luis-how-to-batch-test) capability via NLU.DevOps.

1. Follow the steps described in [Setup the CI/CD pipeline](1-project-setup.md#setup-the-cicd-pipeline) to ensure that the CI/CD pipeline is configured correctly for your project.

1. Check in your changes and raise a PR to merge them into the master branch.

## Starting with an existing project

1. Create a Feature branch in your repository

1. Sign into the [LUIS portal](https://www.luis.ai), and export the active version of your app using the **Export as LU** menu. Rename the export file as **model.lu** and save it to the **luis-app** folder replacing the existing file.

1. Replace the contents of the **luis-app/tests/unittests.json** file with your own unit tests.

1. Replace the contents of the **luis-app/tests/verificationtests.json** file with your own verification tests.

1. Follow the steps described in [Setup the CI/CD pipeline](1-project-setup.md#setup-the-cicd-pipeline) to ensure that the CI/CD pipeline is configured correctly for your project.

1. Check in your changes and raise a PR to merge them into the master branch.

## Enabling the F-measure testing capability

The **LUIS F-measure testing** job measures performance of your LUIS model. This job performs the equivalent of the [LUIS batch testing](https://docs.microsoft.com/azure/cognitive-services/LUIS/luis-how-to-batch-test) that you can perform in the LUIS portal. It uses the [NLU.DevOps](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Analyze.md) tool to execute the tests defined in the `luis-app/tests/verificationtests.json` test file against the newly built model and calculates the test results file, `statistics.json`, from which the F1 score (or [F-measure](https://en.wikipedia.org/wiki/F-measure)) can be calculated. The results file from every run is saved to Azure blob storage and it contains:

* For each Intent and Entity:
  * Count of true positives for passing tests
  * Count of true negatives for passing tests
  * Count of false positives from failing tests
  * Count of false negatives from failing tests
  
As shipped, the **LUIS F-measure testing** job is configured to run concurrently with the **Create LUIS Release** job and does not block the **LUIS CD** job from running should it fail. It runs purely as an advisory and is provided as an example of how to perform model quality testing within the workflow.

This kind of testing is best employed when a LUIS app has been developed to the point where its schema is near or fully complete and development has progressed from the early stages of development to the stage of refining the performance of the app. A release manager can review the build artifacts created by this job to monitor the performance of the LUIS app as improvements are made and can use the F-measure scores that are output to help decide when to promote new versions of the LUIS app to other build environments such as UAT, Staging or Production.

Read more about [running tests using NLU.DevOps](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Test.md) and about [analyzing the test results to measure performance](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Analyze.md) in the NLU.DevOps documentation.

### Configuring the baseline comparison feature

The **LUIS F-measure testing** job can be configured to compare the performance of the newly built model against some baseline test run. The baseline could be the results from the last project milestone, or the latest version that has been promoted for use in test environments.

### Enabling baseline comparison

To enable this feature, you must edit the `.github\workflows\luis_ci.yaml` workflow definition file and define the `BASELINE_CONTAINER_NAME` environment variable at the top:

```yml
env:
  # Set the name of the master LUIS app
  LUIS_MASTER_APP_NAME: LUISDevOps-master
  # If your repository is Private, set this to true
  IS_PRIVATE_REPOSITORY: false

  # Set the path to the lu file for your LUIS app
  LU_FILE: luis-app/model.lu
  # Set the path to the file for your unit tests
  UNIT_TEST_FILE: luis-app/Tests/unittests.json
  # Set the path to the file for your unit tests
  QUALITY_TEST_FILE: luis-app/Tests/verificationtests.json
  # Set the name of the container in the Azure Storage account that contains the baseline F-measure results
  BASELINE_CONTAINER_NAME: '5bccf3a4b6f866354cafb012b0adb2b73d2f5945'
```

The `BASELINE_CONTAINER_NAME` defines the name of the storage container in your Azure Storage account that contains F-measure testing results for your baseline LUIS app version. The name is the SHA-1 hash value of the GitHub commit that was merged and which resulted in the `luis-ci.yaml` workflow executing and the GitHub release created by that workflow.

To get the commit hash for the LUIS app version you want to use for your baseline:

* Go to the releases list for your repo on GitHub.
* The shortened version of the hash value is shown in the metadata for the GitHub Release and is a link to the commit details.
* Click the link to see the details of the commit and to get the full hash value, which gives you the value you must set in the `BASELINE_CONTAINER_NAME` environment variable.

![Getting the commit hash for a Release](images/commit_hash.png?raw=true "Commit hash for a Release")

#### Setting Performance Regression Thresholds for the baseline comparison

When comparing against a baseline, you can specify performance regression thresholds. The **LUIS F-measure testing** job will fail if the baseline comparison results show that the performance of the new model has regressed greater than the regression thresholds you configure.

You set regression thresholds in the file `luis-app\tests\compare.yaml`. By default, it defines regression thresholds of 0.05 across intents and all entities:

```yml
thresholds:
- type: intent
  threshold: 0.05
- type: entity
  threshold: 0.05
```

To learn more about defining regression thresholds, read [Performance Regression Thresholds](https://github.com/microsoft/NLU.DevOps/blob/master/docs/Analyze.md#performance-regression-thresholds) in the NLU.DevOps documentation.

### Making F-measure testing job success mandatory in the workflow

As shipped, the **LUIS F-measure testing** job runs concurrently with the **Create LUIS Release** job and does not block the **LUIS CD** job from running should it fail.

In order to make the job mandatory, and to make the running of the **LUIS CD** job conditional on successful completion of the **LUIS F-measure testing** job, edit the `.github\workflows\luis_ci.yaml` and change the `needs:` property of the **LUIS_CD** job, as follows:

```yml
  # Job: Continuous deployment job for LUIS
  # Requires LUIS_quality_testing job to complete first
  release:
    name: LUIS CD
    needs: LUIS_quality_testing
    runs-on: ubuntu-latest
    steps:
      ...
```

## Further Reading

See the following documents for more information on this template and the engineering practices it demonstrates:

* [Project Setup and configuration](1-project-setup.md)

* [Creating a Feature branch, updating your LUIS app, and executing the CI/CD pipelines](2-feature-branches-and-running-pipelines.md)

* [CI/CD pipeline operation](4-pipeline.md#pipeline-steps)
