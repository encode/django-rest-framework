function getSearchTerm() {
    var sPageURL = window.location.search.substring(1);
    var sURLVariables = sPageURL.split('&');
    for (var i = 0; i < sURLVariables.length; i++) {
        var sParameterName = sURLVariables[i].split('=');
        if (sParameterName[0] == 'q') {
            return sParameterName[1];
        }
    }
}

function applyTopPadding() {
    // Update various absolute positions to match where the main container
    // starts. This is necessary for handling multi-line nav headers, since
    // that pushes the main container down.
    var container = document.querySelector('body > .container');
    var offset = container.offsetTop;

    document.documentElement.style.scrollPaddingTop = offset + 'px';
    document.querySelectorAll('.bs-sidebar.affix').forEach(function(sidebar) {
        sidebar.style.top = offset + 'px';
    });
}

document.addEventListener("DOMContentLoaded", function () {
    var search_term = getSearchTerm();
    var search_modal = new bootstrap.Modal(document.getElementById('mkdocs_search_modal'));
    var keyboard_modal = new bootstrap.Modal(document.getElementById('mkdocs_keyboard_modal'));

    if (search_term) {
        search_modal.show();
    }

    // make sure search input gets autofocus every time modal opens.
    document.getElementById('mkdocs_search_modal').addEventListener('shown.bs.modal', function() {
        document.getElementById('mkdocs-search-query').focus();
    });

    // Close search modal when result is selected
    // The links get added later so listen to parent
    document.getElementById('mkdocs-search-results').addEventListener('click', function(e) {
        if (e.target.tagName === 'A') {
            search_modal.hide();
        }
    });

    // Populate keyboard modal with proper Keys
    document.querySelector('.help.shortcut kbd').innerHTML = keyCodes[shortcuts.help];
    document.querySelector('.prev.shortcut kbd').innerHTML = keyCodes[shortcuts.previous];
    document.querySelector('.next.shortcut kbd').innerHTML = keyCodes[shortcuts.next];
    document.querySelector('.search.shortcut kbd').innerHTML = keyCodes[shortcuts.search];

    // Keyboard navigation
    document.addEventListener("keydown", function(e) {
      if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return true;
      var key = e.which || e.keyCode || window.event && window.event.keyCode;
      var page;
      switch (key) {
          case shortcuts.next:
              page = document.querySelector('.navbar a[rel="next"]:first').getAttribute('href');
              break;
          case shortcuts.previous:
              page = document.querySelector('.navbar a[rel="prev"]:first').getAttribute('href');
              break;
          case shortcuts.search:
              e.preventDefault();
              keyboard_modal.hide();
              search_modal.show();
              document.getElementById('mkdocs-search-query').focus();
              break;
          case shortcuts.help:
              search_modal.hide();
              keyboard_modal.show();
              break;
          default: break;
      }
      if (page) {
          keyboard_modal.hide();
          window.location.href = page;
      }
    });

    document.querySelectorAll('table').forEach(function(table) {
      table.classList.add('table', 'table-striped', 'table-hover');
    });

    function showInnerDropdown(item) {
      var popup = item.nextElementSibling;
      popup.classList.add('show');
      item.classList.add('open');

      // First, close any sibling dropdowns.
      var container = item.parentElement.parentElement;
      container.querySelectorAll('> .dropdown-submenu > a').forEach(function(el) {
          if (el !== item) {
              hideInnerDropdown(el);
          }
      });

      var popupMargin = 10;
      var maxBottom = window.innerHeight - popupMargin;
      var bounds = item.getBoundingClientRect();

      popup.style.left = bounds.right + 'px';
      if (bounds.top + popup.clientHeight > maxBottom &&
          bounds.top > window.innerHeight / 2) {
          popup.style.top = (bounds.bottom - popup.clientHeight) + 'px';
          popup.style.maxHeight = (bounds.bottom - popupMargin) + 'px';
      } else {
          popup.style.top = bounds.top + 'px';
          popup.style.maxHeight = (maxBottom - bounds.top) + 'px';
      }
    }

    function hideInnerDropdown(item) {
        var popup = item.nextElementSibling;
        popup.classList.remove('show');
        item.classList.remove('open');

        popup.scrollTop = 0;
        popup.querySelector('.dropdown-menu').scrollTop = 0;
        popup.querySelector('.dropdown-submenu > a').classList.remove('open');
    }

    document.querySelectorAll('.dropdown-submenu > a').forEach(function(item) {
        item.addEventListener('click', function(e) {
            if (item.nextElementSibling.classList.contains('show')) {
                hideInnerDropdown(item);
            } else {
                showInnerDropdown(item);
            }

            e.stopPropagation();
            e.preventDefault();
        });
    });

    document.querySelectorAll('.dropdown-menu').forEach(function(menu) {
        menu.parentElement.addEventListener('hide.bs.dropdown', function() {
            menu.scrollTop = 0;
            menu.querySelector('.dropdown-submenu > a').classList.remove('open');
            menu.querySelectorAll('.dropdown-menu .dropdown-menu').forEach(function(submenu) {
                submenu.classList.remove('show');
            });
        });
    });

    applyTopPadding();
});

