# Amazon Lex Migration Utility

## Purpose

The Amazon Lex Migration Utility allows you to easily migrate [Amazon Lex Chatbots](https://aws.amazon.com/lex/) between accounts.

The Lex Migration Utility consists of a Python script that exports Lex definitions to an [AWS CloudFormation](https://aws.amazon.com/cloudformation/) template and three [custom resources](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/template-custom-resources.html) to create [bots](https://github.com/andrew-templeton/cfn-lex-bot), [Intents](https://github.com/andrew-templeton/cfn-lex-intent), and [slots](https://github.com/andrew-templeton/cfn-lex-slot-type)

## Installation

### Install the Serverless Application Model

[Getting started with AWS SAM](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/serverless-getting-started.html)

### Install AWS CloudFormation custom resources in the target account

``` bash
sam build -t custom_resource_template.yml  
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
python3 ./exporter/create_lex_template.py --config-file <configuration file>  [--profile <source account>]
```

### Deploy to the destination account

```bash
sam deploy --template-file <utput template> --stack-name <stack name> --resolve-s3 --capabilities "CAPABILITY_NAMED_IAM"
```

### Custom Resources created.

Each custom resource wraps the corresponding API.  

- [CFNBot](https://docs.aws.amazon.com/cli/latest/reference/lex-models/put-bot.html) - Creates an Amazon Lex Bot
- [CFNIntentLex](https://docs.aws.amazon.com/cli/latest/reference/lex-models/put-intent.html) - Creates a Lex Intent
- [CFNSlotLex](https://docs.aws.amazon.com/cli/latest/reference/lex-models/put-slot-type.html) - Creates a Lex Slot
- [CFNBotLexAlias](https://docs.aws.amazon.com/cli/latest/reference/lex-models/put-bot-alias.html) - Creates a Lex Alias
- [CFNConnectAssociateLex](https://docs.aws.amazon.com/cli/latest/reference/connect/associate-lex-bot.html) - Associates a Lex Bot to am Amazon Connect instance.

## Known Issues

- Deleting a stack with custom Lex resources does not always delete cleanly. If the custom resource returns a "Conflict Exception". Keep trying to delete the stack.
The *lex exporter* scripts works around this by adding a [DependsOn](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-attribute-dependson.html) constraint to each resource to force CloudFormation to create and delete synchronously instead of in parallel.


## Acknowledgements

The custom resources used by the Amazon Lex Migration Utility are slightly modified forks of work done by [Andrew Templeton](https://github.com/andrew-templeton)
