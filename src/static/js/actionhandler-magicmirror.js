function getWeather(location, date) {

    if (date) {
        numDaysUntil = parseInt((moment(date) - moment()) / (3600*24*1000)) + 1
    }
    else {
        numDaysUntil = 0
    }

    if (numDaysUntil > 4 || numDaysUntil < 0) {
        console.log('No weather available for that date')
        return
    }

    $.simpleWeather({
      location: location,
      woeid: '',
      unit: 'c',
      success: function(weather) {
        forecast = weather.forecast[numDaysUntil]

        html = '<div id="weather"><h2><i class="icon-'+forecast.code+'"></i> '+forecast.high+'&deg;'+weather.units.temp+'</h2>';
        html += '<ul><li>'+weather.city+', '+weather.region+'</li>';
        html += '<li class="currently">'+weather.currently+'</li>';

        if (numDaysUntil == 0) {
            html += '<li>'+weather.wind.direction+' '+weather.wind.speed+' '+weather.units.speed+'</li></ul></div>';
        }

        addNotification(html, 'warning', 12000);
      },
      error: function(error) {
        console.log(error)
      }
    });
}


function processAction(result) {
    action_name = result['action'];

    switch(action_name) {
        case 'get-weather':
            getWeather(result.contexts[0]['parameters']['geo-city'], null);
            break;
        default:
            break;
    }
}