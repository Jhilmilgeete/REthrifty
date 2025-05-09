// Handle collapsible FAQ sections
let coll = document.querySelectorAll(".collapsible");
coll.forEach(function (button) {
    button.addEventListener("click", function () {
        let content = this.nextElementSibling;
        content.style.display = content.style.display === "block" ? "none" : "block";
    });
});

// Handle search functionality
document.getElementById("searchBar").addEventListener("input", function () {
    let searchText = this.value.toLowerCase();
    let sections = document.querySelectorAll(".content");
    
    sections.forEach(function (section) {
        if (section.innerText.toLowerCase().includes(searchText)) {
            section.style.display = "block";
        } else {
            section.style.display = "none";
        }
    });
});

// Scroll to top button
let scrollBtn = document.getElementById("scrollTopBtn");

window.onscroll = function () {
    if (document.documentElement.scrollTop > 100) {
        scrollBtn.style.display = "block";
    } else {
        scrollBtn.style.display = "none";
    }
};

scrollBtn.addEventListener("click", function () {
    window.scrollTo({ top: 0, behavior: "smooth" });
});
