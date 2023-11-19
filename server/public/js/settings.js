document.addEventListener('DOMContentLoaded', () => {
    fetch('/config')
        .then(response => response.json())
        .then(content => {
            document.getElementById('target_ap_mac_addresses').value = content.TARGET_AP_MAC_ADDRESSES;
            document.getElementById('target_bt_addresses').value = content.TARGET_BT_ADDRESSES;
        })
        .catch(error => console.error('Error fetching config:', error));

    function configureButton(buttonId, url, key, outputElementId) {
        const button = document.getElementById(buttonId);
        button.addEventListener('click', () => {
            const input = button.parentElement.querySelector('input').value;
            fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: key, value: input })
            })
                .then(response => response.json())
                .then(content => {
                    document.getElementById(outputElementId).value = content[key];
                })
                .catch(error => console.error(`Error at ${buttonId}:`, error));
        });
    }

    configureButton('add-ap', '/add-config-item', 'TARGET_AP_MAC_ADDRESSES', 'target_ap_mac_addresses');
    configureButton('remove-ap', '/remove-config-item', 'TARGET_AP_MAC_ADDRESSES', 'target_ap_mac_addresses');
    configureButton('add-bt', '/add-config-item', 'TARGET_BT_ADDRESSES', 'target_bt_addresses');
    configureButton('remove-bt', '/remove-config-item', 'TARGET_BT_ADDRESSES', 'target_bt_addresses');
});
