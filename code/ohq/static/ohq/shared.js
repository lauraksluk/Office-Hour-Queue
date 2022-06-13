function updateAnnouncements(items) {
    // remove questions that don't exist in items anymore
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

    // add new questions in items
    $(items).each(function (index) {
        let announcement_div_id = "id_announcement_div_" + this.announcement_id

        if (document.getElementById(announcement_div_id) == null) {
            $("#announcements-content").prepend(
                '<div id="' + announcement_div_id + '" class="announcement-div">' +
                '<div class="poster-info">' + this.announcement_poster + '</div>' +
                '<div class="announcement-message">' + this.announcement_content + '</div>' +
                '<div class="announcement-creation-time">' + this.announcement_creation_time + '</div>' +
                '<br>' +
                '</div>' +
                '<br>'
            )

            if (index === items.length - 1 && !first_refresh && this_page === "student") {
                alert("Instructor announcement: " + this.announcement_content)
            }
        }
    })

    first_refresh = false
}

// this is taken from https://stackoverflow.com/a/12487454
function getOrdinal(n) {
    if((parseFloat(n) == parseInt(n)) && !isNaN(n)){
        let s = ["th","st","nd","rd"],
        v = n%100;
        return n+(s[(v-20)%10] || s[v] || s[0]);
    }
    return n;
}
