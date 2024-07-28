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

  function changeSubtitle(secs_played) {
      if (formatted_subtitles === undefined) {
          return;
      }

      if (sub_elem === null || sub_elem === undefined) {
          return;
      }

      let new_text = currentSubtitle(formatted_subtitles, secs_played);
      if (sub_elem.innerHTML !== new_text) {
          sub_elem.innerHTML = new_text;
      }
  }

  function addProgress() {
      let sec_played = getSecsPlayed(played_duration);
      text_elem.innerText = convertSeconds(sec_played);

      changeSubtitle(sec_played);

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

  let inter = setInterval(addProgress, 100);
  return inter;
}

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

function fetchSubtitles(url) {
    console.log("Fetching subtitles from: " + url);

    return fetch(url)
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
        return response.json();  // or response.text() for plain text
    })
    .then(data => data)
    .catch(error => {
        console.error('There was a problem with downloading subtitles:', error);
        return null;
    })
}

function downloadSubtitles(lang) {
    if (lang.slice(0, 10) === 'subtitles_' && subtitles !== null) {
        console.log("Fetching subtitles: " + lang.slice(10));

        let response = fetchSubtitles(subtitles['url'] + lang.slice(10) + '&fmt=json3');
        if (response !== null) {
            return response;
        }

        console.log("Error fetching subtitles: " + lang.slice(10));
    }

    if (lang.slice(0, 9) === 'captions_' && captions !== null) {
        console.log("Fetching captions: " + lang.slice(9));

        let response = fetchSubtitles(captions['url'] + lang.slice(9) + '&fmt=json3');
        if (response !== null) {
            return response;
        }

        console.log("Error fetching captions: " + lang.slice(9));
    }

    if (subtitles !== null) {
        console.log("Fetching English subtitles");

        let response = fetchSubtitles(subtitles['en']);
        if (response !== null) {
            return response;
        }

        console.log("Error fetching English subtitles");

        console.log("Fetching first available subtitles");
        let firstResponse = fetchSubtitles(subtitles['url'] + subtitles['langs'][0] + '&fmt=json3');
        if (firstResponse !== null) {
            return firstResponse;
        }

        console.log("Error fetching first available subtitles");
    }

    if (captions !== null) {
        console.log("Fetching English captions");

        let response = fetchSubtitles(captions['en']);
        if (response !== null) {
            return response;
        }

        console.log("Error fetching English captions");

        console.log("Fetching first available captions");
        let firstResponse = fetchSubtitles(captions['url'] + captions['langs'][0] + '&fmt=json3');
        if (firstResponse !== null) {
            return firstResponse;
        }

        console.log("Error fetching first available captions");
    }

    console.log("No subtitles or captions found");
}

function formatSubtitles(subtitles, combine_segments=false) {
    if (subtitles === undefined) {
        console.log("Subtitles are undefined");
        return;
    }

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

    console.log("Formatted subtitles");
    return new_subtitles;
}

function currentSubtitle(subtitles, time) {
    if (subtitles === undefined) {
        return '';
    }

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

let formatted_subtitles;
if (played_duration !== null) {

    if (bot_status !== 'Paused') {
        npProgress(duration, played_duration);
    }

    if (options_subtitles !== 'False') {
        if (subtitles !== null || captions !== null) {
            console.log("Downloading subtitles: " + options_subtitles);

            downloadSubtitles(options_subtitles)
                .then(data => {
                    formatted_subtitles = formatSubtitles(data);
                })
                .then(() => {
                    document.getElementById("subtitles").innerHTML = currentSubtitle(formatted_subtitles, getSecsPlayed(played_duration));
                });
        } else {
            console.log("Subtitles and captions are null");
        }
    } else {
        console.log("Subtitles are disabled");
    }
} else {
    console.log("Played duration is null");
}

