document.addEventListener('DOMContentLoaded', () => {
    fetch('/config')
        .then(response => response.json())
        .then(content => {
            document.getElementById('target_ap_mac_addresses').value = content.TARGET_AP_MAC_ADDRESSES;
            document.getElementById('target_bt_addresses').value = content.TARGET_BT_ADDRESSES;
        })
        .catch(error => console.error('Error fetching config:', error));

    fetch('/config')
        .then(response => response.json())
        .then(content => {
            const ap_container = document.getElementById('ap_list')
            const bt_container = document.getElementById('bt_list')

            for (let i = 0; i < content.TARGET_AP_MAC_ADDRESSES.length; i++) {
                let newDiv = document.createElement("div");
                newDiv.className = "mac_address";
                newDiv.innerHTML = content.TARGET_AP_MAC_ADDRESSES[i];
                let newInput = document.createElement("input");
                newInput.type = "hidden";
                newInput.value = content.TARGET_AP_MAC_ADDRESSES[i];
                newDiv.appendChild(newInput);
                let newButton = document.createElement("button");
                newButton.type = "button";
                newButton.innerHTML = "Remove";
                newDiv.appendChild(newButton);
                ap_container.appendChild(newDiv);
                newButton.addEventListener('click', () => {
                    const input = newButton.parentElement.querySelector('input').value;
                    fetch('/remove-config-item', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ key: 'TARGET_AP_MAC_ADDRESSES', value: input })
                    })
                        .then(response => response.json())
                        .then(content => {
                            document.getElementById('target_ap_mac_addresses').value = content['TARGET_AP_MAC_ADDRESSES'];
                            newDiv.remove();
                        })
                        .catch(error => console.error(`Error at ${buttonId}:`, error));
                });
            }
            for (let i = 0; i < content.TARGET_BT_ADDRESSES.length; i++) {
                let newDiv = document.createElement("div");
                newDiv.className = "mac_address";
                newDiv.innerHTML = content.TARGET_BT_ADDRESSES[i];
                let newInput = document.createElement("input");
                newInput.type = "hidden";
                newInput.value = content.TARGET_BT_ADDRESSES[i];
                newDiv.appendChild(newInput);
                let newButton = document.createElement("button");
                newButton.type = "button";
                newButton.innerHTML = "Remove";
                newDiv.appendChild(newButton);
                bt_container.appendChild(newDiv);
                newButton.addEventListener('click', () => {
                    const input = newButton.parentElement.querySelector('input').value;
                    fetch('/remove-config-item', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ key: 'TARGET_BT_ADDRESSES', value: input })
                    })
                        .then(response => response.json())
                        .then(content => {
                            document.getElementById('target_bt_addresses').value = content['TARGET_BT_ADDRESSES'];
                            newDiv.remove();
                        })
                        .catch(error => console.error(`Error at ${buttonId}:`, error));
                });
            }
        }).catch(error => console.error('Error fetching config:', error));

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
            location.reload();
        });
    }

    configureButton('add-ap', '/add-config-item', 'TARGET_AP_MAC_ADDRESSES', 'target_ap_mac_addresses');
    //configureButton('remove-ap', '/remove-config-item', 'TARGET_AP_MAC_ADDRESSES', 'target_ap_mac_addresses');
    configureButton('add-bt', '/add-config-item', 'TARGET_BT_ADDRESSES', 'target_bt_addresses');
    //configureButton('remove-bt', '/remove-config-item', 'TARGET_BT_ADDRESSES', 'target_bt_addresses');
});
