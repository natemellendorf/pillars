
// - Logic for dynamic required form inputs
const lhLocation = document.getElementById('lh_location');
const lhPort = document.getElementById('lh_port');
const lhIP = document.getElementById('lh_ip');
const joinForm = document.getElementById('nebula_join_form');

joinForm.addEventListener('keyup', function (event) {

  isValidLhLocation = lhLocation.checkValidity();
  isValidLhPort = lhPort.checkValidity();
  isValidLhIP = lhIP.checkValidity();

  if ( isValidLhLocation && lhLocation.value !== "" ) {
    lhPort.required = true;
    lhIP.required = true;
  } else if (isValidLhPort && lhPort.value !== "") {
    lhLocation.required = true;
    lhIP.required = true;
  } else if (isValidLhIP && lhIP.value !== ""){
    lhPort.required = true;
    lhLocation.required = true;
  } else {
    lhLocation.required = false;
    lhPort.required = false;
    lhIP.required = false;
  };
});


$('#nebula_create_form').submit(function () {
 nebula_create();
 return false;
});

$('#nebula_join_form').submit(function () {
 nebula_join();
 return false;
});

function hide(){
  $('#alert_div').hide();
}

function nebula_create() {
    var name = document.forms["nebula_create_form"]["nebula_name"].value;

    var create_data = {
      name: name
    };

    //console.log("Requested: " + create_data);

    // Create a new Nebula
    socket.emit('nebula_create', {"data": create_data})
    // Refresh the list of Nebulas
    socket.emit('nebula_refresh', {"data": "Refresh requested"})
};

function nebula_join() {
    var nebula = document.forms["nebula_join_form"]["nebula_list"].value;
    var device_name = document.forms["nebula_join_form"]["device_name"].value;
    var device_ip = document.forms["nebula_join_form"]["device_ip"].value;
    var device_group = document.forms["nebula_join_form"]["device_group"].value;
    var lh_location = document.forms["nebula_join_form"]["lh_location"].value;
    var lh_port = document.forms["nebula_join_form"]["lh_port"].value;
    var lh_ip = document.forms["nebula_join_form"]["lh_ip"].value;

    var join_data = {
        nebula: nebula,
        device_name: device_name,
        device_ip: device_ip,
        device_group: device_group,
        lh_location: lh_location,
        lh_port: lh_port,
        lh_ip: lh_ip
    };

    if (nebula_name == "") {
    alert("Name must be filled out");
    return false;
    }

    //console.log("Requested: " + join_data);
    socket.emit('nebula_join', {"data": join_data})

};

// SOCKETS
var socket = io.connect('http://' + document.domain + ':' + location.port);
console.log('http://' + document.domain + ':' + location.port);


// When a "nebula_refresh" is received:
socket.on('nebula_refresh', function(data) {
  // Loop over found Nebulas, and create a new list in HTML
  var newOptions = [];
  var selected = document.forms["nebula_create_form"]["nebula_name"].value;
  for (var i = 0; i < data.length; i++) {
    console.log(data[i]);
    if (data[i] == selected){
      newOptions.push("<option selected>"+data[i]+"</option>");
    } else {
    newOptions.push("<option>"+data[i]+"</option>");
    };
  };
  // Once gathered, update the options for Nebulas
  document.getElementById("nebula_list").innerHTML = newOptions.join();
  return false;
});


// When a "return" is received:
socket.on('return', function(data) {
    str_msg = JSON.stringify(data, null, 4);
    console.log(str_msg);
    if (data['error']) {
        $('#alert_div').show();
        document.getElementById("alert_msg").innerHTML = data['error'];
    }
    if (data['zip_location']) {
      var zip = data['zip_location']
      var configFile = data['configFile']
      console.log('Offering ZIP:' + zip);
      console.log('Commands:' + configFile);
      $('#downloadModal').modal({
        backdrop: "static",
        keyboard: false
      });
      $('#download_link').attr("href", zip);
      document.getElementById("runcode").innerHTML = configFile;
      $('#downloadModal').modal('show');
    };
});
