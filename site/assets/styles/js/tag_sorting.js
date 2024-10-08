// JavaScript Document

// Look into sorting in a way that will allow multiple tags to be active at once
// Meaning someone can click humanoids and mobile robots and they will show together
// As all others are off
function sortAll()
{
	$(".sort-button").removeClass("btn-xs-active");
	$(".sort-all").addClass("btn-xs-active");
	$( ".all" ).slideDown( 10 )
	
}

function tagSorting(tag)
{
	
	sortDivs(tag);
	//delay( 800 );
	hideDate(tag);
	
	slide(400);
	//slideAndFade(400);
	//var timeoutID = window.setTimeout(slideUpAndDown, 100);
		
}

function slide(slideDuration) {
	
	$(".slide-up" ).slideUp( slideDuration );
	$(".slide-down" ).slideDown( slideDuration );
	$(".slide-up-tr" ).slideUp( slideDuration );
	$(".slide-down-tr" ).slideDown( slideDuration );
	$(".fade-out" ).fadeOut( slideDuration );
	$(".fade-in" ).fadeIn( slideDuration );
	//var timeoutID = window.setTimeout(slideUpAndDownDates, 500);
	//$(".slide-up-tr" ).slideUp( 400 );
	//$(".slide-down-tr" ).slideDown( 400 )
}

function slideAndFade(slideDuration) {

	//var slideDuration = 400;
	
	$(".slide-down" )
  		.css('opacity', 0)
  		.slideDown(slideDuration)
  		.animate(
    		{ opacity: 1 },
    		{ queue: false, duration: slideDuration }
  	);
	
	$(".slide-up" )
  		.css('opacity', 1)
  		.slideUp(slideDuration)
  		.animate(
    		{ opacity: 0 },
    		{ queue: false, duration: slideDuration }
  	);		
}

/*
function slideUpAndDownDates() {

	$(".slide-up-tr" ).slideUp( 400 );
	$(".slide-down-tr" ).slideDown( 400 )
	
	//$(".slide-up-tr" ).slideUp( 400 );
	//$(".slide-down-tr" ).slideDown( 400 )
	
}
*/


function hideDate(tag)
{
	//alert('after?');
	var hideDate = 1;	
	
	$( '.table-links' ).each(function( index ) {	
	//alert('16');
		$( this ).find('.sortable-div').each(function(){
			//if ($( this ).css('display') == 'none') {
			//if ($( this ).css('overflow') == 'hidden'  || $( this ).css('display') == 'none') {
	
				
			if ( $( this ).hasClass( "slide-up" ) ) {
			}
			else{
			hideDate = 0;
			}
		});
		
		
		//$(this).parents('tr').find('#year').removeClass("slide-up-tr");
		//$(this).parents('tr').find('#year').removeClass("slide-down-tr");
		$(this).parents('tr').find('#year').removeClass("slide-up-tr");
		$(this).parents('tr').find('#year').removeClass("slide-down-tr");
			
		if (hideDate == 1){
			//$(this).parents('tr').find('#year').addClass("slide-up");
			$(this).parents('tr').find('#year').addClass("slide-up-tr");
			
		}
		else{
			//$(this).parents('tr').find('#year').addClass("slide-down");
			$(this).parents('tr').find('#year').addClass("slide-down-tr");
			hideDate = 1;
		}
		
	});	
}


function sortDivs(tag)
{
	var slideTime = 0; //400
	if ( $( "#sort-button-" + tag ).hasClass( "btn-xs-active" ) ) {
		//sortAll();
	}
	else {
		
		$(".sort-button").removeClass("btn-xs-active");
		$(".sort-" + tag ).addClass("btn-xs-active");
		
		// adds or removes class so that all animation can be done at once
		$( "div" ).each(function( index ) {
		//if ( $( this ).hasClass( "humanoid" ) ) {	
			if ( $( this ).hasClass( "sortable-div" ) ) {
				$(this).removeClass("slide-up");
				$(this).removeClass("slide-down");
				
				if ( $( this ).hasClass( tag ) ) {
					$(this).addClass("slide-down");
				}
				else {
					$(this).addClass("slide-up");
				}
			}
			
		});
		
		$( "li" ).each(function( index ) {
		//if ( $( this ).hasClass( "humanoid" ) ) {	
			if ( $( this ).hasClass( "sortable-div" ) ) {
				$(this).removeClass("fade-out");
				$(this).removeClass("fade-in");
				
				if ( $( this ).hasClass( tag ) ) {
					$(this).addClass("fade-in");
				}
				else {
					$(this).addClass("fade-out");
				}
			}
			
		});		
	}
	
}
