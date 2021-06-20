(function() {
    var encode = function(data) {
        var buffer = CBOR.encode(data);
        var typed_arr = new Uint8Array(buffer);
        var arr = Array.from(typed_arr);
        return JSON.stringify(arr);
    };

    var decode = function(json) {
        var arr = JSON.parse(json);
        var typed_arr = new Uint8Array(arr);
        var buffer = typed_arr.buffer;
        return CBOR.decode(buffer);
    };

    var initCreate = function() {
        var form = document.querySelector('form[data-fido2-create]');
        if (form) {
            var options = decode(form.dataset.fido2Create);
            form.addEventListener('submit', function(event) {
                event.preventDefault();

                navigator.credentials.create(options).then(attestation => {
                    this.code.value = encode({
                        'attestationObject': new Uint8Array(attestation.response.attestationObject),
                        'clientData': new Uint8Array(attestation.response.clientDataJSON),
                    });
                    form.submit();
                }).catch(alert);
            });
        }
    };

    var initAuth = function() {
        var form = document.querySelector('form[data-fido2-auth]');
        if (form) {
            var options = decode(form.dataset.fido2Auth);
            form.addEventListener('submit', function(event) {
                event.preventDefault();

                navigator.credentials.get(options).then(assertion => {
                    this.code.value = encode({
                        'credentialId': new Uint8Array(assertion.rawId),
                        'authenticatorData': new Uint8Array(assertion.response.authenticatorData),
                        'clientData': new Uint8Array(assertion.response.clientDataJSON),
                        'signature': new Uint8Array(assertion.response.signature),
                    });
                    form.submit();
                }).catch(alert);
            });
        }
    };

    initCreate();
    initAuth();
})();
