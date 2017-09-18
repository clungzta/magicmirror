function magicMirrorInit(geolocation) {
    apiaiInit();
    var context_parameters = { "given-name" : "Alex" }
    
    if (geolocation) {
        context_parameters['location'] = geolocation.formatted_address
        context_parameters['geo-city'] = geolocation.city
        context_parameters['geo-country'] = geolocation.country
    }

    console.log('geolocation')
    console.log(geolocation)

    setContextParameters(apiai_client, 'person-details', context_parameters);
    change_speech_state('waiting_for_activation')
    beginListening(null, true);
}

function getLargestBBOXLabel(detPeople) {
    
    if (jQuery.isEmptyObject(detPeople)) {
        console.log('No people detected in image')
        return null;
    }

    personName = Object.keys(detPeople).reduce(function(a, b){ return obj[a] > obj[b] ? a : b });
    return personName;
}