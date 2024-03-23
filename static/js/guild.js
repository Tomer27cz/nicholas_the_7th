function convertSeconds(secs) {
    let hours = Math.floor(secs / 3600)
    let minutes = Math.floor((secs % 3600) / 60)
    let seconds = secs % 60

    function pad(num, totalLength) {
        return String(num).padStart(totalLength, '0');
    }

    if (hours) {
        return `${hours}:${pad(minutes, 2)}:${pad(seconds, 2)}`
    } else {
        return `${minutes}:${pad(seconds, 2)}`
    }
}

function getSecsPlayed(played_duration) {
    let len_played_duration = played_duration.length;
    if (len_played_duration === 0) {
        return 0.0;
    }
    let last_segment = played_duration[len_played_duration - 1];
    if (last_segment['end']['epoch'] != null) {
        return last_segment['end']['time_stamp'];
    }

    let start_of_segment = last_segment['start']['epoch'];
    let start_of_segment_time = last_segment['start']['time_stamp'];
    return (Math.round(Date.now() / 1000) - start_of_segment) + start_of_segment_time;
}

function npProgress(duration, played_duration) {
  let bar_elem = document.getElementById("np_progress");
  let text_elem = document.getElementById("progress_time");

  if (duration != null) {
      let sec_remaining = duration - getSecsPlayed(played_duration);

      if (Math.sign(sec_remaining) === -1) {
          bar_elem.style.width = 100 + '%';
          text_elem.innerText = convertSeconds(getSecsPlayed(played_duration));
      }
  }

  let inter = setInterval(addProgress, 1000);
  return inter;

  function addProgress() {
      text_elem.innerText = convertSeconds(getSecsPlayed(played_duration));

      if (duration != null) {
          let sec_remaining_add = duration - getSecsPlayed(played_duration);
          let percentage = 100 - (sec_remaining_add / duration) * 100;

          bar_elem.style.width = percentage + '%';

          if (percentage > 99.99 || sec_remaining_add < 2) {
              clearInterval(inter);
              setTimeout(function () {
                  location.reload();
              }, 3000);
          }
      }
  }
}

// // ---------------------------------------------------------------------------------------------------------------------
// function reloadQueue() {
//     fetch(`/guild/${guild_id}/queue?key=${key}`)
//         .then(response => response.text())
//         .then(data => {
//             document.getElementById("q-main").outerHTML = data;
//         });
// }
//
// function reloadNow(int) {
//     fetch(`/guild/${guild_id}/queue?key=${key}&act=now_video&render=html`)
//         .then(response => response.text())
//         .then(data => {
//             document.getElementById("now-playing").outerHTML = data;
//         });
//
//     clearInterval(int);
//
//     return fetchData();
// }
//
// function reloadHistory() {
//     document.getElementById("history").outerHTML = `<div class="accordion-item" id="history">
//       <div class="accordion-header">
//         <div class="d-grid gap-2">
//           <a class="btn btn-dark accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="false" aria-controls="panelsStayOpen-collapseOne" hx-target="#h-main" hx-swap="outerHTML" hx-trigger="click once" hx-get="/guild/${guild_id}/history?key=${key}">
//             <h3>History</h3>
//             <div class="q-item1 text-center">
//               <div class="spinner-border text-primary htmx-indicator" role="status" style="width: 2rem; height: 2rem;"></div>
//             </div>
//           </a>
//         </div>
//       </div>
//       <div id="panelsStayOpen-collapseOne" class="accordion-collapse collapse">
//         <div class="accordion-body" id="h-main"></div>
//       </div>
//     </div>`;
// }
//
// function reloadSaves() {
//     fetch(`/guild/${guild_id}/modals?type=loadModal?key=${key}}`)
//         .then(response => response.text())
//         .then(data => {
//             document.getElementById("loadModal_content").outerHTML = data;
//         });
// }
//
// function reloadOptions() {
//     fetch(`/guild/${guild_id}/modals?type=optionsModal&key=${key}}`)
//         .then(response => response.text())
//         .then(data => {
//             document.getElementById("optionsModal_content").outerHTML = data;
//         });
// }
//
// // ---------------------------------------------------------------------------------------------------------------------
//
// function checkUpdates(last_updated, new_last_updated, int) {
//     if (new_last_updated['queue'] > last_updated['queue']) {
//         console.log("Reloading queue");
//         reloadQueue();
//     }
//
//     if (new_last_updated['now'] > last_updated['now']) {
//         console.log("Reloading now");
//         try {
//             reloadNow(int);
//         } catch (e) {
//             console.log(e);
//         }
//     }
//
//     if (new_last_updated['history'] > last_updated['history']) {
//         console.log("Reloading history");
//         reloadHistory();
//     }
//
//     if (new_last_updated['saves'] > last_updated['saves']) {
//         console.log("Reloading saves");
//         reloadSaves();
//     }
//
//     if (new_last_updated['options'] > last_updated['options']) {
//         console.log("Reloading options");
//         reloadOptions();
//     }
// }
//
// // ---------------------------------------------------------------------------------------------------------------------

