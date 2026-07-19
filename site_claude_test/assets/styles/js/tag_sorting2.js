// JavaScript Document

function sortAll() {
    $(".sort-button").removeClass("btn-xs-active");
    $(".sort-all").addClass("btn-xs-active");
    $(".all").removeClass("hidden");
}

function tagSorting(tag) {
    sortDivs(tag);
    hideDate(tag);
    // No need to call slide() as CSS transitions handle the animation
}

function hideDate(tag) {
    var hideDate = true;

    $('.table-links').each(function() {
        var $sortableDivs = $(this).find('.sortable-div');
        hideDate = true;

        $sortableDivs.each(function() {
            if (!$(this).hasClass("hidden")) {
                hideDate = false;
            }
        });

        var $yearElement = $(this).parents('tr').find('#year');
        $yearElement.removeClass("hidden");

        if (hideDate) {
            $yearElement.addClass("hidden");
        } else {
            $yearElement.removeClass("hidden");
        }
    });
}

function sortDivs(tag) {
    if ($("#sort-button-" + tag).hasClass("btn-xs-active")) {
        // Do nothing if the button is already active
    } else {
        $(".sort-button").removeClass("btn-xs-active");
        $(".sort-" + tag).addClass("btn-xs-active");

        // Toggle 'hidden' class based on the selected tag
        $("div.sortable-div, li.sortable-div, ul.sortable-div").each(function() {
            if ($(this).hasClass(tag)) {
                $(this).removeClass("hidden");
            } else {
                $(this).addClass("hidden");
            }
        });
    }
}