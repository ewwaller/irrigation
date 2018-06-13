var form;
/* enter actions */
var enterActions = {'theText' : getZones};
$(document).ready(function() {
    form = new formHandler('theZones', enterActions);
    form._extendedKey = [];
    
    $.ajax({
	type: 'POST',
	url: "getzones",
	contentType: "application/json",
	processData: false,
	success: function(data) {
            var a = JSON.parse( data );
            for (var x in a){
                $("#"+x).val(a[x]);
	      }
	},
	dataType: "text"
    });
})

function getZones(){
    $.ajax({
	type: 'POST',
	url: "setzonenames",
	contentType: "application/json",
	processData: false,
	data: JSON.stringify(form.get()),
	success: function(data){ window.location = 'index'},
	dataType: "text"
    });
}
