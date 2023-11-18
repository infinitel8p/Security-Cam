document.addEventListener('DOMContentLoaded', () => {
    fetch('/config')
        .then(response => response.json())
        .then(content => {
            document.getElementById('target_ap_mac_addresses').value = content.TARGET_AP_MAC_ADDRESSES;
            document.getElementById('target_bt_addresses').value = content.TARGET_BT_ADDRESSES;
        })
        .catch(error => console.error('Error fetching config:', error));

    const addApButton = document.getElementById('add-ap');
    addApButton.addEventListener('click', () => {
        const input = addApButton.parentElement.querySelector('input').value;
        fetch('/add-config-item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key: 'TARGET_AP_MAC_ADDRESSES', value: input })
        })
            .then(response => response.json())
            .then(content => {
                document.getElementById('target_ap_mac_addresses').value = content.TARGET_AP_MAC_ADDRESSES;
            })
            .catch(error => console.error('Error adding config item:', error));
    });

    const removeApButton = document.getElementById('remove-ap');
    removeApButton.addEventListener('click', () => {
        const input = removeApButton.parentElement.querySelector('input').value;
        fetch('/remove-config-item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key: 'TARGET_AP_MAC_ADDRESSES', value: input })
        })
            .then(response => response.json())
            .then(content => {
                document.getElementById('target_ap_mac_addresses').value = content.TARGET_AP_MAC_ADDRESSES;
            })
            .catch(error => console.error('Error removing config item:', error));
    });

    const addBtButton = document.getElementById('add-bt');
    addBtButton.addEventListener('click', () => {
        const input = addBtButton.parentElement.querySelector('input').value;
        fetch('/add-config-item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key: 'TARGET_BT_ADDRESSES', value: input })
        })
            .then(response => response.json())
            .then(content => {
                document.getElementById('target_bt_addresses').value = content.TARGET_BT_ADDRESSES;
            })
            .catch(error => console.error('Error adding config item:', error));
    });

    const removeBtButton = document.getElementById('remove-bt');
    removeBtButton.addEventListener('click', () => {
        const input = removeBtButton.parentElement.querySelector('input').value;
        fetch('/remove-config-item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key: 'TARGET_BT_ADDRESSES', value: input })
        })
            .then(response => response.json())
            .then(content => {
                document.getElementById('target_bt_addresses').value = content.TARGET_BT_ADDRESSES;
            })
            .catch(error => console.error('Error removing config item:', error));
    });
});
