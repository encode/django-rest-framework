prettyPrint();

$('.js-tooltip').tooltip({
    delay: 1000
});

$('#patch-form').find('.field-switcher').on('change', function() {
    var $this = $(this);
    $('#patch-form').find('#'+$this.attr('data-field-id'))
                    .prop('disabled', !$this.prop('checked'));
});

$('#form-method-switcher a:first').tab('show');
