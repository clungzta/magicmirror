var geolocation = {'lat' : null, 'lng' : null, 'accuracy' : null}

var tryAPIGeolocation = function() {
    jQuery.post( "https://www.googleapis.com/geolocation/v1/geolocate?key=AIzaSyDCa1LUe1vOczX1hO_iGYgyo8p_jYuGOPU", function(result) {
        console.log('API geolocation success')    
        geolocation['lat'] = result.location.lat
        geolocation['lng'] = result.location.lng
        geolocation['accuracy'] = result.accuracy
        console.log(geolocation);
        geocodeLatLng(geolocation);    
    })
    .fail(function(err) {
        console.log("API Geolocation error! \n\n"+err);
        magicMirrorInit(geolocation=null);        
    });
};

var browserGeolocationSuccess = function(position) {
    console.log('Browser geolocation success')
    geolocation['lat'] = position.coords.latitude
    geolocation['lng'] = position.coords.longitude
    geolocation['accuracy'] = position.coords.accuracy
    console.log(geolocation);
    geocodeLatLng(geolocation);
};

var browserGeolocationFail = function(err) {
    console.log('Browser geolocation failed, trying API geolocation...\n\n' + err)
    tryAPIGeolocation();
};

var tryGeolocation = function() {
  if (navigator.geolocation) {
    req_options = {maximumAge: 50000, timeout: 20000, enableHighAccuracy: true}
    navigator.geolocation.getCurrentPosition(browserGeolocationSuccess, browserGeolocationFail, req_options);
  }
};

function filterGeocodeData(result, filter_name_str) {
    var temp = result.address_components.filter(function(addr){
        return (addr.types[0]==filter_name_str);
    });

    return temp[0].long_name
}

function geocodeLatLng(geolocation) {
    var geocoder = new google.maps.Geocoder;
    
    geocoder.geocode({'location': geolocation}, function(results, status) {
        if (status !== 'OK') {
            console.log('Geocoder failed due to: ' + status);
            return;
        }
        if (results[0]) {
            geodata = {}
            
            geodata['formatted_address'] = results[0].formatted_address
            geodata['city'] = filterGeocodeData(results[0], 'locality')
            geodata['state'] = filterGeocodeData(results[0], 'administrative_area_level_1')
            geodata['country'] = filterGeocodeData(results[0], 'country')

            // Initialize the magic mirror with the users current location
            magicMirrorInit(geodata)

        }
        else {
            console.log('No geocoder results found');
        }
    });
}
// tryGeolocation();
// tryAPIGeolocation();