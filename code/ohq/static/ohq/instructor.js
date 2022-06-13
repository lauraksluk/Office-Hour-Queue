"use strict"

function getWaitingQuestions() {
    $.ajax({
        type: "GET",
        url: "/ohq/waiting-questions",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: update,
        error: updateError
    });
}

function disableAssignButtons() {
    $("#get-assigned-question").attr("disabled", true)
    $(".choose-question-button").attr("disabled", true)
}

function enableAssignButtons() {
    $("#get-assigned-question").attr("disabled", false)
    $(".choose-question-button").attr("disabled", false)
}

function checkIfAssigned() {
    $.ajax({
        type: "GET",
        url: "/ohq/check_if_assigned",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: function(data) {
            if (data.assigned === "true") {
                disableAssignButtons()
            } else {
                enableAssignButtons()
            }
        },
        error: updateError
    });
}

function assignQuestion() {
    $.ajax({
        type: "POST",
        url: '/ohq/assign_student_from_top_of_queue',
        data: "queue_id=" + this_queue_id + "&csrfmiddlewaretoken="+getCSRFToken(),
        dataType: "json",
        success: function(question) { updateNewQuestion(question); getWaitingQuestions(); disableAssignButtons()},
        error: updateError
    });
}

function assignQuestionFromList(question_id) {
    $.ajax({
        type: "POST",
        url: '/ohq/assign_student_from_list',
        data: "queue_id=" + this_queue_id + "&question_id="+question_id+"&csrfmiddlewaretoken="+getCSRFToken(),
        dataType: "json",
        success: function(question) { updateNewQuestion(question); getWaitingQuestions(); disableAssignButtons()},
        error: updateError
    });
}

function getAssignedQuestion() {
    $.ajax({
        type: "GET",
        url: '/ohq/get-assigned-question',
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: updateNewQuestion,
        error: updateError
    });
}

function getQueueStatus() {
    $.ajax({
        type: "GET",
        url: "/ohq/queue-status",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: updateQueueStatus,
        error: updateError
    });
}

function setQueueStatus(endState) {
    $.ajax({
        url: "/ohq/set-queue-status",
        type: "POST",
        data: "queue_id=" + this_queue_id + "&end_state="+endState+"&csrfmiddlewaretoken="+getCSRFToken(),
        dataType : "json",
        success: getQueueStatus,
        error: updateError
    });
}

function removeQuestionFromList() {
    $.ajax({
        type: "POST",
        url: '/ohq/instruct-remove-question',
        data: "queue_id=" + this_queue_id + "&csrfmiddlewaretoken="+getCSRFToken(),
        dataType: "json",
        success: function() { getAssignedQuestion(); getWaitingQuestions() },
        error: updateError
    });
}

function finishCurrentQuestion() {
    $.ajax({
        type: "POST",
        url: '/ohq/finish-current-question',
        data: "queue_id=" + this_queue_id + "&csrfmiddlewaretoken="+getCSRFToken(),
        dataType: "json",
        success: function() { getAssignedQuestion(); getWaitingQuestions(); enableAssignButtons()},
        error: updateError
    });
}

function endOHSession() {
    $.ajax({
        type: "POST",
        url: '/ohq/end_office_hour_session',
        data: "queue_id=" + this_queue_id + "&csrfmiddlewaretoken="+getCSRFToken(),
        dataType: "json",
        success: function() { getAssignedQuestion(); getWaitingQuestions(); getAnnouncementsInstructor(); getQueueStatus() },
        error: updateError
    });
}

function getAnnouncementsInstructor() {
    $.ajax({
        type: "GET",
        url: "/ohq/get-announcements",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: updateAnnouncementsInstructor,
        error: updateError
    });
}

