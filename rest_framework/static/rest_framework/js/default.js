prettyPrint();

$('.js-tooltip').tooltip({
    delay: 1000
});

$('a[data-toggle="tab"]:first').on('shown', function (e) {
    $(e.target).parents('.tabbable').addClass('first-tab-active');
});
$('a[data-toggle="tab"]:not(:first)').on('shown', function (e) {
    $(e.target).parents('.tabbable').removeClass('first-tab-active');
});
$('.form-switcher a:first').tab('show');
