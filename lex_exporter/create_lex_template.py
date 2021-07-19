"""
  Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

  Licensed under the Apache License, Version 2.0 (the "License").
  You may not use this file except in compliance with the License.
  You may obtain a copy of the License at

      http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
"""
import boto3
import jsonschema

from functools import reduce, partial
import re
import json
import sys
import os

# TODO: Handle version updates


def show_help(short=True):
    command_line = f"{sys.argv[0]} --config-file config_file  [--help]"
    if short:
        return command_line
    else:
        with open("./lex_exporter/example-configuration.json") as file:
            config_example = file.read()
        return (command_line + "\n\n"
                               "Configuration file format \n"
                               f"{config_example}")


def get_latest_intent(intent_name):
    max_version = 0
    paginator = client.get_paginator('get_intent_versions')
    iterator = paginator.paginate(name=intent_name)
    for resources in iterator:
        for intent in resources["intents"]:
            if intent["version"] != "$LATEST" and int(intent["version"]) > max_version:
                max_version = int(intent["version"])
    return max_version


def create_lex_bot_aliases(resource_type,
                           name_contains,
                           service_token,
                           alias,
                           dependent_resources):
    depends_on = list(dependent_resources)
    paginator = client.get_paginator('get_bots')
    marker = None
    pages = paginator.paginate(nameContains=name_contains, PaginationConfig={
        'MaxItems': 1000,
        'PageSize': 10,
        'StartingToken': marker
    })
    for page in pages:
        for bot in page["bots"]:
            bot_resource_name = re.sub(r'[\W_]+', '', bot["name"])
            template["Resources"].update(
                    {bot_resource_name + "Alias": {
                        "Type": resource_type,
                        "DependsOn": list(set(depends_on) - set([bot_resource_name + "Alias"])),
                        "Properties": {
                            "ServiceToken": {"Fn::ImportValue": service_token},
                            "name": {"Fn::Sub": alias + "${ResourceSuffix}"},
                            "botVersion": "$LATEST",
                            "botName": bot["name"]
                        }
                    }})
            depends_on.append(bot_resource_name + "Alias")


def create_lex_bot_permissions(resource_type,
                               name_contains,
                               service_token,
                               connect_instance_id):
    paginator = client.get_paginator('get_bots')
    marker = None
    pages = paginator.paginate(nameContains=name_contains, PaginationConfig={
        'MaxItems': 1000,
        'PageSize': 10,
        'StartingToken': marker
    })
    for page in pages:
        for bot in page["bots"]:
            print(bot)
            bot_resource_name = re.sub(r'[\W_]+', '', bot["name"])
            template["Resources"].update(
                    {bot_resource_name + "Permission": {
                        "Type": resource_type,
                        "DependsOn": [bot_resource_name],
                        "Properties": {
                            "ServiceToken": {"Fn::ImportValue": service_token},
                            "InstanceID": "!Ref ConnectInstanceId",
                            "LexRegion": {"Ref": "AWS::Region"},
                            "Name": bot["name"]
                        }
                    }})


def create_resource(resource_type,
                    lex_list_function,
                    lex_get_details_function,
                    lex_type,
                    service_token,
                    name_contains,
                    dependent_resources=[]):
    marker = None
    iterator = lex_list_function(nameContains=name_contains, PaginationConfig={
        'MaxItems': 1000,
        'PageSize': 10,
        'StartingToken': marker
    })

    created_resources = []
    for type in iterator:
        types = type[lex_type]
        for resource in types:
            type_definition = lex_get_details_function(name=resource["name"])
            type_definition["createVersion"] = True
            resource_name = re.sub(r'[\W_]+', '', resource["name"])
            created_resources.append(resource_name)
            template["Resources"].update(
                {resource_name: {
                    "Type": resource_type,
                    "Properties": {
                        "ServiceToken": {"Fn::ImportValue": service_token}
                    }
                }})
            excluded_properties = ["ResponseMetadata", "lastUpdatedDate", "createdDate", "checksum", "version", "status"]
            keys_to_add = list(type_definition.keys() - set(excluded_properties))

            properties_to_add = list(map(lambda x: {x: type_definition[x]}, keys_to_add))
            template["Resources"][resource_name]["Properties"].update(reduce(lambda a, b: dict(a, **b), properties_to_add))
            if len(created_resources) != 0:
                template["Resources"][resource_name]["DependsOn"] = list(set(dependent_resources) - set([resource_name]))
            dependent_resources.append(resource_name)  # Hopefully prevents throttling by limiting the number of parallel requests
    return created_resources


profile = None


for i in range(len(sys.argv)):
    argv = sys.argv[i]
    if argv == "--help":
        print(show_help())
        sys.exit()
    if argv == "--config-file":
        i += 1
        config_file = sys.argv[i]
    if argv == "--profile":
        i += 1
        profile = sys.argv[i]

if profile is None:
    client = boto3.client('lex-models')
else:
    session = boto3.Session(profile_name=profile)
    client = session.client('lex-models')
print(sys.argv[2])
with open(sys.argv[2], "r") as file:
    config = json.load(file)
with open("./lex_exporter/config_schema.json", "r") as file:
    schema = json.load(file)

try:
    jsonschema.validate(instance=config, schema=schema)
except Exception:
    print(f"{config_file} is not valid config file.")
    sys.exit(show_help(True))


template = {
    "AWSTemplateFormatVersion": "2010-09-09",
    "Description": config["Output"]["TemplateDescription"],
    "Resources": {},
    "Parameters": {
        "ResourceSuffix": {
            "Type": "String",
            "Default": "",
            "Description": "Optional suffix to add each resource"
        }

    }
}


paginator = client.get_paginator('get_slot_types')
resources = []
for prefixes in config["ResourceFilters"]["SlotTypes"]:
    resources += create_resource("Custom::LexSlotType",
                                 paginator.paginate,
                                 partial(client.get_slot_type, version="$LATEST"),
                                 "slotTypes",
                                 "LexSlotCustomResource",
                                 prefixes,
                                 resources)

paginator = client.get_paginator('get_intents')
for prefixes in config["ResourceFilters"]["Intents"]:
    resources += create_resource("Custom::LexIntent",
                                 paginator.paginate,
                                 partial(client.get_intent, version="$LATEST"),
                                 "intents",
                                 "LexIntentCustomResource",
                                 prefixes,
                                 resources)


paginator = client.get_paginator('get_bots')
alias = config["Build"]["LexAlias"]
for prefixes in config["ResourceFilters"]["Bots"]:
    bots = create_resource("Custom::LexBot",
                           paginator.paginate,
                           partial(client.get_bot, versionOrAlias="$LATEST"),
                           "bots",
                           "LexBotCustomResource",
                           prefixes,
                           resources)

    create_lex_bot_aliases("Custom::LexBotAlias",
                           prefixes,
                           "LexBotAliasCustomResource",
                           alias, bots)
    if(config["Build"]["CreateConnectPermissions"]):
        create_lex_bot_permissions("Custom::LexBotPermission",
                                   prefixes,
                                   "LexConnectPermissionCustomResource")
        template["Paramters"] = {
            "ConnectInstanceID": {
                "Type": "String",
                "AllowedValues": ".+",
                "ConstraintDescription": "ConnectInstanceID is required"
            }
        }
    resources += bots

for bot in bots:
    intents = template["Resources"][bot]["Properties"]["intents"]
    for intent in intents:
        intent["intentVersion"] = 1


with open(os.path.join(sys.path[0], config["Output"]["Filename"]), 'w') as f:
    json.dump(template, f, indent=4, default=str)