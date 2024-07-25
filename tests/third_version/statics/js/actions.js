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
        this.actionLogAccordion = $("#action-log-accordion");
        this.modalLoadingClose = $("#modal-loading-close");

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
                    <textarea id="{{action-log-textarea-}}" class="form-control mb-1" name="action-log" placeholder="Empty Log" readonly></textarea>
                </div>
            </div>
        </div>`

        // define template id prefixes
        this.actionLogAccordionHeaderIdPrefix = "action-log-accordion-header-";
        this.actionLogAccordionStatusIdPrefix = "action-log-accordion-status-";
        this.actionLogAccordionCollapseIdPrefix = "action-log-accordion-collapse-";
        this.actionLogProgressIdPrefix = "action-log-progress-";
        this.actionLogProgressBarIdPrefix = "action-log-progress-bar-";
        this.actionLogTextareaIdPrefix = "action-log-textarea-";
        this.actionLogCopyIdPrefix = "action-log-copy-";

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

        // show 'action-spinner'
        this.actionSpinner.show();

        // show 'action-spinner-text'
        this.actionSpinnerText.show();

        // hide 'action-log-accordion'
        this.actionLogAccordion.hide();

        // empty actionLogAccordion
        this.actionLogAccordion.html("");

        // hide 'modal-loading-close' button
        this.modalLoadingClose.hide();

        // show 'modal-loading'
        this.modalLoading.modal("show");
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

        // hide 'action-spinner'
        this.actionSpinner.hide();

        // hide 'action-spinner-text'
        this.actionSpinnerText.hide();

        // show 'action-log-accordion'
        this.actionLogAccordion.show();

        // empty actionLogAccordion
        this.actionLogAccordion.html("");

        // hide 'modal-loading-close' button
        this.modalLoadingClose.hide();

        // show 'modal-loading'
        this.modalLoading.modal("show");
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
            () => {},
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

        if (command === "start") {
            // check if action log is initialized
            if (this.subLoggerNames.length === 0) {
                this.initActionLog();
            }

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
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogTextareaIdPrefix + "}}", this.actionLogTextareaIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{" + this.actionLogCopyIdPrefix + "}}", this.actionLogCopyIdPrefix + subLogger);
            accordionTemplate = accordionTemplate.replaceAll("{{logger-name}}", value);

            // create accordion item
            let accordionItem = $(accordionTemplate);

            // append accordion item to actionLogAccordion
            this.actionLogAccordion.append(accordionItem);

            // set copy to clipboard action
            $("#" + this.actionLogCopyIdPrefix + subLogger).on("click", function (_) {
                self.copyClipboard(self.actionLogTextareaIdPrefix + subLogger);
            });

            // set actionLogTextArea height
            $("#" + this.actionLogTextareaIdPrefix + subLogger).height(0);

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
        } else if (command === "log") {
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

            // calculate new height
            let lineHeight = parseInt(actionLogTextArea.css("line-height"));
            let lineCount = currentText.split("\n").length - 1;
            let newHeight = actionLogTextArea.height() + (lineCount) * lineHeight;
            if (newHeight > 500) {
                newHeight = 500;
            }

            // set new text
            actionLogTextArea.text(currentText);

            // set actionLogTextArea height
            actionLogTextArea.height(newHeight);

            // scroll to bottom
            actionLogTextArea.scrollTop(actionLogTextArea[0].scrollHeight);

        } else if (command === "step") {
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
        } else if (command === "finalize") {
            // check if subLogger is in subLoggerNames
            if (!this.subLoggerNames.includes(subLogger)) {
                alert("SubLogger does not exist: " + subLogger);
                return;
            }

            let actionLogStatus = $("#" + this.actionLogAccordionStatusIdPrefix + subLogger);
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
            alert("Unknown command received - subLogger: " + subLogger + " command: " + command + " value: " + value);
        }
    }
}

// // set copy to clipboard action
// $("#action-log-copy").on("click", function (event) {
//     navigator.clipboard.writeText($("#action-log-textarea").text()).then(
//         () => {
//             console.log("clipboard successfully set");
//         },
//         () => {
//             console.error("clipboard write failed");
//         });
// });

