registerFieldInitializer(function (element) {
    // get select with id "object"
    const object = $(element).find("select#object");
    if (object.length === 0) {
        throw ("Select with id object not found");
    }

    // get div with id "query_filter"
    const queryFilter = $(element).find("div#query_filter");
    if (queryFilter.length === 0) {
        throw ("Div with id query_filter not found");
    }
    const queryFilterParent = queryFilter.parent();
    const queryFilterInput = $(`input[name="query_filter"]`);
    // empty queryFilter
    queryFilter.empty();
    // create new JSONEditor
    const queryFilterEditor = new JSONEditor(
        queryFilter[0],
        {
            modes: String(queryFilter.data("modes")).split(","),
            onChangeText: function (json) {
                queryFilterInput.val(json);
            },
            templates: [ // ToDO: Add templates for MongoDB Search Query
                // {
                //     text: 'Person',
                //     title: 'Insert a Person Node',
                //     className: 'jsoneditor-type-object',
                //     field: 'PersonTemplate',
                //     value: {
                //         'firstName': 'John',
                //         'lastName': 'Do',
                //         'age': 28
                //     }
                // },
                // {
                //     text: 'Address',
                //     title: 'Insert a Address Node',
                //     field: 'AddressTemplate',
                //     value: {
                //         'street': '',
                //         'city': '',
                //         'state': '',
                //         'ZIP code': ''
                //     }
                // }
            ]
        },
        JSON.parse(queryFilterInput.val())
    );


    // get input with id "allow_read"
    const allowRead = $(element).find("input#allow_read");
    if (allowRead.length === 0) {
        throw ("Input with id allow_read not found");
    }
    const allowReadParent = allowRead.parent().parent().parent();

    // get input with id "allow_create"
    const allowCreate = $(element).find("input#allow_create");
    if (allowCreate.length === 0) {
        throw ("Input with id allow_create not found");
    }
    const allowCreateParent = allowCreate.parent().parent().parent();

    // get input with id "allow_update"
    const allowUpdate = $(element).find("input#allow_update");
    if (allowUpdate.length === 0) {
        throw ("Input with id allow_update not found");
    }
    const allowUpdateParent = allowUpdate.parent().parent().parent();

    // get input with id "allow_delete"
    const allowDelete = $(element).find("input#allow_delete");
    if (allowDelete.length === 0) {
        throw ("Input with id allow_delete not found");
    }
    const allowDeleteParent = allowDelete.parent().parent().parent();

    // get input with id "allow_execute"
    const allowExecute = $(element).find("input#allow_execute");
    if (allowExecute.length === 0) {
        throw ("Input with id allow_execute not found");
    }
    const allowExecuteParent = allowExecute.parent().parent().parent();

    // get select with id "specify_fields"
    const specifyFields = $(element).find("select#specify_fields");
    if (specifyFields.length === 0) {
        throw ("Select with id specify_fields not found");
    }
    const specifyFieldsParent = specifyFields.parent().parent();

    // backup options of specify_fields
    const specifyFieldsOptions = $(specifyFields).find("option")
    let specifyFieldsOptionsValues = [];
    let specifyFieldsOptionsTexts = [];
    let specifyFieldsOptionsCurrentSelected = [];
    for (let i = 0; i < specifyFieldsOptions.length; i++) {
        const option = $(specifyFieldsOptions[i]);
        specifyFieldsOptionsValues.push(option.val());
        specifyFieldsOptionsTexts.push(option.text());
        if (option.is(":selected")) {
            specifyFieldsOptionsCurrentSelected.push(option.val());
        }
    }

    // get select with id "specify_actions"
    const specifyActions = $(element).find("select#specify_actions");
    if (specifyActions.length === 0) {
        throw ("Select with id specify_actions not found");
    }
    const specifyActionsParent = specifyActions.parent().parent();

    // backup options of specify_actions
    const specifyActionsOptions = $(specifyActions).find("option")
    let specifyActionsOptionsValues = [];
    let specifyActionsOptionsTexts = [];
    let specifyActionsOptionsCurrentSelected = [];
    for (let i = 0; i < specifyActionsOptions.length; i++) {
        const option = $(specifyActionsOptions[i]);
        specifyActionsOptionsValues.push(option.val());
        specifyActionsOptionsTexts.push(option.text());
        if (option.is(":selected")) {
            specifyActionsOptionsCurrentSelected.push(option.val());
        }
    }

    // get value of the current selected object
    let currentSelectedObject = object.val();

    // register change event for object select
    object.change(function () {
        // get value of selected object
        const selectedObject = $(this).val();

        // get type of selected object
        const objectType = selectedObject.split(".")[0];

        // hide all elements
        queryFilterParent.hide();
        allowReadParent.hide();
        allowCreateParent.hide();
        allowUpdateParent.hide();
        allowDeleteParent.hide();
        allowExecuteParent.hide();
        specifyFieldsParent.hide();
        specifyActionsParent.hide();

        // show elements if object is selected
        if (selectedObject !== "") {
            if (objectType === "object") {
                queryFilterParent.show();
                specifyFieldsParent.show();
                specifyActionsParent.show();
            }
            if (objectType === "all" || objectType === "object") {
                allowReadParent.show();
                allowCreateParent.show();
                allowUpdateParent.show();
                allowDeleteParent.show();
                allowExecuteParent.show();
            }
        }

        // reset form if selected object has changed
        if (currentSelectedObject !== selectedObject) {
            // empty queryFilterEditor
            queryFilterEditor.setText("{}");
            queryFilterInput.val("{}");

            // uncheck allow_read
            allowRead.prop("checked", false);
            allowRead.trigger("change");

            // uncheck allow_create
            allowCreate.prop("checked", false);
            allowCreate.trigger("change");

            // uncheck allow_update
            allowUpdate.prop("checked", false);
            allowUpdate.trigger("change");

            // uncheck allow_delete
            allowDelete.prop("checked", false);
            allowDelete.trigger("change");

            // uncheck allow_execute
            allowExecute.prop("checked", false);
            allowExecute.trigger("change");

            // empty specify_fields
            specifyFieldsOptionsCurrentSelected = [];

            // empty specify_actions
            specifyActionsOptionsCurrentSelected = [];
        }

        // empty specify_fields
        specifyFields.empty();

        // add options to specify_fields
        for (let i = 0; i < specifyFieldsOptionsValues.length; i++) {
            const value = specifyFieldsOptionsValues[i];
            const text = specifyFieldsOptionsTexts[i];

            // skip if value is not starting with selected object
            if (!value.startsWith(selectedObject + ".")) {
                continue;
            }

            // create option
            const option = $("<option></option>");
            option.val(value);
            option.text(text);

            // set selected if value is in current selected options
            if (specifyFieldsOptionsCurrentSelected.includes(value)) {
                option.attr("selected", "selected");
            }

            // append option to specify_fields#
            specifyFields.append(option);
        }

        // trigger change event for specify_fields
        specifyFields.trigger("change");

        // empty specify_actions
        specifyActions.empty();

        // add options to specify_actions#
        for (let i = 0; i < specifyActionsOptionsValues.length; i++) {
            const value = specifyActionsOptionsValues[i];
            const text = specifyActionsOptionsTexts[i];

            // skip if value is not starting with selected object
            if (!value.startsWith(selectedObject + ".")) {
                continue;
            }

            // create option
            const option = $("<option></option>");
            option.val(value);
            option.text(text);

            // set selected if value is in current selected options
            if (specifyActionsOptionsCurrentSelected.includes(value)) {
                option.attr("selected", "selected");
            }

            // append option to specify_actions
            specifyActions.append(option);
        }

        // trigger change event for specify_fields
        specifyFields.trigger("change");

        // set current selected object
        currentSelectedObject = selectedObject;
    });

    // trigger change event for object select
    object.trigger("change");
});