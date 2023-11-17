document.addEventListener('DOMContentLoaded', () => {
    fetch('/config')
        .then(response => response.json())
        .then(content => {
            document.getElementById('target_ap_mac_addresses').value = content.TARGET_AP_MAC_ADDRESSES;
            document.getElementById('target_bt_addresses').value = content.TARGET_BT_ADDRESSES;
        })
        .catch(error => console.error('Error fetching config:', error));

    var form = document.querySelector('form');
    form.addEventListener('submit', function (e) {
        e.preventDefault();

        // Create a FormData object, passing in the form
        var formData = new FormData(form);

        fetch('/update-config', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                window.alert("Success");
                console.log('Success:', data);
            })
            .catch((error) => {
                console.error('Error:', error);
            });
    });
});
