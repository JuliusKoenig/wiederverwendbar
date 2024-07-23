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

        // actionLogKey
        this.actionLogClient = null;
        this.actionLogClientIsUsed = false;

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
        this.initActionLogClient(actionLogKey);

        // set on modal-loading close event
        $("#modal-loading").on("hidden.bs.modal", function (event) {
            self.setResultInfo()
        });

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
            this.setActionLogUi();
            fetch(url, {
                method: form ? "POST" : "GET",
                body: form ? new FormData(form) : null,
            })
                .then(async (response) => {
                    await new Promise((r) => setTimeout(r, 500));
                    if (response.ok) {
                        let msg = (await response.json())["msg"];
                        this.setResponseInfo(actionName, element, msg);
                    } else {
                        if (response.status == 400) {
                            return Promise.reject((await response.json())["msg"]);
                        }
                        return Promise.reject("Something went wrong!");
                    }
                })
                .catch(async (error) => {
                    await new Promise((r) => setTimeout(r, 500));
                    this.setResponseInfo(actionName, element, error, true);
                });
        }
    }

    setActionLogUi(actionLog = false) {
        // empty actionLogTextArea
        $("#action-log-textarea").html("");

        // remove class 'modal-sm' and 'modal-full-width' from 'modal-loading-doc'
        $("#modal-loading-doc").removeClass("modal-sm");
        $("#modal-loading-doc").removeClass("modal-full-width");

        // hide 'action-log-progress'
        $("#action-log-progress").hide();

        if (actionLog) {
            // add class 'modal-full-width' to 'modal-loading-doc'
            $("#modal-loading-doc").addClass("modal-full-width");

            /// set width of 'action-log-progress-bar' to 0
            $("#action-log-progress-bar").width("0%");

            // show action-log-textarea
            $("#action-log-textarea").show();

            // set 'action-log-textarea' height
            $("#action-log-textarea").height(0);

            // hide 'action-log-spinner'
            $("#action-log-spinner").hide();
            $("#action-log-spinner-text").hide();
        } else {
            // add class 'modal-sm' to 'modal-loading-doc'
            $("#modal-loading-doc").addClass("modal-sm");

            // hide 'action-log-textarea'
            $("#action-log-textarea").hide();

            // show 'action-log-spinner'
            $("#action-log-spinner").show();
            $("#action-log-spinner-text").show();
        }
        // hide 'modal-loading-close' button
        $("#modal-loading-close").hide();

        // hide 'action-log-copy' button
        $("#action-log-copy").hide();

        // show 'modal-loading'
        $("#modal-loading").modal("show");
    }

    initActionLogClient(actionLogKey) {
        let self = this;
        this.actionLogClient = new WebSocket("ws://" + window.location.host + "/" + window.location.pathname.split("/")[1] + "/ws/action_log/" + actionLogKey);
        this.actionLogClient.onmessage = function (event) {
            self.onActionLogCommand(event)
        };
        this.actionLogClientIsUsed = false;
    }

    onActionLogCommand(event) {
        // parse message
        let data = JSON.parse(event.data);
        if (data["command"] === "start") {
            this.actionLogClientIsUsed = true;
            this.setActionLogUi(true);
        } else if (data["command"] === "finalize") {
            $("#modal-loading-close").show();
            $("#action-log-copy").show();
            this.closeActionLogClient()
        } else if (data["command"] === "log") {
            this.pushActionLogMessage(data["value"]);
        } else if (data["command"] === "use_steps") {
            $("#action-log-progress").show();
        } else if (data["command"] === "step") {
            $("#action-log-progress-bar").width(data["value"] + "%");
        } else {
            console.log("Unknown command received:", data);
        }
    }

    closeActionLogClient() {
        if (this.actionLogClient !== null) {
            this.actionLogClient.close();
            this.actionLogClient = null;
        }
    }

    pushActionLogMessage(msg) {
        // calculate new height
        let newHeight = $("#action-log-textarea").height() + 20
        if (newHeight > 500) {
            newHeight = 500;
        }

        // set 'action-log-textarea' height
        $("#action-log-textarea").height(newHeight);

        // append message to 'action-log-textarea'
        let currentText = $("#action-log-textarea").text();
        if (currentText.length > 0) {
            currentText += "\n";
        }
        currentText += msg;
        $("#action-log-textarea").text(currentText);

        // scroll to bottom
        $("#action-log-textarea").scrollTop($("#action-log-textarea")[0].scrollHeight);
    }

    setResponseInfo(actionName, element, msg, isError = false) {
        this.actionName = actionName;
        this.actionElement = element;
        this.actionMsg = msg;
        this.actionIsError = isError;
        if (!this.actionLogClientIsUsed) {
            $("#modal-loading").modal("hide");
            this.closeActionLogClient()
        }
        if ($("#modal-loading").is(":hidden")) {
            this.setResultInfo()
        }
    }

    setResultInfo() {
        if (!this.actionIsError) {
            this.onSuccess(this.actionName, this.actionElement, this.actionMsg);
        } else {
            this.onError(this.actionName, this.actionElement, this.actionMsg);
        }
    }
}

// set copy to clipboard action
$("#action-log-copy").on("click", function (event) {
    navigator.clipboard.writeText($("#action-log-textarea").text()).then(
        () => {
            console.log("clipboard successfully set");
        },
        () => {
            console.error("clipboard write failed");
        });
});

