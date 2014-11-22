$(document).ready(function() {
    // Offset the navbar height
    var topOffset = $("#navbar").innerHeight();

    // Establish section-subsection pairings
    _.each(_.zip($("#content .section"), $("#sidebar .item")), function(pair) {
        var realSection = $(pair[0]).children("h1");
        var navSection = $(pair[1]).children("a");
        realSection.data("other", navSection);
        navSection.data("other", realSection);

        _.each(_.zip($(pair[0]).find("h2"), $(pair[1]).find(".subitem")), function(pair) {
            var realSubsection = $(pair[0]);
            var navSubsection = $(pair[1]).children("a");
            realSubsection.data("other", navSubsection);
            navSubsection.data("other", realSubsection);
        });
    });

    // Helpers
    var scrollToSection = function(itemToScrollTo) {
        var scrollFrom = $(document).scrollTop();
        var scrollTo = itemToScrollTo.offset().top - topOffset;

        $("html, body").animate({
            scrollTop: scrollTo
        }, Math.abs(scrollTo - scrollFrom) / 1.75);
    }

    // Handle a sidenav click
    $(".item a,.subitem a").click(function (e) {
        var anchor = $(e.target)
        scrollToSection(anchor.data("other"));
        return false;
    });

    // Handle scroll events
    var prevNavAnchor = $();
    var prevSection = $();
    var prevSubitemsNav = $();

    var handleSelectors = function(header, direction) {
        isSubsection = header.is("h2");
        section = header.closest(".section");
        navAnchor = header.data("other");

        // Center selector with the associated navigation item (magic number from css)
        var selectorOffset = ($("#section-selector").height() - $("#sidebar").find("a").height()) / 2;

        if (!prevSection.is(section)) {
            // If section changes, show new items
            prevSubitemsNav.hide();
            prevSubitemsNav = section.find("h1").data("other").closest(".item").find(".subitems");
            prevSubitemsNav.show();
        }

        if (!prevNavAnchor.is(navAnchor)) {
            // Highlight the new anchor
            prevNavAnchor.removeClass("active");
            navAnchor.addClass("active");
        }

        $("#subsection-selector").css({top: navAnchor.position().top - selectorOffset});
        $("#section-selector").css({top: section.find("h1").data("other").position().top - selectorOffset});

        prevNavAnchor = navAnchor;
        prevSection = section;
    }

    $("#content").find("h1,h2").waypoint(function(direction) {
        // Scrolling down
        if (direction === "up") {
            return;
        }
        handleSelectors($(this), direction);
    }, { offset: topOffset + 40 });

    $("#content").find("h1,h2").waypoint(function(direction) {
        // Scrolling up
        if (direction === "down") {
            return;
        }
        handleSelectors($(this), direction);
    }, { offset: topOffset - 25 });
});
