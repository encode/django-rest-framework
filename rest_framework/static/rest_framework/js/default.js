$(document).ready(function() {
  // JSON highlighting.
  prettyPrint();

  // Bootstrap tooltips.
  document.querySelectorAll('.js-tooltip').forEach(function(el) {
    bootstrap.Tooltip.getOrCreateInstance(el, {
      delay: 1000,
      container: 'body'
    });
  });

  var tabLinks = document.querySelectorAll('a[data-bs-toggle="tab"]');

  tabLinks.forEach(function(link) {
    // Deal with rounded tab styling after tab clicks.
    link.addEventListener('shown.bs.tab', function(e) {
      var tabbable = e.target.closest('.tabbable');
      if (!tabbable) {
        return;
      }
      var isFirst = e.target === tabbable.querySelector('a[data-bs-toggle="tab"]');
      tabbable.classList.toggle('first-tab-active', isFirst);
    });

    link.addEventListener('click', function() {
      document.cookie = "tabstyle=" + this.name + "; path=/";
    });
  });

  // Store tab preference in cookies & display appropriate tab on load.
  var selectedTabName = getCookie('tabstyle');

  if (selectedTabName) {
    selectedTabName = selectedTabName.replace(/[^a-z-]/g, '');
  }

  document.querySelectorAll('.form-switcher').forEach(function(switcher) {
    var selectedTab = null;
    if (selectedTabName) {
      selectedTab = switcher.querySelector('a[name=' + selectedTabName + ']');
    }
    if (!selectedTab) {
      // If no tab selected, display rightmost tab.
      selectedTab = switcher.querySelector('a[data-bs-toggle="tab"]');
    }
    if (selectedTab) {
      bootstrap.Tab.getOrCreateInstance(selectedTab).show();
    }
  });

  $(window).on('load', function() {
    var errorModal = document.getElementById('errorModal');
    if (errorModal) {
      bootstrap.Modal.getOrCreateInstance(errorModal).show();
    }
  });
});
