const side_bar_btns = document.querySelectorAll("#sidebar-btn");

side_bar_btns.forEach((elem) => {
  elem.addEventListener("click", () => {
    for (let index = 0; index < side_bar_btns.length; index++) {
      side_bar_btns[index].classList.remove("active");
    }
    elem.classList.add("active");
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
  console.log("hello world");

  document.querySelector(".container").style.transform = "scale(0)";

  setTimeout(() => {
    window.alert(
      "The app is minimized but cannot be opened again because the virtual macos crashed!"
    );
  }, 500);
});