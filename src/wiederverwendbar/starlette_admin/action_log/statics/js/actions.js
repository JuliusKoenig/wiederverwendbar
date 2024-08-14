/**
 * A class for managing bactch and row actions in the admin interface.
 */
class ActionManager {
    /**
     * @param {string} actionUrl - The base URL for actions.
     * @param {string} rowActionUrl - The base URL for row actions.
     * @param {function(URLSearchParams, jQuery)} appendQueryParams - A function to append query parameters to the URL.
     * @param {function(string, jQuery, string)} onSuccess - A callback function to handle successful action responses.
     * @param {function(string, jQuery, string)} onError - A callback function to handle error responses.
     */
    constructor(actionUrl, rowActionUrl, appendQueryParams, onSuccess, onError) {
        this.actionLogStarted = false;
        this.rowActionUrl = rowActionUrl;
        this.actionUrl = actionUrl;
        this.appendQueryParams = appendQueryParams;
        this.onSuccess = onSuccess;
        this.onError = onError;

        // get html elements
        this.modalLoading = $("#modal-loading");
        this.modalLoadingDoc = $("#modal-loading-doc");
        this.actionSpinner = $("#action-spinner");
        this.actionSpinnerText = $("#action-spinner-text");
        this.actionLogContentBody = $("#action-log-content-body");
        this.actionLogAccordion = $("#action-log-accordion");
        this.actionLogFormContainer = $("#action-log-form-container")
        this.actionLogFormBody = $("#action-log-form-body")
        this.actionLogFormAbort = $("#action-log-form-abort")
        this.actionLogFormSubmit = $("#action-log-form-submit")
        this.modalLoadingClose = $("#modal-loading-close");

        // hide actionLogFormContainer
        this.actionLogFormContainer.hide();

        // define accordion item template html
        this.accordionItemTemplate = `<div class="accordion-item">
            <h2 id="{{action-log-accordion-header-}}" class="accordion-header">
                <div class="row">
                    <div class="col float-start ms-1">
                        <div class="d-flex">
                            <span id="{{action-log-accordion-status-}}" class="status-indicator status-blue status-indicator-animated">
                                <span class="status-indicator-circle"></span>
                            </span> 
                            <h3 class="mt-2">
                                {{logger-name}}
                            </h3>
                        </div>
                    </div>
                    <div class="col-2">
                        <div class="d-flex float-end">
                            <button id="{{action-log-copy-}}" type="button" class="btn btn-ghost-secondary fa-regular fa-copy" aria-label="Copy"></button>
                            <button class="accordion-button action-log-accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#{{action-log-accordion-collapse-}}" aria-expanded="true"></button>
                        </div>
                    </div>
                </div>
                
            </h2>
            <div id="{{action-log-accordion-collapse-}}" class="accordion-collapse collapse show action-log-accordion-collapse" data-bs-parent="#action-log-accordion" style="">
                <div class="accordion-body pt-0">
                    <div id="{{action-log-progress-}}" class="progress progress-sm" style="display: none">
                        <div id="{{action-log-progress-bar-}}" class="progress-bar" role="progressbar"></div>
                    </div>
                    <div id="{{action-log-content-body-}}">
                        <textarea id="{{action-log-textarea-}}" class="form-control mb-1" name="action-log" placeholder="Empty Log" readonly></textarea>
                    </div>
                    <div id="{{action-log-form-container-}}">
                        <div id="{{action-log-form-body-}}"></div>
                        <div class="row mt-1">
                            <div class="col">
                                <button id="{{action-log-form-abort-}}" type="button" class="btn btn-red float-end" aria-label="Abort"></button>
                                <button id="{{action-log-form-submit-}}" type="button" class="btn float-end me-2" aria-label="Submit"></button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`

        // define template id prefixes
        this.actionLogAccordionHeaderIdPrefix = "action-log-accordion-header-";
        this.actionLogAccordionStatusIdPrefix = "action-log-accordion-status-";
        this.actionLogAccordionCollapseIdPrefix = "action-log-accordion-collapse-";
        this.actionLogProgressIdPrefix = "action-log-progress-";
        this.actionLogProgressBarIdPrefix = "action-log-progress-bar-";
        this.actionLogContentBodyIdPrefix = "action-log-content-body-";
        this.actionLogTextareaIdPrefix = "action-log-textarea-";
        this.actionLogCopyIdPrefix = "action-log-copy-";
        this.actionLogFormContainerIdPrefix = "action-log-form-container-";
        this.actionLogFormBodyIdPrefix = "action-log-form-body-";
        this.actionLogFormSubmitIdPrefix = "action-log-form-submit-";
        this.actionLogFormAbortIdPrefix = "action-log-form-abort-";

        // define subLoggerNames aray
        this.subLoggerNames = [];

        // actionLogKey
        this.actionLogClient = null;
    }

