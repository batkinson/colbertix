var eventsDays = new Array();

$(document).ready(function() {

	
	$("input.number").change(function(){
    	var str = new String(this.value);
    	if (str.length>10){
    		this.value = str.substring(0, 10);
    	}
    });
	
	$("input.number").live("keypress", function(e){
    	if($.browser.mozilla && e.keyCode) return true;
    	if ((new String(this.value).length)<10){
    		return /\d+/.test(String.fromCharCode(e.keyCode || e.charCode));
    	}
    	else{
    		return false;
    	}
    	
    });
	
	$("input.phoneNumber").live("keypress", function(e)	{
		if($.browser.mozilla && e.keyCode) return true; 
		return /[0-9]+|(-)+|(\()+|(\))+/.test(String.fromCharCode(e.keyCode || e.charCode));});
	
	jQuery(function($) {
		jQuery(".scrollable").scrollable({
			vertical: true,
			keyboard: false,
			size: 8,
			next: '.calendarDown',
			prev: '.calendarUp',
			speed: 200
		}).mousewheel();
	});

	ajaxGetDatesWithEvents();

	$('#lnk_cancel_reservation').click(function(){

		var code = $(this).attr('class');

		$('#rc_container').block();
		$.ajax({
			type:		"POST",
			url:		"/site/cancelreservation",
			data:		{code: code},
			dataType:	'json',
			complete: function(xhr) {
				$('#rc_container').unblock();
			},
			success: function(data){
				$('#cont_question').hide();
				$('#cont_cancel_message').show();
			}
		});
		return false;
	});

	$('#lnk_confirm_reservation').click(function(){

		var code = $(this).attr('class');

		$('#rc_container').block();
		$.ajax({
			type:		"POST",
			url:		"/site/confirmreservation",
			data:		{code: code},
			dataType:	'json',
			complete: function(xhr) {
				$('#rc_container').unblock();
			},
			success: function(data){
				if (data.code && data.code == 2)
				{
					$('#cont_question').hide();
					$('#cont_reservation_already_comlete').show();
				}
				else
				{
					$('#cont_question').hide();
					$('#cont_confirm_message').show();
				}
			}
		});
		return false;
	});

	$('#lnk_show_events_list').addClass('selected').click(function(){
		showEventsList();
		$('#lnk_show_events_list').addClass('selected');
		$('#lnk_show_events_calendar').removeClass('selected');
		return false;
	});
	$('#lnk_show_events_calendar').click(function(){
		showEventsCalendar();
		$('#lnk_show_events_list').removeClass('selected');
		$('#lnk_show_events_calendar').addClass('selected');
		return false;
	});
	showEventsList();

	$('.event_list_item').click(function(){
		var event_id = this.id.replace('event_list_item_', '');
		loadEvent(event_id, true)
	})

	$('.arowedItem').click(function(){
		var venue_id = this.id.replace('venue_item_', '');
		loadVenue(venue_id)
	})

	$('#lnk_show_terms').click(function(){
		$('#cont_ticket_form').hide();
		$('#cont_terms_element').show();
		return false;
	})

	$('#lnk_show_ticket_form').click(function(){
		$('#cont_terms_element').hide();
		$('#cont_ticket_form').show();
		return false;
	})

	// forms

	$('#lnk_form_subscribe_submit').click(function(){
		submitSubscribeForm();
		return false;
	})

	$('#lnk_form_ticket_submit').click(function(){
		submitTicketForm();
		return false;
	})
	
	clearForm($('#ticketForm'));

	if ( $('#fld_country').length && $('#fld_state').length )
	{
		$('#fld_country').change(function(){
			loadStates($('#fld_country').val());
			return false;
		})
		loadStates($('#fld_country').val());
	}
});

