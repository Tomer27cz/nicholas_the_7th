function convertSeconds(secs) {
    let hours = Math.floor(secs / 3600)
    let minutes = Math.floor((secs % 3600) / 60)
    let seconds = Math.round(secs % 60)

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

    return ((Date.now() - start_of_segment*1000) + (start_of_segment_time*1000)) / 1000;
}

function npProgress(duration, played_duration) {
  let bar_elem = document.getElementById("np_progress");
  let text_elem = document.getElementById("progress_time");
  let sub_elem = document.getElementById("subtitles");

  if (duration != null) {
      let sec_remaining = duration - getSecsPlayed(played_duration);

      if (Math.sign(sec_remaining) === -1) {
          bar_elem.style.width = 100 + '%';
          text_elem.innerText = convertSeconds(getSecsPlayed(played_duration));
      }
  }

  let inter = setInterval(addProgress, 100);
  return inter;

  function addProgress() {
      let sec_played = getSecsPlayed(played_duration);
      text_elem.innerText = convertSeconds(sec_played);

      let new_text = currentSubtitle(formatted_subtitles, sec_played);
      if (sub_elem.innerHTML !== new_text) {
            sub_elem.innerHTML = new_text;
      }

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

if (socket_host === null || socket_host === "") {
    socket_host = window.location.origin + ":5001";
}

let socket = io(socket_host);

socket.on('connect', function () {
    console.log("Connected to server");
    socket.emit('getUpdates', guild_id);
    console.log("Sent getUpdates");
});

socket.on('update', function (data) {
    // last_event = Date.now();
    // if (data > last_updated+1) {
    //     console.log("last_updated: " + last_updated);
    //     location.reload();
    // }
    setTimeout(function () {
        if (data > last_updated+1) {
        console.log("last_updated: " + last_updated);
        location.reload();
        }
    }, 1000);
});

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

// ---------------------------------------------------------------------------------------------------------------------

function downloadSubtitles(lang) {
    if (subtitles === null && captions === null) {
        return;
    }
    if (subtitles === null) {
        subtitles = captions;
        console.log("Subtitles are null, using captions");
    }

    let subtitle_url = subtitles[lang];

    return fetch(subtitle_url)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();  // or response.text() for plain text
    })
    .then(data => data)
    .catch(error => {
        console.error('There was a problem with downloading subtitles:', error);
    })
}

function formatSubtitles(subtitles, combine_segments=false) {
    let new_subtitles = [];

    let events = subtitles['events'];
    for (let i = 0; i < events.length; i++) {
        if (events[i]['segs'] === undefined) {
            continue;
        }

        if (combine_segments) {
            let text = '';
            for (let j = 0; j < events[i]['segs'].length; j++) {
                text += events[i]['segs'][j]['utf8'];
            }

            new_subtitles.push({
                'start': events[i]['tStartMs'],
                'duration': events[i]['dDurationMs'],
                'text': text
            });

            continue;
        }

        new_subtitles.push({
            'start': events[i]['tStartMs'],
            'duration': events[i]['dDurationMs'],
            'segments': []
        });

        for (let j = 0; j < events[i]['segs'].length; j++) {
            new_subtitles[new_subtitles.length-1]['segments'].push({
                'offset': events[i]['segs'][j]['tOffsetMs'],
                'text': events[i]['segs'][j]['utf8']
            });
        }
    }

    return new_subtitles;
}

function currentSubtitle(subtitles, time) {
    let subtitle_text = '';
    for (let i = 0; i < subtitles.length; i++) {
        if (((subtitles[i]['start'] + subtitles[i]['duration'])/1000) >= time && (subtitles[i]['start']/1000) <= time) {
            if (subtitles[i]['text'] === undefined) {
                for (let j = 0; j < subtitles[i]['segments'].length; j++) {
                    if (((subtitles[i]['start'] + subtitles[i]['segments'][j]['offset'])/1000) >= time) {
                        break;
                    }
                    subtitle_text += subtitles[i]['segments'][j]['text'];
                }
                continue;
            }
            subtitle_text += subtitles[i]['text'];
        }
    }

    let lines = subtitle_text.split('\n')
    if (lines.length === 1) {
        return '<p>' + subtitle_text + '</p>';
    }

    return '<p>' + lines.join('</p><p>') + '</p>';

    // return '<p>' + subtitle_text.replace(/[\r\n]+/g, ' ') + '</p>';
}

// ---------------------------------------------------------------------------------------------------------------------

scrollNow(scroll_position);

if (duration != null && played_duration != null && bot_status !== 'Paused') {
    npProgress(duration, played_duration);
}

let formatted_subtitles;
if ((subtitles !== null || captions !== null) && played_duration !== null) {
    downloadSubtitles('en').then(data => {formatted_subtitles = formatSubtitles(data);}).then(() => {
        document.getElementById("subtitles").innerHTML = currentSubtitle(formatted_subtitles, getSecsPlayed(played_duration));
    });
}