    /**
     * Initialize actions that do not require user confirmation.
     */
    initNoConfirmationActions() {
        let self = this;
        $('a[data-no-confirmation-action="true"]').each(function () {
            $(this).on("click", function (event) {
                let isRowAction = $(this).data("is-row-action") === true;
                self.submitAction(
                    $(this).data("name"),
                    null,
                    $(this).data("custom-response") === true,
                    isRowAction,
                    $(this)
                );
            });
        });
    }

    /**
     * Initialize actions that trigger a modal dialog for user confirmation.
     */
    initActionModal() {
        let self = this;
        $("#modal-action").on("show.bs.modal", function (event) {
            let button = $(event.relatedTarget); // Button that triggered the modal
            let confirmation = button.data("confirmation");
            let form = button.data("form");
            let name = button.data("name");
            let submit_btn_text = button.data("submit-btn-text");
            let submit_btn_class = button.data("submit-btn-class");
            let customResponse = button.data("custom-response") === true;
            let isRowAction = button.data("is-row-action") === true;

            let modal = $(this);
            modal.find("#actionConfirmation").text(confirmation);
            let modalForm = modal.find("#modal-form");
            modalForm.html(form);
            let actionSubmit = modal.find("#actionSubmit");
            actionSubmit.text(submit_btn_text);
            actionSubmit.removeClass().addClass(`btn ${submit_btn_class}`);
            actionSubmit.unbind();
            actionSubmit.on("click", function (event) {
                const formElements = modalForm.find("form");
                const form = formElements.length ? formElements.get(0) : null;
                self.submitAction(name, form, customResponse, isRowAction, button);
            });
        });
    }

    /**
     * Submit an action to the server.
     * @param {string} actionName - The name of the action.
     * @param {HTMLFormElement | null} form - The HTML form associated with the action.
     * @param {boolean} customResponse
     * @param {boolean} isRowAction - Whether the action is a row action.
     * @param {jQuery} element - The element that triggered the action.
     */
    submitAction(actionName, form, customResponse, isRowAction, element) {
        let self = this;
        if (this.actionLogClient !== null) {
            console.log("Action already in progress!");
            return;
        }

        // generate actionLogKey
        let actionLogKey = window.crypto.randomUUID();

        // init actionLogClient
        this.actionLogClient = new WebSocket("ws://" + window.location.host + "/" + window.location.pathname.split("/")[1] + "/ws/action_log/" + actionLogKey);
        this.actionLogClient.onmessage = function (event) {
            self.onActionLogCommand(event)
        };

        let baseUrl = isRowAction ? this.rowActionUrl : this.actionUrl;
        let query = new URLSearchParams();
        query.append("name", actionName);

        // append actionLogKey to query
        query.append("actionLogKey", actionLogKey);

        this.appendQueryParams(query, element);
        let url = baseUrl + "?" + query.toString();
        if (customResponse) {
            if (form) {
                form.action = url;
                form.method = "POST";
                form.submit();
            } else {
                window.location.replace(url);
            }
        } else {
            this.resetModalLoading();
            fetch(url, {
                method: form ? "POST" : "GET",
                body: form ? new FormData(form) : null,
            })
                .then(async (response) => {
                    await new Promise((r) => setTimeout(r, 500));
                    if (response.ok) {
                        let msg = (await response.json())["msg"];
                        this.setResponse(actionName, element, msg);
                    } else {
                        if (response.status === 400) {
                            return Promise.reject((await response.json())["msg"]);
                        }
                        return Promise.reject("Something went wrong!");
                    }
                })
                .catch(async (error) => {
                    await new Promise((r) => setTimeout(r, 500));
                    this.setResponse(actionName, element, error, true);
                });
        }
    }

