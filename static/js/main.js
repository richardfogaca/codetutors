document.addEventListener('DOMContentLoaded', () => {

    // edit_profile.html actions
    if (document.getElementById('profile_img')) {
        let input = document.getElementById('profile_img');
        let label = input.nextElementSibling;
        let labelVal = label.innerHTML;
        
        input.addEventListener('change', function(e) {
            var fileName = '';
            if (this.files && this.files.length > 1)
                fileName = (this.getAttribute( 'data-multiple-caption') || '' ).replace('{count}', this.files.length);
            else
                fileName = e.target.value.split('\\').pop();
    
            if (fileName)
                label.querySelector( 'span' ).innerHTML = fileName;
            else
                label.innerHTML = labelVal;
        });
    }
    else if (document.getElementById('follow-unfollow-btn')) {
        if (document.getElementById("profileId") != null) {
            var tutor_id = document.getElementById("profileId").value;
            let follow_button = document.getElementById("profileId").value;
            load_follow_link(tutor_id);
        }
    
    }
});
    

function load_follow_link(id) {
    // apply_csrf_token();

    fetch(`/is_following/${id}`)
    .then(response => response.json())
    .then(data => {
        if (data.is_following)
            document.getElementById('follow-unfollow-btn').innerHTML = 'Unfollow';
        else 
            document.getElementById('follow-unfollow-btn').innerHTML = 'Follow';
        
        document.getElementById('followers-count').innerHTML = data.followers_count;
        document.getElementById('following-count').innerHTML = data.following_count;
    });
}

// function follow_unfollow(id) {
//     // apply_csrf_token();
    
//     fetch(`/follow_unfollow/${id}`, {
//         method: 'PATCH'
//     })
//     .then(() => {
//         load_follow_link(id);
//     });
// }

// function apply_csrf_token() {
//     let csrftoken = $('meta[name=csrf-token]').attr('content');

//     $.ajaxSetup({
//         beforeSend: function(xhr, settings) {
//             if (!/^(GET|HEAD|OPTIONS|TRACE)$/i.test(settings.type) && !this.crossDomain) {
//                 xhr.setRequestHeader("X-CSRFToken", csrftoken);
//             }
//         }
//     });
// )}