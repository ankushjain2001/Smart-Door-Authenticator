var apigClient = apigClientFactory.newClient({});

$('document').ready(function () {
  $("#submitOTP").on('click', function () {
    event.preventDefault();
    var body = {
      "otp": document.getElementById("otp").value
    };
    apigClient.rootPost(null, body)
      .then(function (result) {
        alert(result.data.body)
        console.log(result);
      }).catch(function (result) {
        alert('Permission Denied')   
      });
  });
});