    setResponse(actionName, element, msg, isError = false) {
        if (this.actionLogClient === null) {
            console.log("ActionLogClient is not initialized!");
            return;
        }

        // show response message
        if (isError) {
            this.onError(actionName, element, msg);
        } else {
            this.onSuccess(actionName, element, msg);
        }

        // hide 'modal-loading' or show 'modal-loading-close' button
        if (this.subLoggerNames.length > 0) {
            this.modalLoadingClose.show();
        } else {
            this.modalLoading.modal("hide");
        }

        // close actionLogClient
        this.actionLogClient.close();
        this.actionLogClient = null;
        this.subLoggerNames = [];
    }

    resetModalLoading() {
        // add class 'modal-sm' to 'modal-loading-doc' if it does not have it
        if (!this.modalLoadingDoc.hasClass("modal-sm")) {
            this.modalLoadingDoc.addClass("modal-sm");
        }

        // remove class 'modal-full-width' from 'modal-loading-doc' if it has it
        if (this.modalLoadingDoc.hasClass("modal-full-width")) {
            this.modalLoadingDoc.removeClass("modal-full-width");
        }

        // show 'actionSpinner'
        this.actionSpinner.show();

        // show 'actionSpinnerText'
        this.actionSpinnerText.show();

        // hide 'actionLogContentBody'
        this.actionLogContentBody.hide();

        // empty actionLogAccordion
        this.actionLogAccordion.html("");

        // hide actionLogFormContainer
        this.actionLogFormContainer.hide();

        // hide 'modalLoadingClose' button
        this.modalLoadingClose.hide();

        // show 'modalLoading'
        this.modalLoading.modal("show");

        this.actionLogStarted = false;
    }

    initActionLog() {
        // remove class 'modal-sm' if it has it
        if (this.modalLoadingDoc.hasClass("modal-sm")) {
            this.modalLoadingDoc.removeClass("modal-sm");
        }

        // add class 'modal-full-width' to 'modal-loading-doc' if it does not have it
        if (!this.modalLoadingDoc.hasClass("modal-full-width")) {
            this.modalLoadingDoc.addClass("modal-full-width");
        }

        // hide 'actionSpinner'
        this.actionSpinner.hide();

        // hide 'actionSpinnerText'
        this.actionSpinnerText.hide();

        // show 'actionLogContentBody'
        this.actionLogContentBody.show();

        // empty actionLogAccordion
        this.actionLogAccordion.html("");

        // hide 'modalLoadingClose' button
        this.modalLoadingClose.hide();

        // show 'modalLoading'
        this.modalLoading.modal("show");

        this.actionLogStarted = true;
    }

    copyClipboard(actionLogTextAreaId) {
        // get actionLogTextArea
        let actionLogTextArea = $("#" + actionLogTextAreaId);
        if (actionLogTextArea.length === 0) {
            alert("actionLogTextArea not found: " + actionLogTextAreaId);
            return;
        }

        // copy to clipboard
        navigator.clipboard.writeText(actionLogTextArea.text()).then(
            () => {
            },
            () => {
                alert("clipboard write failed from " + actionLogTextAreaId);
            });
    }

