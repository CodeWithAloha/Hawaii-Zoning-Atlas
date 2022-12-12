$(document).ready(function () {
    $('.nav-item').click(function () {
        const navItem = $(this);
        navItem.toggleClass("text-info");
    });
});