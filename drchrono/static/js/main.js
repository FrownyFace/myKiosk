function displayTime() {
    var time = moment().format('HH:mm:ss');
    $('#clock').html(time);
    setTimeout(displayTime, 1000);
}


$(document).ready(function() {
    $('select').material_select();
    console.log('here');
    displayTime();
});
