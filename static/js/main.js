const socket = io.connect(window.location.origin);
socket.on('status_update', function (status) {
    document.getElementById('status').textContent = status;
});