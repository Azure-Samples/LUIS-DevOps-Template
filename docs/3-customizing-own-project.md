# 3. Customizing the repository for your own project

This sample uses a sample LUIS project ***vacation_requests***, defined in this repo in the [model.lu file](../luis-app/model.lu). The sample project creates a language understanding model to handle requests for vacation from employees.

If you have built the sample project and have the pipeline working, it is very simple to adapt it to support your own project.

## Starting a new project from scratch

1. Create a Feature branch in your repository

1. Define your own app model using LUDown by one of the two methods:

   * Write the LUDown directly into the **luis-app/model.lu** file using a text editor, replacing the sample app content.
   * Define your new LUIS app using the [preview portal](https://preview.luis.ai) and when you have made your changes, export the active version using the **Export as LU** menu. Rename the export file as **model.lu** and save it to the **luis-app** folder replacing the existing file.

   ![Export to LU](images/exportlu.png?raw=true "Exporting to LU")

1. Replace the contents of the **luis-app/tests/unittests.json** file with your own unit tests.

1. Replace the contents of the **luis-app/tests/verificationtests.json** file with your own verification tests.

1. Follow the steps described in [Setup the CI/CD pipeline](../README.md#setup-the-ci/cd-pipeline) to ensure that the CI/CD pipeline is configured correctly for your project.

1. Check in your changes and raise a PR to merge them into the master branch.

## Starting with an existing project

1. Create a Feature branch in your repository

1. Sign into the [LUIS preview portal](https://preview.luis.ai), and export the active version of your app using the **Export as LU** menu. Rename the export file as **model.lu** and save it to the **luis-app** folder replacing the existing file.

1. Replace the contents of the **luis-app/tests/unittests.json** file with your own unit tests.

1. Replace the contents of the **luis-app/tests/verificationtests.json** file with your own verification tests.

1. Follow the steps described in [Setup the CI/CD pipeline](1-project-setup.md#setup-the-cicd-pipeline) to ensure that the CI/CD pipeline is configured correctly for your project.

1. Check in your changes and raise a PR to merge them into the master branch.
