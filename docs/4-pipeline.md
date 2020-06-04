# GitHub Actions workflow with NLU.DevOps

This solution uses two GitHub Actions workflow yaml files [luis_pr.yaml](../.github/workflows/luis_pr.yaml) and [luis_ci.yaml](../.github/workflows/luis_ci.yaml). To configure the workflows for use, you must set GitHub Secrets to match your configuration of resources in Azure as described below in [GitHub Secrets](#github-secrets), but you should not need to make any edits to these files to use them in the solution.

This document describes the workflow steps so that you can understand how they work should you need to modify them for your own projects.

## The workflows

The workflows operate in response to two distinct events:

* On raising of a Pull Request (PR) for changes made in a feature branch that will be merged to master, the [luis_pr.yaml](../.github/workflows/luis_pr.yaml) workflow executes.
* When a PR has been merged and the changes are pushed to master, [luis_ci.yaml](../.github/workflows/luis_ci.yaml) executes.

### Triggers

When triggered for a PR, the **luis_pr.yaml** workflow acts as a quality gate. It builds a temporary LUIS app, runs all the unit tests against it and fails the workflow if any tests fail; this will block completion of the PR. At the end the temporary LUIS app is deleted.

When triggered for a merge to master, the **luis_ci.yaml** workflow creates a new version in the LUIS app that has been created for the master branch, runs the unit tests, and if the tests pass, creates a GitHub release which includes a Release artifact containing data identifying the new version, and it runs a simple CD (Continuous Deployment) job that publishes the new LUIS app version to the Production slot. It also runs quality tests to determine the F-measure for the new model.

The configuration of both workflows ensure that they will be triggered only when either the *LUIS model* or the *test suite* is changed:

  ```yml
    name: LUIS-PR

    # Trigger the workflow on pull request, and only for changes to lu or json files
    on:
      pull_request:
        paths:
          - 'luis-app/*.lu'
          - 'luis-app/Tests/*.json'
  ```

The trigger configuration for **luis_ci.yaml** ensures that it runs when a merge to master happens:

  ```yml
    name: LUIS-CI

    # Trigger the workflow on push to the master branch, and only for changes to lu or json files
    on:
      push:
        branches:
          - master
        paths:
          - 'luis-app/*.lu'
          - 'luis-app/Tests/*.json'
  ```

### GitHub Secrets

Both workflows make use of a number of variables that must be defined in GitHub Secrets. Ensure each of the following secrets have been set, using the values appropriate to your configuration of resources in Azure:

| Secret Name | Value |
|-------------|-------|
| **AZURE_CREDENTIALS** | *Service Principle token - see *[Creating the Azure Service Principal](1-project-setup.md#create-the-azure-service-principal)* |
| **AZURE_RESOURCE_GROUP** | *name of the resource group that contains the resources below* |
| **AZURE_LUIS_AUTHORING_RESOURCE_NAME** | *name of the Azure LUIS authoring resource* |
| **AZURE_LUIS_PREDICTION_RESOURCE_NAME** | *name of the Azure LUIS prediction resource* |
| **AZURE_STORAGE_ACCOUNT_NAME** | *name of the Azure storage account* |

### Environment variables

The workflows also use a number of environment variables that are defined at workflow scope:

* **LUIS_MASTER_APP_NAME** Set this to the name of the LUIS app that is built from the source checked into the master branch, and which the workflow will create when it first runs.
* **IS_PRIVATE_REPOSITORY** Set this to `true` if your GitHub repository is private, otherwise set to `false`.

```yml
env:
  # Set the name of the master LUIS app
  LUIS_MASTER_APP_NAME: LUISDevOps-master
  # If your repository is Private, set this to true
  IS_PRIVATE_REPOSITORY: false
```

In addition, the following environment variables set the names of the source file that define your LUIS app, and the files containing the unit tests and the F-measure quality tests:

```yml
  # Set the path to the lu file for your LUIS app
  LU_FILE: luis-app/model.lu
  # Set the path to the file for your unit tests
  UNIT_TEST_FILE: luis-app/Tests/unittests.json
  # Set the path to the file for your unit tests
  QUALITY_TEST_FILE: luis-app/Tests/verificationtests.json
  # Set the name of the container in the Azure Storage account that contains the baseline F-measure results
  BASELINE_CONTAINER_NAME: ''
```

The `BASELINE_CONTAINER_NAME` defines the name of the storage container in your Azure Storage account that contains F-measure testing results for your baseline LUIS app version. This is used for comparison purposes to determine whether the performance of the new model being built from the current source has improved or regressed compared to the baseline. Leave this value blank when starting out with a new app until such time as you have an app of sufficient maturity that you wish to commence comparison testing. See [Job: LUIS F-measure testing](#job-luis-f-measure-testing) to learn more about the use of this environment variable.

### Job: Build

The **[luis_ci.yaml](../.github/workflows/luis_ci.yaml)** workflow is divided into three discrete jobs. Each job runs independently but sequentially in its own environment and the workflow is configured so that the **build** job executes first, followed by the **LUIS_quality_testing** job and the **release** job.
The **[luis_pr.yaml](../.github/workflows/luis_pr.yaml)** workflow is a single job that is almost identical to the first job of the **luis_ci.yaml** workflow, but with these distinct differences:

* *luis_pr.yaml* creates a temporary LUIS app from the source in the PR that acts as the test target and is deleted again at the end of the run
* *luis_ci.yaml* creates a new version in the LUIS app for the master branch from the merged source in master which is not deleted at the end of the run. 

The first job builds and unit tests the LUIS model.

#### Checking out the code and bump Version

**luis_ci.yaml** starts by checking out the code and then fetching all the history and tags for all branches, information that is required by the [GitVersion](https://gitversion.net/docs/) step which increments the version number using semantic versioning on every build:

```yml
  build:
    name: Build and Test LUIS model
    runs-on: ubuntu-latest
  steps:
  - name: Checkout
    uses: actions/checkout@v2

  - name: Fetch all history for all tags and branches - for GitVersion
    if: env.IS_PRIVATE_REPOSITORY == 'false'
    run: git fetch --prune --unshallow
  - name: Fetch all history for all tags and branches (private repo) - for GitVersion
    if: env.IS_PRIVATE_REPOSITORY == 'true'
    run: |
      git config remote.origin.url https://x-access-token:${{ secrets.GITHUB_TOKEN }}@github.com/${{ github.repository }}
      git fetch --prune --unshallow

  - name: Install GitVersion
    uses: gittools/actions/gitversion/setup@v0.9.3
    with:
        versionSpec: '5.2.x'
  - name: Use GitVersion
    id: gitversion
    uses: gittools/actions/gitversion/execute@v0.9.3

  - name: luisAppVersion env
    run: echo "::set-env name=luisAppVersion::$GitVersion_SemVer"
```

#### Log into Azure

We log into Azure using the `AZURE_CREDENTIALS` token saved into GitHub secrets during setup, and query for the LUIS authoring key, prediction key and authoring endpoint that are needed later on. We use the add-mask function to mask sensitive keys to ensure they are hidden in the log files:

```yml
    - uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Get LUIS authoring key
      run: |
         keya=$(az cognitiveservices account keys list --name $AzureLuisAuthoringResourceName --resource-group $AzureResourceGroup --query "key1" | xargs)
         echo "::set-env name=LUISAuthoringKey::$keya"
         echo "::add-mask::$keya"

    - name: Get LUIS prediction key
      run: |
         keyp=$(az cognitiveservices account keys list --name $AzureLuisPredictionResourceName --resource-group $AzureResourceGroup --query "key1" | xargs)
         echo "::set-env name=LUISPredictionKey::$keyp"
         echo "::add-mask::$keyp"

    - name: Get LUIS authoring endpoint
      run: |
          az cognitiveservices account show --name $AzureLuisAuthoringResourceName --resource-group $AzureResourceGroup --query "endpoint" | \
          xargs -I {} echo "::set-env name=luisAuthoringEndpoint::{}"
```

#### Install Bot Framework CLI

Next we install node.js (necessary for running the Bot Framework CLI) and the BF CLI. Before we will be able to run any botframework-cli commands in CI we need to disable telemetry using the workaround shown in this [GitHub issue](https://github.com/microsoft/botframework-cli/issues/370):

  ```yml
    - uses: actions/setup-node@v1
      with:
        node-version: '12.x'

    - name: Bypass botframework-cli telemetry prompts, enable telemetry collection - set to false to disable telemetry collection
      run: echo "::set-env name=BF_CLI_TELEMETRY::true"

    - name: Install @microsoft/botframework-cli
      run: |
        npm i -g @microsoft/botframework-cli
  ```

#### Build LUIS app version

The next stage of the workflow creates a LUIS model.
We import and use a [ludown.lu](./ludown.lu) file for training. We use the [LuDown format](https://github.com/microsoft/botbuilder-tools/tree/master/packages/Ludown#ludown) to define the LUIS app version since it can be maintained in a source control system and is human readable to allow us to work with it outside the LUIS portal's GUI tool.
You can replace this file with another file that defines the intents, utterances, entities that you need for your own model. This may be useful if you are generating your training data from some other system or by some other mechanism. Ultimately, we need to provide the information in the LUIS JSON format and the BF CLI provides tooling to support this.

The first step transforms the ludown file to a LUIS JSON file using the botframework-cli:

  ```yml
    - name: Ludown to LUIS model
      run: bf luis:convert -i $LU_FILE -o ./model.json --name 'LUIS CI pipeline - ${{ github.run_id }}' --versionid $luisAppVersion
  ```

The `model.json` file output must be imported to LUIS. This happens in different ways depending on whether the workflow is operating as a PR gate-check - where it creates a new LUIS app for testing which is deleted at the end of the workflow - or if operating as a Merge workflow.

The *luis_pr.yaml* workflow is operating as a PR quality gate and it creates a temporary app to use as the test target. `bf luis:application:import` returns a string with the LUIS App ID that we will need to use in the next steps, so we save the AppId in an environment variable called *LUISAppId*:

  ```yml
    # When doing a gate check on PRs, we build a new LUIS application for testing that is later deleted
    - name: Create PR check LUIS application 
      run: |
        response=$(bf luis:application:import --endpoint $LUISAuthoringEndpoint --subscriptionKey $LUISAuthoringKey  --in model.json --json)
        status=$(echo "$response" | jq '.Status' | xargs)
        if [ "$status" == "Success" ]
        then
          appId=$(echo "$response" | jq '.id' | xargs)
          echo "::set-env name=LUISAppId::$appId"
        else
          exit 1
        fi
  ```

*luis_ci.yaml* is operating as a Merge workflow, so the LUIS app is the one associated with the master branch and we use the name specified in the YAML file. The app will be created if it does not already exist. This step determines the AppId (GUID) and saves it in the *AppId* environment variable:

  ```yml
    # When doing a merge to master, use the master LUIS app - create if necessary (soft fails if exists)
    - name: Get master LUIS application ID
      run: |
        bf luis:application:create --name $LUIS_MASTER_APP_NAME --subscriptionKey ${{ env.LUISAuthoringKey }} --endpoint $luisAuthoringEndpoint --versionId=0.1
        bf luis:application:list --subscriptionKey ${{ env.LUISAuthoringKey }} --endpoint $luisAuthoringEndpoint | \
        jq -c '.[] | select(.name | . and contains('\"$LUIS_MASTER_APP_NAME\"')) | .id' | \
        xargs -I {} echo "::set-env name=AppId::{}"

    # Check that we found the master app Id - failure probably indicates misconfiguration
    - name: Validate application ID
      run: |
        echo "LUIS app Id: $LUISAppId"
        if [ ${#LUISAppId} -ne 36 ]; then
          echo "ERROR: Failed to find LUIS master app. Check workflow configuration."
          exit 1
        fi
  ```

Next, we check if the LUIS app currently has 100 versions (the limit), and if so print a warning and fail the workflow. In order to resolve this, unneeded versions must be deleted from the LUIS master app.

  ```yml
    - name: Purge LUIS app version
      run: |
        version_count=$(bf luis:version:list --appId $AppId --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ env.LUISAuthoringKey }} | jq 'length')
        if [ $version_count -ge 100 ]; then
          echo "ERROR: LUIS app: $AppId version count will exceed 100. Delete unneeded versions before re-running pipeline"
          exit 1
        fi
  ```

Then we go ahead and create a new version in the LUIS app by importing the JSON created earlier. (This step will only do something when the LUIS app is the one targeted by the Merge workflow):

  ```yml
    # When doing a CI/CD run on push to master, we create a new version in an existing LUIS application
    - name: Create new LUIS application version
      if: github.event_name == 'push'
      run: bf luis:version:import --appId $LUISAppId --endpoint $LUISAuthoringEndpoint --subscriptionKey $LUISAuthoringKey --in model.json
  ```

#### Train and publish the LUIS app

The BF CLI is used to initiate the training of the model and to *wait* for this to complete.

  ```yml
    - name: Train luis
      shell: bash
      run: bf luis:train:run --appId $LUISAppId --versionId $LUISAppVersion --endpoint $LUISAuthoringEndpoint --wait
  ```

After the model has finished training we can publish our LUIS model. We use *direct version publishing* for this rather than publishing to the named slots, staging and production. We do this to be able to support more than two published versions at any one time so that multiple LUIS app versions can be in a published state at any one time to support more then two dev environments simultaneously (for example, DEV, QA, UAT, PRODUCTION. We use a cURL command here to call the REST API directly:

  ```yml
    - name: Publish luis
      run: |
        curl POST $POSTurl \
        -H "Content-Type: application/json" \
        -H "Ocp-Apim-Subscription-Key: ${{ env.LUISAuthoringKey }}" \
        --data-ascii "{'versionId': '$luisAppVersion', 'directVersionPublish': true}"
      env:
        POSTurl: ${{ env.luisAuthoringEndpoint }}luis/authoring/v3.0-preview/apps/${{ env.AppId }}/publish
  ```

#### Testing the LUIS app

To prepare for testing, we install the [NLU.DevOps](https://github.com/Microsoft/NLU.DevOps) test tool:

  ```yml
    - name: Install dotnet-nlu
      run: dotnet tool install -g dotnet-nlu
  ```

On the ubuntu agent, you need to append the tools directory to the system PATH variable for all subsequent actions in the current job to be able to use the cli tool.

  ```yml
    - name: Path
      run: echo "::add-path::$HOME/.dotnet/tools"
  ```

In order to test a LUIS app, you must use an Azure LUIS Prediction resource key. The Authoring key is not practicable since it is subject to throttling which may cause the tests to fail unnecessarily. Here we assign the Azure LUIS prediction resource to the application. Note that once again we access the REST API directly using curl as the BotFramework CLI does not support the allocation of Azure LUIS resources at this time:

  ```yml
    - name: Get Azure subscriptionId
      run: |
          az account show --query 'id' | \
          xargs -I {} echo "::set-env name=AzureSubscriptionId::{}"

    - name: Assign LUIS Azure Prediction resource to application
      shell: pwsh
      run: |
          bf luis:application:assignazureaccount --azureSubscriptionId $env:AzureSubscriptionId --appId $env:LUISAppId --accountName $env:luisPredictionResourceName --subscriptionKey $env:LUISAuthoringKey --endpoint $env:LUISAuthoringEndpoint --resourceGroup $env:azureResourceGroup --armToken $(az account get-access-token --query accessToken -o tsv)
      env:
        luisPredictionResourceName: ${{ secrets.AZURE_LUIS_PREDICTION_RESOURCE_NAME }}
        azureResourceGroup: ${{ secrets.AZURE_RESOURCE_GROUP }}
  ```

To test the LUIS app version that was created, we use the unit test file:

  ```yml
    - name: Test Luis model
      run: dotnet nlu test -s luisV3 -u $UNIT_TEST_FILE -o results.json
      env:
        luisAppId: ${{ env.LUISAppId }}
        luisVersionId: ${{ env.LUISAppVersion }}
        luisDirectVersionPublish: true
        luisEndpointKey: ${{ env.LUISPredictionKey }}
        luisPredictionResourceName: ${{ secrets.AZURE_LUIS_PREDICTION_RESOURCE_NAME }}
  ```

To evaluate results we use two files: the *unit test file* that consists of test utterances and the expected intents and entities results and `results.json` file which was created by the Test LUIS model step and contains the actual results returned from testing the LUIS model:

  ```yml
    - name: Analyze Unit test results
      run: dotnet nlu compare -e $UNIT_TEST_FILE -a results.json --unit-test --output-folder unittest
  ```

We archive the test results as a build workflow artifact:

  ```yml
    - name: Archive Unit Test Results
      uses: actions/upload-artifact@v1
      with:
        name: UnitTestResult
        path: unittest/TestResult.xml
  ```

In *luis_pr.yaml* where the workflow is operating as a PR gate-check, at this point the LUIS app created by this workflow is deleted:

  ```yml
      # Delete the LUIS app again if we are executing as gate check on a PR
    - name: Delete luis test target app
      if: always() && (github.event_name == 'pull_request')
      shell: bash
      run:  bf luis:application:delete --appId $AppId --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ env.LUISAuthoringKey }} --force
  ```

For *luis_ci.yaml* there is still some work to do. It creates a GitHub Release, which also tags the repo using the version Id:

  ```yml
    - name: Create Release
      id: create_release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # This token is provided by Actions, you do not need to create your own token
      with:
        tag_name: ${{ env.LUISAppVersion }}
        release_name: Release ${{ env.LUISAppVersion }}
        body: |
          Releasing new LUIS endpoint
        draft: false
        prerelease: false
  ```

  Finally, it uploads the version details as a Release asset:

  ```yml
    - name: Get LUIS latest version details file
      run: |
        bf luis:version:list --appId $LUISAppId --endpoint $LUISAuthoringEndpoint --subscriptionKey $LUISAuthoringKey  --take 1 --out luis_latest_version.json

    - name: Upload Release Asset
      id: upload-release-asset
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        upload_url: ${{ steps.create_release.outputs.upload_url }} # This pulls from the CREATE RELEASE step above, referencing it's ID to get its outputs object, which include a `upload_url`
        asset_path: ./luis_latest_version.json
        asset_name: luis_latest_version.json
        asset_content_type: application/json
  ```

A *Release Manager* can determine the version Id of the LUIS app by examining the **luis_latest_version.json** file uploaded as the Release artifact which they can find by going to the Releases page for their GitHub repository.

From this, the endpoint URL can be determined, as follows:

<code>
https://<i>azureLUISPredictionResourceName</i>.cognitiveservices.azure.com/luis/prediction/v3.0/apps/<i>appId</i>/versions/<i>versionId</i>/predict?verbose=true&subscription-key=<i>predictionKey</i>&query=<i>query</i>
</code>.

### Job: LUIS F-measure testing

The quality testing step only executes after the **build** step has succeeded and only in **luis_ci.yaml** which is operating as a Merge workflow.

Also note that the `BASELINE_CONTAINER_NAME` environment variable needs to be defined in order to enable comparisons with previous model training runs. This variable should be the name of the Azure blob container which is then used to store the baseline set of test results that we will use to compare our newly built model against. Leaving this environment variable undefined will skip the comparison stage. Read [Configuring the baseline comparison feature](3-customizing-own-project.md#configuring-the-baseline-comparison-feature) to learn more about enabling this feature.

> **Note:** The **LUIS F-measure testing** job runs concurrently with the *Create LUIS Release* job. It is provided in this template as an example of how to perform automated quality testing of a LUIS app. This kind of testing is best employed when a LUIS app has been developed to the point where its schema is near or fully complete and development has progressed from the early stages of development to the stage of refining the performance of the app. A release manager can review the build artifacts created by this job to monitor the performance of the LUIS app as improvements are made and can use the F-measure scores that are output to help decide when to promote new versions of the LUIS app to other build environments such as UAT, Staging or Production.

In the workflow:
  
* We publish the F-measure for this build as a build artifact and save to blob storage
* Fetch the test results for the previous build from blob storage
* Publish the comparison between the current build and the previous build for the F-measure

  ```yml
  # Job: LUIS quality testing
  LUIS_quality_testing:
    name: LUIS F-measure testing
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push'  
  ```

Many of the steps to setup tools and assign Azure LUIS resources are the same as in the previous step so are not repeated here. This section will describe only the significant steps that carry out the F-measure testing.

#### Establish the new App Version built by the Build job

The workflow step executes in its own build environment, so early in this step we must establish what the most recent version of the LUIS app that was created by the build step. The version string is saved in an environment variable named *LuisVersion*.

  ```yml
    - name: Get master LUIS application ID
      run: |
        bf luis:application:list --subscriptionKey ${{ env.LUISAuthoringKey }} --endpoint $luisAuthoringEndpoint | \
        jq -c '.[] | select(.name | . and contains('\"$LUIS_MASTER_APP_NAME\"')) | .id' | \
        xargs -I {} echo "::set-env name=AppId::{}"
        echo "Found LUIS app: $AppId"

    - name: Get LUIS latest version ID
      run: |
        bf luis:version:list --appId $AppId --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ env.LUISAuthoringKey }} --take 1 | \
        jq '.[0].version' | \
        xargs -I {} echo "::set-env name=LuisVersion::{}"
  ```

#### Executing F-measure testing

Testing uses the verification test file rather than the unit test file:

  ```yml
    - name: Test Luis model with quality verification tests
      run: dotnet nlu test -s luisV3 -u $QUALITY_TEST_FILE -o F-results.json
      env:
        AzureLuisResourceName: ${{ env.AzureLuisPredictionResourceName }}
        luisAppId: ${{ env.AppId }}
        luisVersionId: ${{ env.LuisVersion }}
        luisDirectVersionPublish: true
        luisEndpointKey: ${{ env.LUISPredictionKey }}
        luisPredictionResourceName: ${{ env.AzureLuisPredictionResourceName }}
  ```

#### Compare F-measure results with baseline

If you have set the `BASELINE_CONTAINER_NAME` environment variable to the name of a container in Azure Storage then the workflow will begin storing previous test results.  If results from a previous run exists, then we will download those test results to use as the comparison baseline:

  ```yml
    - name: download baseline
      if: env.BASELINE_CONTAINER_NAME != ''
      uses: azure/CLI@v1
      with:
        azcliversion: 2.2.0
        inlineScript: |
          az storage blob download  --account-name ${{  env.AzureStorageAccountName  }} --container-name ${{  env.BASELINE_CONTAINER_NAME  }}  --name statistics.json  --file baselinefile.json --auth-mode login

  ```

Then we compare the results from testing the new model with the test results from the baseline model:

  ```yml
    - name: Compare Luis model F-measure with baseline
      if: env.BASELINE_CONTAINER_NAME != ''
      run: dotnet nlu compare -e $QUALITY_TEST_FILE -a F-results.json --baseline baselinefile.json
  ```

If no previous baseline is configured, then we just generate a new set of results that could be used as a baseline for subsequent runs. To do this for subsequent runs, set the `BASELINE_CONTAINER_NAME` environment variable to the name of the container after this run has completed, to use in subsequent runs.

  ```yml
    # if no baseline configured, then we just compare against the expected results to create statistics that can become the new baseline
    - name: Analyze Luis model F-measure - Create baseline
      if: env.BASELINE_CONTAINER_NAME == ''
      run: dotnet nlu compare -e $QUALITY_TEST_FILE -a F-results.json
  ```

Finally, we upload the F-measure results as a build artifact and also to Azure Storage:

  ```yml
    - name: Archive Quality Test Results
      if: env.BASELINE_CONTAINER_NAME != ''
      uses: actions/upload-artifact@v1
      with:
        name: QualityTestResult
        path: TestResult.xml

    - name: upload statistics
      uses: azure/CLI@v1
      with:
        azcliversion: 2.2.0
        inlineScript: |
          az storage container create  --account-name ${{ env.AzureStorageAccountName }}  --name ${{ github.sha }}  --auth-mode login
          az storage blob upload  --account-name ${{ env.AzureStorageAccountName }}  --container-name ${{ github.sha }} --name statistics.json --file statistics.json  --auth-mode login
  ```

### Job: Create LUIS Release

This step only executes if the *build* step has completed successfully and only within **luis_ci.yaml** which is operating as a Merge workflow to master.

> **Note:** The **Create LUIS Release** job is a simple example of a CD (Continuous Delivery) workflow. In  enterprise development, release procedures and practices differ from one project to another, so the implementation of this job in the workflow is supplied in this template as an example that should be customized as required.

  ```yml
  # Job: Continuous deployment job for LUIS
  release:
    name: LUIS CD
    needs: build
    runs-on: ubuntu-latest
    steps:
  ```

As before, we will not describe steps that are duplicates of those in the **build** step and which are described above.

These steps determine the version Id of the model built by the **build** step:

  ```yml
    - name: Get master LUIS application ID
      run: |
        bf luis:application:list --subscriptionKey $LUISAuthoringKey --endpoint $LUISAuthoringEndpoint | \
        jq -c '.[] | select(.name | . and contains('\"$LUIS_MASTER_APP_NAME\"')) | .id' | \
        xargs -I {} echo "::set-env name=LUISAppId::{}"
        echo "Found LUIS app: $LUISAppId"

    - name: Get LUIS latest version ID
      run: |
        bf luis:version:list --appId $LUISAppId --endpoint $LUISAuthoringEndpoint --subscriptionKey $LUISAuthoringKey --take 1 --out luis_latest_version.json
        cat luis_latest_version.json | jq '.[0].version' | \
        xargs -I {} echo "::set-env name=LUISAppVersion::{}"
  ```

Then this job publishes the LUIS app version to the [Production endpoint](https://docs.microsoft.com/azure/cognitive-services/luis/luis-how-to-publish-app):

```yml

    - name: Publish LUIS to PRODUCTION
      run: bf luis:application:publish --appId $LUISAppId --versionId $LUISAppVersion --endpoint $LUISAuthoringEndpoint --subscriptionKey $LUISAuthoringKey
```

There are many possible deployment strategies and you should implement the functions required by your project at this step.

## Further Reading

See the following documents for more information on this template and the engineering practices it demonstrates:

* [Project Setup and configuration](1-project-setup.md)

* [Creating a Feature branch, updating your LUIS app, and executing the CI/CD workflows](2-feature-branches-and-running-pipelines.md)

* [Adapting this repository to your own project](3-customizing-own-project.md#starting-a-new-project-from-scratch)
