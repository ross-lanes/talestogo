// Redirect tales.robotrachel.com to apps.robotrachel.com
if (window.location.hostname === 'tales.robotrachel.com') {
  var newUrl = window.location.href.replace('tales.robotrachel.com', 'apps.robotrachel.com');
  window.location.replace(newUrl);
}