// function fetchData() {
//     return fetch(`/guild/${guild_id}/queue?key=${key}&act=now_video&render=json`)
//         .then(response => {
//             if (!response.ok) {
//                 throw new Error(`HTTP error! Status: ${response.status}`);
//             }
//             return response.json();
//         })
//         .then(data => {
//             const pd = data['played_duration'];
//             const nd = data['duration'];
//
//             return npProgress(nd, pd);
//         })
//         .catch(error => {
//             console.error('Error fetching data:', error);
//         }).then(int => {
//             return int;
//         });
// }
//
// let int = fetchData();

// ---------------------------------------------------------------------------------------------------------------------

let socket = io(document.domain + ':5001');

socket.on('connect', function () {
    console.log("Connected to server");
    socket.emit('getUpdates', guild_id);
    console.log("Sent getUpdates");
});

socket.on('update', function (data) {
    // last_event = Date.now();
    setTimeout(function () {
        if (data > last_updated+1) {
        console.log("last_updated: " + last_updated);
        location.reload();
        }
    }, 1000);
});

if (duration != null || played_duration != null) {
    npProgress(duration, played_duration);
}

// ---------------------------------------------------------------------------------------------------------------------

window.addEventListener('htmx:beforeRequest', function (event) { // switched from afterSwap to beforeRequest - race condition
    if (event.detail.target.id === 'q-main') {
        console.log("qf");
        qf();
    } else if (event.detail.target.id === 'response-div') {
        console.log("af");
        af();
    }

    last_updated = new Date() / 1000;
    console.log("last_updated: " + last_updated);
  }, false);

window.addEventListener('htmx:afterSwap', function (event) {
    last_updated = new Date() / 1000;
    console.log("last_updated: " + last_updated);
}, false);

// ---------------------------------------------------------------------------------------------------------------------

function qf() {
    let queue_div = document.getElementById('q-main');
    let spinner = '<div class="q-item1 text-center"><div class="spinner-border text-primary" role="status" style="width: 5rem; height: 5rem;"></div></div>';
    queue_div.innerHTML = spinner + queue_div.innerHTML;

    let buttons = queue_div.querySelectorAll(".btn");
    for (let i = 0; i < buttons.length; i++) {
        buttons[i].setAttribute('disabled', '');
    }
}

function af() {
    document.getElementById("loader").style.display = "flex";
}

// ---------------------------------------------------------------------------------------------------------------------

function onSubmitDisable() {
  setTimeout(disableButtons, 10);

  function disableButtons() {
      let buttons = document.querySelectorAll(".btn");
      for (let i = 0; i < buttons.length; i++) {
          buttons[i].setAttribute('disabled', '');
      }
  }
}

function scrollNow(scroll_pos) {
  window.scroll({top: scroll_pos, left: 0, behavior: "auto"});
}

function delay(time) {
  return new Promise(resolve => setTimeout(resolve, time));
}

scrollNow(scroll_position);