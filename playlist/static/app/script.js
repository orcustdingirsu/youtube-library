const ytUrl = document.getElementById('ytUrl');
const author = document.getElementById('author');
const title = document.getElementById('title');
const table = document.getElementsByTagName('table')[0];
const modal = document.getElementById('myModal');
const span = document.getElementsByClassName("close")[0];
const commonFormats = document.getElementById('commonFormats');

let urlTd, selectTd, selectedSongs = [], selectedFormats, selectOptions, urlIndex, urls, tag, checkedUrls,  tds, trs, i, youtubeUrl, res, data, video, autore, titolo, selectTag, tbody, songs = [];

window.onload = async () => {
    load_videos();
}

window.onclick = function(event) {
    if (event.target == modal) {
      modal.style.display = "none";
    }
}

function openModal() {
    modal.style.display = "block";
}

span.onclick = function() {
    modal.style.display = "none";
}

ytUrl.oninput = async () => {
    res = await fetch(location.protocol + "//" + location.host + '/get_url_data?username=' + localStorage.getItem('username') + '&password=' + localStorage.getItem('password') + '&url=' + ytUrl.value);
    data = await res.text();
    data = JSON.parse(data);
    author.value = data["author"];
    title.value = data["title"];
}

function findCommonElement(array1, array2) {
    return array1.filter(value => array2.includes(value));
}

