/* MIT License

Copyright (c) 2018 Eric Waller

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

*/

var form;
var lightingControls;
/* enter actions */
var enterActions = {'theText' : postNewEvent};
var dayNames=['Monday','Tuesday','Wednesday',
	      'Thursday','Friday','Saturday','Sunday']
var oldCount = -1
$(document).ready(function() {
    UpdateTime();
    UpdateSchedule();
    form = new formHandler('theEvent', enterActions);
    form._extendedKey = [];
    manualForm = new formHandler('manualControls', {});
    lightingForm = new formHandler('lightingControls',{});
    setBoxColor('queue',"#50ff50")
    setBoxColor('addevent',"#5050ff")
    $.ajax({
	type: 'POST',
	url: "getzones",
	contentType: "application/json",
	processData: false,
	success: function(data) {
            var a = JSON.parse( data );
            for (var x in a){
                $("#"+x).html(a[x]);
                $("#m"+x).html(a[x]);
	    }
	},
	dataType: "text"
    });
});


function UpdateTime(){
    $.ajax({
	type: 'POST',
	url: "servertime",
	contentType: "application/json",
	processData: false,
	success: function(data) {
	    var theResponse = JSON.parse(data);
	    $("#list").html(dayNames[theResponse.wkday]+ " " +
			    theResponse.hour.toString().padStart(2,'0') + ":" +
			    theResponse.min.toString().padStart(2,'0') + ":" +
			    theResponse.sec.toString().padStart(2,'0'));
	    if (theResponse.running == "running"){
		setBoxColor('queue',"#50ff50")
		$('#manual').hide();
		$("#runStopButton").html("Stop");
	    }
	    else{
		setBoxColor('queue',"#ff5050")
		$('#manual').show();
		$("#runStopButton").html("Run");
	    }
	    for (var x = 0 ; x< theResponse.manual.length ; x++)
		$("#manual"+(x+1)).prop('checked',theResponse.manual[x]);
	    if (theResponse.lightsState.state){
		$("#lightState").html("On")
		$("#lightsButton").html("Turn Lights Off")
	    }
	    else{
		$("#lightState").html("Off")
		$("#lightsButton").html("Turn Lights On")
	    }
	    if (theResponse.lightsState.changeCount>oldCount  && theResponse.lights){
		oldCount = theResponse.lightsState.changeCount;
		$("#lightingAuto").prop('checked',theResponse.lights.lightingAuto);
		$("#lightOnTime").val(theResponse.lights.lightOnTime);
		$("#lightOffTime").val(theResponse.lights.lightOffTime);
		$("#lightOnTime2").val(theResponse.lights.lightOnTime2);
		$("#lightOffTime2").val(theResponse.lights.lightOffTime2);
		$("#extant").hide()
	    }
	    else
		if (oldCount > theResponse.lightsState.changeCount)
		    $("#extant").show();
	},
	error: function(){
	    $("#lightState").html("unknown");
	    $("#list").html("Please stand by...");
	},
	timeout:3000,
	dataType: "text"
    });
    $.ajax({
	type: 'POST',
	url: "getqueue",
	contentType: "application/json",
	processData: false,
	success: function(data) {
	    var theResponse = JSON.parse(data);
	    if (theResponse.length > 0){
		events=[];
		for (i in theResponse){
		    eventString=theResponse[i].duration[0] + ":" +
			theResponse[i].duration[1].toString().padStart(2,'0')
			+ "    " +
			$("#valve"+theResponse[i].zone).text();
		    if (i>0)
			events.push(eventString);
		    else
			$("#activeEvent").html(eventString)
		}
		if (events.length == 0)
		    events.push("Queue is empty");
		$("#queuedEvents").html(listCreateHtml(events));
	    }
	    else{
		$("#activeEvent").html("There are no active events");
		$("#queuedEvents").html("Queue is empty")
	    }
	},
	dataType: "text"
    });
    setTimeout(UpdateTime, 500);
}

function UpdateSchedule(){
    $('#selectable .ui-selected').removeClass('ui-selected');
    resultArray=[];
    $.ajax({
	type: 'POST',
	url: "schedule",
	contentType: "application/json",
	processData: false,
	success: function(data) {
	    var pretty=[];
	    var a = JSON.parse(data);
	    for (var x in a){
		var theString = a[x].day + " at " + a[x].eventTime+ ". Run times: ";
		for (var y = 1 ; "valve"+y in a[x] ; y++)
		    theString += a[x]['valve' + y] + ", "
		theString = theString.substring(0,theString.length-2)
		pretty.push(theString);
	    }
	    $("#selectable").html(listCreateHtml(pretty));
	},
	dataType: "text"
    });
}

function setBoxColor(theBox, theColor){
    a=document.getElementById(theBox);
    a.style.borderColor=theColor ;
    b=a.getElementsByTagName('h3')[0];
    b.style.backgroundColor = theColor;
}
function postNewEvent(){

    $.ajax({
	type: 'POST',
	url: "addevent",
	contentType: "application/json",
	processData: false,
	data: JSON.stringify(form.get()),
	success: setTimeout(UpdateSchedule, 200),
	dataType: "text"
    });
}

function runStop(){
    var newState= "running";
    if 	($('#runStopButton').html() =="Stop")
	newState= "stopped";

    $.ajax({
	type: 'POST',
	url: "runstate",
	contentType: "application/json",
	processData: false,
	data: JSON.stringify({"running": newState}),
	success: setTimeout(UpdateSchedule, 200),
	dataType: "text"
    });
}

function clearQueue(){
    $.ajax({
	type: 'POST',
	url: "clearqueue",
	contentType: "application/json",
	processData: false,
	success: setTimeout(UpdateSchedule, 200),
	dataType: "text"
    });
}


function listCreateHtml(dataObject) {
    var listHtml = "";
    var templateHtml = $("#template-list-item").html();
    
    for (key in dataObject) {
	listHtml += templateHtml.replace(/{{id}}/g, key)
            .replace(/{{value}}/g, dataObject[key]);
    }
    return listHtml;
}


function manualClick(){
    $.ajax({
	type: 'POST',
	url: "manual",
	contentType: "application/json",
	processData: false,
	data: JSON.stringify(manualForm.get()),
	dataType: "text"
    });
}

function lightsToggle(){
    newState="On";
    if ($("#lightState").html()=="On")
	newState="Off";
    $("#lightState").html(newState)
    lightsUpdate();
}
function lightsUpdate(){
    var theData={};
    theData.controls=lightingForm.get();
    theData.state = ($("#lightState").html()=="On");
    $.ajax({
	type: 'POST',
	url: "lights",
	contentType: "application/json",
	processData: false,
	data: JSON.stringify(theData),
	dataType: "text"
    });
}

var result;
var resultArray=[];
$( function() {
    $( "#selectable" ).selectable({
	stop: function() {
	    result = $( "#select-result" ).empty();
	    resultArray=[];
	    $( ".ui-selected", this ).each(function() {
		var index = $( "#selectable li" ).index( this );
		resultArray.push(index+1);
	    });
	}
    });
} );

function deleteEvent(){
    $.ajax({
	type: 'POST',
	url: "deleteevent",
	contentType: "application/json",
	processData: false,
	data: JSON.stringify(resultArray),
	success: setTimeout(UpdateSchedule, 200),
	dataType: "text"
    });
}

function queueEvent(){
    $.ajax({
	type: 'POST',
	url: "queueevent",
	contentType: "application/json",
	processData: false,
	data: JSON.stringify(resultArray),
	success: setTimeout(UpdateSchedule, 200),
	dataType: "text"
    });
}
