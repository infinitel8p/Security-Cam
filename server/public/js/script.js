document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        let currentHref = window.location.href;

        if (currentHref.endsWith('/')) {
            currentHref += 'index.html';
        }

        if (item.href === currentHref) {
            item.classList.add('active');
        }
    });

    // update version div
    function updateSystemInfo() {
        fetch('/version')
            .then(response => response.text())
            .then(data => {
                // Parse RAM usage
                const totalMemMatch = data.match(/MemTotal:\s+(\d+)/);
                const freeMemMatch = data.match(/MemFree:\s+(\d+)/);
                const totalMem = totalMemMatch ? parseInt(totalMemMatch[1]) : 0;
                const freeMem = freeMemMatch ? parseInt(freeMemMatch[1]) : 0;
                const usedMem = totalMem - freeMem;
                const ramUsagePercent = ((usedMem / totalMem) * 100).toFixed(1);

                // Parse Disk usage
                const diskUsageMatch = data.match(/\/dev\/root\s+\S+\s+\S+\s+\S+\s+(\d+)%/);
                const diskUsagePercent = diskUsageMatch ? diskUsageMatch[1] : '0';

                // Parse Load average as CPU usage indicator
                const loadAverageMatch = data.match(/load average: ([\d.]+),/);
                const loadAverage = loadAverageMatch ? Math.round(loadAverageMatch[1] * 100) : 0;

                // Parse Uptime
                const uptimeMatch = data.match(/(\d+)\.\d+\s+\d+/); // Matches the uptime in seconds
                const uptimeSeconds = uptimeMatch ? parseInt(uptimeMatch[1]) : 0;
                const uptimeFormatted = `${Math.floor(uptimeSeconds / 3600)}h ${Math.floor((uptimeSeconds % 3600) / 60)}m ${uptimeSeconds % 60}s`; // Converts seconds to a more readable format

                // Update the HTML elements
                document.querySelector('.version h1:nth-child(1)').textContent = `RAM: ${ramUsagePercent}% used`;
                document.querySelector('.version h1:nth-child(2)').textContent = `CPU Load: ${loadAverage}%`;
                document.querySelector('.version h1:nth-child(3)').textContent = `DISK: ${diskUsagePercent}% used`;
                document.querySelector('.version h1:nth-child(4)').textContent = `UPTIME: ${uptimeFormatted}`;
            })
            .catch(error => console.error('Error fetching system info:', error));
    }
    setInterval(updateSystemInfo, 2000);
    updateSystemInfo();
});

const idea_btns = document.querySelectorAll(".idea");
idea_btns.forEach((btn) => {
    btn.addEventListener("click", () => {
        window.open(btn.getAttribute("href"), "_blank");
    });
});

let min = true;

document.querySelector(".window__close").addEventListener("click", () => {
    document.querySelector(".container").style.display = "none";

    setTimeout(() => {
        window.alert(
            "Oh No! What did you do? Now you have to refresh to open the app again"
        );
    }, 500);
});

document.querySelector(".window__maximize").addEventListener("click", () => {
    if (min == false) {
        min = true;
        document.querySelector(".container").style.width = "90%";
        document.querySelector(".container").style.height = "90%";
    } else {
        min = false;
        document.querySelector(".container").style.width = "100%";
        document.querySelector(".container").style.height = "100%";
    }
});

document.querySelector(".window__minimize").addEventListener("click", () => {
    document.querySelector(".container").style.transform = "scale(0)";

    setTimeout(() => {
        window.alert(
            "The app is minimized but cannot be opened again because the virtual macos crashed!"
        );
    }, 500);
});