    onActionLogCommand(event) {
        let self = this;

        // parse message
        let data = JSON.parse(event.data);

        // get arguments
        let subLogger = data["sub_logger"];
        let command = data["command"];
        let value = data["value"];

        // check if it is a global command
        let globalCommand = false;
        if (subLogger === "") {
            globalCommand = true;
        }

        // check if action log is initialized
        if (!this.actionLogStarted) {
            this.initActionLog();
        }

        if (command === "start" && !globalCommand) {
            // check if subLogger is in subLoggerNames
            if (this.subLoggerNames.includes(subLogger)) {
                alert("SubLogger already exists: " + subLogger);
                return;
            }

            // get accordion template
            let accordionTemplate = this.accordionItemTemplate;

            // replace all placeholders
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogAccordionHeaderIdPrefix + "}}", this.actionLogAccordionHeaderIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogAccordionStatusIdPrefix + "}}", this.actionLogAccordionStatusIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogAccordionCollapseIdPrefix + "}}", this.actionLogAccordionCollapseIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogProgressIdPrefix + "}}", this.actionLogProgressIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogProgressBarIdPrefix + "}}", this.actionLogProgressBarIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogContentBodyIdPrefix + "}}", this.actionLogContentBodyIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogTextareaIdPrefix + "}}", this.actionLogTextareaIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogCopyIdPrefix + "}}", this.actionLogCopyIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogFormContainerIdPrefix + "}}", this.actionLogFormContainerIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogFormBodyIdPrefix + "}}", this.actionLogFormBodyIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogFormSubmitIdPrefix + "}}", this.actionLogFormSubmitIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogFormAbortIdPrefix + "}}", this.actionLogFormAbortIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{logger-name}}", value);

            // create accordion item
            let accordionItem = $(accordionTemplate);

            // append accordion item to actionLogAccordion
            this.actionLogAccordion.append(accordionItem);

            // get copy button
            let copyButton = $("#" + this.actionLogCopyIdPrefix + subLogger);

            // set copy to clipboard action
            copyButton.on("click", function (_) {
                self.copyClipboard(self.actionLogTextareaIdPrefix + subLogger);
            });

            // hide copy button
            copyButton.hide();

            // set actionLogTextArea height
            $("#" + this.actionLogTextareaIdPrefix + subLogger).height(500);

            // get form container
            let formContainer = $("#" + this.actionLogFormContainerIdPrefix + subLogger);

            // hide form container
            formContainer.hide();

            // collapse all accordion items
            let accordionButtons = $(".action-log-accordion-button");
            let accordionCollapses = $(".action-log-accordion-collapse");
            accordionButtons.attr("aria-expanded", "false");
            accordionButtons.addClass("collapsed");
            accordionCollapses.removeClass("show");

            // show new accordion item
            let accordionButton = $("#" + this.actionLogAccordionHeaderIdPrefix + subLogger);
            let accordionCollapse = $("#" + this.actionLogAccordionCollapseIdPrefix + subLogger);
            accordionButton.attr("aria-expanded", "true");
            accordionButton.removeClass("collapsed");
            accordionCollapse.addClass("show");

            // add subLogger to subLoggerNames
            this.subLoggerNames.push(subLogger);
        } else if (command === "log" && !globalCommand) {
            // check if subLogger is in subLoggerNames
            if (!this.subLoggerNames.includes(subLogger)) {
                alert("SubLogger does not exist: " + subLogger);
                return;
            }

            // get actionLogTextArea
            let actionLogTextArea = $("#" + this.actionLogTextareaIdPrefix + subLogger);

            // get current text
            let currentText = actionLogTextArea.text();
            if (currentText.length > 0) {
                currentText += "\n";
            }
            currentText += value;

            // set new text
            actionLogTextArea.text(currentText);

            // scroll to bottom
            actionLogTextArea.scrollTop(actionLogTextArea[0].scrollHeight);

        } else if (command === "step" && !globalCommand) {
            // check if subLogger is in subLoggerNames
            if (!this.subLoggerNames.includes(subLogger)) {
                alert("SubLogger does not exist: " + subLogger);
                return;
            }

            // get actionLogProgress and actionLogProgressBar
            let actionLogProgress = $("#" + this.actionLogProgressIdPrefix + subLogger);
            let actionLogProgressBar = $("#" + this.actionLogProgressBarIdPrefix + subLogger);

            // show actionLogProgress
            actionLogProgress.show();

            // set width of actionLogProgressBar
            actionLogProgressBar.width(value + "%");
        } else if (command === "form") {
            // check if subLogger is in subLoggerNames
            if (!this.subLoggerNames.includes(subLogger) && !globalCommand) {
                alert("SubLogger does not exist: " + subLogger);
                return;
            }

            // get form arguments
            let formHtml = value["form"];
            let formBtnSubmitText = value["submit_btn_text"];
            let formBtnAbortText = value["abort_btn_text"];

            let actionLogContentBody;
            let formContainer;
            let formBody;
            let formSubmit;
            let formAbort;
            if (globalCommand) {
                actionLogContentBody = this.actionLogContentBody;
                formContainer = this.actionLogFormContainer;
                formBody = this.actionLogFormBody;
                formSubmit = this.actionLogFormSubmit;
                formAbort = this.actionLogFormAbort;
            } else {
                actionLogContentBody = $("#" + this.actionLogContentBodyIdPrefix + subLogger);
                formContainer = $("#" + this.actionLogFormContainerIdPrefix + subLogger);
                formBody = $("#" + this.actionLogFormBodyIdPrefix + subLogger);
                formSubmit = $("#" + this.actionLogFormSubmitIdPrefix + subLogger);
                formAbort = $("#" + this.actionLogFormAbortIdPrefix + subLogger);
            }

            // hide content body
            actionLogContentBody.hide();

            // set form body
            formBody.html(formHtml);

            // set form submit button text
            formSubmit.text(formBtnSubmitText);

            // set form submit button action
            formSubmit.off("click");
            formSubmit.on("click", function (_) {
                // get form data
                let formData = Object.fromEntries(new FormData(formBody.find("form")[0]).entries());

                // create form response object
                let formResponseObj = {
                    "result": true,
                    "form_data": formData
                };

                // send form data
                self.sendCommand(subLogger, "form", formResponseObj);

                // hide form container
                formContainer.hide();

                // show content body
                actionLogContentBody.show();
            });

            // set form abort button text
            formAbort.text(formBtnAbortText);

            // set form abort button action
            formAbort.off("click");
            formAbort.on("click", function (_) {
                // create form response object
                let formResponseObj = {
                    "result": false,
                    "form_data": {}
                };

                // send form data
                self.sendCommand(subLogger, "form", formResponseObj);

                // hide form container
                formContainer.hide();

                // show content body
                actionLogContentBody.show();
            });

            // show form container
            formContainer.show();
        } else if (command === "finalize" && !globalCommand) {
            // check if subLogger is in subLoggerNames
            if (!this.subLoggerNames.includes(subLogger)) {
                alert("SubLogger does not exist: " + subLogger);
                return;
            }

            // get copy button
            let copyButton = $("#" + this.actionLogCopyIdPrefix + subLogger);

            // show copy button
            copyButton.show();

            // get actionLogStatus
            let actionLogStatus = $("#" + this.actionLogAccordionStatusIdPrefix + subLogger);

            // get actionLogProgressBar
            let actionLogProgressBar = $("#" + this.actionLogProgressBarIdPrefix + subLogger);

            // disable actionLogStatus animation
            actionLogStatus.removeClass("status-indicator-animated");

            if (value) {
                // make green
                actionLogStatus.removeClass("status-blue").addClass("status-green");
                actionLogProgressBar.addClass("bg-green");
            } else {
                // make red
                actionLogStatus.removeClass("status-blue").addClass("status-red");
                actionLogProgressBar.addClass("bg-red");
            }
        } else {
            alert("Unknown command received - subLogger: '" + subLogger + "' command: '" + command + "' value: '" + value + "'");
        }
    }

    sendCommand(subLogger, command, value) {
        if (this.actionLogClient === null) {
            console.log("ActionLogClient is not initialized!");
            return;
        }

        this.actionLogClient.send(JSON.stringify({
            "sub_logger": subLogger,
            "command": command,
            "value": value
        }));
    }
}
