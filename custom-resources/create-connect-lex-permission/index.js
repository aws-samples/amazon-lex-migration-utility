process.env.AWS_SDK_LOAD_CONFIG = true;
const AWS = require("aws-sdk");
const response = require("cfn-response-async");
const connect = new AWS.Connect();

exports.handler = async function (event, context) {
  try {
    console.log(JSON.stringify(event, null, 2));
    var instanceId = event.ResourceProperties.InstanceId;
    var name = event.ResourceProperties.Name;
    if (!instanceId || !name) {
      throw "InstanceId and Name are required.";
    }

    var params = {
      InstanceId: instanceId,
      LexBot: {
        LexRegion: process.env.AWS_REGION,
        Name: name,
      },
    };

    if (event.RequestType == "Delete") {
      await connect
        .disassociateLexBot({
          BotName: name,
          InstanceId: instanceId,
          LexRegion: process.env.AWS_REGION,
        })
        .promise();
    }
    if (event.RequestType == "Update" || event.RequestType == "Create") {
      await connect.associateLexBot(params).promise();
    }
    await response.send(event, context, "SUCCESS", {});
  } catch (e) {
    console.log(e);
    await response.send(event, context, "FAILED", {});
  }
};
