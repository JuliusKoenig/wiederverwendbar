registerFieldInitializer(function (element) {
    // find all elements with class field-boolean-also
    let fieldBooleanAlso = $(".field-boolean-also", element);
    // iterate over all found elements
    fieldBooleanAlso.each(function () {
        // get the current element
        let el = $(this);

        // get data from dataset
        let also = el.data("booleanAlso");

        // get the related field
        let related = $(`#${also}`);

        // add an event listener
        el.on("change", function () {
            // get the value of the current field
            let value = el.prop("checked");

            // skip false values
            if (!value) {
                return;
            }

            // set the value of the related field to the value of the current field
            related.prop("checked", value);

            // trigger change event on related field
            related.trigger("change");
        });

        // add a reverse event listener for true values of the related field
        related.on("change", function () {
            // get the value of the related field
            let value = related.prop("checked");

            // skip true values
            if (value) {
                return;
            }

            // set the value of the current field to false
            el.prop("checked", false);

            // trigger change event on current field
            el.trigger("change");
        });
    });
});