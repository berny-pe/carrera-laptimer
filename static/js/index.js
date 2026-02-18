let intervalElapsed = null;
let intervalLapTimes = null;
let intervalCheckFinished = null;

function postAction(url) {
    return fetch(url, { method: 'POST' });
}

function getRandomInt(max) {
    return Math.floor(Math.random() * max);
}

function startTimer() {
    let lightsDiv = document.getElementById("startLights");
    lights = lightsDiv.querySelectorAll(":scope > .startLight");

    const rand = getRandomInt(2500);
    for(let i = 0; i < lights.length; i++) {
        setTimeout(function(){
            lights[i].classList.add('redLight');
        }, i*750);
        setTimeout(function(){
            lights[i].classList.add('greenLight');
        }, ((lights.length)*750 + rand) );
    }
    startTimers(((lights.length)*750 + rand));
}

function continueTimer() {
    postAction('/continue_timer');
    startTimers(0);
}

function check_finished() {
    fetch('/check_finished')
        .then(response => response.json())
        .then(data => {
            if (data.finished) {
                refreshLapTimes();
                if (intervalLapTimes)
                    clearInterval(intervalLapTimes);
                if (intervalCheckFinished)
                    clearInterval(intervalCheckFinished);
                if (intervalElapsed)
                    clearInterval(intervalElapsed);
            }
        })
        .catch(function() {
            // do something
        }
    );

}

function stopTimer() {
    postAction('/stop_timer');
    refreshValues();
}
function reset() {
    confirm("Resetting Timer");
    postAction('/reset');
    refreshValues();
    if(null != intervalLapTimes)
        clearInterval(intervalLapTimes);
    if(null != intervalCheckFinished)
        clearInterval(intervalCheckFinished);
    if(null != intervalElapsed)
        clearInterval(intervalElapsed);
}
function refreshValues() {
    refreshElapsed();
    refreshLapTimes();
}
function refreshElapsed() {
    $.ajax({
        url: "/elapsed",
        type: "get",
        success: function(response) {
            $("#elapsed").html(response);
        },
        error: function(xhr) {
            //Do Something to handle error
        }
    });
}
function refreshLapTimes() {
    $.ajax({
        url: "/lap_times",
        type: "get",
        success: function(response) {
            $("#lap_times").html(response);
        },
        error: function(xhr) {
            //Do Something to handle error
        }
    });
}

function startTimers(when) {
    setTimeout(function(){

        postAction('/start_timer');

        intervalElapsed = setInterval(function(){
            refreshElapsed() // this will run after every 5 seconds
        }, 345);

        intervalLapTimes = setInterval(function(){
            refreshLapTimes() // this will run after every 5 seconds
        }, 654);

        intervalCheckFinished = setInterval(function(){
            check_finished() // this will run after every 5 seconds
        }, 125);

    }, when);
}


function lap1() {
    postAction('/lap1');
}
function lap2() {
    postAction('/lap2');
}
