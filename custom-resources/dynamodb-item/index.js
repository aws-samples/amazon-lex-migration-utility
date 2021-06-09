
const AWS = require("aws-sdk");
const response = require("cfn-response");
const docClient = new AWS.Connect
exports.handler = function(event, context) {
try {
    if (event.ResourceProperties.RequestType == "Delete")
    return;
    console.log(JSON.stringify(event, null, 2));
    var item = event.ResourceProperties.Item.replace("\n", "")
    console.log(item)
    var params = {
    TableName: event.ResourceProperties.TableName,
    Item: JSON.parse(event.ResourceProperties.Item.replace("\n", ""))
    };
    docClient.put(params, function(err, data) {
    if (err) {
        console.log(err)
        response.send(event, context, "FAILED", {});
    }
    else {
        response.send(event, context, "SUCCESS", {});
    }
    });
}
catch (e) {
    console.log(e)
    response.send(event, context, "FAILED", {});
}



};