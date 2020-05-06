# GitHub Actions pipeline with NLU.DevOps

This sample uses a [GitHub Actions workflow yaml file](../.github/workflows/luis_ci.yaml). Apart from setting the environment variables at the top of this file to match your configuration of resources in Azure, you do not need to make any changes to this file to use it in the sample.

This document describes the pipeline steps so that you can understand how it works should you need to modify it for your own projects.

## Pipeline steps

The pipeline operates in two distinct modes of operation:

* On raising of a Pull Request (PR) for changes made in a feature branch that will be merged to master
* When a PR has been merged and the changes are pushed to master

### Triggers

When triggered for a PR, the pipeline acts as a quality gate. It builds a temporary LUIS app, runs all the unit tests against it and fails the pipeline if any test fail, which will block completion of the PR. At the end the temporary LUIS app is deleted.

When triggered for a merge to master, the pipeline creates a new version in the LUIS app that has been created for the master branch, runs the unit tests, and if the tests pass, creates a GitHub release which includes a Release artifact containing data identifying the new version, and from which the prediction endpoint URL can be determined for use in release environments. In this mode, it also runs quality tests to determine the F measure for the new model.

The configuration for triggering this in the pipeline is as follows:

  ```yml
    name: LUIS-CI

    # Trigger the workflow on push or pull request, but only for the master branch, and only for changes to lu or json files
    on:
      push:
        branches:
          - master
        paths:
          - 'luis-app/*.lu'
          - 'luis-app/Tests/*.json'
      pull_request:
        paths:
          - 'luis-app/*.lu'
          - 'luis-app/Tests/*.json'
  ```

### Environment variables

The pipeline requires a number of environment variables to be defined at workflow scope:

* Variables for the names of the Azure resources.
* **LUIS_MASTER_APP_NAME** Set this to the name of the LUIS app that is built from the source checked into the master branch, and which the pipeline will create when it first runs.
* **IS_PRIVATE_REPOSITORY** Set this to `true` if your GitHub repository is private, otherwise set to `false`.

You must ensure that the environment variables values match the names of the Azure resources used by this pipeline, and the name of the master LUIS app. For example:

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

In addition, the following environment variables set the names of the source file that defines your LUIS app, and the files containing the unit tests and the F measure quality tests:

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

The `BASELINE_CONTAINER_NAME` defines the name of the storage container in your Azure Storage account that contains F measure testing results for your baseline LUIS app version. This is used for comparison purposes to determine whether the performance of the new model being built from the current source has improved or regressed compared to the baseline. Leave this value blank when starting out with a new app until such time as you have an app of sufficient maturity that you wish to commence comparison testing.

### Job: Build

The pipeline is divided into three discrete jobs. Each job runs independently in its own environment and the pipeline is configured so that the **build** job executes first, followed by the **LUIS_quality_testing** job and the **release** job.

The first job builds and unit tests the LUIS model.

#### Checking out the code and bump Version

It starts by checking out the code and then fetching all the history and tags for all branches, information that is required by the [GitVersion](https://gitversion.net/docs/) step which increments the version number using semantic versioning on every build:

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

  - name: GitVersion
    uses: docker://gittools/gitversion:5.2.5-linux-ubuntu-16.04-netcoreapp2.1
    with:
      args: /github/workspace /nofetch /output buildserver

  - name: luisAppVersion env
    run: echo "::set-env name=luisAppVersion::$GitVersion_SemVer"
```

#### Log into Azure

We log into Azure using the `AZURE_CREDENTIALS` token saved into GitHub secrets during setup, and query for the LUIS authoring endpoint needed later on:

```yml
    - uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}

    - name: Get LUIS authoring endpoint
      run: |
          az cognitiveservices account show --name $AzureLuisAuthoringResourceName --resource-group $AzureResourceGroup --query "endpoint" | \
          xargs -I {} echo "::set-env name=luisAuthoringEndpoint::{}"
