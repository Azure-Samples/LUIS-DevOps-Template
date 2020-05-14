# 3. Customizing the repository for your own project

This sample uses a sample LUIS project ***vacation_requests***, defined in this repo in the [model.lu file](../luis-app/model.lu). The sample project creates a language understanding model to handle requests for vacation from employees.

If you have built the sample project and have the pipeline working, it is very simple to adapt it to support your own project.

## Starting a new project from scratch

1. Create a Feature branch in your repository

1. Define your own app model using LUDown by one of the two methods:

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

## Further Reading

See the following documents for more information on this template and the engineering practices it demonstrates:

* [Project Setup and configuration](1-project-setup.md)

* [Creating a Feature branch, updating your LUIS app, and executing the CI/CD pipelines](2-feature-branches-and-running-pipelines.md)

* [CI/CD pipeline operation](4-pipeline.md#pipeline-steps)
