function getTimeRemaining(endtime) {
  var t = Date.parse(endtime) - Date.parse(new Date());
  var seconds = Math.floor((t / 1000) % 60);
  var minutes = Math.floor((t / 1000 / 60) % 60);
  var hours = Math.floor((t / (1000 * 60 * 60)) % 24);
  var days = Math.floor(t / (1000 * 60 * 60 * 24));

  if (seconds < 0) 
    seconds = 0;
  if (minutes < 0)
    minutes = 0;
  if (hours < 0)
    hours = 0;
  if (days < 0)
    days = 0;

  return {
    'total': t,
    'days': days,
    'hours': hours,
    'minutes': minutes,
    'seconds': seconds
  };
}
 
function initializeClock(id, endtime) {
  var clock = document.getElementById(id);
  var daysSpan = clock.querySelector('.days');
  var hoursSpan = clock.querySelector('.hours');
  var minutesSpan = clock.querySelector('.minutes');
  var secondsSpan = clock.querySelector('.seconds');
 
  function updateClock() {
    var t = getTimeRemaining(endtime);
 
    daysSpan.innerHTML = t.days;
    hoursSpan.innerHTML = ('0' + t.hours).slice(-2);
    minutesSpan.innerHTML = ('0' + t.minutes).slice(-2);
    secondsSpan.innerHTML = ('0' + t.seconds).slice(-2);
 
    if (t.total <= 0) {
      clearInterval(timeinterval);
    }
  }
 
  updateClock();
  var timeinterval = setInterval(updateClock, 1000);
}

var deadline="November 25 2021 09:00:00 GMT+0300";
// var deadline="April 1 2020 09:00:00 GMT+0300";
initializeClock('countdown', deadline);