```

#### Install Bot Framework CLI

Next we install node.js (necessary for running the Bot Framework CLI) and the BF CLI. Before we will be able to run any botframework-cli commands in CI we need to disable telemetry using the workaround shown ([GitHub issue](https://github.com/microsoft/botframework-cli/issues/370)):

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

The next stage of the pipeline creates a LUIS model.
We use [ludown.lu](./ludown.lu) file for training. We use the [LuDown format](https://github.com/microsoft/botbuilder-tools/tree/master/packages/Ludown#ludown) to define the LUIS app version since it can be maintained in a source control system and enables the reviewing process because of its legibility.
You can replace this file with another file that defines the intents, utterances, entities that you need for your own model.

The first step transforms the ludown file to a LUIS JSON file using the botframework-cli:

  ```yml
    - name: Ludown to LUIS model
      run: bf luis:convert -i $LU_FILE -o ./model.json --name 'LUIS CI pipeline - ${{ github.run_id }}' --versionid $luisAppVersion
  ```

The `model.json` file output must be imported to LUIS. This happens in different ways depending on whether the pipeline is operating as a PR gate-check - where it creates a new LUIS app for testing which is deleted at the end of the pipeline - or if operating as a Merge pipeline.

If the pipeline is operating as a PR gateway, it creates a new app. `bf luis:application:import` returns a string with LUIS App ID that we will need to use in the next steps, so we save the AppId in an environment variable called *AppId*:

  ```yml
    # When doing a gate check on PRs, we build a new LUIS application for testing that is later deleted
    - name: Create PR check LUIS application
      if: github.event_name == 'pull_request'
      run: |
        importResult=`bf luis:application:import --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ secrets.LUISAuthoringKey }}  --in model.json`
        echo "::set-env name=AppId::$(echo $(echo $importResult | cut -b 35-70))"
  ```

If operating as a Merge pipeline, the LUIS app is the one associated with the master branch. This app will be created if it does not already exist. This step determines the AppId and saves it in the *AppId* environment variable:

  ```yml
    # When doing a merge to master, use the master LUIS app - create if necessary (soft fails if exists)
    - name: Get master LUIS application ID
      if: github.event_name == 'push'
      run: |
        bf luis:application:create --name $LUIS_MASTER_APP_NAME --subscriptionKey ${{ secrets.LUISAuthoringKey }} --endpoint $luisAuthoringEndpoint --versionId=0.1
        bf luis:application:list --subscriptionKey ${{ secrets.LUISAuthoringKey }} --endpoint $luisAuthoringEndpoint | \
        jq -c '.[] | select(.name | . and contains('\"$LUIS_MASTER_APP_NAME\"')) | .id' | \
        xargs -I {} echo "::set-env name=AppId::{}"
        echo "Found LUIS app: $AppId"
  ```

Next, we check if the LUIS app currently has 100 versions (the limit), and if so print a warning and fail the pipeline. In order to resolve this, unneeded versions must be deleted from the LUIS master app.

  ```yml
    - name: Purge LUIS app version
      run: |
        version_count=$(bf luis:version:list --appId $AppId --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ secrets.LUISAuthoringKey }} | jq 'length')
        if [ $version_count -ge 100 ]; then
          echo "ERROR: LUIS app: $AppId version count will exceed 100. Delete unneeded versions before re-running pipeline"
          exit 1
        fi
  ```

Then we go ahead and create a new version in the LUIS app by importing the JSON created earlier. (This step will only do something when the LUIS app is the one targeted by the Merge pipeline):

  ```yml
    # When doing a CI/CD run on push to master, we create a new version in an existing LUIS application
    - name: Create new LUIS application version
      if: github.event_name == 'push'
      run: bf luis:version:import --appId $AppId --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ secrets.LUISAuthoringKey }} --in model.json
  ```

#### Train and publish the LUIS app

  ```yml
    - name: Train luis
      shell: bash
      run: bf luis:train:run --appId $AppId --versionId $luisAppVersion --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ secrets.LUISAuthoringKey }} --wait
  ```

After the model has finished training we can publish our LUIS model. We use *direct version publishing* for this rather than publishing to the named slots, staging and production. We do this to be able to support more than two published versions at any one time so that multiple LUIS app versions can be in a published state at any one time to support more then two dev environments simultaneously (for example, DEV, QA, UAT, PRODUCTION. We use a cURL command here to call the REST API directly:

  ```yml
    - name: Publish luis
      run: |
        curl POST $POSTurl \
        -H "Content-Type: application/json" \
        -H "Ocp-Apim-Subscription-Key: ${{ secrets.LUISAuthoringKey }}" \
        --data-ascii "{'versionId': '$luisAppVersion', 'directVersionPublish': true}"
      env:
        POSTurl: ${{ env.luisAuthoringEndpoint }}luis/authoring/v3.0-preview/apps/${{ env.AppId }}/publish
  ```

#### Testing the LUIS app

To prepare for testing, we install the NLU.DevOps test tool:

  ```yml
    - name: Install dotnet-nlu
      run: dotnet tool install -g dotnet-nlu
  ```

On the ubuntu agent, you need to append the tools directory to the system PATH variable for all subsequent actions in the current job to be able to use the cli tool.

  ```yml
    - name: Path
      run: echo "::add-path::$HOME/.dotnet/tools"
  ```

In order to test a LUIS app, you must use a Azure LUIS Prediction resource key since the Authoring key is not practicable since it is subject to throttling causing the tests to fail. Here we assign the Azure LUIS prediction resource to the application. Note that here we access the REST API using curl as the BotFramework CLI does not support the allocation of Azure LUIS resources:

  ```yml
    - name: Get Azure subscriptionId
      run: |
          az account show --query 'id' | \
          xargs -I {} echo "::set-env name=AzureSubscriptionId::{}"

    - name: Assign LUIS Azure Prediction resource to application
      run: |
        curl POST $POSTurl \
        -H "Authorization: Bearer $(az account get-access-token --query accessToken -o tsv)" \
        -H "Content-Type: application/json" \
        -H "Ocp-Apim-Subscription-Key: ${{ secrets.LUISAuthoringKey }}" \
        --data-ascii "{'AzureSubscriptionId': '$AzureSubscriptionId', 'ResourceGroup': '$AzureResourceGroup', 'AccountName': '$AzureLuisPredictionResourceName' }"
      env:
        POSTurl: ${{ env.luisAuthoringEndpoint }}luis/authoring/v3.0-preview/apps/${{ env.AppId }}/azureaccounts

  ```

To test the LUIS app version that was created, we use the unit test file:

  ```yml
    - name: Test Luis model
      run: dotnet nlu test -s luisV3 -u $UNIT_TEST_FILE -o results.json
      env:
        luisAppId: ${{ env.AppId }}
        luisVersionId: ${{ env.luisAppVersion }}
        luisDirectVersionPublish: true
        luisEndpointKey: ${{ secrets.LUISPredictionKey }}
        luisPredictionResourceName: ${{ env.AzureLuisPredictionResourceName }}
  ```

To evaluate results we use two files: the *unit test file* that consists of test utterances and the expected intents and entities results and `results.json` file which was created by the Test LUIS model step and contains the actual results returned from testing the LUIS model:

  ```yml
    - name: Analyze Unit test results
      run: dotnet nlu compare -e $UNIT_TEST_FILE -a results.json --unit-test --output-folder unittest
  ```

We archive the test results as a build pipeline artifact:

  ```yml
    - name: Archive Unit Test Results
      uses: actions/upload-artifact@v1
      with:
        name: UnitTestResult
        path: unittest/TestResult.xml
  ```

Finally, if the pipeline is operating as a PR gate-check, the LUIS app created by this pipeline is deleted again:

  ```yml
      # Delete the LUIS app again if we are executing as gate check on a PR
    - name: Delete luis test target app
      if: always() && (github.event_name == 'pull_request')
      shell: bash
      run:  bf luis:application:delete --appId $AppId --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ secrets.LUISAuthoringKey }} --force
  ```

### Job: LUIS quality testing

In the LUIS quality testing job in the CI/CD pipeline, we execute the LUIS F-measure tests to calculate the F-measure and to produce the test results file, which contains:

* For each Intent and Entity:
  * Count of true positives for passing tests
  * Count of true negatives for passing tests
  * Count of false positives from failing tests
  * Count of false negatives from failing tests

In the pipeline:
  
* We publish the F-measure for this build as a build artifact and save to blob storage
* Fetch the test results for the previous build from blob storage
* Publish the comparison between the current build and the previous build for the F-measure

The step only executes after the **build** step has succeeded and only if we are operating as a Merge pipeline. There is also the `BASELINE_CONTAINER_NAME` environment variable that needs to be set at the top of the luis_ci.yaml file with the container name of a baseline set of test results that we want to compare our newly built model to. Leave blank to skip the comparison stage.

  ```yml
  # Job: LUIS quality testing
  LUIS_quality_testing:
    name: LUIS F-measure testing
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push'  
  ```

Many of the steps to setup tools and assign Azure LUIS resources are the same as in the previous step so are not repeated here. This section will describe only the significant steps that carry out the F measure testing.

#### Establish the new App Version built by the Build job

The pipeline step executes in its own build environment, so early in this step we must establish what the most recent version of the LUIS app that was created by the build step. The version string is saved in an environment variable named *LuisVersion*.

  ```yml
    - name: Get master LUIS application ID
      run: |
        bf luis:application:list --subscriptionKey ${{ secrets.LUISAuthoringKey }} --endpoint $luisAuthoringEndpoint | \
        jq -c '.[] | select(.name | . and contains('\"$LUIS_MASTER_APP_NAME\"')) | .id' | \
        xargs -I {} echo "::set-env name=AppId::{}"
        echo "Found LUIS app: $AppId"

    - name: Get LUIS latest version ID
      run: |
        bf luis:version:list --appId $AppId --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ secrets.LUISAuthoringKey }} --take 1 | \
        jq '.[0].version' | \
        xargs -I {} echo "::set-env name=LuisVersion::{}"
  ```

#### Executing F measure testing

Testing uses the verification test file rather than the unit test file:

  ```yml
    - name: Test Luis model with quality verification tests
      run: dotnet nlu test -s luisV3 -u $QUALITY_TEST_FILE -o F-results.json
      env:
        AzureLuisResourceName: ${{ env.AzureLuisPredictionResourceName }}
        luisAppId: ${{ env.AppId }}
        luisVersionId: ${{ env.LuisVersion }}
        luisDirectVersionPublish: true
        luisEndpointKey: ${{ secrets.LUISPredictionKey }}
        luisPredictionResourceName: ${{ env.AzureLuisPredictionResourceName }}
  ```

#### Compare F measure results with baseline

If you have set the `BASELINE_CONTAINER_NAME` environment variable to the name of a container in Azure Storage containing test results from a previous run, then we will download those test results to use as the baseline:

  ```yml
    - name: download baseline
      if: env.BASELINE_CONTAINER_NAME != ''
      uses: azure/CLI@v1
      with:
        azcliversion: 2.2.0
        inlineScript: |
          az storage blob download  --account-name ${{  env.AzureStorageAccountName  }} --container-name ${{  env.BASELINE_CONTAINER_NAME  }}  --name statistics.json  --file baselinefile.json --auth-mode login

  ```

Then we compare the results from testing the new model with the baseline model results:

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

Finally, we upload the F measure results as a build artifact and also to Azure Storage:

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

### Job: Release

The final job in the pipeline simply publishes details of the new endpoint in a GitHub Release. This step only executes if the **build** step has completed successfully, and only if the pipeline is operating as a Merge pipeline to master.

  ```yml
  # Job: Publishes the latest version details, from which the endpoint can be derived
  release:
    name: Create LUIS Release
    runs-on: ubuntu-latest
    needs: build
    if: github.event_name == 'push'
    steps:
  ```

As before, we will not describe steps that are duplicates of those in the **build** step and which are described above.

These steps determine the version Id of the model built by the **build** step:

  ```yml
    - name: Get master LUIS application ID
      run: |
        bf luis:application:list --subscriptionKey ${{ secrets.LUISAuthoringKey }} --endpoint $luisAuthoringEndpoint | \
        jq -c '.[] | select(.name | . and contains('\"$LUIS_MASTER_APP_NAME\"')) | .id' | \
        xargs -I {} echo "::set-env name=AppId::{}"
        echo "Found LUIS app: $AppId"

    - name: Get LUIS latest version ID
      run: |
        bf luis:version:list --appId $AppId --endpoint $luisAuthoringEndpoint --subscriptionKey ${{ secrets.LUISAuthoringKey }} --take 1 --out luis_latest_version.json
        cat luis_latest_version.json | jq '.[0].version' | \
        xargs -I {} echo "::set-env name=LuisVersion::{}"
  ```

Then it creates a GitHub Release, which also tags the repo using the version Id:

  ```yml
      - name: Create Release
      id: create_release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} # This token is provided by Actions, you do not need to create your own token
      with:
        tag_name: ${{ env.LuisVersion }}
        release_name: Release ${{ env.LuisVersion }}
        body: |
          Releasing new LUIS endpoint
        draft: false
        prerelease: false
  ```

  Finally, it uploads the version details as a Release asset:

  ```yml
    - name: Upload Release Asset
      id: upload-release-asset
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        upload_url: ${{ steps.create_release.outputs.upload_url }} # This pulls from the CREATE RELEASE step above, referencing it's ID to get its outputs object, which include a `upload_url`.
        asset_path: ./luis_latest_version.json
        asset_name: luis_latest_version.json
        asset_content_type: application/json
  ```

A *Release Manager* can determine the version Id of the LUIS app by examining the **luis_latest_version.json** file uploaded as the Release artifact which they can find by going to the Releases page for their GitHub repository.

From this, the endpoint URL can be determined, as follows:

<code>
https://<i>azureLUISPredictionResourceName</i>.cognitiveservices.azure.com/luis/prediction/v3.0/apps/<i>appId</i>/versions/<i>versionId</i>/predict?verbose=true&subscription-key=<i>predictionKey</i>&query=<i>query</i>
</code>.
