$(document).ready(function () {
    $(function () {
        $("#query_auto").autocomplete({
            source: "get_cities",
            max:20,
            minLength: 1,
            select: function (event, ui) {
		var name = ui.item.label.replace(/[0-9]/g, '');
                window.open("http://google.com/maps?q=" + name);
                console.log(name ?
                "Selected: " + name :
                "Nothing selected, input was " + this.value);
            }
        });
        
        document.getElementById("query_auto").focus();
    });
})
