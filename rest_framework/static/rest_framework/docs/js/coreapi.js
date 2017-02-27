(function(f){if(typeof exports==="object"&&typeof module!=="undefined"){module.exports=f()}else if(typeof define==="function"&&define.amd){define([],f)}else{var g;if(typeof window!=="undefined"){g=window}else if(typeof global!=="undefined"){g=global}else if(typeof self!=="undefined"){g=self}else{g=this}g.coreapi = f()}})(function(){var define,module,exports;return (function e(t,n,r){function s(o,u){if(!n[o]){if(!t[o]){var a=typeof require=="function"&&require;if(!u&&a)return a(o,!0);if(i)return i(o,!0);var f=new Error("Cannot find module '"+o+"'");throw f.code="MODULE_NOT_FOUND",f}var l=n[o]={exports:{}};t[o][0].call(l.exports,function(e){var n=t[o][1][e];return s(n?n:e)},l,l.exports,e,t,n,r)}return n[o].exports}var i=typeof require=="function"&&require;for(var o=0;o<r.length;o++)s(r[o]);return s})({1:[function(require,module,exports){
'use strict';

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var document = require('./document');
var codecs = require('./codecs');
var errors = require('./errors');
var transports = require('./transports');
var utils = require('./utils');

function lookupLink(node, keys) {
  var _iteratorNormalCompletion = true;
  var _didIteratorError = false;
  var _iteratorError = undefined;

  try {
    for (var _iterator = keys[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
      var key = _step.value;

      if (node instanceof document.Document) {
        node = node.content[key];
      } else {
        node = node[key];
      }
      if (node === undefined) {
        throw new errors.LinkLookupError('Invalid link lookup: ' + JSON.stringify(keys));
      }
    }
  } catch (err) {
    _didIteratorError = true;
    _iteratorError = err;
  } finally {
    try {
      if (!_iteratorNormalCompletion && _iterator.return) {
        _iterator.return();
      }
    } finally {
      if (_didIteratorError) {
        throw _iteratorError;
      }
    }
  }

  if (!(node instanceof document.Link)) {
    throw new errors.LinkLookupError('Invalid link lookup: ' + JSON.stringify(keys));
  }
  return node;
}

var Client = function () {
  function Client() {
    var options = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};

    _classCallCheck(this, Client);

    var transportOptions = {
      csrf: options.csrf,
      headers: options.headers || {},
      requestCallback: options.requestCallback,
      responseCallback: options.responseCallback
    };

    this.decoders = options.decoders || [new codecs.CoreJSONCodec(), new codecs.JSONCodec(), new codecs.TextCodec()];
    this.transports = options.transports || [new transports.HTTPTransport(transportOptions)];
  }

  _createClass(Client, [{
    key: 'action',
    value: function action(document, keys) {
      var params = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};

      var link = lookupLink(document, keys);
      var transport = utils.determineTransport(this.transports, link.url);
      return transport.action(link, this.decoders, params);
    }
  }, {
    key: 'get',
    value: function get(url) {
      var link = new document.Link(url, 'get');
      var transport = utils.determineTransport(this.transports, url);
      return transport.action(link, this.decoders);
    }
  }]);

  return Client;
}();

module.exports = {
  Client: Client
};

},{"./codecs":3,"./document":6,"./errors":7,"./transports":10,"./utils":11}],2:[function(require,module,exports){
'use strict';

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

var _typeof = typeof Symbol === "function" && typeof Symbol.iterator === "symbol" ? function (obj) { return typeof obj; } : function (obj) { return obj && typeof Symbol === "function" && obj.constructor === Symbol && obj !== Symbol.prototype ? "symbol" : typeof obj; };

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var document = require('../document');
var URL = require('url-parse');

function unescapeKey(key) {
  if (key.match(/__(type|meta)$/)) {
    return key.substring(1);
  }
  return key;
}

function getString(obj, key) {
  var value = obj[key];
  if (typeof value === 'string') {
    return value;
  }
  return '';
}

function getBoolean(obj, key) {
  var value = obj[key];
  if (typeof value === 'boolean') {
    return value;
  }
  return false;
}

function getObject(obj, key) {
  var value = obj[key];
  if ((typeof value === 'undefined' ? 'undefined' : _typeof(value)) === 'object') {
    return value;
  }
  return {};
}

function getArray(obj, key) {
  var value = obj[key];
  if (value instanceof Array) {
    return value;
  }
  return [];
}

function getContent(data, baseUrl) {
  var excluded = ['_type', '_meta'];
  var content = {};
  for (var property in data) {
    if (data.hasOwnProperty(property) && !excluded.includes(property)) {
      var key = unescapeKey(property);
      var value = primitiveToNode(data[property], baseUrl);
      content[key] = value;
    }
  }
  return content;
}

function primitiveToNode(data, baseUrl) {
  var isObject = data instanceof Object && !(data instanceof Array);

  if (isObject && data._type === 'document') {
    // Document
    var meta = getObject(data, '_meta');
    var relativeUrl = getString(meta, 'url');
    var url = relativeUrl ? URL(relativeUrl, baseUrl).toString() : '';
    var title = getString(meta, 'title');
    var description = getString(meta, 'description');
    var content = getContent(data, url);
    return new document.Document(url, title, description, content);
  } else if (isObject && data._type === 'link') {
    // Link
    var _relativeUrl = getString(data, 'url');
    var _url = _relativeUrl ? URL(_relativeUrl, baseUrl).toString() : '';
    var method = getString(data, 'action') || 'get';
    var _title = getString(data, 'title');
    var _description = getString(data, 'description');
    var fieldsData = getArray(data, 'fields');
    var fields = [];
    for (var idx = 0, len = fieldsData.length; idx < len; idx++) {
      var value = fieldsData[idx];
      var name = getString(value, 'name');
      var required = getBoolean(value, 'required');
      var location = getString(value, 'location');
      var fieldDescription = getString(value, 'fieldDescription');
      var field = new document.Field(name, required, location, fieldDescription);
      fields.push(field);
    }
    return new document.Link(_url, method, 'application/json', fields, _title, _description);
  } else if (isObject) {
    // Object
    var _content = {};
    for (var key in data) {
      if (data.hasOwnProperty(key)) {
        _content[key] = primitiveToNode(data[key], baseUrl);
      }
    }
    return _content;
  } else if (data instanceof Array) {
    // Object
    var _content2 = [];
    for (var _idx = 0, _len = data.length; _idx < _len; _idx++) {
      _content2.push(primitiveToNode(data[_idx], baseUrl));
    }
    return _content2;
  }
  // Primitive
  return data;
}

var CoreJSONCodec = function () {
  function CoreJSONCodec() {
    _classCallCheck(this, CoreJSONCodec);

    this.mediaType = 'application/coreapi+json';
  }

  _createClass(CoreJSONCodec, [{
    key: 'decode',
    value: function decode(text) {
      var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

      var data = text;
      if (options.preloaded === undefined || !options.preloaded) {
        data = JSON.parse(text);
      }
      return primitiveToNode(data, options.url);
    }
  }]);

  return CoreJSONCodec;
}();

module.exports = {
  CoreJSONCodec: CoreJSONCodec
};

},{"../document":6,"url-parse":15}],3:[function(require,module,exports){
'use strict';

var corejson = require('./corejson');
var json = require('./json');
var text = require('./text');

module.exports = {
  CoreJSONCodec: corejson.CoreJSONCodec,
  JSONCodec: json.JSONCodec,
  TextCodec: text.TextCodec
};

},{"./corejson":2,"./json":4,"./text":5}],4:[function(require,module,exports){
'use strict';

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var JSONCodec = function () {
  function JSONCodec() {
    _classCallCheck(this, JSONCodec);

    this.mediaType = 'application/json';
  }

  _createClass(JSONCodec, [{
    key: 'decode',
    value: function decode(text) {
      var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

      return JSON.parse(text);
    }
  }]);

  return JSONCodec;
}();

module.exports = {
  JSONCodec: JSONCodec
};

},{}],5:[function(require,module,exports){
'use strict';

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var TextCodec = function () {
  function TextCodec() {
    _classCallCheck(this, TextCodec);

    this.mediaType = 'text/*';
  }

  _createClass(TextCodec, [{
    key: 'decode',
    value: function decode(text) {
      var options = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : {};

      return text;
    }
  }]);

  return TextCodec;
}();

module.exports = {
  TextCodec: TextCodec
};

},{}],6:[function(require,module,exports){
'use strict';

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var Document = function Document() {
  var url = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : '';
  var title = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : '';
  var description = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : '';
  var content = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : {};

  _classCallCheck(this, Document);

  this.url = url;
  this.title = title;
  this.description = description;
  this.content = content;
};

var Link = function Link(url, method) {
  var encoding = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : 'application/json';
  var fields = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : [];
  var title = arguments.length > 4 && arguments[4] !== undefined ? arguments[4] : '';
  var description = arguments.length > 5 && arguments[5] !== undefined ? arguments[5] : '';

  _classCallCheck(this, Link);

  if (url === undefined) {
    throw new Error('url argument is required');
  }

  if (method === undefined) {
    throw new Error('method argument is required');
  }

  this.url = url;
  this.method = method;
  this.encoding = encoding;
  this.fields = fields;
  this.title = title;
  this.description = description;
};

var Field = function Field(name) {
  var required = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : false;
  var location = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : '';
  var description = arguments.length > 3 && arguments[3] !== undefined ? arguments[3] : '';

  _classCallCheck(this, Field);

  if (name === undefined) {
    throw new Error('name argument is required');
  }

  this.name = name;
  this.required = required;
  this.location = location;
  this.description = description;
};

module.exports = {
  Document: Document,
  Link: Link,
  Field: Field
};

},{}],7:[function(require,module,exports){
'use strict';

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

function _possibleConstructorReturn(self, call) { if (!self) { throw new ReferenceError("this hasn't been initialised - super() hasn't been called"); } return call && (typeof call === "object" || typeof call === "function") ? call : self; }

function _inherits(subClass, superClass) { if (typeof superClass !== "function" && superClass !== null) { throw new TypeError("Super expression must either be null or a function, not " + typeof superClass); } subClass.prototype = Object.create(superClass && superClass.prototype, { constructor: { value: subClass, enumerable: false, writable: true, configurable: true } }); if (superClass) Object.setPrototypeOf ? Object.setPrototypeOf(subClass, superClass) : subClass.__proto__ = superClass; }

var ParameterError = function (_Error) {
  _inherits(ParameterError, _Error);

  function ParameterError(message) {
    _classCallCheck(this, ParameterError);

    var _this = _possibleConstructorReturn(this, (ParameterError.__proto__ || Object.getPrototypeOf(ParameterError)).call(this, message));

    _this.message = message;
    _this.name = 'ParameterError';
    return _this;
  }

  return ParameterError;
}(Error);

var LinkLookupError = function (_Error2) {
  _inherits(LinkLookupError, _Error2);

  function LinkLookupError(message) {
    _classCallCheck(this, LinkLookupError);

    var _this2 = _possibleConstructorReturn(this, (LinkLookupError.__proto__ || Object.getPrototypeOf(LinkLookupError)).call(this, message));

    _this2.message = message;
    _this2.name = 'LinkLookupError';
    return _this2;
  }

  return LinkLookupError;
}(Error);

var ErrorMessage = function (_Error3) {
  _inherits(ErrorMessage, _Error3);

  function ErrorMessage(message, content) {
    _classCallCheck(this, ErrorMessage);

    var _this3 = _possibleConstructorReturn(this, (ErrorMessage.__proto__ || Object.getPrototypeOf(ErrorMessage)).call(this, message));

    _this3.message = message;
    _this3.content = content;
    _this3.name = 'ErrorMessage';
    return _this3;
  }

  return ErrorMessage;
}(Error);

module.exports = {
  ParameterError: ParameterError,
  LinkLookupError: LinkLookupError,
  ErrorMessage: ErrorMessage
};

},{}],8:[function(require,module,exports){
'use strict';

var client = require('./client');
var codecs = require('./codecs');
var document = require('./document');
var errors = require('./errors');
var transports = require('./transports');
var utils = require('./utils');

var coreapi = {
  Client: client.Client,
  Document: document.Document,
  Link: document.Link,
  codecs: codecs,
  errors: errors,
  transports: transports,
  utils: utils
};

module.exports = coreapi;

},{"./client":1,"./codecs":3,"./document":6,"./errors":7,"./transports":10,"./utils":11}],9:[function(require,module,exports){
'use strict';

var _createClass = function () { function defineProperties(target, props) { for (var i = 0; i < props.length; i++) { var descriptor = props[i]; descriptor.enumerable = descriptor.enumerable || false; descriptor.configurable = true; if ("value" in descriptor) descriptor.writable = true; Object.defineProperty(target, descriptor.key, descriptor); } } return function (Constructor, protoProps, staticProps) { if (protoProps) defineProperties(Constructor.prototype, protoProps); if (staticProps) defineProperties(Constructor, staticProps); return Constructor; }; }();

function _classCallCheck(instance, Constructor) { if (!(instance instanceof Constructor)) { throw new TypeError("Cannot call a class as a function"); } }

var fetch = require('isomorphic-fetch');
var errors = require('../errors');
var utils = require('../utils');
var URL = require('url-parse');
var urlTemplate = require('url-template');

var parseResponse = function parseResponse(response, decoders) {
  return response.text().then(function (text) {
    var contentType = response.headers.get('Content-Type');
    var decoder = utils.negotiateDecoder(decoders, contentType);
    var options = { url: response.url };
    return decoder.decode(text, options);
  });
};

var HTTPTransport = function () {
  function HTTPTransport() {
    var options = arguments.length > 0 && arguments[0] !== undefined ? arguments[0] : {};

    _classCallCheck(this, HTTPTransport);

    this.schemes = ['http', 'https'];
    this.csrf = options.csrf;
    this.headers = options.headers || {};
    this.fetch = options.fetch || fetch;
    this.FormData = options.FormData || window.FormData;
    this.requestCallback = options.requestCallback;
    this.responseCallback = options.responseCallback;
  }

  _createClass(HTTPTransport, [{
    key: 'buildRequest',
    value: function buildRequest(link, decoders) {
      var params = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};

      var fields = link.fields;
      var method = link.method.toUpperCase();
      var queryParams = {};
      var pathParams = {};
      var formParams = {};
      var fieldNames = [];
      var hasBody = false;

      for (var idx = 0, len = fields.length; idx < len; idx++) {
        var field = fields[idx];

        // Ensure any required fields are included
        if (!params.hasOwnProperty(field.name)) {
          if (field.required) {
            throw new errors.ParameterError('Missing required field: "' + field.name + '"');
          } else {
            continue;
          }
        }

        fieldNames.push(field.name);
        if (field.location === 'query') {
          queryParams[field.name] = params[field.name];
        } else if (field.location === 'path') {
          pathParams[field.name] = params[field.name];
        } else if (field.location === 'form') {
          formParams[field.name] = params[field.name];
          hasBody = true;
        } else if (field.location === 'body') {
          formParams = params[field.name];
          hasBody = true;
        }
      }

      // Check for any parameters that did not have a matching field
      for (var property in params) {
        if (params.hasOwnProperty(property) && !fieldNames.includes(property)) {
          throw new errors.ParameterError('Unknown parameter: "' + property + '"');
        }
      }

      var requestOptions = { method: method, headers: {} };

      Object.assign(requestOptions.headers, this.headers);

      if (hasBody) {
        if (link.encoding === 'application/json') {
          requestOptions.body = JSON.stringify(formParams);
          requestOptions.headers['Content-Type'] = 'application/json';
        } else if (link.encoding === 'multipart/form-data') {
          var form = new this.FormData();

          for (var paramKey in formParams) {
            form.append(paramKey, formParams[paramKey]);
          }
          requestOptions.body = form;
        } else if (link.encoding === 'application/x-www-form-urlencoded') {
          var formBody = [];
          for (var _paramKey in formParams) {
            var encodedKey = encodeURIComponent(_paramKey);
            var encodedValue = encodeURIComponent(formParams[_paramKey]);
            formBody.push(encodedKey + '=' + encodedValue);
          }
          formBody = formBody.join('&');

          requestOptions.body = formBody;
          requestOptions.headers['Content-Type'] = 'application/x-www-form-urlencoded';
        }
      }

      if (this.csrf) {
        requestOptions.credentials = 'same-origin';
        if (!utils.csrfSafeMethod(method)) {
          Object.assign(requestOptions.headers, this.csrf);
        }
      }

      var parsedUrl = urlTemplate.parse(link.url);
      parsedUrl = parsedUrl.expand(pathParams);
      parsedUrl = new URL(parsedUrl);
      parsedUrl.set('query', queryParams);

      return {
        url: parsedUrl.toString(),
        options: requestOptions
      };
    }
  }, {
    key: 'action',
    value: function action(link, decoders) {
      var params = arguments.length > 2 && arguments[2] !== undefined ? arguments[2] : {};

      var responseCallback = this.responseCallback;
      var request = this.buildRequest(link, decoders, params);

      if (this.requestCallback) {
        this.requestCallback(request);
      }

      return this.fetch(request.url, request.options).then(function (response) {
        if (responseCallback) {
          responseCallback(response);
        }

        return parseResponse(response, decoders).then(function (data) {
          if (response.ok) {
            return data;
          } else {
            var title = response.status + ' ' + response.statusText;
            var error = new errors.ErrorMessage(title, data);
            return Promise.reject(error);
          }
        });
      });
    }
  }]);

  return HTTPTransport;
}();

module.exports = {
  HTTPTransport: HTTPTransport
};

},{"../errors":7,"../utils":11,"isomorphic-fetch":12,"url-parse":15,"url-template":17}],10:[function(require,module,exports){
'use strict';

var http = require('./http');

module.exports = {
  HTTPTransport: http.HTTPTransport
};

},{"./http":9}],11:[function(require,module,exports){
'use strict';

var URL = require('url-parse');

var determineTransport = function determineTransport(transports, url) {
  var parsedUrl = new URL(url);
  var scheme = parsedUrl.protocol.replace(':', '');

  var _iteratorNormalCompletion = true;
  var _didIteratorError = false;
  var _iteratorError = undefined;

  try {
    for (var _iterator = transports[Symbol.iterator](), _step; !(_iteratorNormalCompletion = (_step = _iterator.next()).done); _iteratorNormalCompletion = true) {
      var transport = _step.value;

      if (transport.schemes.includes(scheme)) {
        return transport;
      }
    }
  } catch (err) {
    _didIteratorError = true;
    _iteratorError = err;
  } finally {
    try {
      if (!_iteratorNormalCompletion && _iterator.return) {
        _iterator.return();
      }
    } finally {
      if (_didIteratorError) {
        throw _iteratorError;
      }
    }
  }

  throw Error('Unsupported scheme in URL: ' + url);
};

var negotiateDecoder = function negotiateDecoder(decoders, contentType) {
  if (contentType === undefined) {
    return decoders[0];
  }

  var fullType = contentType.toLowerCase().split(';')[0].trim();
  var mainType = fullType.split('/')[0] + '/*';
  var wildcardType = '*/*';
  var acceptableTypes = [fullType, mainType, wildcardType];

  var _iteratorNormalCompletion2 = true;
  var _didIteratorError2 = false;
  var _iteratorError2 = undefined;

  try {
    for (var _iterator2 = decoders[Symbol.iterator](), _step2; !(_iteratorNormalCompletion2 = (_step2 = _iterator2.next()).done); _iteratorNormalCompletion2 = true) {
      var decoder = _step2.value;

      if (acceptableTypes.includes(decoder.mediaType)) {
        return decoder;
      }
    }
  } catch (err) {
    _didIteratorError2 = true;
    _iteratorError2 = err;
  } finally {
    try {
      if (!_iteratorNormalCompletion2 && _iterator2.return) {
        _iterator2.return();
      }
    } finally {
      if (_didIteratorError2) {
        throw _iteratorError2;
      }
    }
  }

  throw Error('Unsupported media in Content-Type header: ' + contentType);
};

var csrfSafeMethod = function csrfSafeMethod(method) {
  // these HTTP methods do not require CSRF protection
  return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method)
  );
};

module.exports = {
  determineTransport: determineTransport,
  negotiateDecoder: negotiateDecoder,
  csrfSafeMethod: csrfSafeMethod
};

},{"url-parse":15}],12:[function(require,module,exports){
// the whatwg-fetch polyfill installs the fetch() function
// on the global object (window or self)
//
// Return that as the export for use in Webpack, Browserify etc.
require('whatwg-fetch');
module.exports = self.fetch.bind(self);

},{"whatwg-fetch":18}],13:[function(require,module,exports){
'use strict';

var has = Object.prototype.hasOwnProperty;

/**
 * Simple query string parser.
 *
 * @param {String} query The query string that needs to be parsed.
 * @returns {Object}
 * @api public
 */
function querystring(query) {
  var parser = /([^=?&]+)=?([^&]*)/g
    , result = {}
    , part;

  //
  // Little nifty parsing hack, leverage the fact that RegExp.exec increments
  // the lastIndex property so we can continue executing this loop until we've
  // parsed all results.
  //
  for (;
    part = parser.exec(query);
    result[decodeURIComponent(part[1])] = decodeURIComponent(part[2])
  );

  return result;
}

/**
 * Transform a query string to an object.
 *
 * @param {Object} obj Object that should be transformed.
 * @param {String} prefix Optional prefix.
 * @returns {String}
 * @api public
 */
function querystringify(obj, prefix) {
  prefix = prefix || '';

  var pairs = [];

  //
  // Optionally prefix with a '?' if needed
  //
  if ('string' !== typeof prefix) prefix = '?';

  for (var key in obj) {
    if (has.call(obj, key)) {
      pairs.push(encodeURIComponent(key) +'='+ encodeURIComponent(obj[key]));
    }
  }

  return pairs.length ? prefix + pairs.join('&') : '';
}

//
// Expose the module.
//
exports.stringify = querystringify;
exports.parse = querystring;

},{}],14:[function(require,module,exports){
'use strict';

/**
 * Check if we're required to add a port number.
 *
 * @see https://url.spec.whatwg.org/#default-port
 * @param {Number|String} port Port number we need to check
 * @param {String} protocol Protocol we need to check against.
 * @returns {Boolean} Is it a default port for the given protocol
 * @api private
 */
module.exports = function required(port, protocol) {
  protocol = protocol.split(':')[0];
  port = +port;

  if (!port) return false;

  switch (protocol) {
    case 'http':
    case 'ws':
    return port !== 80;

    case 'https':
    case 'wss':
    return port !== 443;

    case 'ftp':
    return port !== 21;

    case 'gopher':
    return port !== 70;

    case 'file':
    return false;
  }

  return port !== 0;
};

},{}],15:[function(require,module,exports){
'use strict';

var required = require('requires-port')
  , lolcation = require('./lolcation')
  , qs = require('querystringify')
  , protocolre = /^([a-z][a-z0-9.+-]*:)?(\/\/)?([\S\s]*)/i;

/**
 * These are the parse rules for the URL parser, it informs the parser
 * about:
 *
 * 0. The char it Needs to parse, if it's a string it should be done using
 *    indexOf, RegExp using exec and NaN means set as current value.
 * 1. The property we should set when parsing this value.
 * 2. Indication if it's backwards or forward parsing, when set as number it's
 *    the value of extra chars that should be split off.
 * 3. Inherit from location if non existing in the parser.
 * 4. `toLowerCase` the resulting value.
 */
var rules = [
  ['#', 'hash'],                        // Extract from the back.
  ['?', 'query'],                       // Extract from the back.
  ['/', 'pathname'],                    // Extract from the back.
  ['@', 'auth', 1],                     // Extract from the front.
  [NaN, 'host', undefined, 1, 1],       // Set left over value.
  [/:(\d+)$/, 'port', undefined, 1],    // RegExp the back.
  [NaN, 'hostname', undefined, 1, 1]    // Set left over.
];

/**
 * @typedef ProtocolExtract
 * @type Object
 * @property {String} protocol Protocol matched in the URL, in lowercase.
 * @property {Boolean} slashes `true` if protocol is followed by "//", else `false`.
 * @property {String} rest Rest of the URL that is not part of the protocol.
 */

/**
 * Extract protocol information from a URL with/without double slash ("//").
 *
 * @param {String} address URL we want to extract from.
 * @return {ProtocolExtract} Extracted information.
 * @api private
 */
function extractProtocol(address) {
  var match = protocolre.exec(address);

  return {
    protocol: match[1] ? match[1].toLowerCase() : '',
    slashes: !!match[2],
    rest: match[3]
  };
}

/**
 * Resolve a relative URL pathname against a base URL pathname.
 *
 * @param {String} relative Pathname of the relative URL.
 * @param {String} base Pathname of the base URL.
 * @return {String} Resolved pathname.
 * @api private
 */
function resolve(relative, base) {
  var path = (base || '/').split('/').slice(0, -1).concat(relative.split('/'))
    , i = path.length
    , last = path[i - 1]
    , unshift = false
    , up = 0;

  while (i--) {
    if (path[i] === '.') {
      path.splice(i, 1);
    } else if (path[i] === '..') {
      path.splice(i, 1);
      up++;
    } else if (up) {
      if (i === 0) unshift = true;
      path.splice(i, 1);
      up--;
    }
  }

  if (unshift) path.unshift('');
  if (last === '.' || last === '..') path.push('');

  return path.join('/');
}

/**
 * The actual URL instance. Instead of returning an object we've opted-in to
 * create an actual constructor as it's much more memory efficient and
 * faster and it pleases my OCD.
 *
 * @constructor
 * @param {String} address URL we want to parse.
 * @param {Object|String} location Location defaults for relative paths.
 * @param {Boolean|Function} parser Parser for the query string.
 * @api public
 */
function URL(address, location, parser) {
  if (!(this instanceof URL)) {
    return new URL(address, location, parser);
  }

  var relative, extracted, parse, instruction, index, key
    , instructions = rules.slice()
    , type = typeof location
    , url = this
    , i = 0;

  //
  // The following if statements allows this module two have compatibility with
  // 2 different API:
  //
  // 1. Node.js's `url.parse` api which accepts a URL, boolean as arguments
  //    where the boolean indicates that the query string should also be parsed.
  //
  // 2. The `URL` interface of the browser which accepts a URL, object as
  //    arguments. The supplied object will be used as default values / fall-back
  //    for relative paths.
  //
  if ('object' !== type && 'string' !== type) {
    parser = location;
    location = null;
  }

  if (parser && 'function' !== typeof parser) parser = qs.parse;

  location = lolcation(location);

  //
  // Extract protocol information before running the instructions.
  //
  extracted = extractProtocol(address || '');
  relative = !extracted.protocol && !extracted.slashes;
  url.slashes = extracted.slashes || relative && location.slashes;
  url.protocol = extracted.protocol || location.protocol || '';
  address = extracted.rest;

  //
  // When the authority component is absent the URL starts with a path
  // component.
  //
  if (!extracted.slashes) instructions[2] = [/(.*)/, 'pathname'];

  for (; i < instructions.length; i++) {
    instruction = instructions[i];
    parse = instruction[0];
    key = instruction[1];

    if (parse !== parse) {
      url[key] = address;
    } else if ('string' === typeof parse) {
      if (~(index = address.indexOf(parse))) {
        if ('number' === typeof instruction[2]) {
          url[key] = address.slice(0, index);
          address = address.slice(index + instruction[2]);
        } else {
          url[key] = address.slice(index);
          address = address.slice(0, index);
        }
      }
    } else if ((index = parse.exec(address))) {
      url[key] = index[1];
      address = address.slice(0, index.index);
    }

    url[key] = url[key] || (
      relative && instruction[3] ? location[key] || '' : ''
    );

    //
    // Hostname, host and protocol should be lowercased so they can be used to
    // create a proper `origin`.
    //
    if (instruction[4]) url[key] = url[key].toLowerCase();
  }

  //
  // Also parse the supplied query string in to an object. If we're supplied
  // with a custom parser as function use that instead of the default build-in
  // parser.
  //
  if (parser) url.query = parser(url.query);

  //
  // If the URL is relative, resolve the pathname against the base URL.
  //
  if (
      relative
    && location.slashes
    && url.pathname.charAt(0) !== '/'
    && (url.pathname !== '' || location.pathname !== '')
  ) {
    url.pathname = resolve(url.pathname, location.pathname);
  }

  //
  // We should not add port numbers if they are already the default port number
  // for a given protocol. As the host also contains the port number we're going
  // override it with the hostname which contains no port number.
  //
  if (!required(url.port, url.protocol)) {
    url.host = url.hostname;
    url.port = '';
  }

  //
  // Parse down the `auth` for the username and password.
  //
  url.username = url.password = '';
  if (url.auth) {
    instruction = url.auth.split(':');
    url.username = instruction[0] || '';
    url.password = instruction[1] || '';
  }

  url.origin = url.protocol && url.host && url.protocol !== 'file:'
    ? url.protocol +'//'+ url.host
    : 'null';

  //
  // The href is just the compiled result.
  //
  url.href = url.toString();
}

/**
 * This is convenience method for changing properties in the URL instance to
 * insure that they all propagate correctly.
 *
 * @param {String} part          Property we need to adjust.
 * @param {Mixed} value          The newly assigned value.
 * @param {Boolean|Function} fn  When setting the query, it will be the function
 *                               used to parse the query.
 *                               When setting the protocol, double slash will be
 *                               removed from the final url if it is true.
 * @returns {URL}
 * @api public
 */
function set(part, value, fn) {
  var url = this;

  switch (part) {
    case 'query':
      if ('string' === typeof value && value.length) {
        value = (fn || qs.parse)(value);
      }

      url[part] = value;
      break;

    case 'port':
      url[part] = value;

      if (!required(value, url.protocol)) {
        url.host = url.hostname;
        url[part] = '';
      } else if (value) {
        url.host = url.hostname +':'+ value;
      }

      break;

    case 'hostname':
      url[part] = value;

      if (url.port) value += ':'+ url.port;
      url.host = value;
      break;

    case 'host':
      url[part] = value;

      if (/:\d+$/.test(value)) {
        value = value.split(':');
        url.port = value.pop();
        url.hostname = value.join(':');
      } else {
        url.hostname = value;
        url.port = '';
      }

      break;

    case 'protocol':
      url.protocol = value.toLowerCase();
      url.slashes = !fn;
      break;

    case 'pathname':
      url.pathname = value.length && value.charAt(0) !== '/' ? '/' + value : value;

      break;

    default:
      url[part] = value;
  }

  for (var i = 0; i < rules.length; i++) {
    var ins = rules[i];

    if (ins[4]) url[ins[1]] = url[ins[1]].toLowerCase();
  }

  url.origin = url.protocol && url.host && url.protocol !== 'file:'
    ? url.protocol +'//'+ url.host
    : 'null';

  url.href = url.toString();

  return url;
};

/**
 * Transform the properties back in to a valid and full URL string.
 *
 * @param {Function} stringify Optional query stringify function.
 * @returns {String}
 * @api public
 */
function toString(stringify) {
  if (!stringify || 'function' !== typeof stringify) stringify = qs.stringify;

  var query
    , url = this
    , protocol = url.protocol;

  if (protocol && protocol.charAt(protocol.length - 1) !== ':') protocol += ':';

  var result = protocol + (url.slashes ? '//' : '');

  if (url.username) {
    result += url.username;
    if (url.password) result += ':'+ url.password;
    result += '@';
  }

  result += url.host + url.pathname;

  query = 'object' === typeof url.query ? stringify(url.query) : url.query;
  if (query) result += '?' !== query.charAt(0) ? '?'+ query : query;

  if (url.hash) result += url.hash;

  return result;
}

URL.prototype = { set: set, toString: toString };

//
// Expose the URL parser and some additional properties that might be useful for
// others or testing.
//
URL.extractProtocol = extractProtocol;
URL.location = lolcation;
URL.qs = qs;

module.exports = URL;

},{"./lolcation":16,"querystringify":13,"requires-port":14}],16:[function(require,module,exports){
(function (global){
'use strict';

var slashes = /^[A-Za-z][A-Za-z0-9+-.]*:\/\//;

/**
 * These properties should not be copied or inherited from. This is only needed
 * for all non blob URL's as a blob URL does not include a hash, only the
 * origin.
 *
 * @type {Object}
 * @private
 */
var ignore = { hash: 1, query: 1 }
  , URL;

/**
 * The location object differs when your code is loaded through a normal page,
 * Worker or through a worker using a blob. And with the blobble begins the
 * trouble as the location object will contain the URL of the blob, not the
 * location of the page where our code is loaded in. The actual origin is
 * encoded in the `pathname` so we can thankfully generate a good "default"
 * location from it so we can generate proper relative URL's again.
 *
 * @param {Object|String} loc Optional default location object.
 * @returns {Object} lolcation object.
 * @api public
 */
module.exports = function lolcation(loc) {
  loc = loc || global.location || {};
  URL = URL || require('./');

  var finaldestination = {}
    , type = typeof loc
    , key;

  if ('blob:' === loc.protocol) {
    finaldestination = new URL(unescape(loc.pathname), {});
  } else if ('string' === type) {
    finaldestination = new URL(loc, {});
    for (key in ignore) delete finaldestination[key];
  } else if ('object' === type) {
    for (key in loc) {
      if (key in ignore) continue;
      finaldestination[key] = loc[key];
    }

    if (finaldestination.slashes === undefined) {
      finaldestination.slashes = slashes.test(loc.href);
    }
  }

  return finaldestination;
};

}).call(this,typeof global !== "undefined" ? global : typeof self !== "undefined" ? self : typeof window !== "undefined" ? window : {})

},{"./":15}],17:[function(require,module,exports){
(function (root, factory) {
    if (typeof exports === 'object') {
        module.exports = factory();
    } else if (typeof define === 'function' && define.amd) {
        define([], factory);
    } else {
        root.urltemplate = factory();
    }
}(this, function () {
  /**
   * @constructor
   */
  function UrlTemplate() {
  }

  /**
   * @private
   * @param {string} str
   * @return {string}
   */
  UrlTemplate.prototype.encodeReserved = function (str) {
    return str.split(/(%[0-9A-Fa-f]{2})/g).map(function (part) {
      if (!/%[0-9A-Fa-f]/.test(part)) {
        part = encodeURI(part).replace(/%5B/g, '[').replace(/%5D/g, ']');
      }
      return part;
    }).join('');
  };

  /**
   * @private
   * @param {string} str
   * @return {string}
   */
  UrlTemplate.prototype.encodeUnreserved = function (str) {
    return encodeURIComponent(str).replace(/[!'()*]/g, function (c) {
      return '%' + c.charCodeAt(0).toString(16).toUpperCase();
    });
  }

  /**
   * @private
   * @param {string} operator
   * @param {string} value
   * @param {string} key
   * @return {string}
   */
  UrlTemplate.prototype.encodeValue = function (operator, value, key) {
    value = (operator === '+' || operator === '#') ? this.encodeReserved(value) : this.encodeUnreserved(value);

    if (key) {
      return this.encodeUnreserved(key) + '=' + value;
    } else {
      return value;
    }
  };

  /**
   * @private
   * @param {*} value
   * @return {boolean}
   */
  UrlTemplate.prototype.isDefined = function (value) {
    return value !== undefined && value !== null;
  };

  /**
   * @private
   * @param {string}
   * @return {boolean}
   */
  UrlTemplate.prototype.isKeyOperator = function (operator) {
    return operator === ';' || operator === '&' || operator === '?';
  };

  /**
   * @private
   * @param {Object} context
   * @param {string} operator
   * @param {string} key
   * @param {string} modifier
   */
  UrlTemplate.prototype.getValues = function (context, operator, key, modifier) {
    var value = context[key],
        result = [];

    if (this.isDefined(value) && value !== '') {
      if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
        value = value.toString();

        if (modifier && modifier !== '*') {
          value = value.substring(0, parseInt(modifier, 10));
        }

        result.push(this.encodeValue(operator, value, this.isKeyOperator(operator) ? key : null));
      } else {
        if (modifier === '*') {
          if (Array.isArray(value)) {
            value.filter(this.isDefined).forEach(function (value) {
              result.push(this.encodeValue(operator, value, this.isKeyOperator(operator) ? key : null));
            }, this);
          } else {
            Object.keys(value).forEach(function (k) {
              if (this.isDefined(value[k])) {
                result.push(this.encodeValue(operator, value[k], k));
              }
            }, this);
          }
        } else {
          var tmp = [];

          if (Array.isArray(value)) {
            value.filter(this.isDefined).forEach(function (value) {
              tmp.push(this.encodeValue(operator, value));
            }, this);
          } else {
            Object.keys(value).forEach(function (k) {
              if (this.isDefined(value[k])) {
                tmp.push(this.encodeUnreserved(k));
                tmp.push(this.encodeValue(operator, value[k].toString()));
              }
            }, this);
          }

          if (this.isKeyOperator(operator)) {
            result.push(this.encodeUnreserved(key) + '=' + tmp.join(','));
          } else if (tmp.length !== 0) {
            result.push(tmp.join(','));
          }
        }
      }
    } else {
      if (operator === ';') {
        if (this.isDefined(value)) {
          result.push(this.encodeUnreserved(key));
        }
      } else if (value === '' && (operator === '&' || operator === '?')) {
        result.push(this.encodeUnreserved(key) + '=');
      } else if (value === '') {
        result.push('');
      }
    }
    return result;
  };

  /**
   * @param {string} template
   * @return {function(Object):string}
   */
  UrlTemplate.prototype.parse = function (template) {
    var that = this;
    var operators = ['+', '#', '.', '/', ';', '?', '&'];

    return {
      expand: function (context) {
        return template.replace(/\{([^\{\}]+)\}|([^\{\}]+)/g, function (_, expression, literal) {
          if (expression) {
            var operator = null,
                values = [];

            if (operators.indexOf(expression.charAt(0)) !== -1) {
              operator = expression.charAt(0);
              expression = expression.substr(1);
            }

            expression.split(/,/g).forEach(function (variable) {
              var tmp = /([^:\*]*)(?::(\d+)|(\*))?/.exec(variable);
              values.push.apply(values, that.getValues(context, operator, tmp[1], tmp[2] || tmp[3]));
            });

            if (operator && operator !== '+') {
              var separator = ',';

              if (operator === '?') {
                separator = '&';
              } else if (operator !== '#') {
                separator = operator;
              }
              return (values.length !== 0 ? operator : '') + values.join(separator);
            } else {
              return values.join(',');
            }
          } else {
            return that.encodeReserved(literal);
          }
        });
      }
    };
  };

  return new UrlTemplate();
}));

},{}],18:[function(require,module,exports){
(function(self) {
  'use strict';

  if (self.fetch) {
    return
  }

  var support = {
    searchParams: 'URLSearchParams' in self,
    iterable: 'Symbol' in self && 'iterator' in Symbol,
    blob: 'FileReader' in self && 'Blob' in self && (function() {
      try {
        new Blob()
        return true
      } catch(e) {
        return false
      }
    })(),
    formData: 'FormData' in self,
    arrayBuffer: 'ArrayBuffer' in self
  }

  if (support.arrayBuffer) {
    var viewClasses = [
      '[object Int8Array]',
      '[object Uint8Array]',
      '[object Uint8ClampedArray]',
      '[object Int16Array]',
      '[object Uint16Array]',
      '[object Int32Array]',
      '[object Uint32Array]',
      '[object Float32Array]',
      '[object Float64Array]'
    ]

    var isDataView = function(obj) {
      return obj && DataView.prototype.isPrototypeOf(obj)
    }

    var isArrayBufferView = ArrayBuffer.isView || function(obj) {
      return obj && viewClasses.indexOf(Object.prototype.toString.call(obj)) > -1
    }
  }

  function normalizeName(name) {
    if (typeof name !== 'string') {
      name = String(name)
    }
    if (/[^a-z0-9\-#$%&'*+.\^_`|~]/i.test(name)) {
      throw new TypeError('Invalid character in header field name')
    }
    return name.toLowerCase()
  }

  function normalizeValue(value) {
    if (typeof value !== 'string') {
      value = String(value)
    }
    return value
  }

  // Build a destructive iterator for the value list
  function iteratorFor(items) {
    var iterator = {
      next: function() {
        var value = items.shift()
        return {done: value === undefined, value: value}
      }
    }

    if (support.iterable) {
      iterator[Symbol.iterator] = function() {
        return iterator
      }
    }

    return iterator
  }

  function Headers(headers) {
    this.map = {}

    if (headers instanceof Headers) {
      headers.forEach(function(value, name) {
        this.append(name, value)
      }, this)

    } else if (headers) {
      Object.getOwnPropertyNames(headers).forEach(function(name) {
        this.append(name, headers[name])
      }, this)
    }
  }

  Headers.prototype.append = function(name, value) {
    name = normalizeName(name)
    value = normalizeValue(value)
    var oldValue = this.map[name]
    this.map[name] = oldValue ? oldValue+','+value : value
  }

  Headers.prototype['delete'] = function(name) {
    delete this.map[normalizeName(name)]
  }

  Headers.prototype.get = function(name) {
    name = normalizeName(name)
    return this.has(name) ? this.map[name] : null
  }

  Headers.prototype.has = function(name) {
    return this.map.hasOwnProperty(normalizeName(name))
  }

  Headers.prototype.set = function(name, value) {
    this.map[normalizeName(name)] = normalizeValue(value)
  }

  Headers.prototype.forEach = function(callback, thisArg) {
    for (var name in this.map) {
      if (this.map.hasOwnProperty(name)) {
        callback.call(thisArg, this.map[name], name, this)
      }
    }
  }

  Headers.prototype.keys = function() {
    var items = []
    this.forEach(function(value, name) { items.push(name) })
    return iteratorFor(items)
  }

  Headers.prototype.values = function() {
    var items = []
    this.forEach(function(value) { items.push(value) })
    return iteratorFor(items)
  }

  Headers.prototype.entries = function() {
    var items = []
    this.forEach(function(value, name) { items.push([name, value]) })
    return iteratorFor(items)
  }

  if (support.iterable) {
    Headers.prototype[Symbol.iterator] = Headers.prototype.entries
  }

  function consumed(body) {
    if (body.bodyUsed) {
      return Promise.reject(new TypeError('Already read'))
    }
    body.bodyUsed = true
  }

  function fileReaderReady(reader) {
    return new Promise(function(resolve, reject) {
      reader.onload = function() {
        resolve(reader.result)
      }
      reader.onerror = function() {
        reject(reader.error)
      }
    })
  }

  function readBlobAsArrayBuffer(blob) {
    var reader = new FileReader()
    var promise = fileReaderReady(reader)
    reader.readAsArrayBuffer(blob)
    return promise
  }

  function readBlobAsText(blob) {
    var reader = new FileReader()
    var promise = fileReaderReady(reader)
    reader.readAsText(blob)
    return promise
  }

  function readArrayBufferAsText(buf) {
    var view = new Uint8Array(buf)
    var chars = new Array(view.length)

    for (var i = 0; i < view.length; i++) {
      chars[i] = String.fromCharCode(view[i])
    }
    return chars.join('')
  }

  function bufferClone(buf) {
    if (buf.slice) {
      return buf.slice(0)
    } else {
      var view = new Uint8Array(buf.byteLength)
      view.set(new Uint8Array(buf))
      return view.buffer
    }
  }

  function Body() {
    this.bodyUsed = false

    this._initBody = function(body) {
      this._bodyInit = body
      if (!body) {
        this._bodyText = ''
      } else if (typeof body === 'string') {
        this._bodyText = body
      } else if (support.blob && Blob.prototype.isPrototypeOf(body)) {
        this._bodyBlob = body
      } else if (support.formData && FormData.prototype.isPrototypeOf(body)) {
        this._bodyFormData = body
      } else if (support.searchParams && URLSearchParams.prototype.isPrototypeOf(body)) {
        this._bodyText = body.toString()
      } else if (support.arrayBuffer && support.blob && isDataView(body)) {
        this._bodyArrayBuffer = bufferClone(body.buffer)
        // IE 10-11 can't handle a DataView body.
        this._bodyInit = new Blob([this._bodyArrayBuffer])
      } else if (support.arrayBuffer && (ArrayBuffer.prototype.isPrototypeOf(body) || isArrayBufferView(body))) {
        this._bodyArrayBuffer = bufferClone(body)
      } else {
        throw new Error('unsupported BodyInit type')
      }

      if (!this.headers.get('content-type')) {
        if (typeof body === 'string') {
          this.headers.set('content-type', 'text/plain;charset=UTF-8')
        } else if (this._bodyBlob && this._bodyBlob.type) {
          this.headers.set('content-type', this._bodyBlob.type)
        } else if (support.searchParams && URLSearchParams.prototype.isPrototypeOf(body)) {
          this.headers.set('content-type', 'application/x-www-form-urlencoded;charset=UTF-8')
        }
      }
    }

    if (support.blob) {
      this.blob = function() {
        var rejected = consumed(this)
        if (rejected) {
          return rejected
        }

        if (this._bodyBlob) {
          return Promise.resolve(this._bodyBlob)
        } else if (this._bodyArrayBuffer) {
          return Promise.resolve(new Blob([this._bodyArrayBuffer]))
        } else if (this._bodyFormData) {
          throw new Error('could not read FormData body as blob')
        } else {
          return Promise.resolve(new Blob([this._bodyText]))
        }
      }

      this.arrayBuffer = function() {
        if (this._bodyArrayBuffer) {
          return consumed(this) || Promise.resolve(this._bodyArrayBuffer)
        } else {
          return this.blob().then(readBlobAsArrayBuffer)
        }
      }
    }

    this.text = function() {
      var rejected = consumed(this)
      if (rejected) {
        return rejected
      }

      if (this._bodyBlob) {
        return readBlobAsText(this._bodyBlob)
      } else if (this._bodyArrayBuffer) {
        return Promise.resolve(readArrayBufferAsText(this._bodyArrayBuffer))
      } else if (this._bodyFormData) {
        throw new Error('could not read FormData body as text')
      } else {
        return Promise.resolve(this._bodyText)
      }
    }

    if (support.formData) {
      this.formData = function() {
        return this.text().then(decode)
      }
    }

    this.json = function() {
      return this.text().then(JSON.parse)
    }

    return this
  }

  // HTTP methods whose capitalization should be normalized
  var methods = ['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST', 'PUT']

  function normalizeMethod(method) {
    var upcased = method.toUpperCase()
    return (methods.indexOf(upcased) > -1) ? upcased : method
  }

  function Request(input, options) {
    options = options || {}
    var body = options.body

    if (input instanceof Request) {
      if (input.bodyUsed) {
        throw new TypeError('Already read')
      }
      this.url = input.url
      this.credentials = input.credentials
      if (!options.headers) {
        this.headers = new Headers(input.headers)
      }
      this.method = input.method
      this.mode = input.mode
      if (!body && input._bodyInit != null) {
        body = input._bodyInit
        input.bodyUsed = true
      }
    } else {
      this.url = String(input)
    }

    this.credentials = options.credentials || this.credentials || 'omit'
    if (options.headers || !this.headers) {
      this.headers = new Headers(options.headers)
    }
    this.method = normalizeMethod(options.method || this.method || 'GET')
    this.mode = options.mode || this.mode || null
    this.referrer = null

    if ((this.method === 'GET' || this.method === 'HEAD') && body) {
      throw new TypeError('Body not allowed for GET or HEAD requests')
    }
    this._initBody(body)
  }

  Request.prototype.clone = function() {
    return new Request(this, { body: this._bodyInit })
  }

  function decode(body) {
    var form = new FormData()
    body.trim().split('&').forEach(function(bytes) {
      if (bytes) {
        var split = bytes.split('=')
        var name = split.shift().replace(/\+/g, ' ')
        var value = split.join('=').replace(/\+/g, ' ')
        form.append(decodeURIComponent(name), decodeURIComponent(value))
      }
    })
    return form
  }

  function parseHeaders(rawHeaders) {
    var headers = new Headers()
    rawHeaders.split(/\r?\n/).forEach(function(line) {
      var parts = line.split(':')
      var key = parts.shift().trim()
      if (key) {
        var value = parts.join(':').trim()
        headers.append(key, value)
      }
    })
    return headers
  }

  Body.call(Request.prototype)

  function Response(bodyInit, options) {
    if (!options) {
      options = {}
    }

    this.type = 'default'
    this.status = 'status' in options ? options.status : 200
    this.ok = this.status >= 200 && this.status < 300
    this.statusText = 'statusText' in options ? options.statusText : 'OK'
    this.headers = new Headers(options.headers)
    this.url = options.url || ''
    this._initBody(bodyInit)
  }

  Body.call(Response.prototype)

  Response.prototype.clone = function() {
    return new Response(this._bodyInit, {
      status: this.status,
      statusText: this.statusText,
      headers: new Headers(this.headers),
      url: this.url
    })
  }

  Response.error = function() {
    var response = new Response(null, {status: 0, statusText: ''})
    response.type = 'error'
    return response
  }

  var redirectStatuses = [301, 302, 303, 307, 308]

  Response.redirect = function(url, status) {
    if (redirectStatuses.indexOf(status) === -1) {
      throw new RangeError('Invalid status code')
    }

    return new Response(null, {status: status, headers: {location: url}})
  }

  self.Headers = Headers
  self.Request = Request
  self.Response = Response

  self.fetch = function(input, init) {
    return new Promise(function(resolve, reject) {
      var request = new Request(input, init)
      var xhr = new XMLHttpRequest()

      xhr.onload = function() {
        var options = {
          status: xhr.status,
          statusText: xhr.statusText,
          headers: parseHeaders(xhr.getAllResponseHeaders() || '')
        }
        options.url = 'responseURL' in xhr ? xhr.responseURL : options.headers.get('X-Request-URL')
        var body = 'response' in xhr ? xhr.response : xhr.responseText
        resolve(new Response(body, options))
      }

      xhr.onerror = function() {
        reject(new TypeError('Network request failed'))
      }

      xhr.ontimeout = function() {
        reject(new TypeError('Network request failed'))
      }

      xhr.open(request.method, request.url, true)

      if (request.credentials === 'include') {
        xhr.withCredentials = true
      }

      if ('responseType' in xhr && support.blob) {
        xhr.responseType = 'blob'
      }

      request.headers.forEach(function(value, name) {
        xhr.setRequestHeader(name, value)
      })

      xhr.send(typeof request._bodyInit === 'undefined' ? null : request._bodyInit)
    })
  }
  self.fetch.polyfill = true
})(typeof self !== 'undefined' ? self : this);

},{}]},{},[8])(8)
});
//# sourceMappingURL=data:application/json;charset=utf-8;base64,eyJ2ZXJzaW9uIjozLCJzb3VyY2VzIjpbIm5vZGVfbW9kdWxlcy9icm93c2VyLXBhY2svX3ByZWx1ZGUuanMiLCJsaWIvY2xpZW50LmpzIiwibGliL2NvZGVjcy9jb3JlanNvbi5qcyIsImxpYi9jb2RlY3MvaW5kZXguanMiLCJsaWIvY29kZWNzL2pzb24uanMiLCJsaWIvY29kZWNzL3RleHQuanMiLCJsaWIvZG9jdW1lbnQuanMiLCJsaWIvZXJyb3JzLmpzIiwibGliL2luZGV4LmpzIiwibGliL3RyYW5zcG9ydHMvaHR0cC5qcyIsImxpYi90cmFuc3BvcnRzL2luZGV4LmpzIiwibGliL3V0aWxzLmpzIiwibm9kZV9tb2R1bGVzL2lzb21vcnBoaWMtZmV0Y2gvZmV0Y2gtbnBtLWJyb3dzZXJpZnkuanMiLCJub2RlX21vZHVsZXMvcXVlcnlzdHJpbmdpZnkvaW5kZXguanMiLCJub2RlX21vZHVsZXMvcmVxdWlyZXMtcG9ydC9pbmRleC5qcyIsIm5vZGVfbW9kdWxlcy91cmwtcGFyc2UvaW5kZXguanMiLCJub2RlX21vZHVsZXMvdXJsLXBhcnNlL2xvbGNhdGlvbi5qcyIsIm5vZGVfbW9kdWxlcy91cmwtdGVtcGxhdGUvbGliL3VybC10ZW1wbGF0ZS5qcyIsIm5vZGVfbW9kdWxlcy93aGF0d2ctZmV0Y2gvZmV0Y2guanMiXSwibmFtZXMiOltdLCJtYXBwaW5ncyI6IkFBQUE7Ozs7Ozs7QUNBQSxJQUFNLFdBQVcsUUFBUSxZQUFSLENBQWpCO0FBQ0EsSUFBTSxTQUFTLFFBQVEsVUFBUixDQUFmO0FBQ0EsSUFBTSxTQUFTLFFBQVEsVUFBUixDQUFmO0FBQ0EsSUFBTSxhQUFhLFFBQVEsY0FBUixDQUFuQjtBQUNBLElBQU0sUUFBUSxRQUFRLFNBQVIsQ0FBZDs7QUFFQSxTQUFTLFVBQVQsQ0FBcUIsSUFBckIsRUFBMkIsSUFBM0IsRUFBaUM7QUFBQTtBQUFBO0FBQUE7O0FBQUE7QUFDL0IseUJBQWdCLElBQWhCLDhIQUFzQjtBQUFBLFVBQWIsR0FBYTs7QUFDcEIsVUFBSSxnQkFBZ0IsU0FBUyxRQUE3QixF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QTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7O0FDN0RBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTs7QUN0Q0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7QUN2V0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOzs7O0FDckRBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBOztBQ2hNQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0E7QUFDQTtBQUNBO0FBQ0EiLCJmaWxlIjoiZ2VuZXJhdGVkLmpzIiwic291cmNlUm9vdCI6IiIsInNvdXJjZXNDb250ZW50IjpbIihmdW5jdGlvbiBlKHQsbixyKXtmdW5jdGlvbiBzKG8sdSl7aWYoIW5bb10pe2lmKCF0W29dKXt2YXIgYT10eXBlb2YgcmVxdWlyZT09XCJmdW5jdGlvblwiJiZyZXF1aXJlO2lmKCF1JiZhKXJldHVybiBhKG8sITApO2lmKGkpcmV0dXJuIGkobywhMCk7dmFyIGY9bmV3IEVycm9yKFwiQ2Fubm90IGZpbmQgbW9kdWxlICdcIitvK1wiJ1wiKTt0aHJvdyBmLmNvZGU9XCJNT0RVTEVfTk9UX0ZPVU5EXCIsZn12YXIgbD1uW29dPXtleHBvcnRzOnt9fTt0W29dWzBdLmNhbGwobC5leHBvcnRzLGZ1bmN0aW9uKGUpe3ZhciBuPXRbb11bMV1bZV07cmV0dXJuIHMobj9uOmUpfSxsLGwuZXhwb3J0cyxlLHQsbixyKX1yZXR1cm4gbltvXS5leHBvcnRzfXZhciBpPXR5cGVvZiByZXF1aXJlPT1cImZ1bmN0aW9uXCImJnJlcXVpcmU7Zm9yKHZhciBvPTA7bzxyLmxlbmd0aDtvKyspcyhyW29dKTtyZXR1cm4gc30pIiwiY29uc3QgZG9jdW1lbnQgPSByZXF1aXJlKCcuL2RvY3VtZW50JylcbmNvbnN0IGNvZGVjcyA9IHJlcXVpcmUoJy4vY29kZWNzJylcbmNvbnN0IGVycm9ycyA9IHJlcXVpcmUoJy4vZXJyb3JzJylcbmNvbnN0IHRyYW5zcG9ydHMgPSByZXF1aXJlKCcuL3RyYW5zcG9ydHMnKVxuY29uc3QgdXRpbHMgPSByZXF1aXJlKCcuL3V0aWxzJylcblxuZnVuY3Rpb24gbG9va3VwTGluayAobm9kZSwga2V5cykge1xuICBmb3IgKGxldCBrZXkgb2Yga2V5cykge1xuICAgIGlmIChub2RlIGluc3RhbmNlb2YgZG9jdW1lbnQuRG9jdW1lbnQpIHtcbiAgICAgIG5vZGUgPSBub2RlLmNvbnRlbnRba2V5XVxuICAgIH0gZWxzZSB7XG4gICAgICBub2RlID0gbm9kZVtrZXldXG4gICAgfVxuICAgIGlmIChub2RlID09PSB1bmRlZmluZWQpIHtcbiAgICAgIHRocm93IG5ldyBlcnJvcnMuTGlua0xvb2t1cEVycm9yKGBJbnZhbGlkIGxpbmsgbG9va3VwOiAke0pTT04uc3RyaW5naWZ5KGtleXMpfWApXG4gICAgfVxuICB9XG4gIGlmICghKG5vZGUgaW5zdGFuY2VvZiBkb2N1bWVudC5MaW5rKSkge1xuICAgIHRocm93IG5ldyBlcnJvcnMuTGlua0xvb2t1cEVycm9yKGBJbnZhbGlkIGxpbmsgbG9va3VwOiAke0pTT04uc3RyaW5naWZ5KGtleXMpfWApXG4gIH1cbiAgcmV0dXJuIG5vZGVcbn1cblxuY2xhc3MgQ2xpZW50IHtcbiAgY29uc3RydWN0b3IgKG9wdGlvbnMgPSB7fSkge1xuICAgIGNvbnN0IHRyYW5zcG9ydE9wdGlvbnMgPSB7XG4gICAgICBjc3JmOiBvcHRpb25zLmNzcmYsXG4gICAgICBoZWFkZXJzOiBvcHRpb25zLmhlYWRlcnMgfHwge30sXG4gICAgICByZXF1ZXN0Q2FsbGJhY2s6IG9wdGlvbnMucmVxdWVzdENhbGxiYWNrLFxuICAgICAgcmVzcG9uc2VDYWxsYmFjazogb3B0aW9ucy5yZXNwb25zZUNhbGxiYWNrXG4gICAgfVxuXG4gICAgdGhpcy5kZWNvZGVycyA9IG9wdGlvbnMuZGVjb2RlcnMgfHwgW25ldyBjb2RlY3MuQ29yZUpTT05Db2RlYygpLCBuZXcgY29kZWNzLkpTT05Db2RlYygpLCBuZXcgY29kZWNzLlRleHRDb2RlYygpXVxuICAgIHRoaXMudHJhbnNwb3J0cyA9IG9wdGlvbnMudHJhbnNwb3J0cyB8fCBbbmV3IHRyYW5zcG9ydHMuSFRUUFRyYW5zcG9ydCh0cmFuc3BvcnRPcHRpb25zKV1cbiAgfVxuXG4gIGFjdGlvbiAoZG9jdW1lbnQsIGtleXMsIHBhcmFtcyA9IHt9KSB7XG4gICAgY29uc3QgbGluayA9IGxvb2t1cExpbmsoZG9jdW1lbnQsIGtleXMpXG4gICAgY29uc3QgdHJhbnNwb3J0ID0gdXRpbHMuZGV0ZXJtaW5lVHJhbnNwb3J0KHRoaXMudHJhbnNwb3J0cywgbGluay51cmwpXG4gICAgcmV0dXJuIHRyYW5zcG9ydC5hY3Rpb24obGluaywgdGhpcy5kZWNvZGVycywgcGFyYW1zKVxuICB9XG5cbiAgZ2V0ICh1cmwpIHtcbiAgICBjb25zdCBsaW5rID0gbmV3IGRvY3VtZW50LkxpbmsodXJsLCAnZ2V0JylcbiAgICBjb25zdCB0cmFuc3BvcnQgPSB1dGlscy5kZXRlcm1pbmVUcmFuc3BvcnQodGhpcy50cmFuc3BvcnRzLCB1cmwpXG4gICAgcmV0dXJuIHRyYW5zcG9ydC5hY3Rpb24obGluaywgdGhpcy5kZWNvZGVycylcbiAgfVxufVxuXG5tb2R1bGUuZXhwb3J0cyA9IHtcbiAgQ2xpZW50OiBDbGllbnRcbn1cbiIsImNvbnN0IGRvY3VtZW50ID0gcmVxdWlyZSgnLi4vZG9jdW1lbnQnKVxuY29uc3QgVVJMID0gcmVxdWlyZSgndXJsLXBhcnNlJylcblxuZnVuY3Rpb24gdW5lc2NhcGVLZXkgKGtleSkge1xuICBpZiAoa2V5Lm1hdGNoKC9fXyh0eXBlfG1ldGEpJC8pKSB7XG4gICAgcmV0dXJuIGtleS5zdWJzdHJpbmcoMSlcbiAgfVxuICByZXR1cm4ga2V5XG59XG5cbmZ1bmN0aW9uIGdldFN0cmluZyAob2JqLCBrZXkpIHtcbiAgY29uc3QgdmFsdWUgPSBvYmpba2V5XVxuICBpZiAodHlwZW9mICh2YWx1ZSkgPT09ICdzdHJpbmcnKSB7XG4gICAgcmV0dXJuIHZhbHVlXG4gIH1cbiAgcmV0dXJuICcnXG59XG5cbmZ1bmN0aW9uIGdldEJvb2xlYW4gKG9iaiwga2V5KSB7XG4gIGNvbnN0IHZhbHVlID0gb2JqW2tleV1cbiAgaWYgKHR5cGVvZiAodmFsdWUpID09PSAnYm9vbGVhbicpIHtcbiAgICByZXR1cm4gdmFsdWVcbiAgfVxuICByZXR1cm4gZmFsc2Vcbn1cblxuZnVuY3Rpb24gZ2V0T2JqZWN0IChvYmosIGtleSkge1xuICBjb25zdCB2YWx1ZSA9IG9ialtrZXldXG4gIGlmICh0eXBlb2YgKHZhbHVlKSA9PT0gJ29iamVjdCcpIHtcbiAgICByZXR1cm4gdmFsdWVcbiAgfVxuICByZXR1cm4ge31cbn1cblxuZnVuY3Rpb24gZ2V0QXJyYXkgKG9iaiwga2V5KSB7XG4gIGNvbnN0IHZhbHVlID0gb2JqW2tleV1cbiAgaWYgKHZhbHVlIGluc3RhbmNlb2YgQXJyYXkpIHtcbiAgICByZXR1cm4gdmFsdWVcbiAgfVxuICByZXR1cm4gW11cbn1cblxuZnVuY3Rpb24gZ2V0Q29udGVudCAoZGF0YSwgYmFzZVVybCkge1xuICBjb25zdCBleGNsdWRlZCA9IFsnX3R5cGUnLCAnX21ldGEnXVxuICB2YXIgY29udGVudCA9IHt9XG4gIGZvciAodmFyIHByb3BlcnR5IGluIGRhdGEpIHtcbiAgICBpZiAoZGF0YS5oYXNPd25Qcm9wZXJ0eShwcm9wZXJ0eSkgJiYgIWV4Y2x1ZGVkLmluY2x1ZGVzKHByb3BlcnR5KSkge1xuICAgICAgY29uc3Qga2V5ID0gdW5lc2NhcGVLZXkocHJvcGVydHkpXG4gICAgICBjb25zdCB2YWx1ZSA9IHByaW1pdGl2ZVRvTm9kZShkYXRhW3Byb3BlcnR5XSwgYmFzZVVybClcbiAgICAgIGNvbnRlbnRba2V5XSA9IHZhbHVlXG4gICAgfVxuICB9XG4gIHJldHVybiBjb250ZW50XG59XG5cbmZ1bmN0aW9uIHByaW1pdGl2ZVRvTm9kZSAoZGF0YSwgYmFzZVVybCkge1xuICBjb25zdCBpc09iamVjdCA9IGRhdGEgaW5zdGFuY2VvZiBPYmplY3QgJiYgIShkYXRhIGluc3RhbmNlb2YgQXJyYXkpXG5cbiAgaWYgKGlzT2JqZWN0ICYmIGRhdGEuX3R5cGUgPT09ICdkb2N1bWVudCcpIHtcbiAgICAvLyBEb2N1bWVudFxuICAgIGNvbnN0IG1ldGEgPSBnZXRPYmplY3QoZGF0YSwgJ19tZXRhJylcbiAgICBjb25zdCByZWxhdGl2ZVVybCA9IGdldFN0cmluZyhtZXRhLCAndXJsJylcbiAgICBjb25zdCB1cmwgPSByZWxhdGl2ZVVybCA/IFVSTChyZWxhdGl2ZVVybCwgYmFzZVVybCkudG9TdHJpbmcoKSA6ICcnXG4gICAgY29uc3QgdGl0bGUgPSBnZXRTdHJpbmcobWV0YSwgJ3RpdGxlJylcbiAgICBjb25zdCBkZXNjcmlwdGlvbiA9IGdldFN0cmluZyhtZXRhLCAnZGVzY3JpcHRpb24nKVxuICAgIGNvbnN0IGNvbnRlbnQgPSBnZXRDb250ZW50KGRhdGEsIHVybClcbiAgICByZXR1cm4gbmV3IGRvY3VtZW50LkRvY3VtZW50KHVybCwgdGl0bGUsIGRlc2NyaXB0aW9uLCBjb250ZW50KVxuICB9IGVsc2UgaWYgKGlzT2JqZWN0ICYmIGRhdGEuX3R5cGUgPT09ICdsaW5rJykge1xuICAgIC8vIExpbmtcbiAgICBjb25zdCByZWxhdGl2ZVVybCA9IGdldFN0cmluZyhkYXRhLCAndXJsJylcbiAgICBjb25zdCB1cmwgPSByZWxhdGl2ZVVybCA/IFVSTChyZWxhdGl2ZVVybCwgYmFzZVVybCkudG9TdHJpbmcoKSA6ICcnXG4gICAgY29uc3QgbWV0aG9kID0gZ2V0U3RyaW5nKGRhdGEsICdhY3Rpb24nKSB8fCAnZ2V0J1xuICAgIGNvbnN0IHRpdGxlID0gZ2V0U3RyaW5nKGRhdGEsICd0aXRsZScpXG4gICAgY29uc3QgZGVzY3JpcHRpb24gPSBnZXRTdHJpbmcoZGF0YSwgJ2Rlc2NyaXB0aW9uJylcbiAgICBjb25zdCBmaWVsZHNEYXRhID0gZ2V0QXJyYXkoZGF0YSwgJ2ZpZWxkcycpXG4gICAgdmFyIGZpZWxkcyA9IFtdXG4gICAgZm9yIChsZXQgaWR4ID0gMCwgbGVuID0gZmllbGRzRGF0YS5sZW5ndGg7IGlkeCA8IGxlbjsgaWR4KyspIHtcbiAgICAgIGxldCB2YWx1ZSA9IGZpZWxkc0RhdGFbaWR4XVxuICAgICAgbGV0IG5hbWUgPSBnZXRTdHJpbmcodmFsdWUsICduYW1lJylcbiAgICAgIGxldCByZXF1aXJlZCA9IGdldEJvb2xlYW4odmFsdWUsICdyZXF1aXJlZCcpXG4gICAgICBsZXQgbG9jYXRpb24gPSBnZXRTdHJpbmcodmFsdWUsICdsb2NhdGlvbicpXG4gICAgICBsZXQgZmllbGREZXNjcmlwdGlvbiA9IGdldFN0cmluZyh2YWx1ZSwgJ2ZpZWxkRGVzY3JpcHRpb24nKVxuICAgICAgbGV0IGZpZWxkID0gbmV3IGRvY3VtZW50LkZpZWxkKG5hbWUsIHJlcXVpcmVkLCBsb2NhdGlvbiwgZmllbGREZXNjcmlwdGlvbilcbiAgICAgIGZpZWxkcy5wdXNoKGZpZWxkKVxuICAgIH1cbiAgICByZXR1cm4gbmV3IGRvY3VtZW50LkxpbmsodXJsLCBtZXRob2QsICdhcHBsaWNhdGlvbi9qc29uJywgZmllbGRzLCB0aXRsZSwgZGVzY3JpcHRpb24pXG4gIH0gZWxzZSBpZiAoaXNPYmplY3QpIHtcbiAgICAvLyBPYmplY3RcbiAgICBsZXQgY29udGVudCA9IHt9XG4gICAgZm9yIChsZXQga2V5IGluIGRhdGEpIHtcbiAgICAgIGlmIChkYXRhLmhhc093blByb3BlcnR5KGtleSkpIHtcbiAgICAgICAgY29udGVudFtrZXldID0gcHJpbWl0aXZlVG9Ob2RlKGRhdGFba2V5XSwgYmFzZVVybClcbiAgICAgIH1cbiAgICB9XG4gICAgcmV0dXJuIGNvbnRlbnRcbiAgfSBlbHNlIGlmIChkYXRhIGluc3RhbmNlb2YgQXJyYXkpIHtcbiAgICAvLyBPYmplY3RcbiAgICBsZXQgY29udGVudCA9IFtdXG4gICAgZm9yIChsZXQgaWR4ID0gMCwgbGVuID0gZGF0YS5sZW5ndGg7IGlkeCA8IGxlbjsgaWR4KyspIHtcbiAgICAgIGNvbnRlbnQucHVzaChwcmltaXRpdmVUb05vZGUoZGF0YVtpZHhdLCBiYXNlVXJsKSlcbiAgICB9XG4gICAgcmV0dXJuIGNvbnRlbnRcbiAgfVxuICAvLyBQcmltaXRpdmVcbiAgcmV0dXJuIGRhdGFcbn1cblxuY2xhc3MgQ29yZUpTT05Db2RlYyB7XG4gIGNvbnN0cnVjdG9yICgpIHtcbiAgICB0aGlzLm1lZGlhVHlwZSA9ICdhcHBsaWNhdGlvbi9jb3JlYXBpK2pzb24nXG4gIH1cblxuICBkZWNvZGUgKHRleHQsIG9wdGlvbnMgPSB7fSkge1xuICAgIGxldCBkYXRhID0gdGV4dFxuICAgIGlmIChvcHRpb25zLnByZWxvYWRlZCA9PT0gdW5kZWZpbmVkIHx8ICFvcHRpb25zLnByZWxvYWRlZCkge1xuICAgICAgZGF0YSA9IEpTT04ucGFyc2UodGV4dClcbiAgICB9XG4gICAgcmV0dXJuIHByaW1pdGl2ZVRvTm9kZShkYXRhLCBvcHRpb25zLnVybClcbiAgfVxufVxuXG5tb2R1bGUuZXhwb3J0cyA9IHtcbiAgQ29yZUpTT05Db2RlYzogQ29yZUpTT05Db2RlY1xufVxuIiwiY29uc3QgY29yZWpzb24gPSByZXF1aXJlKCcuL2NvcmVqc29uJylcbmNvbnN0IGpzb24gPSByZXF1aXJlKCcuL2pzb24nKVxuY29uc3QgdGV4dCA9IHJlcXVpcmUoJy4vdGV4dCcpXG5cbm1vZHVsZS5leHBvcnRzID0ge1xuICBDb3JlSlNPTkNvZGVjOiBjb3JlanNvbi5Db3JlSlNPTkNvZGVjLFxuICBKU09OQ29kZWM6IGpzb24uSlNPTkNvZGVjLFxuICBUZXh0Q29kZWM6IHRleHQuVGV4dENvZGVjXG59XG4iLCJjbGFzcyBKU09OQ29kZWMge1xuICBjb25zdHJ1Y3RvciAoKSB7XG4gICAgdGhpcy5tZWRpYVR5cGUgPSAnYXBwbGljYXRpb24vanNvbidcbiAgfVxuXG4gIGRlY29kZSAodGV4dCwgb3B0aW9ucyA9IHt9KSB7XG4gICAgcmV0dXJuIEpTT04ucGFyc2UodGV4dClcbiAgfVxufVxuXG5tb2R1bGUuZXhwb3J0cyA9IHtcbiAgSlNPTkNvZGVjOiBKU09OQ29kZWNcbn1cbiIsImNsYXNzIFRleHRDb2RlYyB7XG4gIGNvbnN0cnVjdG9yICgpIHtcbiAgICB0aGlzLm1lZGlhVHlwZSA9ICd0ZXh0LyonXG4gIH1cblxuICBkZWNvZGUgKHRleHQsIG9wdGlvbnMgPSB7fSkge1xuICAgIHJldHVybiB0ZXh0XG4gIH1cbn1cblxubW9kdWxlLmV4cG9ydHMgPSB7XG4gIFRleHRDb2RlYzogVGV4dENvZGVjXG59XG4iLCJjbGFzcyBEb2N1bWVudCB7XG4gIGNvbnN0cnVjdG9yICh1cmwgPSAnJywgdGl0bGUgPSAnJywgZGVzY3JpcHRpb24gPSAnJywgY29udGVudCA9IHt9KSB7XG4gICAgdGhpcy51cmwgPSB1cmxcbiAgICB0aGlzLnRpdGxlID0gdGl0bGVcbiAgICB0aGlzLmRlc2NyaXB0aW9uID0gZGVzY3JpcHRpb25cbiAgICB0aGlzLmNvbnRlbnQgPSBjb250ZW50XG4gIH1cbn1cblxuY2xhc3MgTGluayB7XG4gIGNvbnN0cnVjdG9yICh1cmwsIG1ldGhvZCwgZW5jb2RpbmcgPSAnYXBwbGljYXRpb24vanNvbicsIGZpZWxkcyA9IFtdLCB0aXRsZSA9ICcnLCBkZXNjcmlwdGlvbiA9ICcnKSB7XG4gICAgaWYgKHVybCA9PT0gdW5kZWZpbmVkKSB7XG4gICAgICB0aHJvdyBuZXcgRXJyb3IoJ3VybCBhcmd1bWVudCBpcyByZXF1aXJlZCcpXG4gICAgfVxuXG4gICAgaWYgKG1ldGhvZCA9PT0gdW5kZWZpbmVkKSB7XG4gICAgICB0aHJvdyBuZXcgRXJyb3IoJ21ldGhvZCBhcmd1bWVudCBpcyByZXF1aXJlZCcpXG4gICAgfVxuXG4gICAgdGhpcy51cmwgPSB1cmxcbiAgICB0aGlzLm1ldGhvZCA9IG1ldGhvZFxuICAgIHRoaXMuZW5jb2RpbmcgPSBlbmNvZGluZ1xuICAgIHRoaXMuZmllbGRzID0gZmllbGRzXG4gICAgdGhpcy50aXRsZSA9IHRpdGxlXG4gICAgdGhpcy5kZXNjcmlwdGlvbiA9IGRlc2NyaXB0aW9uXG4gIH1cbn1cblxuY2xhc3MgRmllbGQge1xuICBjb25zdHJ1Y3RvciAobmFtZSwgcmVxdWlyZWQgPSBmYWxzZSwgbG9jYXRpb24gPSAnJywgZGVzY3JpcHRpb24gPSAnJykge1xuICAgIGlmIChuYW1lID09PSB1bmRlZmluZWQpIHtcbiAgICAgIHRocm93IG5ldyBFcnJvcignbmFtZSBhcmd1bWVudCBpcyByZXF1aXJlZCcpXG4gICAgfVxuXG4gICAgdGhpcy5uYW1lID0gbmFtZVxuICAgIHRoaXMucmVxdWlyZWQgPSByZXF1aXJlZFxuICAgIHRoaXMubG9jYXRpb24gPSBsb2NhdGlvblxuICAgIHRoaXMuZGVzY3JpcHRpb24gPSBkZXNjcmlwdGlvblxuICB9XG59XG5cbm1vZHVsZS5leHBvcnRzID0ge1xuICBEb2N1bWVudDogRG9jdW1lbnQsXG4gIExpbms6IExpbmssXG4gIEZpZWxkOiBGaWVsZFxufVxuIiwiY2xhc3MgUGFyYW1ldGVyRXJyb3IgZXh0ZW5kcyBFcnJvciB7XG4gIGNvbnN0cnVjdG9yIChtZXNzYWdlKSB7XG4gICAgc3VwZXIobWVzc2FnZSlcbiAgICB0aGlzLm1lc3NhZ2UgPSBtZXNzYWdlXG4gICAgdGhpcy5uYW1lID0gJ1BhcmFtZXRlckVycm9yJ1xuICB9XG59XG5cbmNsYXNzIExpbmtMb29rdXBFcnJvciBleHRlbmRzIEVycm9yIHtcbiAgY29uc3RydWN0b3IgKG1lc3NhZ2UpIHtcbiAgICBzdXBlcihtZXNzYWdlKVxuICAgIHRoaXMubWVzc2FnZSA9IG1lc3NhZ2VcbiAgICB0aGlzLm5hbWUgPSAnTGlua0xvb2t1cEVycm9yJ1xuICB9XG59XG5cbmNsYXNzIEVycm9yTWVzc2FnZSBleHRlbmRzIEVycm9yIHtcbiAgY29uc3RydWN0b3IgKG1lc3NhZ2UsIGNvbnRlbnQpIHtcbiAgICBzdXBlcihtZXNzYWdlKVxuICAgIHRoaXMubWVzc2FnZSA9IG1lc3NhZ2VcbiAgICB0aGlzLmNvbnRlbnQgPSBjb250ZW50XG4gICAgdGhpcy5uYW1lID0gJ0Vycm9yTWVzc2FnZSdcbiAgfVxufVxuXG5tb2R1bGUuZXhwb3J0cyA9IHtcbiAgUGFyYW1ldGVyRXJyb3I6IFBhcmFtZXRlckVycm9yLFxuICBMaW5rTG9va3VwRXJyb3I6IExpbmtMb29rdXBFcnJvcixcbiAgRXJyb3JNZXNzYWdlOiBFcnJvck1lc3NhZ2Vcbn1cbiIsImNvbnN0IGNsaWVudCA9IHJlcXVpcmUoJy4vY2xpZW50JylcbmNvbnN0IGNvZGVjcyA9IHJlcXVpcmUoJy4vY29kZWNzJylcbmNvbnN0IGRvY3VtZW50ID0gcmVxdWlyZSgnLi9kb2N1bWVudCcpXG5jb25zdCBlcnJvcnMgPSByZXF1aXJlKCcuL2Vycm9ycycpXG5jb25zdCB0cmFuc3BvcnRzID0gcmVxdWlyZSgnLi90cmFuc3BvcnRzJylcbmNvbnN0IHV0aWxzID0gcmVxdWlyZSgnLi91dGlscycpXG5cbmNvbnN0IGNvcmVhcGkgPSB7XG4gIENsaWVudDogY2xpZW50LkNsaWVudCxcbiAgRG9jdW1lbnQ6IGRvY3VtZW50LkRvY3VtZW50LFxuICBMaW5rOiBkb2N1bWVudC5MaW5rLFxuICBjb2RlY3M6IGNvZGVjcyxcbiAgZXJyb3JzOiBlcnJvcnMsXG4gIHRyYW5zcG9ydHM6IHRyYW5zcG9ydHMsXG4gIHV0aWxzOiB1dGlsc1xufVxuXG5tb2R1bGUuZXhwb3J0cyA9IGNvcmVhcGlcbiIsImNvbnN0IGZldGNoID0gcmVxdWlyZSgnaXNvbW9ycGhpYy1mZXRjaCcpXG5jb25zdCBlcnJvcnMgPSByZXF1aXJlKCcuLi9lcnJvcnMnKVxuY29uc3QgdXRpbHMgPSByZXF1aXJlKCcuLi91dGlscycpXG5jb25zdCBVUkwgPSByZXF1aXJlKCd1cmwtcGFyc2UnKVxuY29uc3QgdXJsVGVtcGxhdGUgPSByZXF1aXJlKCd1cmwtdGVtcGxhdGUnKVxuXG5jb25zdCBwYXJzZVJlc3BvbnNlID0gKHJlc3BvbnNlLCBkZWNvZGVycykgPT4ge1xuICByZXR1cm4gcmVzcG9uc2UudGV4dCgpLnRoZW4odGV4dCA9PiB7XG4gICAgY29uc3QgY29udGVudFR5cGUgPSByZXNwb25zZS5oZWFkZXJzLmdldCgnQ29udGVudC1UeXBlJylcbiAgICBjb25zdCBkZWNvZGVyID0gdXRpbHMubmVnb3RpYXRlRGVjb2RlcihkZWNvZGVycywgY29udGVudFR5cGUpXG4gICAgY29uc3Qgb3B0aW9ucyA9IHt1cmw6IHJlc3BvbnNlLnVybH1cbiAgICByZXR1cm4gZGVjb2Rlci5kZWNvZGUodGV4dCwgb3B0aW9ucylcbiAgfSlcbn1cblxuY2xhc3MgSFRUUFRyYW5zcG9ydCB7XG4gIGNvbnN0cnVjdG9yIChvcHRpb25zID0ge30pIHtcbiAgICB0aGlzLnNjaGVtZXMgPSBbJ2h0dHAnLCAnaHR0cHMnXVxuICAgIHRoaXMuY3NyZiA9IG9wdGlvbnMuY3NyZlxuICAgIHRoaXMuaGVhZGVycyA9IG9wdGlvbnMuaGVhZGVycyB8fCB7fVxuICAgIHRoaXMuZmV0Y2ggPSBvcHRpb25zLmZldGNoIHx8IGZldGNoXG4gICAgdGhpcy5Gb3JtRGF0YSA9IG9wdGlvbnMuRm9ybURhdGEgfHwgd2luZG93LkZvcm1EYXRhXG4gICAgdGhpcy5yZXF1ZXN0Q2FsbGJhY2sgPSBvcHRpb25zLnJlcXVlc3RDYWxsYmFja1xuICAgIHRoaXMucmVzcG9uc2VDYWxsYmFjayA9IG9wdGlvbnMucmVzcG9uc2VDYWxsYmFja1xuICB9XG5cbiAgYnVpbGRSZXF1ZXN0IChsaW5rLCBkZWNvZGVycywgcGFyYW1zID0ge30pIHtcbiAgICBjb25zdCBmaWVsZHMgPSBsaW5rLmZpZWxkc1xuICAgIGNvbnN0IG1ldGhvZCA9IGxpbmsubWV0aG9kLnRvVXBwZXJDYXNlKClcbiAgICBsZXQgcXVlcnlQYXJhbXMgPSB7fVxuICAgIGxldCBwYXRoUGFyYW1zID0ge31cbiAgICBsZXQgZm9ybVBhcmFtcyA9IHt9XG4gICAgbGV0IGZpZWxkTmFtZXMgPSBbXVxuICAgIGxldCBoYXNCb2R5ID0gZmFsc2VcblxuICAgIGZvciAobGV0IGlkeCA9IDAsIGxlbiA9IGZpZWxkcy5sZW5ndGg7IGlkeCA8IGxlbjsgaWR4KyspIHtcbiAgICAgIGNvbnN0IGZpZWxkID0gZmllbGRzW2lkeF1cblxuICAgICAgLy8gRW5zdXJlIGFueSByZXF1aXJlZCBmaWVsZHMgYXJlIGluY2x1ZGVkXG4gICAgICBpZiAoIXBhcmFtcy5oYXNPd25Qcm9wZXJ0eShmaWVsZC5uYW1lKSkge1xuICAgICAgICBpZiAoZmllbGQucmVxdWlyZWQpIHtcbiAgICAgICAgICB0aHJvdyBuZXcgZXJyb3JzLlBhcmFtZXRlckVycm9yKGBNaXNzaW5nIHJlcXVpcmVkIGZpZWxkOiBcIiR7ZmllbGQubmFtZX1cImApXG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgY29udGludWVcbiAgICAgICAgfVxuICAgICAgfVxuXG4gICAgICBmaWVsZE5hbWVzLnB1c2goZmllbGQubmFtZSlcbiAgICAgIGlmIChmaWVsZC5sb2NhdGlvbiA9PT0gJ3F1ZXJ5Jykge1xuICAgICAgICBxdWVyeVBhcmFtc1tmaWVsZC5uYW1lXSA9IHBhcmFtc1tmaWVsZC5uYW1lXVxuICAgICAgfSBlbHNlIGlmIChmaWVsZC5sb2NhdGlvbiA9PT0gJ3BhdGgnKSB7XG4gICAgICAgIHBhdGhQYXJhbXNbZmllbGQubmFtZV0gPSBwYXJhbXNbZmllbGQubmFtZV1cbiAgICAgIH0gZWxzZSBpZiAoZmllbGQubG9jYXRpb24gPT09ICdmb3JtJykge1xuICAgICAgICBmb3JtUGFyYW1zW2ZpZWxkLm5hbWVdID0gcGFyYW1zW2ZpZWxkLm5hbWVdXG4gICAgICAgIGhhc0JvZHkgPSB0cnVlXG4gICAgICB9IGVsc2UgaWYgKGZpZWxkLmxvY2F0aW9uID09PSAnYm9keScpIHtcbiAgICAgICAgZm9ybVBhcmFtcyA9IHBhcmFtc1tmaWVsZC5uYW1lXVxuICAgICAgICBoYXNCb2R5ID0gdHJ1ZVxuICAgICAgfVxuICAgIH1cblxuICAgIC8vIENoZWNrIGZvciBhbnkgcGFyYW1ldGVycyB0aGF0IGRpZCBub3QgaGF2ZSBhIG1hdGNoaW5nIGZpZWxkXG4gICAgZm9yICh2YXIgcHJvcGVydHkgaW4gcGFyYW1zKSB7XG4gICAgICBpZiAocGFyYW1zLmhhc093blByb3BlcnR5KHByb3BlcnR5KSAmJiAhZmllbGROYW1lcy5pbmNsdWRlcyhwcm9wZXJ0eSkpIHtcbiAgICAgICAgdGhyb3cgbmV3IGVycm9ycy5QYXJhbWV0ZXJFcnJvcihgVW5rbm93biBwYXJhbWV0ZXI6IFwiJHtwcm9wZXJ0eX1cImApXG4gICAgICB9XG4gICAgfVxuXG4gICAgbGV0IHJlcXVlc3RPcHRpb25zID0ge21ldGhvZDogbWV0aG9kLCBoZWFkZXJzOiB7fX1cblxuICAgIE9iamVjdC5hc3NpZ24ocmVxdWVzdE9wdGlvbnMuaGVhZGVycywgdGhpcy5oZWFkZXJzKVxuXG4gICAgaWYgKGhhc0JvZHkpIHtcbiAgICAgIGlmIChsaW5rLmVuY29kaW5nID09PSAnYXBwbGljYXRpb24vanNvbicpIHtcbiAgICAgICAgcmVxdWVzdE9wdGlvbnMuYm9keSA9IEpTT04uc3RyaW5naWZ5KGZvcm1QYXJhbXMpXG4gICAgICAgIHJlcXVlc3RPcHRpb25zLmhlYWRlcnNbJ0NvbnRlbnQtVHlwZSddID0gJ2FwcGxpY2F0aW9uL2pzb24nXG4gICAgICB9IGVsc2UgaWYgKGxpbmsuZW5jb2RpbmcgPT09ICdtdWx0aXBhcnQvZm9ybS1kYXRhJykge1xuICAgICAgICBsZXQgZm9ybSA9IG5ldyB0aGlzLkZvcm1EYXRhKClcblxuICAgICAgICBmb3IgKGxldCBwYXJhbUtleSBpbiBmb3JtUGFyYW1zKSB7XG4gICAgICAgICAgZm9ybS5hcHBlbmQocGFyYW1LZXksIGZvcm1QYXJhbXNbcGFyYW1LZXldKVxuICAgICAgICB9XG4gICAgICAgIHJlcXVlc3RPcHRpb25zLmJvZHkgPSBmb3JtXG4gICAgICB9IGVsc2UgaWYgKGxpbmsuZW5jb2RpbmcgPT09ICdhcHBsaWNhdGlvbi94LXd3dy1mb3JtLXVybGVuY29kZWQnKSB7XG4gICAgICAgIGxldCBmb3JtQm9keSA9IFtdXG4gICAgICAgIGZvciAobGV0IHBhcmFtS2V5IGluIGZvcm1QYXJhbXMpIHtcbiAgICAgICAgICBjb25zdCBlbmNvZGVkS2V5ID0gZW5jb2RlVVJJQ29tcG9uZW50KHBhcmFtS2V5KVxuICAgICAgICAgIGNvbnN0IGVuY29kZWRWYWx1ZSA9IGVuY29kZVVSSUNvbXBvbmVudChmb3JtUGFyYW1zW3BhcmFtS2V5XSlcbiAgICAgICAgICBmb3JtQm9keS5wdXNoKGVuY29kZWRLZXkgKyAnPScgKyBlbmNvZGVkVmFsdWUpXG4gICAgICAgIH1cbiAgICAgICAgZm9ybUJvZHkgPSBmb3JtQm9keS5qb2luKCcmJylcblxuICAgICAgICByZXF1ZXN0T3B0aW9ucy5ib2R5ID0gZm9ybUJvZHlcbiAgICAgICAgcmVxdWVzdE9wdGlvbnMuaGVhZGVyc1snQ29udGVudC1UeXBlJ10gPSAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkJ1xuICAgICAgfVxuICAgIH1cblxuICAgIGlmICh0aGlzLmNzcmYpIHtcbiAgICAgIHJlcXVlc3RPcHRpb25zLmNyZWRlbnRpYWxzID0gJ3NhbWUtb3JpZ2luJ1xuICAgICAgaWYgKCF1dGlscy5jc3JmU2FmZU1ldGhvZChtZXRob2QpKSB7XG4gICAgICAgIE9iamVjdC5hc3NpZ24ocmVxdWVzdE9wdGlvbnMuaGVhZGVycywgdGhpcy5jc3JmKVxuICAgICAgfVxuICAgIH1cblxuICAgIGxldCBwYXJzZWRVcmwgPSB1cmxUZW1wbGF0ZS5wYXJzZShsaW5rLnVybClcbiAgICBwYXJzZWRVcmwgPSBwYXJzZWRVcmwuZXhwYW5kKHBhdGhQYXJhbXMpXG4gICAgcGFyc2VkVXJsID0gbmV3IFVSTChwYXJzZWRVcmwpXG4gICAgcGFyc2VkVXJsLnNldCgncXVlcnknLCBxdWVyeVBhcmFtcylcblxuICAgIHJldHVybiB7XG4gICAgICB1cmw6IHBhcnNlZFVybC50b1N0cmluZygpLFxuICAgICAgb3B0aW9uczogcmVxdWVzdE9wdGlvbnNcbiAgICB9XG4gIH1cblxuICBhY3Rpb24gKGxpbmssIGRlY29kZXJzLCBwYXJhbXMgPSB7fSkge1xuICAgIGNvbnN0IHJlc3BvbnNlQ2FsbGJhY2sgPSB0aGlzLnJlc3BvbnNlQ2FsbGJhY2tcbiAgICBjb25zdCByZXF1ZXN0ID0gdGhpcy5idWlsZFJlcXVlc3QobGluaywgZGVjb2RlcnMsIHBhcmFtcylcblxuICAgIGlmICh0aGlzLnJlcXVlc3RDYWxsYmFjaykge1xuICAgICAgdGhpcy5yZXF1ZXN0Q2FsbGJhY2socmVxdWVzdClcbiAgICB9XG5cbiAgICByZXR1cm4gdGhpcy5mZXRjaChyZXF1ZXN0LnVybCwgcmVxdWVzdC5vcHRpb25zKVxuICAgICAgLnRoZW4oZnVuY3Rpb24gKHJlc3BvbnNlKSB7XG4gICAgICAgIGlmIChyZXNwb25zZUNhbGxiYWNrKSB7XG4gICAgICAgICAgcmVzcG9uc2VDYWxsYmFjayhyZXNwb25zZSlcbiAgICAgICAgfVxuXG4gICAgICAgIHJldHVybiBwYXJzZVJlc3BvbnNlKHJlc3BvbnNlLCBkZWNvZGVycylcbiAgICAgICAgICAudGhlbihmdW5jdGlvbiAoZGF0YSkge1xuICAgICAgICAgICAgaWYgKHJlc3BvbnNlLm9rKSB7XG4gICAgICAgICAgICAgIHJldHVybiBkYXRhXG4gICAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgICBjb25zdCB0aXRsZSA9IHJlc3BvbnNlLnN0YXR1cyArICcgJyArIHJlc3BvbnNlLnN0YXR1c1RleHRcbiAgICAgICAgICAgICAgY29uc3QgZXJyb3IgPSBuZXcgZXJyb3JzLkVycm9yTWVzc2FnZSh0aXRsZSwgZGF0YSlcbiAgICAgICAgICAgICAgcmV0dXJuIFByb21pc2UucmVqZWN0KGVycm9yKVxuICAgICAgICAgICAgfVxuICAgICAgICAgIH0pXG4gICAgICB9KVxuICB9XG59XG5cbm1vZHVsZS5leHBvcnRzID0ge1xuICBIVFRQVHJhbnNwb3J0OiBIVFRQVHJhbnNwb3J0XG59XG4iLCJjb25zdCBodHRwID0gcmVxdWlyZSgnLi9odHRwJylcblxubW9kdWxlLmV4cG9ydHMgPSB7XG4gIEhUVFBUcmFuc3BvcnQ6IGh0dHAuSFRUUFRyYW5zcG9ydFxufVxuIiwiY29uc3QgVVJMID0gcmVxdWlyZSgndXJsLXBhcnNlJylcblxuY29uc3QgZGV0ZXJtaW5lVHJhbnNwb3J0ID0gZnVuY3Rpb24gKHRyYW5zcG9ydHMsIHVybCkge1xuICBjb25zdCBwYXJzZWRVcmwgPSBuZXcgVVJMKHVybClcbiAgY29uc3Qgc2NoZW1lID0gcGFyc2VkVXJsLnByb3RvY29sLnJlcGxhY2UoJzonLCAnJylcblxuICBmb3IgKGxldCB0cmFuc3BvcnQgb2YgdHJhbnNwb3J0cykge1xuICAgIGlmICh0cmFuc3BvcnQuc2NoZW1lcy5pbmNsdWRlcyhzY2hlbWUpKSB7XG4gICAgICByZXR1cm4gdHJhbnNwb3J0XG4gICAgfVxuICB9XG5cbiAgdGhyb3cgRXJyb3IoYFVuc3VwcG9ydGVkIHNjaGVtZSBpbiBVUkw6ICR7dXJsfWApXG59XG5cbmNvbnN0IG5lZ290aWF0ZURlY29kZXIgPSBmdW5jdGlvbiAoZGVjb2RlcnMsIGNvbnRlbnRUeXBlKSB7XG4gIGlmIChjb250ZW50VHlwZSA9PT0gdW5kZWZpbmVkKSB7XG4gICAgcmV0dXJuIGRlY29kZXJzWzBdXG4gIH1cblxuICBjb25zdCBmdWxsVHlwZSA9IGNvbnRlbnRUeXBlLnRvTG93ZXJDYXNlKCkuc3BsaXQoJzsnKVswXS50cmltKClcbiAgY29uc3QgbWFpblR5cGUgPSBmdWxsVHlwZS5zcGxpdCgnLycpWzBdICsgJy8qJ1xuICBjb25zdCB3aWxkY2FyZFR5cGUgPSAnKi8qJ1xuICBjb25zdCBhY2NlcHRhYmxlVHlwZXMgPSBbZnVsbFR5cGUsIG1haW5UeXBlLCB3aWxkY2FyZFR5cGVdXG5cbiAgZm9yIChsZXQgZGVjb2RlciBvZiBkZWNvZGVycykge1xuICAgIGlmIChhY2NlcHRhYmxlVHlwZXMuaW5jbHVkZXMoZGVjb2Rlci5tZWRpYVR5cGUpKSB7XG4gICAgICByZXR1cm4gZGVjb2RlclxuICAgIH1cbiAgfVxuXG4gIHRocm93IEVycm9yKGBVbnN1cHBvcnRlZCBtZWRpYSBpbiBDb250ZW50LVR5cGUgaGVhZGVyOiAke2NvbnRlbnRUeXBlfWApXG59XG5cbmNvbnN0IGNzcmZTYWZlTWV0aG9kID0gZnVuY3Rpb24gKG1ldGhvZCkge1xuICAvLyB0aGVzZSBIVFRQIG1ldGhvZHMgZG8gbm90IHJlcXVpcmUgQ1NSRiBwcm90ZWN0aW9uXG4gIHJldHVybiAoL14oR0VUfEhFQUR8T1BUSU9OU3xUUkFDRSkkLy50ZXN0KG1ldGhvZCkpXG59XG5cbm1vZHVsZS5leHBvcnRzID0ge1xuICBkZXRlcm1pbmVUcmFuc3BvcnQ6IGRldGVybWluZVRyYW5zcG9ydCxcbiAgbmVnb3RpYXRlRGVjb2RlcjogbmVnb3RpYXRlRGVjb2RlcixcbiAgY3NyZlNhZmVNZXRob2Q6IGNzcmZTYWZlTWV0aG9kXG59XG4iLCIvLyB0aGUgd2hhdHdnLWZldGNoIHBvbHlmaWxsIGluc3RhbGxzIHRoZSBmZXRjaCgpIGZ1bmN0aW9uXG4vLyBvbiB0aGUgZ2xvYmFsIG9iamVjdCAod2luZG93IG9yIHNlbGYpXG4vL1xuLy8gUmV0dXJuIHRoYXQgYXMgdGhlIGV4cG9ydCBmb3IgdXNlIGluIFdlYnBhY2ssIEJyb3dzZXJpZnkgZXRjLlxucmVxdWlyZSgnd2hhdHdnLWZldGNoJyk7XG5tb2R1bGUuZXhwb3J0cyA9IHNlbGYuZmV0Y2guYmluZChzZWxmKTtcbiIsIid1c2Ugc3RyaWN0JztcblxudmFyIGhhcyA9IE9iamVjdC5wcm90b3R5cGUuaGFzT3duUHJvcGVydHk7XG5cbi8qKlxuICogU2ltcGxlIHF1ZXJ5IHN0cmluZyBwYXJzZXIuXG4gKlxuICogQHBhcmFtIHtTdHJpbmd9IHF1ZXJ5IFRoZSBxdWVyeSBzdHJpbmcgdGhhdCBuZWVkcyB0byBiZSBwYXJzZWQuXG4gKiBAcmV0dXJucyB7T2JqZWN0fVxuICogQGFwaSBwdWJsaWNcbiAqL1xuZnVuY3Rpb24gcXVlcnlzdHJpbmcocXVlcnkpIHtcbiAgdmFyIHBhcnNlciA9IC8oW149PyZdKyk9PyhbXiZdKikvZ1xuICAgICwgcmVzdWx0ID0ge31cbiAgICAsIHBhcnQ7XG5cbiAgLy9cbiAgLy8gTGl0dGxlIG5pZnR5IHBhcnNpbmcgaGFjaywgbGV2ZXJhZ2UgdGhlIGZhY3QgdGhhdCBSZWdFeHAuZXhlYyBpbmNyZW1lbnRzXG4gIC8vIHRoZSBsYXN0SW5kZXggcHJvcGVydHkgc28gd2UgY2FuIGNvbnRpbnVlIGV4ZWN1dGluZyB0aGlzIGxvb3AgdW50aWwgd2UndmVcbiAgLy8gcGFyc2VkIGFsbCByZXN1bHRzLlxuICAvL1xuICBmb3IgKDtcbiAgICBwYXJ0ID0gcGFyc2VyLmV4ZWMocXVlcnkpO1xuICAgIHJlc3VsdFtkZWNvZGVVUklDb21wb25lbnQocGFydFsxXSldID0gZGVjb2RlVVJJQ29tcG9uZW50KHBhcnRbMl0pXG4gICk7XG5cbiAgcmV0dXJuIHJlc3VsdDtcbn1cblxuLyoqXG4gKiBUcmFuc2Zvcm0gYSBxdWVyeSBzdHJpbmcgdG8gYW4gb2JqZWN0LlxuICpcbiAqIEBwYXJhbSB7T2JqZWN0fSBvYmogT2JqZWN0IHRoYXQgc2hvdWxkIGJlIHRyYW5zZm9ybWVkLlxuICogQHBhcmFtIHtTdHJpbmd9IHByZWZpeCBPcHRpb25hbCBwcmVmaXguXG4gKiBAcmV0dXJucyB7U3RyaW5nfVxuICogQGFwaSBwdWJsaWNcbiAqL1xuZnVuY3Rpb24gcXVlcnlzdHJpbmdpZnkob2JqLCBwcmVmaXgpIHtcbiAgcHJlZml4ID0gcHJlZml4IHx8ICcnO1xuXG4gIHZhciBwYWlycyA9IFtdO1xuXG4gIC8vXG4gIC8vIE9wdGlvbmFsbHkgcHJlZml4IHdpdGggYSAnPycgaWYgbmVlZGVkXG4gIC8vXG4gIGlmICgnc3RyaW5nJyAhPT0gdHlwZW9mIHByZWZpeCkgcHJlZml4ID0gJz8nO1xuXG4gIGZvciAodmFyIGtleSBpbiBvYmopIHtcbiAgICBpZiAoaGFzLmNhbGwob2JqLCBrZXkpKSB7XG4gICAgICBwYWlycy5wdXNoKGVuY29kZVVSSUNvbXBvbmVudChrZXkpICsnPScrIGVuY29kZVVSSUNvbXBvbmVudChvYmpba2V5XSkpO1xuICAgIH1cbiAgfVxuXG4gIHJldHVybiBwYWlycy5sZW5ndGggPyBwcmVmaXggKyBwYWlycy5qb2luKCcmJykgOiAnJztcbn1cblxuLy9cbi8vIEV4cG9zZSB0aGUgbW9kdWxlLlxuLy9cbmV4cG9ydHMuc3RyaW5naWZ5ID0gcXVlcnlzdHJpbmdpZnk7XG5leHBvcnRzLnBhcnNlID0gcXVlcnlzdHJpbmc7XG4iLCIndXNlIHN0cmljdCc7XG5cbi8qKlxuICogQ2hlY2sgaWYgd2UncmUgcmVxdWlyZWQgdG8gYWRkIGEgcG9ydCBudW1iZXIuXG4gKlxuICogQHNlZSBodHRwczovL3VybC5zcGVjLndoYXR3Zy5vcmcvI2RlZmF1bHQtcG9ydFxuICogQHBhcmFtIHtOdW1iZXJ8U3RyaW5nfSBwb3J0IFBvcnQgbnVtYmVyIHdlIG5lZWQgdG8gY2hlY2tcbiAqIEBwYXJhbSB7U3RyaW5nfSBwcm90b2NvbCBQcm90b2NvbCB3ZSBuZWVkIHRvIGNoZWNrIGFnYWluc3QuXG4gKiBAcmV0dXJucyB7Qm9vbGVhbn0gSXMgaXQgYSBkZWZhdWx0IHBvcnQgZm9yIHRoZSBnaXZlbiBwcm90b2NvbFxuICogQGFwaSBwcml2YXRlXG4gKi9cbm1vZHVsZS5leHBvcnRzID0gZnVuY3Rpb24gcmVxdWlyZWQocG9ydCwgcHJvdG9jb2wpIHtcbiAgcHJvdG9jb2wgPSBwcm90b2NvbC5zcGxpdCgnOicpWzBdO1xuICBwb3J0ID0gK3BvcnQ7XG5cbiAgaWYgKCFwb3J0KSByZXR1cm4gZmFsc2U7XG5cbiAgc3dpdGNoIChwcm90b2NvbCkge1xuICAgIGNhc2UgJ2h0dHAnOlxuICAgIGNhc2UgJ3dzJzpcbiAgICByZXR1cm4gcG9ydCAhPT0gODA7XG5cbiAgICBjYXNlICdodHRwcyc6XG4gICAgY2FzZSAnd3NzJzpcbiAgICByZXR1cm4gcG9ydCAhPT0gNDQzO1xuXG4gICAgY2FzZSAnZnRwJzpcbiAgICByZXR1cm4gcG9ydCAhPT0gMjE7XG5cbiAgICBjYXNlICdnb3BoZXInOlxuICAgIHJldHVybiBwb3J0ICE9PSA3MDtcblxuICAgIGNhc2UgJ2ZpbGUnOlxuICAgIHJldHVybiBmYWxzZTtcbiAgfVxuXG4gIHJldHVybiBwb3J0ICE9PSAwO1xufTtcbiIsIid1c2Ugc3RyaWN0JztcblxudmFyIHJlcXVpcmVkID0gcmVxdWlyZSgncmVxdWlyZXMtcG9ydCcpXG4gICwgbG9sY2F0aW9uID0gcmVxdWlyZSgnLi9sb2xjYXRpb24nKVxuICAsIHFzID0gcmVxdWlyZSgncXVlcnlzdHJpbmdpZnknKVxuICAsIHByb3RvY29scmUgPSAvXihbYS16XVthLXowLTkuKy1dKjopPyhcXC9cXC8pPyhbXFxTXFxzXSopL2k7XG5cbi8qKlxuICogVGhlc2UgYXJlIHRoZSBwYXJzZSBydWxlcyBmb3IgdGhlIFVSTCBwYXJzZXIsIGl0IGluZm9ybXMgdGhlIHBhcnNlclxuICogYWJvdXQ6XG4gKlxuICogMC4gVGhlIGNoYXIgaXQgTmVlZHMgdG8gcGFyc2UsIGlmIGl0J3MgYSBzdHJpbmcgaXQgc2hvdWxkIGJlIGRvbmUgdXNpbmdcbiAqICAgIGluZGV4T2YsIFJlZ0V4cCB1c2luZyBleGVjIGFuZCBOYU4gbWVhbnMgc2V0IGFzIGN1cnJlbnQgdmFsdWUuXG4gKiAxLiBUaGUgcHJvcGVydHkgd2Ugc2hvdWxkIHNldCB3aGVuIHBhcnNpbmcgdGhpcyB2YWx1ZS5cbiAqIDIuIEluZGljYXRpb24gaWYgaXQncyBiYWNrd2FyZHMgb3IgZm9yd2FyZCBwYXJzaW5nLCB3aGVuIHNldCBhcyBudW1iZXIgaXQnc1xuICogICAgdGhlIHZhbHVlIG9mIGV4dHJhIGNoYXJzIHRoYXQgc2hvdWxkIGJlIHNwbGl0IG9mZi5cbiAqIDMuIEluaGVyaXQgZnJvbSBsb2NhdGlvbiBpZiBub24gZXhpc3RpbmcgaW4gdGhlIHBhcnNlci5cbiAqIDQuIGB0b0xvd2VyQ2FzZWAgdGhlIHJlc3VsdGluZyB2YWx1ZS5cbiAqL1xudmFyIHJ1bGVzID0gW1xuICBbJyMnLCAnaGFzaCddLCAgICAgICAgICAgICAgICAgICAgICAgIC8vIEV4dHJhY3QgZnJvbSB0aGUgYmFjay5cbiAgWyc/JywgJ3F1ZXJ5J10sICAgICAgICAgICAgICAgICAgICAgICAvLyBFeHRyYWN0IGZyb20gdGhlIGJhY2suXG4gIFsnLycsICdwYXRobmFtZSddLCAgICAgICAgICAgICAgICAgICAgLy8gRXh0cmFjdCBmcm9tIHRoZSBiYWNrLlxuICBbJ0AnLCAnYXV0aCcsIDFdLCAgICAgICAgICAgICAgICAgICAgIC8vIEV4dHJhY3QgZnJvbSB0aGUgZnJvbnQuXG4gIFtOYU4sICdob3N0JywgdW5kZWZpbmVkLCAxLCAxXSwgICAgICAgLy8gU2V0IGxlZnQgb3ZlciB2YWx1ZS5cbiAgWy86KFxcZCspJC8sICdwb3J0JywgdW5kZWZpbmVkLCAxXSwgICAgLy8gUmVnRXhwIHRoZSBiYWNrLlxuICBbTmFOLCAnaG9zdG5hbWUnLCB1bmRlZmluZWQsIDEsIDFdICAgIC8vIFNldCBsZWZ0IG92ZXIuXG5dO1xuXG4vKipcbiAqIEB0eXBlZGVmIFByb3RvY29sRXh0cmFjdFxuICogQHR5cGUgT2JqZWN0XG4gKiBAcHJvcGVydHkge1N0cmluZ30gcHJvdG9jb2wgUHJvdG9jb2wgbWF0Y2hlZCBpbiB0aGUgVVJMLCBpbiBsb3dlcmNhc2UuXG4gKiBAcHJvcGVydHkge0Jvb2xlYW59IHNsYXNoZXMgYHRydWVgIGlmIHByb3RvY29sIGlzIGZvbGxvd2VkIGJ5IFwiLy9cIiwgZWxzZSBgZmFsc2VgLlxuICogQHByb3BlcnR5IHtTdHJpbmd9IHJlc3QgUmVzdCBvZiB0aGUgVVJMIHRoYXQgaXMgbm90IHBhcnQgb2YgdGhlIHByb3RvY29sLlxuICovXG5cbi8qKlxuICogRXh0cmFjdCBwcm90b2NvbCBpbmZvcm1hdGlvbiBmcm9tIGEgVVJMIHdpdGgvd2l0aG91dCBkb3VibGUgc2xhc2ggKFwiLy9cIikuXG4gKlxuICogQHBhcmFtIHtTdHJpbmd9IGFkZHJlc3MgVVJMIHdlIHdhbnQgdG8gZXh0cmFjdCBmcm9tLlxuICogQHJldHVybiB7UHJvdG9jb2xFeHRyYWN0fSBFeHRyYWN0ZWQgaW5mb3JtYXRpb24uXG4gKiBAYXBpIHByaXZhdGVcbiAqL1xuZnVuY3Rpb24gZXh0cmFjdFByb3RvY29sKGFkZHJlc3MpIHtcbiAgdmFyIG1hdGNoID0gcHJvdG9jb2xyZS5leGVjKGFkZHJlc3MpO1xuXG4gIHJldHVybiB7XG4gICAgcHJvdG9jb2w6IG1hdGNoWzFdID8gbWF0Y2hbMV0udG9Mb3dlckNhc2UoKSA6ICcnLFxuICAgIHNsYXNoZXM6ICEhbWF0Y2hbMl0sXG4gICAgcmVzdDogbWF0Y2hbM11cbiAgfTtcbn1cblxuLyoqXG4gKiBSZXNvbHZlIGEgcmVsYXRpdmUgVVJMIHBhdGhuYW1lIGFnYWluc3QgYSBiYXNlIFVSTCBwYXRobmFtZS5cbiAqXG4gKiBAcGFyYW0ge1N0cmluZ30gcmVsYXRpdmUgUGF0aG5hbWUgb2YgdGhlIHJlbGF0aXZlIFVSTC5cbiAqIEBwYXJhbSB7U3RyaW5nfSBiYXNlIFBhdGhuYW1lIG9mIHRoZSBiYXNlIFVSTC5cbiAqIEByZXR1cm4ge1N0cmluZ30gUmVzb2x2ZWQgcGF0aG5hbWUuXG4gKiBAYXBpIHByaXZhdGVcbiAqL1xuZnVuY3Rpb24gcmVzb2x2ZShyZWxhdGl2ZSwgYmFzZSkge1xuICB2YXIgcGF0aCA9IChiYXNlIHx8ICcvJykuc3BsaXQoJy8nKS5zbGljZSgwLCAtMSkuY29uY2F0KHJlbGF0aXZlLnNwbGl0KCcvJykpXG4gICAgLCBpID0gcGF0aC5sZW5ndGhcbiAgICAsIGxhc3QgPSBwYXRoW2kgLSAxXVxuICAgICwgdW5zaGlmdCA9IGZhbHNlXG4gICAgLCB1cCA9IDA7XG5cbiAgd2hpbGUgKGktLSkge1xuICAgIGlmIChwYXRoW2ldID09PSAnLicpIHtcbiAgICAgIHBhdGguc3BsaWNlKGksIDEpO1xuICAgIH0gZWxzZSBpZiAocGF0aFtpXSA9PT0gJy4uJykge1xuICAgICAgcGF0aC5zcGxpY2UoaSwgMSk7XG4gICAgICB1cCsrO1xuICAgIH0gZWxzZSBpZiAodXApIHtcbiAgICAgIGlmIChpID09PSAwKSB1bnNoaWZ0ID0gdHJ1ZTtcbiAgICAgIHBhdGguc3BsaWNlKGksIDEpO1xuICAgICAgdXAtLTtcbiAgICB9XG4gIH1cblxuICBpZiAodW5zaGlmdCkgcGF0aC51bnNoaWZ0KCcnKTtcbiAgaWYgKGxhc3QgPT09ICcuJyB8fCBsYXN0ID09PSAnLi4nKSBwYXRoLnB1c2goJycpO1xuXG4gIHJldHVybiBwYXRoLmpvaW4oJy8nKTtcbn1cblxuLyoqXG4gKiBUaGUgYWN0dWFsIFVSTCBpbnN0YW5jZS4gSW5zdGVhZCBvZiByZXR1cm5pbmcgYW4gb2JqZWN0IHdlJ3ZlIG9wdGVkLWluIHRvXG4gKiBjcmVhdGUgYW4gYWN0dWFsIGNvbnN0cnVjdG9yIGFzIGl0J3MgbXVjaCBtb3JlIG1lbW9yeSBlZmZpY2llbnQgYW5kXG4gKiBmYXN0ZXIgYW5kIGl0IHBsZWFzZXMgbXkgT0NELlxuICpcbiAqIEBjb25zdHJ1Y3RvclxuICogQHBhcmFtIHtTdHJpbmd9IGFkZHJlc3MgVVJMIHdlIHdhbnQgdG8gcGFyc2UuXG4gKiBAcGFyYW0ge09iamVjdHxTdHJpbmd9IGxvY2F0aW9uIExvY2F0aW9uIGRlZmF1bHRzIGZvciByZWxhdGl2ZSBwYXRocy5cbiAqIEBwYXJhbSB7Qm9vbGVhbnxGdW5jdGlvbn0gcGFyc2VyIFBhcnNlciBmb3IgdGhlIHF1ZXJ5IHN0cmluZy5cbiAqIEBhcGkgcHVibGljXG4gKi9cbmZ1bmN0aW9uIFVSTChhZGRyZXNzLCBsb2NhdGlvbiwgcGFyc2VyKSB7XG4gIGlmICghKHRoaXMgaW5zdGFuY2VvZiBVUkwpKSB7XG4gICAgcmV0dXJuIG5ldyBVUkwoYWRkcmVzcywgbG9jYXRpb24sIHBhcnNlcik7XG4gIH1cblxuICB2YXIgcmVsYXRpdmUsIGV4dHJhY3RlZCwgcGFyc2UsIGluc3RydWN0aW9uLCBpbmRleCwga2V5XG4gICAgLCBpbnN0cnVjdGlvbnMgPSBydWxlcy5zbGljZSgpXG4gICAgLCB0eXBlID0gdHlwZW9mIGxvY2F0aW9uXG4gICAgLCB1cmwgPSB0aGlzXG4gICAgLCBpID0gMDtcblxuICAvL1xuICAvLyBUaGUgZm9sbG93aW5nIGlmIHN0YXRlbWVudHMgYWxsb3dzIHRoaXMgbW9kdWxlIHR3byBoYXZlIGNvbXBhdGliaWxpdHkgd2l0aFxuICAvLyAyIGRpZmZlcmVudCBBUEk6XG4gIC8vXG4gIC8vIDEuIE5vZGUuanMncyBgdXJsLnBhcnNlYCBhcGkgd2hpY2ggYWNjZXB0cyBhIFVSTCwgYm9vbGVhbiBhcyBhcmd1bWVudHNcbiAgLy8gICAgd2hlcmUgdGhlIGJvb2xlYW4gaW5kaWNhdGVzIHRoYXQgdGhlIHF1ZXJ5IHN0cmluZyBzaG91bGQgYWxzbyBiZSBwYXJzZWQuXG4gIC8vXG4gIC8vIDIuIFRoZSBgVVJMYCBpbnRlcmZhY2Ugb2YgdGhlIGJyb3dzZXIgd2hpY2ggYWNjZXB0cyBhIFVSTCwgb2JqZWN0IGFzXG4gIC8vICAgIGFyZ3VtZW50cy4gVGhlIHN1cHBsaWVkIG9iamVjdCB3aWxsIGJlIHVzZWQgYXMgZGVmYXVsdCB2YWx1ZXMgLyBmYWxsLWJhY2tcbiAgLy8gICAgZm9yIHJlbGF0aXZlIHBhdGhzLlxuICAvL1xuICBpZiAoJ29iamVjdCcgIT09IHR5cGUgJiYgJ3N0cmluZycgIT09IHR5cGUpIHtcbiAgICBwYXJzZXIgPSBsb2NhdGlvbjtcbiAgICBsb2NhdGlvbiA9IG51bGw7XG4gIH1cblxuICBpZiAocGFyc2VyICYmICdmdW5jdGlvbicgIT09IHR5cGVvZiBwYXJzZXIpIHBhcnNlciA9IHFzLnBhcnNlO1xuXG4gIGxvY2F0aW9uID0gbG9sY2F0aW9uKGxvY2F0aW9uKTtcblxuICAvL1xuICAvLyBFeHRyYWN0IHByb3RvY29sIGluZm9ybWF0aW9uIGJlZm9yZSBydW5uaW5nIHRoZSBpbnN0cnVjdGlvbnMuXG4gIC8vXG4gIGV4dHJhY3RlZCA9IGV4dHJhY3RQcm90b2NvbChhZGRyZXNzIHx8ICcnKTtcbiAgcmVsYXRpdmUgPSAhZXh0cmFjdGVkLnByb3RvY29sICYmICFleHRyYWN0ZWQuc2xhc2hlcztcbiAgdXJsLnNsYXNoZXMgPSBleHRyYWN0ZWQuc2xhc2hlcyB8fCByZWxhdGl2ZSAmJiBsb2NhdGlvbi5zbGFzaGVzO1xuICB1cmwucHJvdG9jb2wgPSBleHRyYWN0ZWQucHJvdG9jb2wgfHwgbG9jYXRpb24ucHJvdG9jb2wgfHwgJyc7XG4gIGFkZHJlc3MgPSBleHRyYWN0ZWQucmVzdDtcblxuICAvL1xuICAvLyBXaGVuIHRoZSBhdXRob3JpdHkgY29tcG9uZW50IGlzIGFic2VudCB0aGUgVVJMIHN0YXJ0cyB3aXRoIGEgcGF0aFxuICAvLyBjb21wb25lbnQuXG4gIC8vXG4gIGlmICghZXh0cmFjdGVkLnNsYXNoZXMpIGluc3RydWN0aW9uc1syXSA9IFsvKC4qKS8sICdwYXRobmFtZSddO1xuXG4gIGZvciAoOyBpIDwgaW5zdHJ1Y3Rpb25zLmxlbmd0aDsgaSsrKSB7XG4gICAgaW5zdHJ1Y3Rpb24gPSBpbnN0cnVjdGlvbnNbaV07XG4gICAgcGFyc2UgPSBpbnN0cnVjdGlvblswXTtcbiAgICBrZXkgPSBpbnN0cnVjdGlvblsxXTtcblxuICAgIGlmIChwYXJzZSAhPT0gcGFyc2UpIHtcbiAgICAgIHVybFtrZXldID0gYWRkcmVzcztcbiAgICB9IGVsc2UgaWYgKCdzdHJpbmcnID09PSB0eXBlb2YgcGFyc2UpIHtcbiAgICAgIGlmICh+KGluZGV4ID0gYWRkcmVzcy5pbmRleE9mKHBhcnNlKSkpIHtcbiAgICAgICAgaWYgKCdudW1iZXInID09PSB0eXBlb2YgaW5zdHJ1Y3Rpb25bMl0pIHtcbiAgICAgICAgICB1cmxba2V5XSA9IGFkZHJlc3Muc2xpY2UoMCwgaW5kZXgpO1xuICAgICAgICAgIGFkZHJlc3MgPSBhZGRyZXNzLnNsaWNlKGluZGV4ICsgaW5zdHJ1Y3Rpb25bMl0pO1xuICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgIHVybFtrZXldID0gYWRkcmVzcy5zbGljZShpbmRleCk7XG4gICAgICAgICAgYWRkcmVzcyA9IGFkZHJlc3Muc2xpY2UoMCwgaW5kZXgpO1xuICAgICAgICB9XG4gICAgICB9XG4gICAgfSBlbHNlIGlmICgoaW5kZXggPSBwYXJzZS5leGVjKGFkZHJlc3MpKSkge1xuICAgICAgdXJsW2tleV0gPSBpbmRleFsxXTtcbiAgICAgIGFkZHJlc3MgPSBhZGRyZXNzLnNsaWNlKDAsIGluZGV4LmluZGV4KTtcbiAgICB9XG5cbiAgICB1cmxba2V5XSA9IHVybFtrZXldIHx8IChcbiAgICAgIHJlbGF0aXZlICYmIGluc3RydWN0aW9uWzNdID8gbG9jYXRpb25ba2V5XSB8fCAnJyA6ICcnXG4gICAgKTtcblxuICAgIC8vXG4gICAgLy8gSG9zdG5hbWUsIGhvc3QgYW5kIHByb3RvY29sIHNob3VsZCBiZSBsb3dlcmNhc2VkIHNvIHRoZXkgY2FuIGJlIHVzZWQgdG9cbiAgICAvLyBjcmVhdGUgYSBwcm9wZXIgYG9yaWdpbmAuXG4gICAgLy9cbiAgICBpZiAoaW5zdHJ1Y3Rpb25bNF0pIHVybFtrZXldID0gdXJsW2tleV0udG9Mb3dlckNhc2UoKTtcbiAgfVxuXG4gIC8vXG4gIC8vIEFsc28gcGFyc2UgdGhlIHN1cHBsaWVkIHF1ZXJ5IHN0cmluZyBpbiB0byBhbiBvYmplY3QuIElmIHdlJ3JlIHN1cHBsaWVkXG4gIC8vIHdpdGggYSBjdXN0b20gcGFyc2VyIGFzIGZ1bmN0aW9uIHVzZSB0aGF0IGluc3RlYWQgb2YgdGhlIGRlZmF1bHQgYnVpbGQtaW5cbiAgLy8gcGFyc2VyLlxuICAvL1xuICBpZiAocGFyc2VyKSB1cmwucXVlcnkgPSBwYXJzZXIodXJsLnF1ZXJ5KTtcblxuICAvL1xuICAvLyBJZiB0aGUgVVJMIGlzIHJlbGF0aXZlLCByZXNvbHZlIHRoZSBwYXRobmFtZSBhZ2FpbnN0IHRoZSBiYXNlIFVSTC5cbiAgLy9cbiAgaWYgKFxuICAgICAgcmVsYXRpdmVcbiAgICAmJiBsb2NhdGlvbi5zbGFzaGVzXG4gICAgJiYgdXJsLnBhdGhuYW1lLmNoYXJBdCgwKSAhPT0gJy8nXG4gICAgJiYgKHVybC5wYXRobmFtZSAhPT0gJycgfHwgbG9jYXRpb24ucGF0aG5hbWUgIT09ICcnKVxuICApIHtcbiAgICB1cmwucGF0aG5hbWUgPSByZXNvbHZlKHVybC5wYXRobmFtZSwgbG9jYXRpb24ucGF0aG5hbWUpO1xuICB9XG5cbiAgLy9cbiAgLy8gV2Ugc2hvdWxkIG5vdCBhZGQgcG9ydCBudW1iZXJzIGlmIHRoZXkgYXJlIGFscmVhZHkgdGhlIGRlZmF1bHQgcG9ydCBudW1iZXJcbiAgLy8gZm9yIGEgZ2l2ZW4gcHJvdG9jb2wuIEFzIHRoZSBob3N0IGFsc28gY29udGFpbnMgdGhlIHBvcnQgbnVtYmVyIHdlJ3JlIGdvaW5nXG4gIC8vIG92ZXJyaWRlIGl0IHdpdGggdGhlIGhvc3RuYW1lIHdoaWNoIGNvbnRhaW5zIG5vIHBvcnQgbnVtYmVyLlxuICAvL1xuICBpZiAoIXJlcXVpcmVkKHVybC5wb3J0LCB1cmwucHJvdG9jb2wpKSB7XG4gICAgdXJsLmhvc3QgPSB1cmwuaG9zdG5hbWU7XG4gICAgdXJsLnBvcnQgPSAnJztcbiAgfVxuXG4gIC8vXG4gIC8vIFBhcnNlIGRvd24gdGhlIGBhdXRoYCBmb3IgdGhlIHVzZXJuYW1lIGFuZCBwYXNzd29yZC5cbiAgLy9cbiAgdXJsLnVzZXJuYW1lID0gdXJsLnBhc3N3b3JkID0gJyc7XG4gIGlmICh1cmwuYXV0aCkge1xuICAgIGluc3RydWN0aW9uID0gdXJsLmF1dGguc3BsaXQoJzonKTtcbiAgICB1cmwudXNlcm5hbWUgPSBpbnN0cnVjdGlvblswXSB8fCAnJztcbiAgICB1cmwucGFzc3dvcmQgPSBpbnN0cnVjdGlvblsxXSB8fCAnJztcbiAgfVxuXG4gIHVybC5vcmlnaW4gPSB1cmwucHJvdG9jb2wgJiYgdXJsLmhvc3QgJiYgdXJsLnByb3RvY29sICE9PSAnZmlsZTonXG4gICAgPyB1cmwucHJvdG9jb2wgKycvLycrIHVybC5ob3N0XG4gICAgOiAnbnVsbCc7XG5cbiAgLy9cbiAgLy8gVGhlIGhyZWYgaXMganVzdCB0aGUgY29tcGlsZWQgcmVzdWx0LlxuICAvL1xuICB1cmwuaHJlZiA9IHVybC50b1N0cmluZygpO1xufVxuXG4vKipcbiAqIFRoaXMgaXMgY29udmVuaWVuY2UgbWV0aG9kIGZvciBjaGFuZ2luZyBwcm9wZXJ0aWVzIGluIHRoZSBVUkwgaW5zdGFuY2UgdG9cbiAqIGluc3VyZSB0aGF0IHRoZXkgYWxsIHByb3BhZ2F0ZSBjb3JyZWN0bHkuXG4gKlxuICogQHBhcmFtIHtTdHJpbmd9IHBhcnQgICAgICAgICAgUHJvcGVydHkgd2UgbmVlZCB0byBhZGp1c3QuXG4gKiBAcGFyYW0ge01peGVkfSB2YWx1ZSAgICAgICAgICBUaGUgbmV3bHkgYXNzaWduZWQgdmFsdWUuXG4gKiBAcGFyYW0ge0Jvb2xlYW58RnVuY3Rpb259IGZuICBXaGVuIHNldHRpbmcgdGhlIHF1ZXJ5LCBpdCB3aWxsIGJlIHRoZSBmdW5jdGlvblxuICogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgdXNlZCB0byBwYXJzZSB0aGUgcXVlcnkuXG4gKiAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICBXaGVuIHNldHRpbmcgdGhlIHByb3RvY29sLCBkb3VibGUgc2xhc2ggd2lsbCBiZVxuICogICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgcmVtb3ZlZCBmcm9tIHRoZSBmaW5hbCB1cmwgaWYgaXQgaXMgdHJ1ZS5cbiAqIEByZXR1cm5zIHtVUkx9XG4gKiBAYXBpIHB1YmxpY1xuICovXG5mdW5jdGlvbiBzZXQocGFydCwgdmFsdWUsIGZuKSB7XG4gIHZhciB1cmwgPSB0aGlzO1xuXG4gIHN3aXRjaCAocGFydCkge1xuICAgIGNhc2UgJ3F1ZXJ5JzpcbiAgICAgIGlmICgnc3RyaW5nJyA9PT0gdHlwZW9mIHZhbHVlICYmIHZhbHVlLmxlbmd0aCkge1xuICAgICAgICB2YWx1ZSA9IChmbiB8fCBxcy5wYXJzZSkodmFsdWUpO1xuICAgICAgfVxuXG4gICAgICB1cmxbcGFydF0gPSB2YWx1ZTtcbiAgICAgIGJyZWFrO1xuXG4gICAgY2FzZSAncG9ydCc6XG4gICAgICB1cmxbcGFydF0gPSB2YWx1ZTtcblxuICAgICAgaWYgKCFyZXF1aXJlZCh2YWx1ZSwgdXJsLnByb3RvY29sKSkge1xuICAgICAgICB1cmwuaG9zdCA9IHVybC5ob3N0bmFtZTtcbiAgICAgICAgdXJsW3BhcnRdID0gJyc7XG4gICAgICB9IGVsc2UgaWYgKHZhbHVlKSB7XG4gICAgICAgIHVybC5ob3N0ID0gdXJsLmhvc3RuYW1lICsnOicrIHZhbHVlO1xuICAgICAgfVxuXG4gICAgICBicmVhaztcblxuICAgIGNhc2UgJ2hvc3RuYW1lJzpcbiAgICAgIHVybFtwYXJ0XSA9IHZhbHVlO1xuXG4gICAgICBpZiAodXJsLnBvcnQpIHZhbHVlICs9ICc6JysgdXJsLnBvcnQ7XG4gICAgICB1cmwuaG9zdCA9IHZhbHVlO1xuICAgICAgYnJlYWs7XG5cbiAgICBjYXNlICdob3N0JzpcbiAgICAgIHVybFtwYXJ0XSA9IHZhbHVlO1xuXG4gICAgICBpZiAoLzpcXGQrJC8udGVzdCh2YWx1ZSkpIHtcbiAgICAgICAgdmFsdWUgPSB2YWx1ZS5zcGxpdCgnOicpO1xuICAgICAgICB1cmwucG9ydCA9IHZhbHVlLnBvcCgpO1xuICAgICAgICB1cmwuaG9zdG5hbWUgPSB2YWx1ZS5qb2luKCc6Jyk7XG4gICAgICB9IGVsc2Uge1xuICAgICAgICB1cmwuaG9zdG5hbWUgPSB2YWx1ZTtcbiAgICAgICAgdXJsLnBvcnQgPSAnJztcbiAgICAgIH1cblxuICAgICAgYnJlYWs7XG5cbiAgICBjYXNlICdwcm90b2NvbCc6XG4gICAgICB1cmwucHJvdG9jb2wgPSB2YWx1ZS50b0xvd2VyQ2FzZSgpO1xuICAgICAgdXJsLnNsYXNoZXMgPSAhZm47XG4gICAgICBicmVhaztcblxuICAgIGNhc2UgJ3BhdGhuYW1lJzpcbiAgICAgIHVybC5wYXRobmFtZSA9IHZhbHVlLmxlbmd0aCAmJiB2YWx1ZS5jaGFyQXQoMCkgIT09ICcvJyA/ICcvJyArIHZhbHVlIDogdmFsdWU7XG5cbiAgICAgIGJyZWFrO1xuXG4gICAgZGVmYXVsdDpcbiAgICAgIHVybFtwYXJ0XSA9IHZhbHVlO1xuICB9XG5cbiAgZm9yICh2YXIgaSA9IDA7IGkgPCBydWxlcy5sZW5ndGg7IGkrKykge1xuICAgIHZhciBpbnMgPSBydWxlc1tpXTtcblxuICAgIGlmIChpbnNbNF0pIHVybFtpbnNbMV1dID0gdXJsW2luc1sxXV0udG9Mb3dlckNhc2UoKTtcbiAgfVxuXG4gIHVybC5vcmlnaW4gPSB1cmwucHJvdG9jb2wgJiYgdXJsLmhvc3QgJiYgdXJsLnByb3RvY29sICE9PSAnZmlsZTonXG4gICAgPyB1cmwucHJvdG9jb2wgKycvLycrIHVybC5ob3N0XG4gICAgOiAnbnVsbCc7XG5cbiAgdXJsLmhyZWYgPSB1cmwudG9TdHJpbmcoKTtcblxuICByZXR1cm4gdXJsO1xufTtcblxuLyoqXG4gKiBUcmFuc2Zvcm0gdGhlIHByb3BlcnRpZXMgYmFjayBpbiB0byBhIHZhbGlkIGFuZCBmdWxsIFVSTCBzdHJpbmcuXG4gKlxuICogQHBhcmFtIHtGdW5jdGlvbn0gc3RyaW5naWZ5IE9wdGlvbmFsIHF1ZXJ5IHN0cmluZ2lmeSBmdW5jdGlvbi5cbiAqIEByZXR1cm5zIHtTdHJpbmd9XG4gKiBAYXBpIHB1YmxpY1xuICovXG5mdW5jdGlvbiB0b1N0cmluZyhzdHJpbmdpZnkpIHtcbiAgaWYgKCFzdHJpbmdpZnkgfHwgJ2Z1bmN0aW9uJyAhPT0gdHlwZW9mIHN0cmluZ2lmeSkgc3RyaW5naWZ5ID0gcXMuc3RyaW5naWZ5O1xuXG4gIHZhciBxdWVyeVxuICAgICwgdXJsID0gdGhpc1xuICAgICwgcHJvdG9jb2wgPSB1cmwucHJvdG9jb2w7XG5cbiAgaWYgKHByb3RvY29sICYmIHByb3RvY29sLmNoYXJBdChwcm90b2NvbC5sZW5ndGggLSAxKSAhPT0gJzonKSBwcm90b2NvbCArPSAnOic7XG5cbiAgdmFyIHJlc3VsdCA9IHByb3RvY29sICsgKHVybC5zbGFzaGVzID8gJy8vJyA6ICcnKTtcblxuICBpZiAodXJsLnVzZXJuYW1lKSB7XG4gICAgcmVzdWx0ICs9IHVybC51c2VybmFtZTtcbiAgICBpZiAodXJsLnBhc3N3b3JkKSByZXN1bHQgKz0gJzonKyB1cmwucGFzc3dvcmQ7XG4gICAgcmVzdWx0ICs9ICdAJztcbiAgfVxuXG4gIHJlc3VsdCArPSB1cmwuaG9zdCArIHVybC5wYXRobmFtZTtcblxuICBxdWVyeSA9ICdvYmplY3QnID09PSB0eXBlb2YgdXJsLnF1ZXJ5ID8gc3RyaW5naWZ5KHVybC5xdWVyeSkgOiB1cmwucXVlcnk7XG4gIGlmIChxdWVyeSkgcmVzdWx0ICs9ICc/JyAhPT0gcXVlcnkuY2hhckF0KDApID8gJz8nKyBxdWVyeSA6IHF1ZXJ5O1xuXG4gIGlmICh1cmwuaGFzaCkgcmVzdWx0ICs9IHVybC5oYXNoO1xuXG4gIHJldHVybiByZXN1bHQ7XG59XG5cblVSTC5wcm90b3R5cGUgPSB7IHNldDogc2V0LCB0b1N0cmluZzogdG9TdHJpbmcgfTtcblxuLy9cbi8vIEV4cG9zZSB0aGUgVVJMIHBhcnNlciBhbmQgc29tZSBhZGRpdGlvbmFsIHByb3BlcnRpZXMgdGhhdCBtaWdodCBiZSB1c2VmdWwgZm9yXG4vLyBvdGhlcnMgb3IgdGVzdGluZy5cbi8vXG5VUkwuZXh0cmFjdFByb3RvY29sID0gZXh0cmFjdFByb3RvY29sO1xuVVJMLmxvY2F0aW9uID0gbG9sY2F0aW9uO1xuVVJMLnFzID0gcXM7XG5cbm1vZHVsZS5leHBvcnRzID0gVVJMO1xuIiwiJ3VzZSBzdHJpY3QnO1xuXG52YXIgc2xhc2hlcyA9IC9eW0EtWmEtel1bQS1aYS16MC05Ky0uXSo6XFwvXFwvLztcblxuLyoqXG4gKiBUaGVzZSBwcm9wZXJ0aWVzIHNob3VsZCBub3QgYmUgY29waWVkIG9yIGluaGVyaXRlZCBmcm9tLiBUaGlzIGlzIG9ubHkgbmVlZGVkXG4gKiBmb3IgYWxsIG5vbiBibG9iIFVSTCdzIGFzIGEgYmxvYiBVUkwgZG9lcyBub3QgaW5jbHVkZSBhIGhhc2gsIG9ubHkgdGhlXG4gKiBvcmlnaW4uXG4gKlxuICogQHR5cGUge09iamVjdH1cbiAqIEBwcml2YXRlXG4gKi9cbnZhciBpZ25vcmUgPSB7IGhhc2g6IDEsIHF1ZXJ5OiAxIH1cbiAgLCBVUkw7XG5cbi8qKlxuICogVGhlIGxvY2F0aW9uIG9iamVjdCBkaWZmZXJzIHdoZW4geW91ciBjb2RlIGlzIGxvYWRlZCB0aHJvdWdoIGEgbm9ybWFsIHBhZ2UsXG4gKiBXb3JrZXIgb3IgdGhyb3VnaCBhIHdvcmtlciB1c2luZyBhIGJsb2IuIEFuZCB3aXRoIHRoZSBibG9iYmxlIGJlZ2lucyB0aGVcbiAqIHRyb3VibGUgYXMgdGhlIGxvY2F0aW9uIG9iamVjdCB3aWxsIGNvbnRhaW4gdGhlIFVSTCBvZiB0aGUgYmxvYiwgbm90IHRoZVxuICogbG9jYXRpb24gb2YgdGhlIHBhZ2Ugd2hlcmUgb3VyIGNvZGUgaXMgbG9hZGVkIGluLiBUaGUgYWN0dWFsIG9yaWdpbiBpc1xuICogZW5jb2RlZCBpbiB0aGUgYHBhdGhuYW1lYCBzbyB3ZSBjYW4gdGhhbmtmdWxseSBnZW5lcmF0ZSBhIGdvb2QgXCJkZWZhdWx0XCJcbiAqIGxvY2F0aW9uIGZyb20gaXQgc28gd2UgY2FuIGdlbmVyYXRlIHByb3BlciByZWxhdGl2ZSBVUkwncyBhZ2Fpbi5cbiAqXG4gKiBAcGFyYW0ge09iamVjdHxTdHJpbmd9IGxvYyBPcHRpb25hbCBkZWZhdWx0IGxvY2F0aW9uIG9iamVjdC5cbiAqIEByZXR1cm5zIHtPYmplY3R9IGxvbGNhdGlvbiBvYmplY3QuXG4gKiBAYXBpIHB1YmxpY1xuICovXG5tb2R1bGUuZXhwb3J0cyA9IGZ1bmN0aW9uIGxvbGNhdGlvbihsb2MpIHtcbiAgbG9jID0gbG9jIHx8IGdsb2JhbC5sb2NhdGlvbiB8fCB7fTtcbiAgVVJMID0gVVJMIHx8IHJlcXVpcmUoJy4vJyk7XG5cbiAgdmFyIGZpbmFsZGVzdGluYXRpb24gPSB7fVxuICAgICwgdHlwZSA9IHR5cGVvZiBsb2NcbiAgICAsIGtleTtcblxuICBpZiAoJ2Jsb2I6JyA9PT0gbG9jLnByb3RvY29sKSB7XG4gICAgZmluYWxkZXN0aW5hdGlvbiA9IG5ldyBVUkwodW5lc2NhcGUobG9jLnBhdGhuYW1lKSwge30pO1xuICB9IGVsc2UgaWYgKCdzdHJpbmcnID09PSB0eXBlKSB7XG4gICAgZmluYWxkZXN0aW5hdGlvbiA9IG5ldyBVUkwobG9jLCB7fSk7XG4gICAgZm9yIChrZXkgaW4gaWdub3JlKSBkZWxldGUgZmluYWxkZXN0aW5hdGlvbltrZXldO1xuICB9IGVsc2UgaWYgKCdvYmplY3QnID09PSB0eXBlKSB7XG4gICAgZm9yIChrZXkgaW4gbG9jKSB7XG4gICAgICBpZiAoa2V5IGluIGlnbm9yZSkgY29udGludWU7XG4gICAgICBmaW5hbGRlc3RpbmF0aW9uW2tleV0gPSBsb2Nba2V5XTtcbiAgICB9XG5cbiAgICBpZiAoZmluYWxkZXN0aW5hdGlvbi5zbGFzaGVzID09PSB1bmRlZmluZWQpIHtcbiAgICAgIGZpbmFsZGVzdGluYXRpb24uc2xhc2hlcyA9IHNsYXNoZXMudGVzdChsb2MuaHJlZik7XG4gICAgfVxuICB9XG5cbiAgcmV0dXJuIGZpbmFsZGVzdGluYXRpb247XG59O1xuIiwiKGZ1bmN0aW9uIChyb290LCBmYWN0b3J5KSB7XG4gICAgaWYgKHR5cGVvZiBleHBvcnRzID09PSAnb2JqZWN0Jykge1xuICAgICAgICBtb2R1bGUuZXhwb3J0cyA9IGZhY3RvcnkoKTtcbiAgICB9IGVsc2UgaWYgKHR5cGVvZiBkZWZpbmUgPT09ICdmdW5jdGlvbicgJiYgZGVmaW5lLmFtZCkge1xuICAgICAgICBkZWZpbmUoW10sIGZhY3RvcnkpO1xuICAgIH0gZWxzZSB7XG4gICAgICAgIHJvb3QudXJsdGVtcGxhdGUgPSBmYWN0b3J5KCk7XG4gICAgfVxufSh0aGlzLCBmdW5jdGlvbiAoKSB7XG4gIC8qKlxuICAgKiBAY29uc3RydWN0b3JcbiAgICovXG4gIGZ1bmN0aW9uIFVybFRlbXBsYXRlKCkge1xuICB9XG5cbiAgLyoqXG4gICAqIEBwcml2YXRlXG4gICAqIEBwYXJhbSB7c3RyaW5nfSBzdHJcbiAgICogQHJldHVybiB7c3RyaW5nfVxuICAgKi9cbiAgVXJsVGVtcGxhdGUucHJvdG90eXBlLmVuY29kZVJlc2VydmVkID0gZnVuY3Rpb24gKHN0cikge1xuICAgIHJldHVybiBzdHIuc3BsaXQoLyglWzAtOUEtRmEtZl17Mn0pL2cpLm1hcChmdW5jdGlvbiAocGFydCkge1xuICAgICAgaWYgKCEvJVswLTlBLUZhLWZdLy50ZXN0KHBhcnQpKSB7XG4gICAgICAgIHBhcnQgPSBlbmNvZGVVUkkocGFydCkucmVwbGFjZSgvJTVCL2csICdbJykucmVwbGFjZSgvJTVEL2csICddJyk7XG4gICAgICB9XG4gICAgICByZXR1cm4gcGFydDtcbiAgICB9KS5qb2luKCcnKTtcbiAgfTtcblxuICAvKipcbiAgICogQHByaXZhdGVcbiAgICogQHBhcmFtIHtzdHJpbmd9IHN0clxuICAgKiBAcmV0dXJuIHtzdHJpbmd9XG4gICAqL1xuICBVcmxUZW1wbGF0ZS5wcm90b3R5cGUuZW5jb2RlVW5yZXNlcnZlZCA9IGZ1bmN0aW9uIChzdHIpIHtcbiAgICByZXR1cm4gZW5jb2RlVVJJQ29tcG9uZW50KHN0cikucmVwbGFjZSgvWyEnKCkqXS9nLCBmdW5jdGlvbiAoYykge1xuICAgICAgcmV0dXJuICclJyArIGMuY2hhckNvZGVBdCgwKS50b1N0cmluZygxNikudG9VcHBlckNhc2UoKTtcbiAgICB9KTtcbiAgfVxuXG4gIC8qKlxuICAgKiBAcHJpdmF0ZVxuICAgKiBAcGFyYW0ge3N0cmluZ30gb3BlcmF0b3JcbiAgICogQHBhcmFtIHtzdHJpbmd9IHZhbHVlXG4gICAqIEBwYXJhbSB7c3RyaW5nfSBrZXlcbiAgICogQHJldHVybiB7c3RyaW5nfVxuICAgKi9cbiAgVXJsVGVtcGxhdGUucHJvdG90eXBlLmVuY29kZVZhbHVlID0gZnVuY3Rpb24gKG9wZXJhdG9yLCB2YWx1ZSwga2V5KSB7XG4gICAgdmFsdWUgPSAob3BlcmF0b3IgPT09ICcrJyB8fCBvcGVyYXRvciA9PT0gJyMnKSA/IHRoaXMuZW5jb2RlUmVzZXJ2ZWQodmFsdWUpIDogdGhpcy5lbmNvZGVVbnJlc2VydmVkKHZhbHVlKTtcblxuICAgIGlmIChrZXkpIHtcbiAgICAgIHJldHVybiB0aGlzLmVuY29kZVVucmVzZXJ2ZWQoa2V5KSArICc9JyArIHZhbHVlO1xuICAgIH0gZWxzZSB7XG4gICAgICByZXR1cm4gdmFsdWU7XG4gICAgfVxuICB9O1xuXG4gIC8qKlxuICAgKiBAcHJpdmF0ZVxuICAgKiBAcGFyYW0geyp9IHZhbHVlXG4gICAqIEByZXR1cm4ge2Jvb2xlYW59XG4gICAqL1xuICBVcmxUZW1wbGF0ZS5wcm90b3R5cGUuaXNEZWZpbmVkID0gZnVuY3Rpb24gKHZhbHVlKSB7XG4gICAgcmV0dXJuIHZhbHVlICE9PSB1bmRlZmluZWQgJiYgdmFsdWUgIT09IG51bGw7XG4gIH07XG5cbiAgLyoqXG4gICAqIEBwcml2YXRlXG4gICAqIEBwYXJhbSB7c3RyaW5nfVxuICAgKiBAcmV0dXJuIHtib29sZWFufVxuICAgKi9cbiAgVXJsVGVtcGxhdGUucHJvdG90eXBlLmlzS2V5T3BlcmF0b3IgPSBmdW5jdGlvbiAob3BlcmF0b3IpIHtcbiAgICByZXR1cm4gb3BlcmF0b3IgPT09ICc7JyB8fCBvcGVyYXRvciA9PT0gJyYnIHx8IG9wZXJhdG9yID09PSAnPyc7XG4gIH07XG5cbiAgLyoqXG4gICAqIEBwcml2YXRlXG4gICAqIEBwYXJhbSB7T2JqZWN0fSBjb250ZXh0XG4gICAqIEBwYXJhbSB7c3RyaW5nfSBvcGVyYXRvclxuICAgKiBAcGFyYW0ge3N0cmluZ30ga2V5XG4gICAqIEBwYXJhbSB7c3RyaW5nfSBtb2RpZmllclxuICAgKi9cbiAgVXJsVGVtcGxhdGUucHJvdG90eXBlLmdldFZhbHVlcyA9IGZ1bmN0aW9uIChjb250ZXh0LCBvcGVyYXRvciwga2V5LCBtb2RpZmllcikge1xuICAgIHZhciB2YWx1ZSA9IGNvbnRleHRba2V5XSxcbiAgICAgICAgcmVzdWx0ID0gW107XG5cbiAgICBpZiAodGhpcy5pc0RlZmluZWQodmFsdWUpICYmIHZhbHVlICE9PSAnJykge1xuICAgICAgaWYgKHR5cGVvZiB2YWx1ZSA9PT0gJ3N0cmluZycgfHwgdHlwZW9mIHZhbHVlID09PSAnbnVtYmVyJyB8fCB0eXBlb2YgdmFsdWUgPT09ICdib29sZWFuJykge1xuICAgICAgICB2YWx1ZSA9IHZhbHVlLnRvU3RyaW5nKCk7XG5cbiAgICAgICAgaWYgKG1vZGlmaWVyICYmIG1vZGlmaWVyICE9PSAnKicpIHtcbiAgICAgICAgICB2YWx1ZSA9IHZhbHVlLnN1YnN0cmluZygwLCBwYXJzZUludChtb2RpZmllciwgMTApKTtcbiAgICAgICAgfVxuXG4gICAgICAgIHJlc3VsdC5wdXNoKHRoaXMuZW5jb2RlVmFsdWUob3BlcmF0b3IsIHZhbHVlLCB0aGlzLmlzS2V5T3BlcmF0b3Iob3BlcmF0b3IpID8ga2V5IDogbnVsbCkpO1xuICAgICAgfSBlbHNlIHtcbiAgICAgICAgaWYgKG1vZGlmaWVyID09PSAnKicpIHtcbiAgICAgICAgICBpZiAoQXJyYXkuaXNBcnJheSh2YWx1ZSkpIHtcbiAgICAgICAgICAgIHZhbHVlLmZpbHRlcih0aGlzLmlzRGVmaW5lZCkuZm9yRWFjaChmdW5jdGlvbiAodmFsdWUpIHtcbiAgICAgICAgICAgICAgcmVzdWx0LnB1c2godGhpcy5lbmNvZGVWYWx1ZShvcGVyYXRvciwgdmFsdWUsIHRoaXMuaXNLZXlPcGVyYXRvcihvcGVyYXRvcikgPyBrZXkgOiBudWxsKSk7XG4gICAgICAgICAgICB9LCB0aGlzKTtcbiAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgT2JqZWN0LmtleXModmFsdWUpLmZvckVhY2goZnVuY3Rpb24gKGspIHtcbiAgICAgICAgICAgICAgaWYgKHRoaXMuaXNEZWZpbmVkKHZhbHVlW2tdKSkge1xuICAgICAgICAgICAgICAgIHJlc3VsdC5wdXNoKHRoaXMuZW5jb2RlVmFsdWUob3BlcmF0b3IsIHZhbHVlW2tdLCBrKSk7XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH0sIHRoaXMpO1xuICAgICAgICAgIH1cbiAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICB2YXIgdG1wID0gW107XG5cbiAgICAgICAgICBpZiAoQXJyYXkuaXNBcnJheSh2YWx1ZSkpIHtcbiAgICAgICAgICAgIHZhbHVlLmZpbHRlcih0aGlzLmlzRGVmaW5lZCkuZm9yRWFjaChmdW5jdGlvbiAodmFsdWUpIHtcbiAgICAgICAgICAgICAgdG1wLnB1c2godGhpcy5lbmNvZGVWYWx1ZShvcGVyYXRvciwgdmFsdWUpKTtcbiAgICAgICAgICAgIH0sIHRoaXMpO1xuICAgICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgICBPYmplY3Qua2V5cyh2YWx1ZSkuZm9yRWFjaChmdW5jdGlvbiAoaykge1xuICAgICAgICAgICAgICBpZiAodGhpcy5pc0RlZmluZWQodmFsdWVba10pKSB7XG4gICAgICAgICAgICAgICAgdG1wLnB1c2godGhpcy5lbmNvZGVVbnJlc2VydmVkKGspKTtcbiAgICAgICAgICAgICAgICB0bXAucHVzaCh0aGlzLmVuY29kZVZhbHVlKG9wZXJhdG9yLCB2YWx1ZVtrXS50b1N0cmluZygpKSk7XG4gICAgICAgICAgICAgIH1cbiAgICAgICAgICAgIH0sIHRoaXMpO1xuICAgICAgICAgIH1cblxuICAgICAgICAgIGlmICh0aGlzLmlzS2V5T3BlcmF0b3Iob3BlcmF0b3IpKSB7XG4gICAgICAgICAgICByZXN1bHQucHVzaCh0aGlzLmVuY29kZVVucmVzZXJ2ZWQoa2V5KSArICc9JyArIHRtcC5qb2luKCcsJykpO1xuICAgICAgICAgIH0gZWxzZSBpZiAodG1wLmxlbmd0aCAhPT0gMCkge1xuICAgICAgICAgICAgcmVzdWx0LnB1c2godG1wLmpvaW4oJywnKSk7XG4gICAgICAgICAgfVxuICAgICAgICB9XG4gICAgICB9XG4gICAgfSBlbHNlIHtcbiAgICAgIGlmIChvcGVyYXRvciA9PT0gJzsnKSB7XG4gICAgICAgIGlmICh0aGlzLmlzRGVmaW5lZCh2YWx1ZSkpIHtcbiAgICAgICAgICByZXN1bHQucHVzaCh0aGlzLmVuY29kZVVucmVzZXJ2ZWQoa2V5KSk7XG4gICAgICAgIH1cbiAgICAgIH0gZWxzZSBpZiAodmFsdWUgPT09ICcnICYmIChvcGVyYXRvciA9PT0gJyYnIHx8IG9wZXJhdG9yID09PSAnPycpKSB7XG4gICAgICAgIHJlc3VsdC5wdXNoKHRoaXMuZW5jb2RlVW5yZXNlcnZlZChrZXkpICsgJz0nKTtcbiAgICAgIH0gZWxzZSBpZiAodmFsdWUgPT09ICcnKSB7XG4gICAgICAgIHJlc3VsdC5wdXNoKCcnKTtcbiAgICAgIH1cbiAgICB9XG4gICAgcmV0dXJuIHJlc3VsdDtcbiAgfTtcblxuICAvKipcbiAgICogQHBhcmFtIHtzdHJpbmd9IHRlbXBsYXRlXG4gICAqIEByZXR1cm4ge2Z1bmN0aW9uKE9iamVjdCk6c3RyaW5nfVxuICAgKi9cbiAgVXJsVGVtcGxhdGUucHJvdG90eXBlLnBhcnNlID0gZnVuY3Rpb24gKHRlbXBsYXRlKSB7XG4gICAgdmFyIHRoYXQgPSB0aGlzO1xuICAgIHZhciBvcGVyYXRvcnMgPSBbJysnLCAnIycsICcuJywgJy8nLCAnOycsICc/JywgJyYnXTtcblxuICAgIHJldHVybiB7XG4gICAgICBleHBhbmQ6IGZ1bmN0aW9uIChjb250ZXh0KSB7XG4gICAgICAgIHJldHVybiB0ZW1wbGF0ZS5yZXBsYWNlKC9cXHsoW15cXHtcXH1dKylcXH18KFteXFx7XFx9XSspL2csIGZ1bmN0aW9uIChfLCBleHByZXNzaW9uLCBsaXRlcmFsKSB7XG4gICAgICAgICAgaWYgKGV4cHJlc3Npb24pIHtcbiAgICAgICAgICAgIHZhciBvcGVyYXRvciA9IG51bGwsXG4gICAgICAgICAgICAgICAgdmFsdWVzID0gW107XG5cbiAgICAgICAgICAgIGlmIChvcGVyYXRvcnMuaW5kZXhPZihleHByZXNzaW9uLmNoYXJBdCgwKSkgIT09IC0xKSB7XG4gICAgICAgICAgICAgIG9wZXJhdG9yID0gZXhwcmVzc2lvbi5jaGFyQXQoMCk7XG4gICAgICAgICAgICAgIGV4cHJlc3Npb24gPSBleHByZXNzaW9uLnN1YnN0cigxKTtcbiAgICAgICAgICAgIH1cblxuICAgICAgICAgICAgZXhwcmVzc2lvbi5zcGxpdCgvLC9nKS5mb3JFYWNoKGZ1bmN0aW9uICh2YXJpYWJsZSkge1xuICAgICAgICAgICAgICB2YXIgdG1wID0gLyhbXjpcXCpdKikoPzo6KFxcZCspfChcXCopKT8vLmV4ZWModmFyaWFibGUpO1xuICAgICAgICAgICAgICB2YWx1ZXMucHVzaC5hcHBseSh2YWx1ZXMsIHRoYXQuZ2V0VmFsdWVzKGNvbnRleHQsIG9wZXJhdG9yLCB0bXBbMV0sIHRtcFsyXSB8fCB0bXBbM10pKTtcbiAgICAgICAgICAgIH0pO1xuXG4gICAgICAgICAgICBpZiAob3BlcmF0b3IgJiYgb3BlcmF0b3IgIT09ICcrJykge1xuICAgICAgICAgICAgICB2YXIgc2VwYXJhdG9yID0gJywnO1xuXG4gICAgICAgICAgICAgIGlmIChvcGVyYXRvciA9PT0gJz8nKSB7XG4gICAgICAgICAgICAgICAgc2VwYXJhdG9yID0gJyYnO1xuICAgICAgICAgICAgICB9IGVsc2UgaWYgKG9wZXJhdG9yICE9PSAnIycpIHtcbiAgICAgICAgICAgICAgICBzZXBhcmF0b3IgPSBvcGVyYXRvcjtcbiAgICAgICAgICAgICAgfVxuICAgICAgICAgICAgICByZXR1cm4gKHZhbHVlcy5sZW5ndGggIT09IDAgPyBvcGVyYXRvciA6ICcnKSArIHZhbHVlcy5qb2luKHNlcGFyYXRvcik7XG4gICAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgICByZXR1cm4gdmFsdWVzLmpvaW4oJywnKTtcbiAgICAgICAgICAgIH1cbiAgICAgICAgICB9IGVsc2Uge1xuICAgICAgICAgICAgcmV0dXJuIHRoYXQuZW5jb2RlUmVzZXJ2ZWQobGl0ZXJhbCk7XG4gICAgICAgICAgfVxuICAgICAgICB9KTtcbiAgICAgIH1cbiAgICB9O1xuICB9O1xuXG4gIHJldHVybiBuZXcgVXJsVGVtcGxhdGUoKTtcbn0pKTtcbiIsIihmdW5jdGlvbihzZWxmKSB7XG4gICd1c2Ugc3RyaWN0JztcblxuICBpZiAoc2VsZi5mZXRjaCkge1xuICAgIHJldHVyblxuICB9XG5cbiAgdmFyIHN1cHBvcnQgPSB7XG4gICAgc2VhcmNoUGFyYW1zOiAnVVJMU2VhcmNoUGFyYW1zJyBpbiBzZWxmLFxuICAgIGl0ZXJhYmxlOiAnU3ltYm9sJyBpbiBzZWxmICYmICdpdGVyYXRvcicgaW4gU3ltYm9sLFxuICAgIGJsb2I6ICdGaWxlUmVhZGVyJyBpbiBzZWxmICYmICdCbG9iJyBpbiBzZWxmICYmIChmdW5jdGlvbigpIHtcbiAgICAgIHRyeSB7XG4gICAgICAgIG5ldyBCbG9iKClcbiAgICAgICAgcmV0dXJuIHRydWVcbiAgICAgIH0gY2F0Y2goZSkge1xuICAgICAgICByZXR1cm4gZmFsc2VcbiAgICAgIH1cbiAgICB9KSgpLFxuICAgIGZvcm1EYXRhOiAnRm9ybURhdGEnIGluIHNlbGYsXG4gICAgYXJyYXlCdWZmZXI6ICdBcnJheUJ1ZmZlcicgaW4gc2VsZlxuICB9XG5cbiAgaWYgKHN1cHBvcnQuYXJyYXlCdWZmZXIpIHtcbiAgICB2YXIgdmlld0NsYXNzZXMgPSBbXG4gICAgICAnW29iamVjdCBJbnQ4QXJyYXldJyxcbiAgICAgICdbb2JqZWN0IFVpbnQ4QXJyYXldJyxcbiAgICAgICdbb2JqZWN0IFVpbnQ4Q2xhbXBlZEFycmF5XScsXG4gICAgICAnW29iamVjdCBJbnQxNkFycmF5XScsXG4gICAgICAnW29iamVjdCBVaW50MTZBcnJheV0nLFxuICAgICAgJ1tvYmplY3QgSW50MzJBcnJheV0nLFxuICAgICAgJ1tvYmplY3QgVWludDMyQXJyYXldJyxcbiAgICAgICdbb2JqZWN0IEZsb2F0MzJBcnJheV0nLFxuICAgICAgJ1tvYmplY3QgRmxvYXQ2NEFycmF5XSdcbiAgICBdXG5cbiAgICB2YXIgaXNEYXRhVmlldyA9IGZ1bmN0aW9uKG9iaikge1xuICAgICAgcmV0dXJuIG9iaiAmJiBEYXRhVmlldy5wcm90b3R5cGUuaXNQcm90b3R5cGVPZihvYmopXG4gICAgfVxuXG4gICAgdmFyIGlzQXJyYXlCdWZmZXJWaWV3ID0gQXJyYXlCdWZmZXIuaXNWaWV3IHx8IGZ1bmN0aW9uKG9iaikge1xuICAgICAgcmV0dXJuIG9iaiAmJiB2aWV3Q2xhc3Nlcy5pbmRleE9mKE9iamVjdC5wcm90b3R5cGUudG9TdHJpbmcuY2FsbChvYmopKSA+IC0xXG4gICAgfVxuICB9XG5cbiAgZnVuY3Rpb24gbm9ybWFsaXplTmFtZShuYW1lKSB7XG4gICAgaWYgKHR5cGVvZiBuYW1lICE9PSAnc3RyaW5nJykge1xuICAgICAgbmFtZSA9IFN0cmluZyhuYW1lKVxuICAgIH1cbiAgICBpZiAoL1teYS16MC05XFwtIyQlJicqKy5cXF5fYHx+XS9pLnRlc3QobmFtZSkpIHtcbiAgICAgIHRocm93IG5ldyBUeXBlRXJyb3IoJ0ludmFsaWQgY2hhcmFjdGVyIGluIGhlYWRlciBmaWVsZCBuYW1lJylcbiAgICB9XG4gICAgcmV0dXJuIG5hbWUudG9Mb3dlckNhc2UoKVxuICB9XG5cbiAgZnVuY3Rpb24gbm9ybWFsaXplVmFsdWUodmFsdWUpIHtcbiAgICBpZiAodHlwZW9mIHZhbHVlICE9PSAnc3RyaW5nJykge1xuICAgICAgdmFsdWUgPSBTdHJpbmcodmFsdWUpXG4gICAgfVxuICAgIHJldHVybiB2YWx1ZVxuICB9XG5cbiAgLy8gQnVpbGQgYSBkZXN0cnVjdGl2ZSBpdGVyYXRvciBmb3IgdGhlIHZhbHVlIGxpc3RcbiAgZnVuY3Rpb24gaXRlcmF0b3JGb3IoaXRlbXMpIHtcbiAgICB2YXIgaXRlcmF0b3IgPSB7XG4gICAgICBuZXh0OiBmdW5jdGlvbigpIHtcbiAgICAgICAgdmFyIHZhbHVlID0gaXRlbXMuc2hpZnQoKVxuICAgICAgICByZXR1cm4ge2RvbmU6IHZhbHVlID09PSB1bmRlZmluZWQsIHZhbHVlOiB2YWx1ZX1cbiAgICAgIH1cbiAgICB9XG5cbiAgICBpZiAoc3VwcG9ydC5pdGVyYWJsZSkge1xuICAgICAgaXRlcmF0b3JbU3ltYm9sLml0ZXJhdG9yXSA9IGZ1bmN0aW9uKCkge1xuICAgICAgICByZXR1cm4gaXRlcmF0b3JcbiAgICAgIH1cbiAgICB9XG5cbiAgICByZXR1cm4gaXRlcmF0b3JcbiAgfVxuXG4gIGZ1bmN0aW9uIEhlYWRlcnMoaGVhZGVycykge1xuICAgIHRoaXMubWFwID0ge31cblxuICAgIGlmIChoZWFkZXJzIGluc3RhbmNlb2YgSGVhZGVycykge1xuICAgICAgaGVhZGVycy5mb3JFYWNoKGZ1bmN0aW9uKHZhbHVlLCBuYW1lKSB7XG4gICAgICAgIHRoaXMuYXBwZW5kKG5hbWUsIHZhbHVlKVxuICAgICAgfSwgdGhpcylcblxuICAgIH0gZWxzZSBpZiAoaGVhZGVycykge1xuICAgICAgT2JqZWN0LmdldE93blByb3BlcnR5TmFtZXMoaGVhZGVycykuZm9yRWFjaChmdW5jdGlvbihuYW1lKSB7XG4gICAgICAgIHRoaXMuYXBwZW5kKG5hbWUsIGhlYWRlcnNbbmFtZV0pXG4gICAgICB9LCB0aGlzKVxuICAgIH1cbiAgfVxuXG4gIEhlYWRlcnMucHJvdG90eXBlLmFwcGVuZCA9IGZ1bmN0aW9uKG5hbWUsIHZhbHVlKSB7XG4gICAgbmFtZSA9IG5vcm1hbGl6ZU5hbWUobmFtZSlcbiAgICB2YWx1ZSA9IG5vcm1hbGl6ZVZhbHVlKHZhbHVlKVxuICAgIHZhciBvbGRWYWx1ZSA9IHRoaXMubWFwW25hbWVdXG4gICAgdGhpcy5tYXBbbmFtZV0gPSBvbGRWYWx1ZSA/IG9sZFZhbHVlKycsJyt2YWx1ZSA6IHZhbHVlXG4gIH1cblxuICBIZWFkZXJzLnByb3RvdHlwZVsnZGVsZXRlJ10gPSBmdW5jdGlvbihuYW1lKSB7XG4gICAgZGVsZXRlIHRoaXMubWFwW25vcm1hbGl6ZU5hbWUobmFtZSldXG4gIH1cblxuICBIZWFkZXJzLnByb3RvdHlwZS5nZXQgPSBmdW5jdGlvbihuYW1lKSB7XG4gICAgbmFtZSA9IG5vcm1hbGl6ZU5hbWUobmFtZSlcbiAgICByZXR1cm4gdGhpcy5oYXMobmFtZSkgPyB0aGlzLm1hcFtuYW1lXSA6IG51bGxcbiAgfVxuXG4gIEhlYWRlcnMucHJvdG90eXBlLmhhcyA9IGZ1bmN0aW9uKG5hbWUpIHtcbiAgICByZXR1cm4gdGhpcy5tYXAuaGFzT3duUHJvcGVydHkobm9ybWFsaXplTmFtZShuYW1lKSlcbiAgfVxuXG4gIEhlYWRlcnMucHJvdG90eXBlLnNldCA9IGZ1bmN0aW9uKG5hbWUsIHZhbHVlKSB7XG4gICAgdGhpcy5tYXBbbm9ybWFsaXplTmFtZShuYW1lKV0gPSBub3JtYWxpemVWYWx1ZSh2YWx1ZSlcbiAgfVxuXG4gIEhlYWRlcnMucHJvdG90eXBlLmZvckVhY2ggPSBmdW5jdGlvbihjYWxsYmFjaywgdGhpc0FyZykge1xuICAgIGZvciAodmFyIG5hbWUgaW4gdGhpcy5tYXApIHtcbiAgICAgIGlmICh0aGlzLm1hcC5oYXNPd25Qcm9wZXJ0eShuYW1lKSkge1xuICAgICAgICBjYWxsYmFjay5jYWxsKHRoaXNBcmcsIHRoaXMubWFwW25hbWVdLCBuYW1lLCB0aGlzKVxuICAgICAgfVxuICAgIH1cbiAgfVxuXG4gIEhlYWRlcnMucHJvdG90eXBlLmtleXMgPSBmdW5jdGlvbigpIHtcbiAgICB2YXIgaXRlbXMgPSBbXVxuICAgIHRoaXMuZm9yRWFjaChmdW5jdGlvbih2YWx1ZSwgbmFtZSkgeyBpdGVtcy5wdXNoKG5hbWUpIH0pXG4gICAgcmV0dXJuIGl0ZXJhdG9yRm9yKGl0ZW1zKVxuICB9XG5cbiAgSGVhZGVycy5wcm90b3R5cGUudmFsdWVzID0gZnVuY3Rpb24oKSB7XG4gICAgdmFyIGl0ZW1zID0gW11cbiAgICB0aGlzLmZvckVhY2goZnVuY3Rpb24odmFsdWUpIHsgaXRlbXMucHVzaCh2YWx1ZSkgfSlcbiAgICByZXR1cm4gaXRlcmF0b3JGb3IoaXRlbXMpXG4gIH1cblxuICBIZWFkZXJzLnByb3RvdHlwZS5lbnRyaWVzID0gZnVuY3Rpb24oKSB7XG4gICAgdmFyIGl0ZW1zID0gW11cbiAgICB0aGlzLmZvckVhY2goZnVuY3Rpb24odmFsdWUsIG5hbWUpIHsgaXRlbXMucHVzaChbbmFtZSwgdmFsdWVdKSB9KVxuICAgIHJldHVybiBpdGVyYXRvckZvcihpdGVtcylcbiAgfVxuXG4gIGlmIChzdXBwb3J0Lml0ZXJhYmxlKSB7XG4gICAgSGVhZGVycy5wcm90b3R5cGVbU3ltYm9sLml0ZXJhdG9yXSA9IEhlYWRlcnMucHJvdG90eXBlLmVudHJpZXNcbiAgfVxuXG4gIGZ1bmN0aW9uIGNvbnN1bWVkKGJvZHkpIHtcbiAgICBpZiAoYm9keS5ib2R5VXNlZCkge1xuICAgICAgcmV0dXJuIFByb21pc2UucmVqZWN0KG5ldyBUeXBlRXJyb3IoJ0FscmVhZHkgcmVhZCcpKVxuICAgIH1cbiAgICBib2R5LmJvZHlVc2VkID0gdHJ1ZVxuICB9XG5cbiAgZnVuY3Rpb24gZmlsZVJlYWRlclJlYWR5KHJlYWRlcikge1xuICAgIHJldHVybiBuZXcgUHJvbWlzZShmdW5jdGlvbihyZXNvbHZlLCByZWplY3QpIHtcbiAgICAgIHJlYWRlci5vbmxvYWQgPSBmdW5jdGlvbigpIHtcbiAgICAgICAgcmVzb2x2ZShyZWFkZXIucmVzdWx0KVxuICAgICAgfVxuICAgICAgcmVhZGVyLm9uZXJyb3IgPSBmdW5jdGlvbigpIHtcbiAgICAgICAgcmVqZWN0KHJlYWRlci5lcnJvcilcbiAgICAgIH1cbiAgICB9KVxuICB9XG5cbiAgZnVuY3Rpb24gcmVhZEJsb2JBc0FycmF5QnVmZmVyKGJsb2IpIHtcbiAgICB2YXIgcmVhZGVyID0gbmV3IEZpbGVSZWFkZXIoKVxuICAgIHZhciBwcm9taXNlID0gZmlsZVJlYWRlclJlYWR5KHJlYWRlcilcbiAgICByZWFkZXIucmVhZEFzQXJyYXlCdWZmZXIoYmxvYilcbiAgICByZXR1cm4gcHJvbWlzZVxuICB9XG5cbiAgZnVuY3Rpb24gcmVhZEJsb2JBc1RleHQoYmxvYikge1xuICAgIHZhciByZWFkZXIgPSBuZXcgRmlsZVJlYWRlcigpXG4gICAgdmFyIHByb21pc2UgPSBmaWxlUmVhZGVyUmVhZHkocmVhZGVyKVxuICAgIHJlYWRlci5yZWFkQXNUZXh0KGJsb2IpXG4gICAgcmV0dXJuIHByb21pc2VcbiAgfVxuXG4gIGZ1bmN0aW9uIHJlYWRBcnJheUJ1ZmZlckFzVGV4dChidWYpIHtcbiAgICB2YXIgdmlldyA9IG5ldyBVaW50OEFycmF5KGJ1ZilcbiAgICB2YXIgY2hhcnMgPSBuZXcgQXJyYXkodmlldy5sZW5ndGgpXG5cbiAgICBmb3IgKHZhciBpID0gMDsgaSA8IHZpZXcubGVuZ3RoOyBpKyspIHtcbiAgICAgIGNoYXJzW2ldID0gU3RyaW5nLmZyb21DaGFyQ29kZSh2aWV3W2ldKVxuICAgIH1cbiAgICByZXR1cm4gY2hhcnMuam9pbignJylcbiAgfVxuXG4gIGZ1bmN0aW9uIGJ1ZmZlckNsb25lKGJ1Zikge1xuICAgIGlmIChidWYuc2xpY2UpIHtcbiAgICAgIHJldHVybiBidWYuc2xpY2UoMClcbiAgICB9IGVsc2Uge1xuICAgICAgdmFyIHZpZXcgPSBuZXcgVWludDhBcnJheShidWYuYnl0ZUxlbmd0aClcbiAgICAgIHZpZXcuc2V0KG5ldyBVaW50OEFycmF5KGJ1ZikpXG4gICAgICByZXR1cm4gdmlldy5idWZmZXJcbiAgICB9XG4gIH1cblxuICBmdW5jdGlvbiBCb2R5KCkge1xuICAgIHRoaXMuYm9keVVzZWQgPSBmYWxzZVxuXG4gICAgdGhpcy5faW5pdEJvZHkgPSBmdW5jdGlvbihib2R5KSB7XG4gICAgICB0aGlzLl9ib2R5SW5pdCA9IGJvZHlcbiAgICAgIGlmICghYm9keSkge1xuICAgICAgICB0aGlzLl9ib2R5VGV4dCA9ICcnXG4gICAgICB9IGVsc2UgaWYgKHR5cGVvZiBib2R5ID09PSAnc3RyaW5nJykge1xuICAgICAgICB0aGlzLl9ib2R5VGV4dCA9IGJvZHlcbiAgICAgIH0gZWxzZSBpZiAoc3VwcG9ydC5ibG9iICYmIEJsb2IucHJvdG90eXBlLmlzUHJvdG90eXBlT2YoYm9keSkpIHtcbiAgICAgICAgdGhpcy5fYm9keUJsb2IgPSBib2R5XG4gICAgICB9IGVsc2UgaWYgKHN1cHBvcnQuZm9ybURhdGEgJiYgRm9ybURhdGEucHJvdG90eXBlLmlzUHJvdG90eXBlT2YoYm9keSkpIHtcbiAgICAgICAgdGhpcy5fYm9keUZvcm1EYXRhID0gYm9keVxuICAgICAgfSBlbHNlIGlmIChzdXBwb3J0LnNlYXJjaFBhcmFtcyAmJiBVUkxTZWFyY2hQYXJhbXMucHJvdG90eXBlLmlzUHJvdG90eXBlT2YoYm9keSkpIHtcbiAgICAgICAgdGhpcy5fYm9keVRleHQgPSBib2R5LnRvU3RyaW5nKClcbiAgICAgIH0gZWxzZSBpZiAoc3VwcG9ydC5hcnJheUJ1ZmZlciAmJiBzdXBwb3J0LmJsb2IgJiYgaXNEYXRhVmlldyhib2R5KSkge1xuICAgICAgICB0aGlzLl9ib2R5QXJyYXlCdWZmZXIgPSBidWZmZXJDbG9uZShib2R5LmJ1ZmZlcilcbiAgICAgICAgLy8gSUUgMTAtMTEgY2FuJ3QgaGFuZGxlIGEgRGF0YVZpZXcgYm9keS5cbiAgICAgICAgdGhpcy5fYm9keUluaXQgPSBuZXcgQmxvYihbdGhpcy5fYm9keUFycmF5QnVmZmVyXSlcbiAgICAgIH0gZWxzZSBpZiAoc3VwcG9ydC5hcnJheUJ1ZmZlciAmJiAoQXJyYXlCdWZmZXIucHJvdG90eXBlLmlzUHJvdG90eXBlT2YoYm9keSkgfHwgaXNBcnJheUJ1ZmZlclZpZXcoYm9keSkpKSB7XG4gICAgICAgIHRoaXMuX2JvZHlBcnJheUJ1ZmZlciA9IGJ1ZmZlckNsb25lKGJvZHkpXG4gICAgICB9IGVsc2Uge1xuICAgICAgICB0aHJvdyBuZXcgRXJyb3IoJ3Vuc3VwcG9ydGVkIEJvZHlJbml0IHR5cGUnKVxuICAgICAgfVxuXG4gICAgICBpZiAoIXRoaXMuaGVhZGVycy5nZXQoJ2NvbnRlbnQtdHlwZScpKSB7XG4gICAgICAgIGlmICh0eXBlb2YgYm9keSA9PT0gJ3N0cmluZycpIHtcbiAgICAgICAgICB0aGlzLmhlYWRlcnMuc2V0KCdjb250ZW50LXR5cGUnLCAndGV4dC9wbGFpbjtjaGFyc2V0PVVURi04JylcbiAgICAgICAgfSBlbHNlIGlmICh0aGlzLl9ib2R5QmxvYiAmJiB0aGlzLl9ib2R5QmxvYi50eXBlKSB7XG4gICAgICAgICAgdGhpcy5oZWFkZXJzLnNldCgnY29udGVudC10eXBlJywgdGhpcy5fYm9keUJsb2IudHlwZSlcbiAgICAgICAgfSBlbHNlIGlmIChzdXBwb3J0LnNlYXJjaFBhcmFtcyAmJiBVUkxTZWFyY2hQYXJhbXMucHJvdG90eXBlLmlzUHJvdG90eXBlT2YoYm9keSkpIHtcbiAgICAgICAgICB0aGlzLmhlYWRlcnMuc2V0KCdjb250ZW50LXR5cGUnLCAnYXBwbGljYXRpb24veC13d3ctZm9ybS11cmxlbmNvZGVkO2NoYXJzZXQ9VVRGLTgnKVxuICAgICAgICB9XG4gICAgICB9XG4gICAgfVxuXG4gICAgaWYgKHN1cHBvcnQuYmxvYikge1xuICAgICAgdGhpcy5ibG9iID0gZnVuY3Rpb24oKSB7XG4gICAgICAgIHZhciByZWplY3RlZCA9IGNvbnN1bWVkKHRoaXMpXG4gICAgICAgIGlmIChyZWplY3RlZCkge1xuICAgICAgICAgIHJldHVybiByZWplY3RlZFxuICAgICAgICB9XG5cbiAgICAgICAgaWYgKHRoaXMuX2JvZHlCbG9iKSB7XG4gICAgICAgICAgcmV0dXJuIFByb21pc2UucmVzb2x2ZSh0aGlzLl9ib2R5QmxvYilcbiAgICAgICAgfSBlbHNlIGlmICh0aGlzLl9ib2R5QXJyYXlCdWZmZXIpIHtcbiAgICAgICAgICByZXR1cm4gUHJvbWlzZS5yZXNvbHZlKG5ldyBCbG9iKFt0aGlzLl9ib2R5QXJyYXlCdWZmZXJdKSlcbiAgICAgICAgfSBlbHNlIGlmICh0aGlzLl9ib2R5Rm9ybURhdGEpIHtcbiAgICAgICAgICB0aHJvdyBuZXcgRXJyb3IoJ2NvdWxkIG5vdCByZWFkIEZvcm1EYXRhIGJvZHkgYXMgYmxvYicpXG4gICAgICAgIH0gZWxzZSB7XG4gICAgICAgICAgcmV0dXJuIFByb21pc2UucmVzb2x2ZShuZXcgQmxvYihbdGhpcy5fYm9keVRleHRdKSlcbiAgICAgICAgfVxuICAgICAgfVxuXG4gICAgICB0aGlzLmFycmF5QnVmZmVyID0gZnVuY3Rpb24oKSB7XG4gICAgICAgIGlmICh0aGlzLl9ib2R5QXJyYXlCdWZmZXIpIHtcbiAgICAgICAgICByZXR1cm4gY29uc3VtZWQodGhpcykgfHwgUHJvbWlzZS5yZXNvbHZlKHRoaXMuX2JvZHlBcnJheUJ1ZmZlcilcbiAgICAgICAgfSBlbHNlIHtcbiAgICAgICAgICByZXR1cm4gdGhpcy5ibG9iKCkudGhlbihyZWFkQmxvYkFzQXJyYXlCdWZmZXIpXG4gICAgICAgIH1cbiAgICAgIH1cbiAgICB9XG5cbiAgICB0aGlzLnRleHQgPSBmdW5jdGlvbigpIHtcbiAgICAgIHZhciByZWplY3RlZCA9IGNvbnN1bWVkKHRoaXMpXG4gICAgICBpZiAocmVqZWN0ZWQpIHtcbiAgICAgICAgcmV0dXJuIHJlamVjdGVkXG4gICAgICB9XG5cbiAgICAgIGlmICh0aGlzLl9ib2R5QmxvYikge1xuICAgICAgICByZXR1cm4gcmVhZEJsb2JBc1RleHQodGhpcy5fYm9keUJsb2IpXG4gICAgICB9IGVsc2UgaWYgKHRoaXMuX2JvZHlBcnJheUJ1ZmZlcikge1xuICAgICAgICByZXR1cm4gUHJvbWlzZS5yZXNvbHZlKHJlYWRBcnJheUJ1ZmZlckFzVGV4dCh0aGlzLl9ib2R5QXJyYXlCdWZmZXIpKVxuICAgICAgfSBlbHNlIGlmICh0aGlzLl9ib2R5Rm9ybURhdGEpIHtcbiAgICAgICAgdGhyb3cgbmV3IEVycm9yKCdjb3VsZCBub3QgcmVhZCBGb3JtRGF0YSBib2R5IGFzIHRleHQnKVxuICAgICAgfSBlbHNlIHtcbiAgICAgICAgcmV0dXJuIFByb21pc2UucmVzb2x2ZSh0aGlzLl9ib2R5VGV4dClcbiAgICAgIH1cbiAgICB9XG5cbiAgICBpZiAoc3VwcG9ydC5mb3JtRGF0YSkge1xuICAgICAgdGhpcy5mb3JtRGF0YSA9IGZ1bmN0aW9uKCkge1xuICAgICAgICByZXR1cm4gdGhpcy50ZXh0KCkudGhlbihkZWNvZGUpXG4gICAgICB9XG4gICAgfVxuXG4gICAgdGhpcy5qc29uID0gZnVuY3Rpb24oKSB7XG4gICAgICByZXR1cm4gdGhpcy50ZXh0KCkudGhlbihKU09OLnBhcnNlKVxuICAgIH1cblxuICAgIHJldHVybiB0aGlzXG4gIH1cblxuICAvLyBIVFRQIG1ldGhvZHMgd2hvc2UgY2FwaXRhbGl6YXRpb24gc2hvdWxkIGJlIG5vcm1hbGl6ZWRcbiAgdmFyIG1ldGhvZHMgPSBbJ0RFTEVURScsICdHRVQnLCAnSEVBRCcsICdPUFRJT05TJywgJ1BPU1QnLCAnUFVUJ11cblxuICBmdW5jdGlvbiBub3JtYWxpemVNZXRob2QobWV0aG9kKSB7XG4gICAgdmFyIHVwY2FzZWQgPSBtZXRob2QudG9VcHBlckNhc2UoKVxuICAgIHJldHVybiAobWV0aG9kcy5pbmRleE9mKHVwY2FzZWQpID4gLTEpID8gdXBjYXNlZCA6IG1ldGhvZFxuICB9XG5cbiAgZnVuY3Rpb24gUmVxdWVzdChpbnB1dCwgb3B0aW9ucykge1xuICAgIG9wdGlvbnMgPSBvcHRpb25zIHx8IHt9XG4gICAgdmFyIGJvZHkgPSBvcHRpb25zLmJvZHlcblxuICAgIGlmIChpbnB1dCBpbnN0YW5jZW9mIFJlcXVlc3QpIHtcbiAgICAgIGlmIChpbnB1dC5ib2R5VXNlZCkge1xuICAgICAgICB0aHJvdyBuZXcgVHlwZUVycm9yKCdBbHJlYWR5IHJlYWQnKVxuICAgICAgfVxuICAgICAgdGhpcy51cmwgPSBpbnB1dC51cmxcbiAgICAgIHRoaXMuY3JlZGVudGlhbHMgPSBpbnB1dC5jcmVkZW50aWFsc1xuICAgICAgaWYgKCFvcHRpb25zLmhlYWRlcnMpIHtcbiAgICAgICAgdGhpcy5oZWFkZXJzID0gbmV3IEhlYWRlcnMoaW5wdXQuaGVhZGVycylcbiAgICAgIH1cbiAgICAgIHRoaXMubWV0aG9kID0gaW5wdXQubWV0aG9kXG4gICAgICB0aGlzLm1vZGUgPSBpbnB1dC5tb2RlXG4gICAgICBpZiAoIWJvZHkgJiYgaW5wdXQuX2JvZHlJbml0ICE9IG51bGwpIHtcbiAgICAgICAgYm9keSA9IGlucHV0Ll9ib2R5SW5pdFxuICAgICAgICBpbnB1dC5ib2R5VXNlZCA9IHRydWVcbiAgICAgIH1cbiAgICB9IGVsc2Uge1xuICAgICAgdGhpcy51cmwgPSBTdHJpbmcoaW5wdXQpXG4gICAgfVxuXG4gICAgdGhpcy5jcmVkZW50aWFscyA9IG9wdGlvbnMuY3JlZGVudGlhbHMgfHwgdGhpcy5jcmVkZW50aWFscyB8fCAnb21pdCdcbiAgICBpZiAob3B0aW9ucy5oZWFkZXJzIHx8ICF0aGlzLmhlYWRlcnMpIHtcbiAgICAgIHRoaXMuaGVhZGVycyA9IG5ldyBIZWFkZXJzKG9wdGlvbnMuaGVhZGVycylcbiAgICB9XG4gICAgdGhpcy5tZXRob2QgPSBub3JtYWxpemVNZXRob2Qob3B0aW9ucy5tZXRob2QgfHwgdGhpcy5tZXRob2QgfHwgJ0dFVCcpXG4gICAgdGhpcy5tb2RlID0gb3B0aW9ucy5tb2RlIHx8IHRoaXMubW9kZSB8fCBudWxsXG4gICAgdGhpcy5yZWZlcnJlciA9IG51bGxcblxuICAgIGlmICgodGhpcy5tZXRob2QgPT09ICdHRVQnIHx8IHRoaXMubWV0aG9kID09PSAnSEVBRCcpICYmIGJvZHkpIHtcbiAgICAgIHRocm93IG5ldyBUeXBlRXJyb3IoJ0JvZHkgbm90IGFsbG93ZWQgZm9yIEdFVCBvciBIRUFEIHJlcXVlc3RzJylcbiAgICB9XG4gICAgdGhpcy5faW5pdEJvZHkoYm9keSlcbiAgfVxuXG4gIFJlcXVlc3QucHJvdG90eXBlLmNsb25lID0gZnVuY3Rpb24oKSB7XG4gICAgcmV0dXJuIG5ldyBSZXF1ZXN0KHRoaXMsIHsgYm9keTogdGhpcy5fYm9keUluaXQgfSlcbiAgfVxuXG4gIGZ1bmN0aW9uIGRlY29kZShib2R5KSB7XG4gICAgdmFyIGZvcm0gPSBuZXcgRm9ybURhdGEoKVxuICAgIGJvZHkudHJpbSgpLnNwbGl0KCcmJykuZm9yRWFjaChmdW5jdGlvbihieXRlcykge1xuICAgICAgaWYgKGJ5dGVzKSB7XG4gICAgICAgIHZhciBzcGxpdCA9IGJ5dGVzLnNwbGl0KCc9JylcbiAgICAgICAgdmFyIG5hbWUgPSBzcGxpdC5zaGlmdCgpLnJlcGxhY2UoL1xcKy9nLCAnICcpXG4gICAgICAgIHZhciB2YWx1ZSA9IHNwbGl0LmpvaW4oJz0nKS5yZXBsYWNlKC9cXCsvZywgJyAnKVxuICAgICAgICBmb3JtLmFwcGVuZChkZWNvZGVVUklDb21wb25lbnQobmFtZSksIGRlY29kZVVSSUNvbXBvbmVudCh2YWx1ZSkpXG4gICAgICB9XG4gICAgfSlcbiAgICByZXR1cm4gZm9ybVxuICB9XG5cbiAgZnVuY3Rpb24gcGFyc2VIZWFkZXJzKHJhd0hlYWRlcnMpIHtcbiAgICB2YXIgaGVhZGVycyA9IG5ldyBIZWFkZXJzKClcbiAgICByYXdIZWFkZXJzLnNwbGl0KC9cXHI/XFxuLykuZm9yRWFjaChmdW5jdGlvbihsaW5lKSB7XG4gICAgICB2YXIgcGFydHMgPSBsaW5lLnNwbGl0KCc6JylcbiAgICAgIHZhciBrZXkgPSBwYXJ0cy5zaGlmdCgpLnRyaW0oKVxuICAgICAgaWYgKGtleSkge1xuICAgICAgICB2YXIgdmFsdWUgPSBwYXJ0cy5qb2luKCc6JykudHJpbSgpXG4gICAgICAgIGhlYWRlcnMuYXBwZW5kKGtleSwgdmFsdWUpXG4gICAgICB9XG4gICAgfSlcbiAgICByZXR1cm4gaGVhZGVyc1xuICB9XG5cbiAgQm9keS5jYWxsKFJlcXVlc3QucHJvdG90eXBlKVxuXG4gIGZ1bmN0aW9uIFJlc3BvbnNlKGJvZHlJbml0LCBvcHRpb25zKSB7XG4gICAgaWYgKCFvcHRpb25zKSB7XG4gICAgICBvcHRpb25zID0ge31cbiAgICB9XG5cbiAgICB0aGlzLnR5cGUgPSAnZGVmYXVsdCdcbiAgICB0aGlzLnN0YXR1cyA9ICdzdGF0dXMnIGluIG9wdGlvbnMgPyBvcHRpb25zLnN0YXR1cyA6IDIwMFxuICAgIHRoaXMub2sgPSB0aGlzLnN0YXR1cyA+PSAyMDAgJiYgdGhpcy5zdGF0dXMgPCAzMDBcbiAgICB0aGlzLnN0YXR1c1RleHQgPSAnc3RhdHVzVGV4dCcgaW4gb3B0aW9ucyA/IG9wdGlvbnMuc3RhdHVzVGV4dCA6ICdPSydcbiAgICB0aGlzLmhlYWRlcnMgPSBuZXcgSGVhZGVycyhvcHRpb25zLmhlYWRlcnMpXG4gICAgdGhpcy51cmwgPSBvcHRpb25zLnVybCB8fCAnJ1xuICAgIHRoaXMuX2luaXRCb2R5KGJvZHlJbml0KVxuICB9XG5cbiAgQm9keS5jYWxsKFJlc3BvbnNlLnByb3RvdHlwZSlcblxuICBSZXNwb25zZS5wcm90b3R5cGUuY2xvbmUgPSBmdW5jdGlvbigpIHtcbiAgICByZXR1cm4gbmV3IFJlc3BvbnNlKHRoaXMuX2JvZHlJbml0LCB7XG4gICAgICBzdGF0dXM6IHRoaXMuc3RhdHVzLFxuICAgICAgc3RhdHVzVGV4dDogdGhpcy5zdGF0dXNUZXh0LFxuICAgICAgaGVhZGVyczogbmV3IEhlYWRlcnModGhpcy5oZWFkZXJzKSxcbiAgICAgIHVybDogdGhpcy51cmxcbiAgICB9KVxuICB9XG5cbiAgUmVzcG9uc2UuZXJyb3IgPSBmdW5jdGlvbigpIHtcbiAgICB2YXIgcmVzcG9uc2UgPSBuZXcgUmVzcG9uc2UobnVsbCwge3N0YXR1czogMCwgc3RhdHVzVGV4dDogJyd9KVxuICAgIHJlc3BvbnNlLnR5cGUgPSAnZXJyb3InXG4gICAgcmV0dXJuIHJlc3BvbnNlXG4gIH1cblxuICB2YXIgcmVkaXJlY3RTdGF0dXNlcyA9IFszMDEsIDMwMiwgMzAzLCAzMDcsIDMwOF1cblxuICBSZXNwb25zZS5yZWRpcmVjdCA9IGZ1bmN0aW9uKHVybCwgc3RhdHVzKSB7XG4gICAgaWYgKHJlZGlyZWN0U3RhdHVzZXMuaW5kZXhPZihzdGF0dXMpID09PSAtMSkge1xuICAgICAgdGhyb3cgbmV3IFJhbmdlRXJyb3IoJ0ludmFsaWQgc3RhdHVzIGNvZGUnKVxuICAgIH1cblxuICAgIHJldHVybiBuZXcgUmVzcG9uc2UobnVsbCwge3N0YXR1czogc3RhdHVzLCBoZWFkZXJzOiB7bG9jYXRpb246IHVybH19KVxuICB9XG5cbiAgc2VsZi5IZWFkZXJzID0gSGVhZGVyc1xuICBzZWxmLlJlcXVlc3QgPSBSZXF1ZXN0XG4gIHNlbGYuUmVzcG9uc2UgPSBSZXNwb25zZVxuXG4gIHNlbGYuZmV0Y2ggPSBmdW5jdGlvbihpbnB1dCwgaW5pdCkge1xuICAgIHJldHVybiBuZXcgUHJvbWlzZShmdW5jdGlvbihyZXNvbHZlLCByZWplY3QpIHtcbiAgICAgIHZhciByZXF1ZXN0ID0gbmV3IFJlcXVlc3QoaW5wdXQsIGluaXQpXG4gICAgICB2YXIgeGhyID0gbmV3IFhNTEh0dHBSZXF1ZXN0KClcblxuICAgICAgeGhyLm9ubG9hZCA9IGZ1bmN0aW9uKCkge1xuICAgICAgICB2YXIgb3B0aW9ucyA9IHtcbiAgICAgICAgICBzdGF0dXM6IHhoci5zdGF0dXMsXG4gICAgICAgICAgc3RhdHVzVGV4dDogeGhyLnN0YXR1c1RleHQsXG4gICAgICAgICAgaGVhZGVyczogcGFyc2VIZWFkZXJzKHhoci5nZXRBbGxSZXNwb25zZUhlYWRlcnMoKSB8fCAnJylcbiAgICAgICAgfVxuICAgICAgICBvcHRpb25zLnVybCA9ICdyZXNwb25zZVVSTCcgaW4geGhyID8geGhyLnJlc3BvbnNlVVJMIDogb3B0aW9ucy5oZWFkZXJzLmdldCgnWC1SZXF1ZXN0LVVSTCcpXG4gICAgICAgIHZhciBib2R5ID0gJ3Jlc3BvbnNlJyBpbiB4aHIgPyB4aHIucmVzcG9uc2UgOiB4aHIucmVzcG9uc2VUZXh0XG4gICAgICAgIHJlc29sdmUobmV3IFJlc3BvbnNlKGJvZHksIG9wdGlvbnMpKVxuICAgICAgfVxuXG4gICAgICB4aHIub25lcnJvciA9IGZ1bmN0aW9uKCkge1xuICAgICAgICByZWplY3QobmV3IFR5cGVFcnJvcignTmV0d29yayByZXF1ZXN0IGZhaWxlZCcpKVxuICAgICAgfVxuXG4gICAgICB4aHIub250aW1lb3V0ID0gZnVuY3Rpb24oKSB7XG4gICAgICAgIHJlamVjdChuZXcgVHlwZUVycm9yKCdOZXR3b3JrIHJlcXVlc3QgZmFpbGVkJykpXG4gICAgICB9XG5cbiAgICAgIHhoci5vcGVuKHJlcXVlc3QubWV0aG9kLCByZXF1ZXN0LnVybCwgdHJ1ZSlcblxuICAgICAgaWYgKHJlcXVlc3QuY3JlZGVudGlhbHMgPT09ICdpbmNsdWRlJykge1xuICAgICAgICB4aHIud2l0aENyZWRlbnRpYWxzID0gdHJ1ZVxuICAgICAgfVxuXG4gICAgICBpZiAoJ3Jlc3BvbnNlVHlwZScgaW4geGhyICYmIHN1cHBvcnQuYmxvYikge1xuICAgICAgICB4aHIucmVzcG9uc2VUeXBlID0gJ2Jsb2InXG4gICAgICB9XG5cbiAgICAgIHJlcXVlc3QuaGVhZGVycy5mb3JFYWNoKGZ1bmN0aW9uKHZhbHVlLCBuYW1lKSB7XG4gICAgICAgIHhoci5zZXRSZXF1ZXN0SGVhZGVyKG5hbWUsIHZhbHVlKVxuICAgICAgfSlcblxuICAgICAgeGhyLnNlbmQodHlwZW9mIHJlcXVlc3QuX2JvZHlJbml0ID09PSAndW5kZWZpbmVkJyA/IG51bGwgOiByZXF1ZXN0Ll9ib2R5SW5pdClcbiAgICB9KVxuICB9XG4gIHNlbGYuZmV0Y2gucG9seWZpbGwgPSB0cnVlXG59KSh0eXBlb2Ygc2VsZiAhPT0gJ3VuZGVmaW5lZCcgPyBzZWxmIDogdGhpcyk7XG4iXX0=
