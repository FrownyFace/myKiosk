

function displayTime() {
    var time = moment().format('HH:mm:ss');
    $('#clock').html(time);
    setTimeout(displayTime, 1000);
}

function millsecs_to_readable(date){
    var str = '';

        hours = date.getUTCHours()
        minutes = date.getUTCMinutes()
        seconds = date.getUTCSeconds()

        if(hours < 10){
            str +=  '0' + hours + ":";
        }else{
            str +=  hours + ":";
        }
        if(minutes < 10){
            str +=  '0' + minutes + ":";
        }else{
            str +=  minutes + ":";
        }
        if(seconds < 10){
            str +=  '0' + seconds;
        }else{
            str +=  seconds;
        }
    return str
}

function update_waiting_time(selection){
    $("."+selection+"_time").each(function (){
        parsed = new Date($(this).text())

        date = new Date(Math.abs(new Date() - parsed))
        str = millsecs_to_readable(date)

        id_num = this.id.replace( /^\D+/g, '');
        $("#"+selection+"_timediff_"+id_num).html(str)

    });
    setTimeout(function(){
        update_waiting_time(selection)
    }, 1000)
}

var init = false;

function avg_time(){
    if(init) return;
    init = true;
    x = $('#avg_waiting_time').text()
    str = millsecs_to_readable(new Date(parseInt(x,10)));
    $('#avg_waiting_time').html(str)

}

$(document).ready(function() {
    $('select').material_select();
    //$('.modal-trigger').leanModal();
    $('.grid').masonry({
      itemSelector: '.grid-item',
      columnWidth: 160,
      gutter: 2
    });

    $('#calendar').fullCalendar({
        header: {
				left: 'prev,next today',
				center: 'title',
				right: 'month,agendaWeek,agendaDay,listWeek'
				},
		navLinks: true, // can click day/week names to navigate views
		editable: false,
		eventLimit: true, // allow "more" link when too many events
        weekends: false,
        events: '/schedule/api/occurrences?calendar_slug=main',
    })
    $('#calendar').fullCalendar('changeView', 'agendaWeek')
    displayTime();
    update_waiting_time('checked_in');
    update_waiting_time('seen_at');
    avg_time();
});
