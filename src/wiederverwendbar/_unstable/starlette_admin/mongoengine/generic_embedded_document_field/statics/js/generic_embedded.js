/**
 * This function is called when a select field is changed.
 * @param select - The select field that was changed.
 */
function onchange_generic_emb_select(select) {
    // get the selected value
    let selected_value = select.value;

    // get current id
    let current_id = select.id;

    // get fieldset
    let fieldset_id = current_id + ".fieldset";
    let fieldset = document.getElementById(fieldset_id);

    // get all field divs in the fieldset
    let all_field_divs = fieldset.getElementsByTagName("div");
    let field_divs = [];
    for (let i = 0; i < all_field_divs.length; i++) {
        let field_div = all_field_divs[i];

        // if '.div' is in the id
        if (field_div.id.includes(".div")) {
            field_divs.push(field_div);
        }
    }

    if (selected_value === "") {
        // hide fieldset
        fieldset.style.display = "none";
    } else {
        // show fieldset
        fieldset.style.display = "";

        // hide invisible fields and show visible fields
        for (let i = 0; i < field_divs.length; i++) {
            let field_div = field_divs[i];
            field_div.style.display = "none";
            if (field_div.id.includes(selected_value + ".") && selected_value !== "") {
                field_div.style.display = "";
            }
        }
    }
}

/**
 * This function initializes all select fields with the class 'generic-emb-select
 * @type {HTMLCollectionOf<Element>}
 */
function initialize_generic_emb_select() {
    // get all select fields by class 'generic-emb-select'
    let selects = document.getElementsByClassName("generic-emb-select");

    // call onchange_generic_emb_select for each select field
    for (let i = 0; i < selects.length; i++) {
        let select = selects[i];
        onchange_generic_emb_select(select);
    }
}

// call initialize_generic_emb_select when the document is ready
$(function () {
    initialize_generic_emb_select();
});