// JavaScript Document

function initializeMapDelay(delay) {
	
	var timeoutID = window.setTimeout(initializeMap, delay);
	
	google.maps.event.trigger(map, 'resize');
	map.setZoom( map.getZoom() );
	
}

function initializeMap() {

	// http://software.stadtwerk.org/google_maps_colorizr/#water/labels/FFFFFF/off/landscape/labels/FFFFFF/simplified/water/geometry/FFFFFF/simplified/landscape/geometry/BBBBBB/simplified/road.highway/geometry/888888/on/road/geometry/969696/on/road.highway/labels/999999/on/road/labels/aeaeae/on/////poi/geometry/b7b7b7/on
	
	
  // Create an array of styles.
  google.maps.visualRefresh = true;
  /*var styles = [
    {
      stylers: [
        { hue: "#0088cc" },
        { saturation: -20 }
      ]
    },{
      featureType: "road",
      elementType: "geometry",
      stylers: [
        { lightness: 50 },
        { visibility: "simplified" }
      ]
    },{
      featureType: "road",
      elementType: "labels",
      stylers: [
        { visibility: "off" }
      ]
    }*/
	var styles = [
	{
		featureType: 'water',
		elementType: 'labels',
		stylers: [
			{ hue: '#FFFFFF' },
			{ saturation: -100 },
			{ lightness: 100 },
			{ visibility: 'off' }
		]
	},{
		featureType: 'landscape',
		elementType: 'labels',
		stylers: [
			{ hue: '#FFFFFF' },
			{ saturation: -100 },
			{ lightness: 100 },
			{ visibility: 'simplified' }
		]
	},{
		featureType: 'water',
		elementType: 'geometry',
		stylers: [
			{ hue: '#FFFFFF' },
			{ saturation: -100 },
			{ lightness: 100 },
			{ visibility: 'simplified' }
		]
	},{
		featureType: 'landscape',
		elementType: 'geometry',
		stylers: [
			{ hue: '#BBBBBB' },
			{ saturation: -100 },
			{ lightness: -18 },
			{ visibility: 'simplified' }
		]
	},{
		featureType: 'road.highway',
		elementType: 'geometry',
		stylers: [
			{ hue: '#888888' },
			{ saturation: -100 },
			{ lightness: -17 },
			{ visibility: 'on' }
		]
	},{
		featureType: 'road',
		elementType: 'geometry',
		stylers: [
			{ hue: '#969696' },
			{ saturation: -100 },
			{ lightness: -8 },
			{ visibility: 'on' }
		]
	},{
		featureType: 'road.highway',
		elementType: 'labels',
		stylers: [
			{ hue: '#999999' },
			{ saturation: -100 },
			{ lightness: -6 },
			{ visibility: 'on' }
		]
	},{
		featureType: 'road',
		elementType: 'labels',
		stylers: [
			{ hue: '#aeaeae' },
			{ saturation: -100 },
			{ lightness: 12 },
			{ visibility: 'on' }
		]
	},{
		featureType: 'water',
		elementType: 'all',
		stylers: [

		]
	},{
		featureType: 'poi',
		elementType: 'geometry',
		stylers: [
			{ hue: '#b7b7b7' },
			{ saturation: -100 },
			{ lightness: -8 },
			{ visibility: 'on' }
		]
	}
];


  

  // Create a new StyledMapType object, passing it the array of styles,
  // as well as the name to be displayed on the map type control.
  var styledMap = new google.maps.StyledMapType(styles,
    {name: "Gray"});

  // Create a map object, and include the MapTypeId to add
  // to the map type control.
  var mapOptions = {
    zoom: 2,
    center: new google.maps.LatLng(23,-1.054687),
    mapTypeControlOptions: {
      mapTypeIds: [google.maps.MapTypeId.ROADMAP, 'map_style']
    },
	panControl: false,
    panControlOptions: {
        position: google.maps.ControlPosition.TOP_RIGHT
    },
    zoomControl: true,
    zoomControlOptions: {
        style: google.maps.ZoomControlStyle.SMALL,
        position: google.maps.ControlPosition.LEFT_CENTER
    },
    scaleControl: false,
    scaleControlOptions: {
        position: google.maps.ControlPosition.TOP_LEFT
    },
    streetViewControl: false,
    streetViewControlOptions: {
        position: google.maps.ControlPosition.LEFT_TOP
    }
  };
  var map = new google.maps.Map(document.getElementById('map_canvas2'),
    mapOptions);	
	
	/*
  var overlayKML = new google.maps.KmlLayer({
 	 	url: 'http://maps.google.com/maps/ms?authuser=0&vps=2&hl=en&ie=UTF8&msa=0&output=kml&msid=214538591805489379567.0004e390f8ffde3b93322'},
		{preserveViewport:true}
   );
  ctaLayer.setMap(map,{preserveViewport:true}); */
  
  var kmlLayer = new google.maps.KmlLayer();
  //var url_end = "?nocache=" + (new Date()).valueOf(); //For No KML Caching 
  var kmlUrl = "https://maps.google.com/maps/ms?authuser=0&vps=2&hl=en&ie=UTF8&msa=0&output=kml&msid=214538591805489379567.0004e390f8ffde3b93322";// + url_end;
  var kmlOptions = {
  suppressInfoWindows: false,
  preserveViewport: true,
  map: map
  };
  var kmlLayer = new google.maps.KmlLayer(kmlUrl, kmlOptions);

  //Associate the styled map with the MapTypeId and set it to display.
  map.mapTypes.set('map_style', styledMap);
  map.setMapTypeId('map_style');


}

google.maps.event.addDomListener(window, 'load', initializeMap);