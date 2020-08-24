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
        if (document.getElementById("user-id") != null) {
            let user_id = document.getElementById("user-id").value;
            let tutor_id = document.getElementById("tutor-id").value;
            load_follow_link(user_id, tutor_id);
        }
    
    }
});
    

function load_follow_link(user_id, tutor_id) {
    fetch(`/is_following/${user_id}/${tutor_id}`)
    .then(response => response.json())
    .then(data => {
        if (data.is_following)
            document.getElementById('follow-unfollow-btn').innerHTML = 'Unfollow';
        else 
            document.getElementById('follow-unfollow-btn').innerHTML = 'Follow';
    });
}
