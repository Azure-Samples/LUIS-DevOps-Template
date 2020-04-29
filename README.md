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

Use this repository to develop a LUIS application while following DevOps engineering practices that adhere to software engineering fundamentals around source control, testing, CI/CD and release management. This template repository provides a working project structure and GitHub Actions pipelines that you can customize for use with your own project.

You can find out more about LUIS in the [Language Understanding (LUIS) documentation](https://docs.microsoft.com/azure/cognitive-services/luis/).

## Contents

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
- [Azure CLI](https://docs.microsoft.com/cli/azure/install-azure-cli?view=azure-cli-latest)

## How to use this template repository

Follow these steps to run this workflow in your personal GitHub repository:

1. Follow the [Project setup instructions](1-project-setup.md) to clone this template repository to your own GitHub account and to configure it for use.
2. Follow the [Making updates to a LUIS app in a feature branch](./docs/2-feature-branches-and-running-pipelines.md) tutorial to understand the "dev inner loop" workflow for making updates to the LUIS app while using DevOps practices.
3. This template repository uses a sample LUIS project ***vacation_requests***, defined in this repo in the [model.lu file](../luis-app/model.lu). To use this repository with your own project, follow these instructions: [Customizing the repository for your own project](./docs/3-customizing-own-project.md).

## Contributing

This project welcomes contributions and suggestions.  Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit <https://cla.opensource.microsoft.com.>

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