function updateAnnouncementsInstructor(items) {
    // remove questions that don't exist in items anymore
    let announcements = items["announcements"]

    $(".announcement-div").each(function () {
        let announcement_div_id = this.id
        let found = false

        $(items).each(function () {
            if (announcement_div_id === "id_announcement_div_" + this.announcement_id) {
                found = true
            }
        })

        if (!found) {
            this.remove()
        }
    })

    $(announcements).each(function (index) {
        if (this.type === "announcement") {
            let announcement_div_id = "id_announcement_div_" + this.announcement_id

            if (document.getElementById(announcement_div_id) == null) {
                $("#announcements-content").prepend(
                    '<div id="' + announcement_div_id + '" class="announcement-div">' +
                    '<div class="poster-info">' + this.announcement_poster + '</div>' +
                    '<div class="announcement-message">' + this.announcement_content + '</div>' +
                    '<div class="announcement-creation-time">' + this.announcement_creation_time + '</div>' +
                    '<br>' +
                    '</div>'
                )
    
                if (index === items.length - 1 && !first_refresh && this_page === "student") {
                    alert("Instructor announcement: " + this.announcement_content)
                }
            }
        } else if (this.type === "private_message") {
            let private_message_div_id = "id_announcement_div_" + this.private_message_id

            if (document.getElementById(private_message_div_id) == null ) {
                $("#announcements-content").prepend(
                    '<div id="' + private_message_div_id + '" class="announcement-div">' +
                    '<div class="pm-poster-info" style="color: red">' + "(Private Message to " + this.private_message_receiver_name + ") " + this.private_message_poster + '</div>' +
                    '<div class="private-message-message">' + this.private_message_content + '</div>' +
                    '<div class="private-message-creation-time">' + this.private_message_creation_time + '</div>' +
                    '<br>' +
                    '</div>'
                )
    
                if (index === items.length - 1 && !first_refresh && this_page === "student") {
                    alert("Instructor Private message: " + this.private_message_content)
                }
            }
        }
    })
    first_refresh = false
}

function update(items) {
    updateList(items)
    updateQuestionsCount(items)
}

function updateList(items) {
    // remove questions that don't exist in items anymore
    $(".question-div").each(function () {
        let question_div_id = this.id
        let found = false

        $(items).each(function () {
            if (question_div_id === "id_question_div_" + this.id) {
                found = true
            }
        })

        if (!found) {
            this.remove()
        }
    })

    // add new questions in items
    $(items).each(function () {
        let question_div_id = "id_question_div_" + this.id
        let question_content_id = "id_question_content_" + this.id
        let question_location_id = "id_question_location_" + this.id
        let question_type_id = "id_question_type_" + this.id

        if (document.getElementById(question_div_id) == null) {
            let choose_question_button_id = "choose-question-button-" + this.id
            let send_private_message_button_id = "send-private-message-button-" + this.id
            let type = "'question_list'"
            $("#questions").append(
                '<div id="' + question_div_id + '" class="question-div">' +

                '<div class="student-info">' + `${this.student_name}` + " " + `(${this.student_email})` + '</div>' +
                '<div class="question-location" id="' + question_location_id + '">' + 'Location: ' + this.location + '</div>' +
                '<div class="question-type" id="' + question_type_id + '">' + 'Type: ' + this.question_type + '</div>' +
                '<div class="question-content" id="' + question_content_id + '">' + 'Question: ' + this.content + '</div>' +
                '<button id="' + choose_question_button_id + '" onclick="assignQuestionFromList(' + this.id + ')" class="choose-question-button">Help This Student</button>' +
                '<input type="button" value="Send Private Message" id="' + send_private_message_button_id + '" onclick="addPrivateMessageTextarea(' + this.id + "," + this.student_id + "," + type + ')" class="send-message-button">' +
                '<br>' +
                '</div>' +
                '<br>'
            )
        } else {
            let updated_question = "Question: " + this.content
            let question_content = document.getElementById(question_content_id)
            if (question_content.innerHTML != updated_question) {
                question_content.innerHTML = updated_question
            }

            let updated_location = "Location: " + this.location
            let question_location = document.getElementById(question_location_id)
            if (question_location.innerHTML != updated_location) {
                question_location.innerHTML = updated_location
            }

            let updated_type = "Type: " + this.question_type
            let question_type = document.getElementById(question_type_id)
            if (question_type.innerHTML != updated_type) {
                question_type.innerHTML = updated_type
            }
        }
    })
}

function addPrivateMessageTextarea(question_id, student_id, type) {
    var input = document.createElement("input");
    input.setAttribute("class", "private-message-input")
    input.setAttribute("id", "private-message-input-" + question_id)

    var submit_button = document.createElement("button");
    submit_button.setAttribute("class", "submit-private-message-button")
    submit_button.setAttribute("id", "submit-private-message-button-" + question_id)
    submit_button.setAttribute("onclick", "sendPrivateMessage(" + student_id + ")")
    submit_button.innerHTML = "Submit"

    var cancel_button = document.createElement("button");
    cancel_button.setAttribute("class", "cancel-private-message-button")
    cancel_button.setAttribute("id", "cancel-private-message-button-" + question_id)
    cancel_button.setAttribute("onclick", "deletePrivateMessageTextarea(" + question_id + ",'" + type + "')")
    cancel_button.innerHTML = "Cancel"

    if (type == "question_list") {
        var question = document.getElementById("id_question_div_" + question_id)
        document.getElementById('send-private-message-button-' + question_id).setAttribute("disabled", true)
    } else {
        var question = document.getElementById("id_assigned_question_div_" + question_id)
        document.getElementById('send-private-message-assigned-question-button-' + question_id).setAttribute("disabled", true)
    }

    question.appendChild(input);
    question.appendChild(submit_button);
    question.appendChild(cancel_button);
}

