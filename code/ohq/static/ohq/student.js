"use strict"

function getWaitingQuestionsCount() {
    $.ajax({
        type: "GET",
        url: "/ohq/waiting-questions-count",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: updateQuestionsCount,
        error: updateError
    });

    $.ajax({
        type: "GET",
        url: "/ohq/student_current_position",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: showCurrentStudentPosition,
        error: updateError
    });
}

function getRemove() {
    $.ajax({
        type: "GET",
        url: "/ohq/remove-question",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: removeQuestion,
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

function getAlertWhenInFrontOfQueue() {
    $.ajax({
        type: "GET",
        url: "/ohq/student_current_position",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: alertWhenInFrontOfQueue,
        error: updateError
    });
}

function getAlertWhenItIsTheirTurn() {
    $.ajax({
        type: "GET",
        url: "/ohq/student_current_position",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: alertWhenItIsTheirTurn,
        error: updateError
    });
}

function getAnnouncementStudent() {
    $.ajax({
        type: "GET",
        url: "/ohq/get-announcements",
        data: "queue_id=" + this_queue_id,
        dataType: "json",
        success: updateAnnouncementStudent,
        error: updateError
    });
}

function updateAnnouncementStudent(items) {
    // remove questions that don't exist in items anymore
    let announcements = items["announcements"]
    let request_user_id = items["request_user_id"]

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

            if (document.getElementById(private_message_div_id) == null && request_user_id === this.private_message_receiver_id) {
                $("#announcements-content").prepend(
                    '<div id="' + private_message_div_id + '" class="announcement-div">' +
                    '<div class="pm-poster-info" style="color: red">' + "(" + this.private_message_poster + "'s Private Message to You) " + this.private_message_poster + '</div>' +
                    '<div class="private-message-message">' + this.private_message_content + '</div>' +
                    '<div class="private-message-creation-time">' + this.private_message_creation_time + '</div>' +
                    '<br>' +
                    '</div>'
                )
    
                if (index === items.length - 1 && !first_refresh && this_page === "student") {
                    alert("Instructor Private Message: " + this.private_message_content)
                }
            }
        }
    })
    first_refresh = false
}

function updateQuestionsCount(response) {
    let num_questions = response.waiting_questions_count

    let color = "green"
    if (num_questions > 20) {
        color = "red"
    } else if (num_questions > 10) {
        color = "yellow"
    }

    $("#student-number").html(num_questions)

    document.getElementById("student-number").style.backgroundColor = color
}

function removeQuestion(response) {
    let qPos = $("#curr-position-in-queue")
    qPos.html("You haven't asked a question yet.")
    document.getElementById("curr-position-in-queue").style.color = "black"
    document.getElementById('remove-ques').style.visibility = 'hidden'
}

function showCurrentStudentPosition(response) {
    if (response.student_curr_position == 1) {
        $("#curr-position-in-queue").html("You are the next in line!")
        document.getElementById("curr-position-in-queue").style.color = "yellow"
    } else if (response.student_curr_position == -1) {
        $("#curr-position-in-queue").html("You haven't asked a question yet.")
        document.getElementById("curr-position-in-queue").style.color = "black"
    } else if (response.student_curr_position == 0) {
        $("#curr-position-in-queue").html("It is your turn! Please enter " + response.assigned_instructor + "'s room.")
        document.getElementById("curr-position-in-queue").style.color = "yellow"
    } else {
        let position_ordinal = getOrdinal(response.student_curr_position)
        $("#curr-position-in-queue").html("You are " + position_ordinal + " place in queue.")
        document.getElementById("curr-position-in-queue").style.color = "black"
    }


    if (response.student_curr_position > 0) {
        // display the remove question button
        document.getElementById("remove-question-button").style.visibility = "visible"
    } else {
        document.getElementById("remove-question-button").style.visibility = "hidden"
    }

    if (response.student_curr_position >= 0) {
        document.getElementById("id_post_button").style.visibility = "visible"
        document.getElementById("id_post_button").innerHTML = "Update"
    } else {
        // student hasn't asked a question yet
        if (document.getElementById("queue-status").innerHTML == "closed") {
            // if the queue is closed, the student shouldn't be allowed to ask a new question
            document.getElementById("id_post_button").style.visibility = "hidden"
        } else {
            // if the queue is open, the student should be allowed to ask a new question
            document.getElementById("id_post_button").style.visibility = "visible"
            document.getElementById("id_post_button").innerHTML = "Submit"
        }
    }
}

function alertWhenInFrontOfQueue(response) {
    if (response.student_curr_position == 1) {
        setTimeout(() => alert("You are the next in line!"), 500)
    }
}

function alertWhenItIsTheirTurn(response) {
    if (response.student_curr_position == 0) {
        setTimeout(() => alert("It is your turn! Please enter " + response.assigned_instructor + "'s room."), 500)
    }
}

function updateQueueStatus(response) {
    if (response.queue_status === true) {
        $("#queue-status").html("open")
        document.getElementById("queue-status").style.color = "#04FF87"
    } else {
        $("#queue-status").html("closed")
        document.getElementById("queue-status").style.color = "red"
    }
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
