function normalizeHTTPHeader(str) {
    return (str.charAt(0).toUpperCase() + str.substring(1))
        .replace( /-(.)/g, function($1) { return $1.toUpperCase(); })
        .replace( /(Www)/g, function($1) { return 'WWW'; })
        .replace( /(Xss)/g, function($1) { return 'XSS'; })
        .replace( /(Md5)/g, function($1) { return 'MD5'; })
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

let responseDisplay = 'data';
const coreapi = window.coreapi
const schema = window.schema

// Language Control
$('#language-control li').click(function (event) {
    event.preventDefault();
    const languageMenuItem = $(this).find('a');
    var language = languageMenuItem.data("language")

    var languageControls = $(this).closest('ul').find('li');
    languageControls.find('a').not('[data-language="' + language +'"]').parent().removeClass("active")
    languageControls.find('a').filter('[data-language="' + language +'"]').parent().addClass("active")

    $('#selected-language').text(language)

    var codeBlocks = $('pre.highlight')
    codeBlocks.not('[data-language="' + language +'"]').addClass("hide")
    codeBlocks.filter('[data-language="' + language +'"]').removeClass("hide")
})

// API Explorer
$('form.api-interaction').submit(function(event) {
    event.preventDefault();

    const form = $(this).closest("form");
    const key = form.data("key");
    var params = {};

    const formData = new FormData(form.get()[0]);
    for (var [paramKey, paramValue] of formData.entries()) {
        var elem = form.find("[name=" + paramKey + "]")
        var dataType = elem.data('type') || 'string'
        var dataLocation = elem.data('location')

        if (dataType === 'integer' && paramValue) {
            paramValue = parseInt(paramValue)
        } else if (dataType === 'number' && paramValue) {
            paramValue = parseFloat(paramValue)
        } else if (dataType === 'boolean' && paramValue) {
            paramValue = {
                'true': true,
                'false': false
            }[paramValue.toLowerCase()]
        } else if (dataType === 'array' && paramValue) {
            paramValue = JSON.parse(paramValue)
        }

        if (dataLocation === 'query' && !paramValue) {
            continue
        }
        params[paramKey] = paramValue
    }

    form.find(":checkbox").each(function( index ) {
        var name = $(this).attr("name");
        if (!params.hasOwnProperty(name)) {
            params[name] = false
        }
    })

    function requestCallback(request) {
        // Fill in the "GET /foo/" display.
        let parser = document.createElement('a');
        parser.href = request.url;
        const method = request.options.method
        const path = parser.pathname + parser.hash + parser.search

        form.find(".request-method").text(method)
        form.find(".request-url").text(path)
    }

    function responseCallback(response, responseText) {
        // Display the 'Data'/'Raw' control.
        form.closest(".modal-content").find(".toggle-view").removeClass("hide")

        // Fill in the "200 OK" display.
        form.find(".response-status-code").removeClass("label-success").removeClass("label-danger")
        if (response.ok) {
            form.find(".response-status-code").addClass("label-success")
        } else {
            form.find(".response-status-code").addClass("label-danger")
        }
        form.find(".response-status-code").text(response.status)
        form.find(".meta").removeClass("hide")

        // Fill in the Raw HTTP response display.
        var panelText = 'HTTP/1.1 ' + response.status + ' ' + response.statusText + '\n';
        response.headers.forEach((header, key) => {
            panelText += normalizeHTTPHeader(key) + ': ' + header + '\n'
        })
        if (responseText) {
            panelText += '\n' + responseText
        }
        form.find(".response-raw-response").text(panelText)
    }

    // Instantiate a client to make the outgoing request.
    let options = {
        requestCallback: requestCallback,
        responseCallback: responseCallback,
    }

    // Setup authentication options.
    if (window.auth && window.auth.type === 'token') {
        // Header authentication
        options.headers = {
            'Authorization': window.auth.value
        }
    } else if (window.auth && window.auth.type === 'basic') {
        // Basic authentication
        const token = window.auth.username + ':' + window.auth.password
        const hash = window.btoa(token)
        options.headers = {
            'Authorization': 'Basic ' + hash
        }
    } else if (window.auth && window.auth.type === 'session') {
        // Session authentication
        options.csrf = {
            'X-CSRFToken': getCookie('csrftoken')
        }
    }

    const client = new coreapi.Client(options)

    client.action(schema, key, params).then(function (data) {
        var response = JSON.stringify(data, null, 2);
        form.find(".request-awaiting").addClass("hide")
        form.find(".response-raw").addClass("hide")
        form.find(".response-data").addClass("hide")
        form.find(".response-data").text('')
        form.find(".response-data").jsonView(response)

        if (responseDisplay === 'data') {
            form.find(".response-data").removeClass("hide")
        } else {
            form.find(".response-raw").removeClass("hide")
        }
    }).catch(function (error) {
        var response = JSON.stringify(error.content, null, 2);
        form.find(".request-awaiting").addClass("hide")
        form.find(".response-raw").addClass("hide")
        form.find(".response-data").addClass("hide")
        form.find(".response-data").text('')
        form.find(".response-data").jsonView(response)

        if (responseDisplay === 'data') {
            form.find(".response-data").removeClass("hide")
        } else {
            form.find(".response-raw").removeClass("hide")
        }
    })
});

// 'Data'/'Raw' control
$('.toggle-view button').click(function() {
    responseDisplay = $(this).data("display-toggle");
    $(this).removeClass("btn-default").addClass('btn-info').siblings().removeClass('btn-info');
    if (responseDisplay === 'raw') {
        $(this).closest(".modal-content").find(".response-raw").removeClass("hide");
        $(this).closest(".modal-content").find(".response-data").addClass("hide");
    } else {
        $(this).closest(".modal-content").find(".response-data").removeClass("hide");
        $(this).closest(".modal-content").find(".response-raw").addClass("hide");
    }
});

// Authentication: none
$('#auth-control').find("[data-auth='none']").click(function (event) {
    event.preventDefault();
    window.auth = null;
    $('#selected-authentication').text('none');
    $('#auth-control').children().removeClass('active');
    $('#auth-control').find("[data-auth='none']").addClass('active');
})

// Authentication: token
$('form.authentication-token-form').submit(function(event) {
    event.preventDefault();
    const form = $(this).closest("form");
    const value = form.find('input').val();
    window.auth = {
        'type': 'token',
        'value': value,
    };
    $('#selected-authentication').text('header');
    $('#auth-control').children().removeClass('active');
    $('#auth-control').find("[data-auth='token']").addClass('active');
    $('#auth_token_modal').modal('hide');
});

// Authentication: basic
$('form.authentication-basic-form').submit(function(event) {
    event.preventDefault();
    const form = $(this).closest("form");
    const username = form.find('input#username').val();
    const password = form.find('input#password').val();
    window.auth = {
        'type': 'basic',
        'username': username,
        'password': password,
    };
    $('#selected-authentication').text('basic');
    $('#auth-control').children().removeClass('active');
    $('#auth-control').find("[data-auth='basic']").addClass('active');
    $('#auth_basic_modal').modal('hide');
});

// Authentication: session
$('form.authentication-session-form').submit(function(event) {
    event.preventDefault();
    window.auth = {
        'type': 'session',
    };
    $('#selected-authentication').text('session');
    $('#auth-control').children().removeClass('active');
    $('#auth-control').find("[data-auth='session']").addClass('active');
    $('#auth_session_modal').modal('hide');
});