function deletePrivateMessageTextarea(question_id, type) {
    var input = document.getElementById("private-message-input-" + question_id)
    var submit_button = document.getElementById("submit-private-message-button-" + question_id)
    var cancel_button = document.getElementById("cancel-private-message-button-" + question_id)

    if (type == "question_list") {
        var question = document.getElementById("id_question_div_" + question_id)
        document.getElementById('send-private-message-button-' + question_id).removeAttribute("disabled")
    } else {
        var question = document.getElementById("id_assigned_question_div_" + question_id)
        document.getElementById('send-private-message-assigned-question-button-' + question_id).removeAttribute("disabled")
    }

    question.removeChild(input);
    question.removeChild(submit_button);
    question.removeChild(cancel_button);
}

function sendPrivateMessage(receiveUserId) {
    let itemTextElement = $("." + "private-message-input")
    let privateMessageContent = itemTextElement.val()

    // Clear input box and old error message (if any)
    itemTextElement.val('')
    displayError('');

    $.ajax({
        url: '/ohq/send_private_message',
        type: "POST",
        data: "queue_id=" + this_queue_id + "&private_message_content=" + privateMessageContent 
            + "&receive_user_id=" + receiveUserId + "&csrfmiddlewaretoken="+getCSRFToken(),
        dataType: "json",
        success: function() { getAnnouncementsInstructor(); },
        error: updateError
    });
}

function updateQuestionsCount(items) {
    let num_questions = items.length

    let color = "green"
    if (num_questions > 20) {
        color = "red"
    } else if (num_questions > 10) {
        color = "yellow"
    }

    $("#student-number").html(num_questions)

    document.getElementById("student-number").style.backgroundColor = color
}

function updateNewQuestion(question) {
    if (question.status == "false") {
        $("#assigned-question-status").html("Hang on! There is no student in queue.")
        document.getElementById("assigned-question-status").style.color = "red"
        $("#assigned-question-content").html("")
    } else if (question.status == "no_question") {
        $("#assigned-question-status").html("You are not assigned a question at this point.")
        document.getElementById("assigned-question-status").style.color = "black"
        $("#assigned-question-content").html("")
        $("#instruct-remove-question").html("")
    } else {
        $("#assigned-question-status").html("You are assigned to answer the following question:")
        document.getElementById("assigned-question-status").style.color = "#3373eb"
        let question_div_id = "id_assigned_question_div_" + question.id
        let send_private_message_assigned_question_button_id = "send-private-message-assigned-question-button-" + question.id
        let type = "'assigned_question'"

        if (document.getElementById(question_div_id) == null) {
            $("#assigned-question-content").html('<div id="' + question_div_id + '" class="assigned-question-div">' +
                '<div class="student-info">' + question.student_name + ' '  + `(${question.student_email})` + '</div>' +
                '<div class="question-location">' + 'Location: ' + question.location + '</div>' +
                '<div class="question-type">' + 'Type: ' + question.question_type + '</div>' +
                '<div class="question-content">' + 'Question: ' + question.content + '</div>' +
                '<button id="remove-question-button-' + question.id + '" class="remove-question-button" onclick="addRemoveReasonTextarea(' + question.id + "," + question.student_id + ')">Remove This Student From Queue</button>' +
                '<input type="button" value="Send Private Message" id="' + send_private_message_assigned_question_button_id + '" onclick="addPrivateMessageTextarea(' + question.id + "," + question.student_id + "," + type + ')" class="send-message-button">' +
                '<br>' +
                '</div>' +
                '<br>')
        }
    }
}

function sendRemoveReasonMessage(studentRecieveId) {
    let messageElem = $("." + "remove-question-reason-input")
    let message = messageElem.val()

    messageElem.val('')
    displayError('');

    $.ajax({
        url: '/ohq/send_remove_reason_message',
        type: "POST",
        data: "queue_id=" + this_queue_id + "&remove_reason_message_content=" + message 
            + "&receive_student_user_id=" + studentRecieveId + "&csrfmiddlewaretoken=" + getCSRFToken(),
        dataType: "json",
        success: function() { removeQuestionFromList(); enableAssignButtons()},
        error: updateError
    });
}