window.addEventListener('resize', applyTopPadding);

var scrollSpy = new bootstrap.ScrollSpy(document.body, {
    target: '.bs-sidebar'
});

/* Prevent disabled links from causing a page reload */
document.querySelectorAll("li.disabled a").forEach(function(item) {
    item.addEventListener("click", function(event) {
        event.preventDefault();
    });
});

// See https://www.cambiaresearch.com/articles/15/javascript-char-codes-key-codes
// We only list common keys below. Obscure keys are omitted and their use is discouraged.
var keyCodes = {
    8: 'backspace',
    9: 'tab',
    13: 'enter',
    16: 'shift',
    17: 'ctrl',
    18: 'alt',
    19: 'pause/break',
    20: 'caps lock',
    27: 'escape',
    32: 'spacebar',
    33: 'page up',
    34: 'page down',
    35: 'end',
    36: 'home',
    37: '&larr;',
    38: '&uarr;',
    39: '&rarr;',
    40: '&darr;',
    45: 'insert',
    46: 'delete',
    48: '0',
    49: '1',
    50: '2',
    51: '3',
    52: '4',
    53: '5',
    54: '6',
    55: '7',
    56: '8',
    57: '9',
    65: 'a',
    66: 'b',
    67: 'c',
    68: 'd',
    69: 'e',
    70: 'f',
    71: 'g',
    72: 'h',
    73: 'i',
    74: 'j',
    75: 'k',
    76: 'l',
    77: 'm',
    78: 'n',
    79: 'o',
    80: 'p',
    81: 'q',
    82: 'r',
    83: 's',
    84: 't',
    85: 'u',
    86: 'v',
    87: 'w',
    88: 'x',
    89: 'y',
    90: 'z',
    91: 'Left Windows Key / Left ⌘',
    92: 'Right Windows Key',
    93: 'Windows Menu / Right ⌘',
    96: 'numpad 0',
    97: 'numpad 1',
    98: 'numpad 2',
    99: 'numpad 3',
    100: 'numpad 4',
    101: 'numpad 5',
    102: 'numpad 6',
    103: 'numpad 7',
    104: 'numpad 8',
    105: 'numpad 9',
    106: 'multiply',
    107: 'add',
    109: 'subtract',
    110: 'decimal point',
    111: 'divide',
    112: 'f1',
    113: 'f2',
    114: 'f3',
    115: 'f4',
    116: 'f5',
    117: 'f6',
    118: 'f7',
    119: 'f8',
    120: 'f9',
    121: 'f10',
    122: 'f11',
    123: 'f12',
    124: 'f13',
    125: 'f14',
    126: 'f15',
    127: 'f16',
    128: 'f17',
    129: 'f18',
    130: 'f19',
    131: 'f20',
    132: 'f21',
    133: 'f22',
    134: 'f23',
    135: 'f24',
    144: 'num lock',
    145: 'scroll lock',
    186: '&semi;',
    187: '&equals;',
    188: '&comma;',
    189: '&hyphen;',
    190: '&period;',
    191: '&quest;',
    192: '&grave;',
    219: '&lsqb;',
    220: '&bsol;',
    221: '&rsqb;',
    222: '&apos;',
};
