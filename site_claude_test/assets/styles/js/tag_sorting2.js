// JavaScript Document

function sortAll() {
    $(".sort-button").removeClass("btn-xs-active");
    $(".sort-all").addClass("btn-xs-active");
    $(".all").removeClass("hidden");
}

// Titles for the timeline heading that need special capitalization (acronyms/brand names).
// Any tag NOT listed here falls back to its button's own label, title-cased — so new tags work
// automatically; add an entry only when the auto-capitalized label isn't what you want.
var TAG_TITLE_OVERRIDES = {
    all: "Timeline",
    hri: "HRI",
    designmfg: "Design/Mfg",
    hwdev: "H/W Dev",
    swdev: "S/W Dev",
    tri: "Toyota (TRI)",
    hubolab: "HuboLab",
    simlab: "SimLab"
};

function tagTitle(tag) {
    if (TAG_TITLE_OVERRIDES[tag]) return TAG_TITLE_OVERRIDES[tag];
    // Default: take the button's visible label and capitalize the first letter of each word.
    var label = ($(".sort-" + tag + ":first").text() || tag).trim();
    return label.replace(/\b\w/g, function (c) { return c.toUpperCase(); });
}

function tagSorting(tag) {
    sortDivs(tag);
    hideDate(tag);
    // TOC title: "Timeline" for the "all" filter, otherwise the tag's proper name.
    $("#timeline-heading").text(tagTitle(tag));
    // A full year skeleton is pointless for a single hit, so when a filter yields exactly one result
    // collapse the TOC to just its one populated row (year + title). CSS (.toc-single) hides the rest.
    var visibleEntries = $(".toc-table.sortable-div .table-links .sortable-div").not(".hidden").length;
    $(".toc-table.sortable-div").toggleClass("toc-single", visibleEntries === 1);
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