function addRemoveReasonTextarea(question_id, student_id) {
    var input = document.createElement("input");
    input.setAttribute("class", "remove-question-reason-input")
    input.setAttribute("id", "remove-question-reason-input-" + question_id)

    var submit_button = document.createElement("button");
    submit_button.setAttribute("class", "submit-question-remove-reason-button")
    submit_button.setAttribute("id", "submit-question-remove-reason-button-" + question_id)
    submit_button.setAttribute("onclick", "sendRemoveReasonMessage(" + student_id + ")")
    submit_button.innerHTML = "Submit"

    var message = document.createElement("p")
    message.setAttribute("class", "prompt-submit-question-remove-reason-text")
    message.setAttribute("id", "prompt-submit-question-remove-reason-text-" + question_id)
    message.innerHTML = "Please submit your reason for removing this student from queue: "
    message.setAttribute("style", "color:red")

    var cancel_button = document.createElement("button");
    cancel_button.setAttribute("class", "cancel-question-remove-reason-button")
    cancel_button.setAttribute("id", "cancel-question-remove-reason-button-" + question_id)
    cancel_button.setAttribute("onclick", "deleteRemoveReasonTextarea(" + question_id + ")")
    cancel_button.innerHTML = "Cancel"

    var question = document.getElementById("id_assigned_question_div_" + question_id)

    question.appendChild(message);
    question.appendChild(input);
    question.appendChild(submit_button);
    question.appendChild(cancel_button);

    document.getElementById('remove-question-button-' + question_id).setAttribute("disabled", true)
}

function deleteRemoveReasonTextarea(question_id) {
    var input = document.getElementById("remove-question-reason-input-" + question_id)
    var submit_button = document.getElementById("submit-question-remove-reason-button-" + question_id)
    var message = document.getElementById("prompt-submit-question-remove-reason-text-" + question_id)
    var cancel_button = document.getElementById("cancel-question-remove-reason-button-" + question_id)

    var question = document.getElementById("id_assigned_question_div_" + question_id)

    question.removeChild(input);
    question.removeChild(submit_button);
    question.removeChild(message);
    question.removeChild(cancel_button);

    document.getElementById('remove-question-button-' + question_id).removeAttribute("disabled")
}

function updateQueueStatus(response) {
    if (response.queue_status === true) {
        $("#queue-status").html("open")
        document.getElementById("queue-status").style.color = "#04FF87"
        document.getElementById("set-queue-status-button").onclick =
            function () { setQueueStatus(false); }
        document.getElementById("set-queue-status-button").innerText = "Disable Queue"
    } else {
        $("#queue-status").html("closed")
        document.getElementById("queue-status").style.color = "red"
        document.getElementById("set-queue-status-button").onclick =
            function () { setQueueStatus(true); }
        document.getElementById("set-queue-status-button").innerText = "Enable Queue"
    }
}

function addAnnouncement() {
    let itemTextElement = $("#" + "announcement-board-input")
    let itemTextValue = itemTextElement.val()
    // Clear input box and old error message (if any)
    itemTextElement.val('')
    displayError('');

    $.ajax({
        url: "/ohq/add-announcement",
        type: "POST",
        data: "queue_id=" + this_queue_id + "&announcement_content="+itemTextValue+"&csrfmiddlewaretoken="+getCSRFToken(),
        dataType : "json",
        success: getAnnouncementsInstructor,
        error: updateError
    });
}

function updateError(xhr) {
    if (xhr.status == 0) {
        displayError("Cannot connect to server")
        return
    }

    if (!xhr.getResponseHeader('content-type') == 'application/json') {
        displayError("Received status=" + xhr.status)
        return
    }

    let response = JSON.parse(xhr.responseText)
    if (response.hasOwnProperty('error')) {
        displayError(response.error)
        return
    }

    displayError(response)
}

function displayError(message) {
    $("#error").html(message);
}

function getCSRFToken() {
    let cookies = document.cookie.split(";")
    for (let i = 0; i < cookies.length; i++) {
        let c = cookies[i].trim()
        if (c.startsWith("csrftoken=")) {
            return c.substring("csrftoken=".length, c.length)
        }
    }
    return "unknown";
}