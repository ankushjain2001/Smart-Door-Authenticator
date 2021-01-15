var apigClient = apigClientFactory.newClient({});

$('document').ready(function () {
    
  $("#acceptReq").on('click', function () {
    event.preventDefault();

    const urlParams = new URLSearchParams(window.location.search);
    const uid = urlParams.get('uid');

    var body = {
      "name": document.getElementById("name").value,
      "phone": document.getElementById("phone").value,
      "faceId": uid
    };
	
	apigClient.rootPost(null, body)
      .then(function (result) {
        // console.log(result);
        alert("Visitor has been authorized.");
        setTimeout(function () { window.location.reload(); }, 10);
    
      }).catch(function (result) {
        console.log("Error occurred");
      });

  });
  
  $("#rejectReq").on('click', function () {
    event.preventDefault();
	var body = {
      "name": document.getElementById("name").value,
      "phone": document.getElementById("phone").value,
      "faceId": ""
    };
	apigClient.rootPost(null, body)
      .then(function (result) {
        // console.log(result);
        alert("Visitor has been rejected.");
        setTimeout(function () { window.location.reload(); }, 10);
    
      }).catch(function (result) {
        console.log("Error occurred");
      });
  });

});

window.onload = function () {
  const urlParams = new URLSearchParams(window.location.search);
  const uid = urlParams.get('uid');
  var img = document.createElement('img');
  img.style.height = "480px";
  img.style.width = "640px";
  img.style.marginTop = "20px";
  img.style.marginLeft = "auto";
  img.style.marginRight = "auto";
  img.src = "https://cc-hw2-ownerportal.s3.amazonaws.com/img/" + uid;
  document.getElementById("visitor-img").appendChild(img)
};
