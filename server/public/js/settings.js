document.addEventListener('DOMContentLoaded', () => {
    fetch('/config')
        .then(response => response.json())
        .then(content => {
            document.getElementById('target_ap_mac_addresses').value = content.TARGET_AP_MAC_ADDRESSES;
            document.getElementById('target_bt_addresses').value = content.TARGET_BT_ADDRESSES;
        })
        .catch(error => console.error('Error fetching config:', error));
});
