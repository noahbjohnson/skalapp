function toggleCommentBlock(id){
    $('#'.concat(id)).toggleClass('hidden');
    if(this.innerHTML === 'show comments'){
        this.innerHTML = 'hide comments'
    }else{
        this.innerHTML = 'show comments'
    }
}

function actionHandler(url){
    $.get(url);
    setTimeout(function() {
        window.location.reload()
    },25)
}

function goBack() {
    window.history.back();
}
