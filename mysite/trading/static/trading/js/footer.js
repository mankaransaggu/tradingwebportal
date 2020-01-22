$('#collapseOne').on('show.bs.collapse', function () {
    $('.panel-heading').animate({
        backgroundColor: "#515151"
    }, 500);
})

$('#collapseOne').on('hide.bs.collapse', function () {
    $('.panel-heading').animate({
        backgroundColor: "#00B4FF"
    }, 500);
})

$(function() {
    var index = 'key';
    var datastore = window.sessionStorage;

    try  {
    var oldIndex = datastore.getItem(index);
    } catch(e) {
        var oldIndex = 0;
    }
    $('#collapseOne')
})