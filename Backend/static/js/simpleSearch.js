let gameCards = document.querySelectorAll('.game')
let gameGenres = document.querySelectorAll('#game-genre')

function liveSearch() {
    let search_query = document.getElementById("searchbox").value;

    //Use innerText if all contents are visible
    //Use textContent for including hidden elements
    for (var i = 0; i < gameCards.length; i++) {
        var gameName = gameCards[i].getElementsByClassName("game-name")[0].textContent;
        if(gameName.toLowerCase()
                .includes(search_query.toLowerCase())) {
            gameCards[i].classList.remove("is-hidden");
        } else {
            gameCards[i].classList.add("is-hidden");
        }
    }
}

//A little delay
let typingTimer;
let typeInterval = 500;
let searchInput = document.getElementById('searchbox');

searchInput.addEventListener('keyup', () => {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(liveSearch, typeInterval);
});
