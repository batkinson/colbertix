$.mockjax({
  url: "/ajax/ticketlist",
  responseText: {
      "status":"success",
      "dates": [
         ["09\/30\/2014",1481],
         ["10\/02\/2014",1021],
         ["10\/06\/2014",1061],
      ]} 
});
$.mockjax({
  url: "/ajax/getstates",
  response: function(obj) {
      var countryId = obj.data['country_id'];
      var result = {};
      if (countryId == 'US') {
         result = {"states":{"":"Select","AK":"AK","AL":"AL","AR":"AR","AZ":"AZ","CA":"CA","CO":"CO","CT":"CT","DC":"DC","DE":"DE","FL":"FL","GA":"GA","HI":"HI","IA":"IA","ID":"ID","IL":"IL","IN":"IN","KS":"KS","KY":"KY","LA":"LA","MA":"MA","MD":"MD","ME":"ME","MI":"MI","MN":"MN","MO":"MO","MS":"MS","MT":"MT","NC":"NC","ND":"ND","NE":"NE","NH":"NH","NJ":"NJ","NM":"NM","NV":"NV","NY":"NY","OH":"OH","OK":"OK","OR":"OR","PA":"PA","RI":"RI","SC":"SC","SD":"SD","TN":"TN","TX":"TX","UT":"UT","VA":"VA","VT":"VT","WA":"WA","WI":"WI","WV":"WV","WY":"WY","OO":"APO\/FPO"}};
      }
      this.responseText = result;
   }
});

var events = {
      "1471": { 
         "id": "1471",
         "message": "Submit your contact information below to receive your free tickets to The Colbert Report.",
         "weekday": "Tuesday",
         "date": "September 30, 2014",
         "date_datepicker_formatted": "09\/30\/2014", 
         "XTK_START_TIME": "19:30",
         "XTK_TICKET_CUT_OFF": "15:30",
         "XTK_AUDIENCE_CUT_OFF": "18:00",
         "XTK_SPECIAL_EVENT_TICKET_TIME": "6:00pm",
         "XTK_MAX_TICKETS_PER_REQUEST": "4",
         "XTK_MAX_TICKETS": "160",
         "reserved_tickets": "159",
         "available_tickets": 12,
         "opt_ticket_title_singular": "ticket",
         "opt_ticket_title_plural": "tickets" },
      "1473": {
         "id": "1473",
         "message": "Submit your contact information below to receive your free tickets to The Colbert Report.",
         "weekday": "Thursday",
         "date": "October 2, 2014",
         "date_datepicker_formatted": "10\/02\/2014", 
         "XTK_START_TIME": "19:30",
         "XTK_TICKET_CUT_OFF": "15:30",
         "XTK_AUDIENCE_CUT_OFF": "18:00",
         "XTK_SPECIAL_EVENT_TICKET_TIME": "6:00pm",
         "XTK_MAX_TICKETS_PER_REQUEST": "4",
         "XTK_MAX_TICKETS": "160",
         "reserved_tickets": "159",
         "available_tickets": 1,
         "opt_ticket_title_singular": "ticket",
         "opt_ticket_title_plural": "tickets" },
      "1490": { 
         "id": "1490",
         "message": "Submit your contact information below to receive your free tickets to The Colbert Report.",
         "weekday": "Monday",
         "date": "October 6, 2014",
         "date_datepicker_formatted": "10\/12\/2014", 
         "XTK_START_TIME": "19:30",
         "XTK_TICKET_CUT_OFF": "15:30",
         "XTK_AUDIENCE_CUT_OFF": "18:00",
         "XTK_SPECIAL_EVENT_TICKET_TIME": "6:00pm",
         "XTK_MAX_TICKETS_PER_REQUEST": "4",
         "XTK_MAX_TICKETS": "160",
         "reserved_tickets": "159",
         "available_tickets": 12,
         "opt_ticket_title_singular": "ticket",
         "opt_ticket_title_plural": "tickets" }
};

$.mockjax({
  url: "/site/getevent",
  response: function(obj) {
    this.responseText = events[obj.data['event_id']];
  }
});

var postedFormData;

$.mockjax({
  url: '/ajax',
  response: function(obj) {
     var data = obj.data;
     var parsedData = {};
     var items = data.split('&');
     for (var i=0; i<items.length; i++) {
        var keyVal = items[i].split('=');
        var key = keyVal[0];
        var value = decodeURIComponent(keyVal[1].replace(/\+/g, ' '));
        parsedData[key] = value;
     }
     postedFormData = data;
     parsedFormData = parsedData;
  }
});

/**
 * Convenience method for grabbing elements by xpath.
 * Returns a list of elements
 */
function getXpath(expr) {
   var result = new Array()
   var xpr = document.evaluate(expr, document.body, null,
                               XPathResult.ORDERED_NODE_ITERATOR_TYPE, null);
   for (var item = xpr.iterateNext(); item != null; item = xpr.iterateNext()) {
      result.push(item);
   }
   return result;
}

/**
 * For getting the date string for an event by its cid.
 */
function getEventDate(id) {
   var xpath = "//*[parent::*[@id = 'event_list_item_" + id + "']]/text()[position() = 1]";
   return getXpath(xpath)[0].data;
}

/**
 * Used to verify the contents of the ajax submission.
 */
function verifySubmit(data) {
   if (typeof parsedFormData === 'undefined') {
      return false;
   }
   for (key in data) {
      if (key == 'event_date') {
         if (!'cid' in parsedFormData || getEventDate(parsedFormData['cid']) != data[key])
            return false;
      } else if (!key in parsedFormData || parsedFormData[key] != data[key]) {
         return false;
      }
   }
   return true;
}