function ajaxGetDatesWithEvents()
{
	$('#rc_container').block();
    $.ajax({
        'type': 'POST',
		'url': '/ajax/ticketlist',
		'dataType': 'json',
		'cache': false,
		'data': {type: 'dates', show_code: getShowCode(), venue_id: getVenueId(), all_future: true},
        'complete': function(xhr) {
			$('#rc_container').unblock();
		},
        'success': function(json) {
            eventsDays = eval( json['dates'] );

            $("#datepicker").datepicker({
                showButtonPanel: false,
                beforeShowDay: eventsDates,
                onSelect: function(dateText, inst) {
					var eDay = $('.date_' + dateText.replace(/\//g, ''));

					if ( eDay && eDay.hasClass('hasEvent') )
					{
						var class_str = eDay.attr('class');
						var classes = class_str.split(' ');

						var event_id = 0;

						for ( var i = 0; i < classes.length; i++ )
						{
							if ( classes[i].indexOf('event_') == 0 )
							{
								event_id = classes[i].replace('event_', '');
								break;
							}
						}

						if ( event_id )
						{
							loadEvent(event_id, true);
						}
					}
					else
					{
						$('.form_header').hide();
						$('#cont_ticket_form').hide();
						$('.confirmBox').hide();
						clearForm($('#ticketForm'));
						$('#cont_no_tickets_on_day').show();
					}
                }
            });

            $("#datepicker").datepicker('refresh');

			if ( eventsDays.length > 0 )
			{
				$("#datepicker").datepicker('setDate', eventsDays[0][0]);
			}
        }
    });
}

function getDate(date)
{
    var day = (date.getDate() < 10 ? '0' : '') + date.getDate();
    var month = (date.getMonth() < 9 ? '0' : '') + (date.getMonth() + 1);
    var year = date.getFullYear();

    return (month +'/'+ day +'/'+ year);
}

function eventsDates(date)
{
	var dt = getDate(date);
	var cl = dt.replace(/\//g, '');

	for (i = 0; i < eventsDays.length; i++)
	{
		if ( dt == eventsDays[i][0] )
		{
			return [true, 'hasEvent date_' + cl + ' event_' + eventsDays[i][1]];
		}
	}
	return [true, ''];
}

function showEventsList() {
	$('#container_events_calendar').hide();
	$('#dailyCalendar').show();
	updateEventListHeight($('.event_list_item'));
}

function showEventsCalendar() {
	$('#dailyCalendar').hide();
	$('#container_events_calendar').show();
}

function submitTicketForm() {

	var formData = jQuery("#ticketForm").serialize();

	clearErrors();

	$('#rc_container').block();
	$.ajax({
		'type':		'POST',
		'url':		'/ajax' + ((isDisableSMTP)?'?disableSMTP=true':'') ,
		'cache':	false,
		'data':		formData,
		'dataType':	'json',
		'complete': function(xhr) {
			$('#rc_container').unblock();
		},
		'success':	function(data) {
			if ( data.result )
			{
				$('#cont_ticket_form').hide();

				if ( data.message ){
					if( data.is_auto_complete &&  data.is_auto_complete == "1" ){
						$('#cont_reservation_comlete_auto p').html(data.message);
					} else {
						$('#cont_successful_message p').html(data.message);
					}
				}
				if( data.is_auto_complete &&  data.is_auto_complete == "1"){
					$('#cont_reservation_comlete_auto').show();
				} else {
					$('#cont_successful_message').show();
				}

				if ( data.event_id )
				{
					loadEvent(data.event_id, false);
				}
			}
			else
			{
				// too soon
				if ( data.code && data.code == 7 )
				{
					$('#cont_ticket_form').hide();
					clearForm($('#ticketForm'));
					$('#cont_back_soon p').html(data.message);
					$('#cont_back_soon').show();
				}
				// banned
				else if ( data.code && data.code == 9 )
				{
					$('#cont_ticket_form').hide();
					clearForm($('#ticketForm'));
					$('#cont_banned p').html(data.message);
					$('#cont_banned').show();
				}
				// already reserved
				else if ( data.code && data.code == 8 )
				{
					$('#cont_ticket_form').hide();
					clearForm($('#ticketForm'));
					$('#cont_already_reserved p').html(data.message);
					$('#cont_already_reserved').show();
				}
				else if ( data.code && data.code == 10 )
				{
					$('#cont_ticket_form').hide();
					clearForm($('#ticketForm'));
					$('#cont_no_tickets_on_day').show();

					loadEvent(data.event_id, false);
				}
				else if ( data.errors )
				{
					for ( var k in data.errors )
					{
						var field = $('#fld_' + k);
						if (k != 'terms')
						{
							field.after('<span class="form_error_message">' + data.errors[k][0] + '</span>');
						}
						else
						{
							field.parent().append('<span class="form_error_message" style="margin-left:0px;">' + data.errors[k] + '</span>');
						}
						field.parent().addClass('form_error');
						$('.form_note_message', field.parent()).hide();
					}
				}
			}
		}
	});

    return false;
}

function clearForm(form)
{
	$(":text", form).val('');
	//$("select", form).get(0).options.selectedIndex = 0;
	$("select").attr("selectedIndex", 0);
	$("select", form).val('');
	$("textarea", form).text('');
	$(":checkbox", form).attr('checked', '');

	$.each($("select", form), function(i) {
		this.options.selectedIndex = 0;
	});


	loadStates($("#fld_country", form).val());

	clearErrors();
}

function clearErrors()
{
	$('.form_row').removeClass('form_error');
	$('.form_error_message').remove();
	$('.form_note_message').show();
}

function submitSubscribeForm() {
	$('#rc_container').block();
    $.ajax({
		'type':		'POST',
		'url':		'/ajax',
		'dataType':	'json',
		'cache':	false,
		'data':		jQuery("#subscribeForm").serialize(),
        'complete': function(xhr) {
			$('#rc_container').unblock();
		},
		'success':	function(json) {

			if ( json['status'] == 'failure' )
			{
				var $errors = '';
				jQuery.each(json['errors'], function(i, val) {
					$errors += val+'<br>';
				});
				$("#subscriptionErrors").html($errors);
				$('#cont_semail').addClass('form_error');
			}
			else
			{
				if (json.title)
				{
					$('#subscribe_title').html(json.title)
				}
				if (json.message)
				{
					$('#subscribe_message').html(json.message)
				}
				$('#fld_semail').val('');
				$("#subscriptionErrors").html('');
				$('#cont_semail').removeClass('form_error');
				$('#subscribe').hide();
			}
		}
	});
    return false;
}

function loadVenue(id)
{
	var unblockUi = true;

	$('#rc_container').block();
	$.ajax({
		type:		"POST",
		url:		"/site/getvenue",
		data:		{venue_id: id, show_code: getShowCode()},
		dataType:	'json',
        complete: function(xhr) {
			if (unblockUi)
			{
				$('#rc_container').unblock();
			}
		},
		success: function(data){
			if (data.error)
			{
				//TODO no tickets
				//alert('Error: ' + data.error)
			}
			else
			{
				if (data.map_url)
				{
					var mapHtml = '<p class="cont_map_link"><img width="18" height="18" align="absmiddle" src="/images/globe1.gif">&nbsp;<a class="rc_blue1" target="_blank" href="' + data.map_url + '">Click here</a> to view a map and get directions.</p>';
				}
				else
				{
					var mapHtml = '';
				}
				
				$('#cont_venue_info').html(data.info);
				$('#cont_venue_message').html(data.message + mapHtml);
				$('#cont_venue_terms').html(data.terms);

				var html = '';

				if ( data.events.length )
				{
					var activeEventId = null;

					for ( var k in data.events )
					{
						if ( !activeEventId )
						{
							activeEventId = data.events[k].id;
						}
						html += '<div id="event_list_item_' + data.events[k].id + '" class="carItem event_list_item">'
							+ '<div class="carEvent"><span>' + data.events[k].weekday + '</span><br />' + data.events[k].date + '</div>'
							+ '<div id="event_list_item_' + data.events[k].id + '_available" class="eventsCount">' + data.events[k].available_tickets + '</div>'
						+ '</div>';
					}
					
					if ( activeEventId )
					{
						unblockUi = false;
						loadEvent(activeEventId, true);
					}
				}
				else
				{
					//TODO
				}
				$('#dailyCalendar .items').html(html);

				var oEventListItem = $('.event_list_item');

				oEventListItem.click(function(){
					var event_id = this.id.replace('event_list_item_', '');
					loadEvent(event_id, true)
				})

				updateEventListHeight(oEventListItem);

				$('.arowedItem').removeClass('selectedItem');
				$('#venue_item_' + id).addClass('selectedItem');

				ajaxGetDatesWithEvents();
			}
		}
	});
}

function updateEventListHeight(oEventListItem)
{
	if ( oEventListItem.length < 8 )
	{
	    var height = oEventListItem.length * 35; // (parseInt($('.carItem').height()) + 1)
		$('.scrollable').height(height);
	};
}

function loadEvent(id, show_form)
{
	if (show_form)
	{
		$('.confirmBox').hide();
	}
	$('.event_list_item').removeClass('selectedDay');

	clearForm($('#ticketForm'));

	$('#rc_container').block();
	$.ajax({
		type:		"POST",
		url:		"/site/getevent",
		data:		{event_id: id},
		dataType:	'json',
        complete: function(xhr) {
			$('#rc_container').unblock();
		},
		success: function(data){

			if (data.error)
			{
				//TODO no tickets
				//alert('Error: ' + data.error)
			}
			else
			{
				var dateHtml = data.weekday + '<br /><span class="current_date">' + data.date + '</span>';
				$('#cont_active_event_date').html(dateHtml);

				if ( data.available_tickets && parseInt(data.available_tickets) > 0 )
				{
					$('#event_list_item_' + data.id).addClass('selectedDay');
					$('#fld_cid').val(data.id);
					$('#event_list_item_' + data.id + '_available').html(data.available_tickets);
					$('#cont_max_tickets_per_request').html('(max ' + data.XTK_MAX_TICKETS_PER_REQUEST + ')');

					if (data.message)
					{
						$('#cont_event_message').html(data.message);
						$('#cont_event_message').show();
					}
					else
					{
						$('#cont_event_message').html('');
						$('#cont_event_message').hide();
					}

					var ticketsHtml = '<span>' + data.available_tickets + '</span> '
						+ (data.available_tickets > 1 ? data.opt_ticket_title_plural : data.opt_ticket_title_singular ) + ' remaining';
					$('#cont_active_event_ticket_available').html(ticketsHtml);

					$('#event_list_item_' + data.id + '_available').html(data.available_tickets);

					var fldTicketsNumber = $('#fld_tickets_number').html('');

					var max = data.available_tickets > data.XTK_MAX_TICKETS_PER_REQUEST ? data.XTK_MAX_TICKETS_PER_REQUEST : data.available_tickets;

					for ( var i = 1; i <= max; i++ )
					{
						title = i + ' ' + (i > 1 ? data.opt_ticket_title_plural : data.opt_ticket_title_singular);
						fldTicketsNumber.append($("<option></option>").attr("value",i).text(title));
					}

					if ( show_form )
					{
						$('.form_header').show();
						$('#cont_ticket_form').show();
					}
				}
				else
				{
					var ticketsHtml = 'No tickets available';
					$('#cont_active_event_ticket_available').html(ticketsHtml);
					$('#event_list_item_' + data.id).remove();
					updateEventListHeight($('.event_list_item'));

					if ($('.event_list_item').length == 0)
					{
						$('.items').append('<div class="carNoItems"><div class="carEvent">No events available</div></div>');
					}

					if ( show_form )
					{
						$('#cont_ticket_form').hide();
						$('.confirmBox').hide();
						$('#cont_no_tickets_on_day').show();
					}
				}
 			}
		}
	});
	return false;
}

function getShowCode()
{
	var ind = location.href.lastIndexOf('/');
	return location.href.substr(ind + 1);
}

function getVenueId()
{
	var vid = 0;
	$('.arowedItem').each(function() {
		if ( $(this).hasClass('selectedItem') )
		{
			vid = this.id.replace('venue_item_', '');
		}
	})
	return vid;
}

function loadStates(country_id)
{
	$('#rc_container').block();
	
	$.ajax({
		type:		"POST",
		url:		"/ajax/getstates",
		data:		{country_id: country_id},
		dataType:	'json',
        complete: function(xhr) {
			$('#rc_container').unblock();
		},
		error: function(data){
			$('#cont_state').hide();
		},
		success: function(data){

			if (!data.states || data.states.length == 0)
			{
				$('#cont_state').hide();
				$('#fld_state').attr('disabled', 'disabled');
			}
			else
			{
				var currentStateId = $('#fld_current_state').val();

				var html = '';

				for (var state_id in data.states)
				{
					if (currentStateId != state_id)
					{
						html += '<option value="' + state_id + '">' + data.states[state_id] + '</option>';
					}
					else
					{
						html += '<option value="' + state_id + '" selected="selected">' + data.states[state_id] + '</option>';
					}
				}

				$('#fld_state').attr('disabled', '');
				$('#fld_state').html(html);
				$('#cont_state').show();
			}
		}
	});
}