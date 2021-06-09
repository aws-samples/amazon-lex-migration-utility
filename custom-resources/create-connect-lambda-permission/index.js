
const AWS = require("aws-sdk");
const response = require("cfn-response");
const docClient = new AWS.Connect();
exports.handler = function(event, context) {
try {

    console.log(JSON.stringify(event, null, 2));
    var instanceId = event.ResourceProperties.InstanceId;
    var lexRegion = event.ResourceProperties.LexRegion;
    var name = event.ResourceProperties.Name
    if(!instanceId && !lexRegion && !name){
        throw("InstanceId,LexRegion, and Name are required.")
    }
    var params = {
        InstanceId: instanceId,
        LexBot: { 
          LexRegion: lexRegion,
          Name: name
        }
      };

    if (event.ResourceProperties.RequestType == "Delete"){
        connect.disassociateLambdaFunction(params,(err,data) =>{
            if(err){
                throw err;
            }
            else console.log(data)
        })
    }
    if(event.ResourceProperties.RequestType == "Update" || event.ResourceProperties.RequestType == "Create"){
        connect.associateLambdaFunction(params,(err,data) =>{
            if(err){
                throw err;
            }
            else console.log(data)
        })   
    }
    response.send(event, context, "SUCCESS", {});

}
catch (e) {
    console.log(e)
    response.send(event, context, "FAILED", {});
}



};