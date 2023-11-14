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
        console.log(min);
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