async function load_videos() {
    // get user video data from api
    res = await fetch(location.protocol + "//" + location.host + '/get_videos?username=' + localStorage.getItem('username') + '&password=' + localStorage.getItem('password'));
    data = await res.text();
    data = data.replace(/\\n/g, '').replace(/\\'/g, "'");
    data = JSON.parse(data);
    // declare variables and filter checked videos
    tds = document.getElementsByTagName('td');
    checkedUrls = [];

    for (i = 4; i < tds.length; i = i + 6) {
        tag = tds[i].getElementsByTagName('input')[0];
        if (tag.checked === true) {
            checkedUrls.push(tds[i - 2].innerText);
        }
    }

    // fill table with header

    table.innerHTML = `
        <thead>
            <tr>
                <th>Autore</th>
                <th>Titolo</th>
                <th>YouTube URL</th>
                <th onclick='openModal()'>Formato</th>
                <th>Seleziona</th>
                <th>Elimina</th>
            </tr>
        </thead>
        <tbody>
        </tbody>
    `;

    tbody = document.getElementsByTagName('tbody')[0];

    // get youtube url, author, title and formats, in html format, of every video

    for (video in data) {
        for (info in data[video]) {
            youtubeUrl = data[video][0];
            autore = data[video][1];
            titolo = data[video][2];
            if (typeof(data[video][info]) === 'object') {
                selectTag = `
                    <select>
                `;
                for (format in data[video][info]) {
                    selectTag += '<option>' + data[video][info][format] + '</option>';
                }
                selectTag += '</select>';
            }
        }

        // fill the table body with video info

        tbody.innerHTML += `
                <tr>
                    <td>${autore}</td>
                    <td>${titolo}</td>
                    <td><a href="${youtubeUrl}" target="_blank">${youtubeUrl}</a></td>
                    <td>${selectTag}</td>
                    <td><input type="checkbox" onclick="checkSong(this, '${youtubeUrl}')"></td>
                    <td onclick="deleteSong('${youtubeUrl}')">delete</td>
                <tr>
            `;
    }

    // re-check previous checked videos

    for (i = 2; i < tds.length; i = i + 5) {
        if (checkedUrls.includes(tds[i].innerText)) {
            tag = tds[i + 2].getElementsByTagName('input')[0];
            tag.checked = true;
        }
    }

    trs = tbody.getElementsByTagName('tr');
    for (i = 0; i < trs.length; i++) {
        if (trs[i].innerText === '') {
            trs[i].remove();
        }
    }
    
    return 0;
}

function logout() {
    // confirm logout
    if (window.confirm('Sei sicuro di voler fare il logout?')) {
        server.logout();
    }
}

function deleteAccount() {
    // confirm account deletion
    if (window.confirm("Sei sicuro di voler eliminare l'account?")) {
        server.deleteAccount();
    }
}

async function waitVideoFinish(video) {
    return new Promise(resolve => {
      function checkCondition() {
        const currentTime = video.currentTime;
        const duration = video.duration;
  
        if (currentTime === duration) {
          resolve();
        } else {
          setTimeout(checkCondition, 100);
        }
      }
  
      checkCondition();
    });
  }

async function playSongs() {
    // declare variables and filter checked videos
    tds = document.getElementsByTagName('td');
    checkedUrls = [];
    checkedFormats = [];
    selectedFormats = [];
    urlsArgs = '';

    for (i = 4; i < tds.length; i = i + 6) {
        tag = tds[i].getElementsByTagName('input')[0];
        if (tag.checked === true) {
            checkedUrls.push(tds[i - 2].innerText);
            //checkedFormats.push(tds[i - 1].getElementsByTagName('select')[0].value);
        }
    }

    
    for (i = 0; i < selectedSongs.length; i++) {
        for (j = 0; j * 6 + 2 < tds.length; j++) {
            if (tds[j * 6 + 2].innerText == selectedSongs[i]) {
                selectedFormats.push(tds[j * 6 + 3].getElementsByTagName('select')[0].value)
                break;
            }
        }
    }

    for (i = 1; i <= selectedSongs.length; i++) {
        urlsArgs += '&url' + i + '=' + selectedSongs[i - 1] + '&format' + i + '=' + selectedFormats[i - 1];
    }

    //response = await fetch(`${location.protocol}//${location.host}/cors?url=https://youtube-dl-web.vercel.app/_next/data/PbOv99VFHjh7d1YcpOw_T/result.json?f=bestvideo+bestaudio/best&q=${selectedSongs[0]}`);
    //text = await response.text();
    //text = JSON.parse(text);
    //console.log(text);
    res = await fetch(location.protocol + "//" + location.host + '/get_video_urls?username=' + localStorage.getItem('username') + '&password=' + localStorage.getItem('password') + urlsArgs);
    data = await res.text();
    data = JSON.parse(data);



    for (i = 0; i < data.length; i++) {
        console.log(data[i][0])
        document.body.innerHTML = `
            <video src="/video?url=${data[i][0]}&mime_type=${data[i][1]}" id="video" controls width="400"></video>
        `;
        
        video = document.getElementById('video');
        video.play();

        await waitVideoFinish(video);

        if (i === data.length - 1) {
            location.reload();
        }
    }
}

function deleteSong(url) {
    server.deleteSong(localStorage.getItem('username'), localStorage.getItem('password'), url);
    trs = document.getElementsByTagName('tbody')[0].getElementsByTagName('tr');
    tds = document.getElementsByTagName('tbody')[0].getElementsByTagName('td');

    for (i = 0; i , trs.length; i++) {
        urlIndex = i * 6 + 2;
        if (tds[urlIndex].innerText == url) {
            trs[i].remove();
            return 0;
        }
    }
}

function checkSong(element, url) {
    tds = document.getElementsByTagName('tbody')[0].getElementsByTagName('td');
    selectOptions = [];
    commonFormats.innerHTML = '';

    if (!selectedSongs.includes(url) && element.checked === true) {
        selectedSongs.push(url);
    }
    else {
        if (selectedSongs.includes(url) && element.checked === false) {
            index = selectedSongs.indexOf(url);
            selectedSongs.splice(index, 1);
        }
    }

    for (i = 0; i * 6 + 2 < tds.length; i++) {
        urlTd = tds[i * 6 + 2];
        selectTd = tds[i * 6 + 3].getElementsByTagName('select')[0];

        if (selectedSongs.includes(urlTd.innerText)) {
            tempArr = []
            for (j = 0; j < selectTd.options.length; j++) {
                tempArr.push(selectTd.options[j].value);
            }
            selectOptions.push(tempArr);
        }
    }
    if (selectOptions.length > 1) {
        occurrences = selectOptions[0];
        for (i = 0; i < selectOptions.length; i++) {
            occurrences = findCommonElement(occurrences, selectOptions[i]);
        }
        for (i = 0; i < selectOptions[0].length; i++) {
            commonFormats.innerHTML += `<option>${occurrences[i]}</option>`;
        }
    }
    else {
        if (selectOptions.length === 1) {
            for (i = 0; i < selectOptions[0].length; i++) {
                commonFormats.innerHTML += `<option>${selectOptions[0][i]}</option>`;
            }
        }
        else {
            commonFormats.innerHTML = '';
        }
    }

    /*for (i = 0; i < tds.length; i++) {
        urlTd = tds[i * 6 + 2];
        selectTd = tds[i * 6 + 3];
        if (urlTd.innerText == url) {
            for (j = 0; j < selectTd.options.length; j++) {

            }
        }
    }*/


}

function loadFormats() {
    format = commonFormats.value;
    tds = document.getElementsByTagName('tbody')[0].getElementsByTagName('td');

    for (i = 0; i * 6 + 4 < tds.length; i++) {
        checkbox = tds[i * 6 + 4].getElementsByTagName('input')[0];
        select = tds[i * 6 + 3].getElementsByTagName('select')[0];
        if (checkbox.checked == true) {
            select.value = format;
        }
    }
}

async function addSong() {
    // send to back-end video info and clear the inputs
    server.addSong(ytUrl.value, author.value, title.value);
    ytUrl.value = '';
    author.value = '';
    title.value = '';
}