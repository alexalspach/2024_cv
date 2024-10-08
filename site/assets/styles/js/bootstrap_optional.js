<!-- Bootstrap Tooltip -->  
	$(function(){
	   $('a').tooltip();
	});
<!-- Bootstrap Carousel -->  

$(function(){
	$('#carousel-example-generic').carousel({ interval: 4000, cycle: true });
	$('#carousel-example-generic').carousel('cycle');
});

function startSlideShow() {
	$('#carousel-example-generic').carousel({ interval: 4000, cycle: true });
	$('#carousel-example-generic').carousel('cycle');
}
