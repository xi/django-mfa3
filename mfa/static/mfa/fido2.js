(function() {
    var encode = function(data) {
        var buffer = CBOR.encode(data);
        var arr = new Uint8Array(buffer);
        return arr.reduce((s, b) => s + b.toString(16).padStart(2, '0'), '');
    };

    var decode = function(hex) {
        var arr = new Uint8Array(hex.length / 2);
        for (var i = 0; i < arr.length; i += 1) {
            arr[i] = parseInt(hex.substring(i * 2, i * 2 + 2), 16);
        }
        return CBOR.decode(arr.buffer);
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
