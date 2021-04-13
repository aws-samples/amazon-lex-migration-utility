# Amazon Lex Migration Utility

## Purpose

The Amazon Lex Migration Utility allows you to easily migrate [Amazon Lex Chatbots](https://aws.amazon.com/lex/) between accounts.

The Lex Migration Utility consists of a Python script that exports Lex definitions to an [AWS CloudFormation](https://aws.amazon.com/cloudformation/) template and three [custom resources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html) to create [bots](https://github.com/andrew-templeton/cfn-lex-bot), [Intents](https://github.com/andrew-templeton/cfn-lex-intent), and [slots](https://github.com/andrew-templeton/cfn-lex-slot-type)

## Installation

### Install the Serverless Application Model

[Getting started with AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started.html)

### Install CloudFormation custom resources in the target account

``` bash
sam build -t lex_custom_resource_template.yml  
sam package --output-template-file custom-resources-sam-template.yml --resolve-s3
sam deploy --template-file custom-resources-sam-template.yml  --stack-name lex-custom-resources --capabilities "CAPABILITY_NAMED_IAM"
```

## Usage

### Create a configuration file

```json
{
    "ResourceFilters":
    {
        "SlotTypes":["FlowerType","PickupDate","PickupTime"],
        "Intents":["OrderFlowers"],
        "Bots":["OrderFlowers"]
    },
    "Output":{
        "Filename": "order-flowers-template.json",
        "TemplateDescription":"Creates resources needed for the OrderFlowers Sample "
    }
}
```

`ResourceFilters` allow you to choose which bots, intents, and slots get exported.  Any resources which contain the specified values as part of their name will be exported.

`Output`

&nbsp;&nbsp;&nbsp;&nbsp;`Filename` the name of the exported template

&nbsp;&nbsp;&nbsp;&nbsp;`TemplateDescription` Populates the `Description` field of the CloudFormation template

### Export Lex definitions from the source account

#### Prerequisites

##### Python 3.x

The Amazon Lex Migration Utility requires [Python 3.x](https://www.python.org/downloads/)

##### Configure the AWS CLI with a profile for the source account

The easiest method to export the definition is to create a [named profile](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) for the *source_account*:

`aws configure --profile <source_account>`

##### Install dependencies

```bash
pip install --requirements requirements.txt #installs dependencies.  This only needs to be run the first time.
```

#### Export resources

Then from the destination account:

```bash
python create_lex_template.py --config-file <configuration file>  --profile <source account>
```

### Deploy to the destination account

```bash
sam deploy --template-file <utput template> --stack-name <stack name> --resolve-s3 --capabilities "CAPABILITY_NAMED_IAM"
```

## Known Issues

- Deleting a stack with custom Lex resources does not always delete cleanly. If the custom resource returns a "Conflict Exception". Keep trying to delete the stack.
- Occasionally, some resources are not deleted successfully although CloudFormation will report success.

## Acknowledgements

The custom resources used by the Lex Migration Utility are slightly modified forks of work done by [Andrew Templeton](https://github.com/andrew-templeton)
