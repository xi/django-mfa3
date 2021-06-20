document.querySelectorAll('[data-qr]').forEach(function(element) {
    new QRious({
        element: element,
        value: element.dataset.qr,
        size: 200,
    });
});
