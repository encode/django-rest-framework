/**
 * Preserve form's raw input after do POST
 */
function persistPostRawDataForm() {
  var formContainerId = '#post-generic-content-form'
  var $form = $(`${formContainerId} form`)
  var $formInput = $(`${formContainerId} textarea`);
  var localStorageKey = 'rawDataSubmitted'
  var formAction = $form.attr('action')

  $form.submit(function () {
    var data = sessionStorage.getItem(localStorageKey)
    data = data ? JSON.parse(data) : {}
    data[formAction] = $formInput.val()
    sessionStorage.setItem(localStorageKey, JSON.stringify(data))
  });

  if (sessionStorage.getItem(localStorageKey)) {
    var data = JSON.parse(sessionStorage.getItem(localStorageKey))
    $formInput.text(data[formAction])
  };
}