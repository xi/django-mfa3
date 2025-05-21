import * as webauthnJSON from './vendor/webauthn-json.browser-ponyfill.js';

var initCreate = function() {
    var form = document.querySelector('form[data-fido2-create]');
    if (form) {
        var options = webauthnJSON.parseCreationOptionsFromJSON(
            JSON.parse(form.dataset.fido2Create)
        );
        form.addEventListener('submit', function(event) {
            event.preventDefault();

            webauthnJSON.create(options).then(attestation => {
                this.code.value = JSON.stringify(attestation);
                form.submit();
            }).catch(alert);
        });
    }
};

var initAuth = function() {
    var form = document.querySelector('form[data-fido2-auth]');
    if (form) {
        var options = webauthnJSON.parseRequestOptionsFromJSON(
            JSON.parse(form.dataset.fido2Auth)
        );
        form.addEventListener('submit', function(event) {
            event.preventDefault();

            webauthnJSON.get(options).then(assertion => {
                this.code.value = JSON.stringify(assertion);
                form.submit();
            }).catch(alert);
        });
    }
};

initCreate();
initAuth();
