# import libraries
import json
import uuid
import requests
import re
import jyserver.Flask as jsf
from flask import Flask, render_template, request, make_response, redirect, Response
from pytube import YouTube
from io import BytesIO
from urllib.parse import unquote
from moviepy.editor import VideoFileClip

# initialize flask
app = Flask(__name__)

# constants
GET_USER_DATA = "<script>server.getItem([localStorage.getItem('username'), localStorage.getItem('password')]);</script>"
REDIRECT_LOGIN_PAGE = '<script>location.href = location.protocol + "//" + location.host + "/login";</script>'
REDIRECT_APP_PAGE = '<script>location.href = location.protocol + "//" + location.host;</script>'

# user data variables and done variable to check if the user data variables have been got
username = ''
password = ''
done = 0

#get randon id
def rand_id():
    # get random id and save it in a database and return the id
    id = uuid.uuid4().hex
    db = json.load(open('id.json', 'r'))
    with open('id.json', 'w') as f:
        ip = request.environ['REMOTE_ADDR']
        db[ip] = id
        f.write(json.dumps(db, indent=4))
    return id

def replace_ip(url):
    # Define the regular expression pattern
    pattern = r'(&ip=)[^&]+'
    ip = request.headers.get('X-Forwarded-For', request.remote_addr).split(', ')[0]

    # Replace the matched pattern with &ip=127.0.0.1
    replaced_url = re.sub(pattern, r'\g<1>' + ip, url)

    return replaced_url

# get youtube id from video
def getYoutubeId(url):
    regExp = r'(https?://)?(www\.)?((youtube\.(com))/watch\?v=([-\w]+)|youtu\.be/([-\w]+))'
    id = re.match(regExp, url).group(0)
    return id[-11:]

def generate(url, headers, chunk_size):
    start_time = 0
    response = requests.get(url, headers = headers, stream=True)
    total_size = int(response.headers.get('content-length', 0))

    with VideoFileClip(url) as video:
        duration = video.duration

    start_byte = int(total_size * start_time / duration)
    end_byte = total_size

    for chunk in response.iter_content(chunk_size=chunk_size):
        if chunk:
            yield chunk

# initialize jyserver
@jsf.use(app)
class App:
    # init jyserver function
    def __init__(self):
        self.count = 0
    # get author and title of a youtube video
    def ytVideoInfo(self, url):
        yout = YouTube(url)
        author = yout.author
        title = yout.title
    # add song to database
    def addSong(self, url, author, title):
        # get username, password and youtube data and open the database
        self.username = str(self.js.localStorage.getItem('username'))
        self.password = str(self.js.localStorage.getItem('password'))
        streams = YouTube(url).streams
        db = json.load(open('database.json', 'r'))
        formats = []
        
        # get formats data from youtube video
        for video in streams:
            if video.resolution:
                formats.append(f'{video.mime_type} {video.resolution}{" (no audio)" if video.is_progressive == False and video.type == "video" else ""}')
            else:
                formats.append(f'{video.mime_type} {video.abr}')

        # check if the client password is the same as the user saved password
        if db[self.username]["password"] == self.password:
            # check if the 'songs' element exists in the database and if not create it
            if 'songs' in db[self.username]:
                # check if the video isn't in the database yet
                for video in db[self.username]['songs']:
                    urlId = getYoutubeId(url)
                    videoId = getYoutubeId(video)
                    if urlId == videoId:
                        self.js.window.alert("il video e' stato gia' salvato")
                        return 0
                # add video data to the 'songs' element
                db[self.username]['songs'].update({url: {'author': author, 'title': title, 'formats': formats}})
                with open('database.json', 'w') as jsonFile:
                    jsonFile.write(json.dumps(db, indent=4))
                self.js.load_videos()
            else:
                # create 'songs' element with vieo data in the database
                db[self.username]['songs'] = {url: {'author': author, 'title': title, 'formats': formats}}
                with open('database.json', 'w') as jsonFile:
                    jsonFile.write(json.dumps(db, indent=4))
                self.js.load_videos()
    # login function
    def login(self):
        # initialize variables and check if username exists, else return error
        self.username = str(self.js.document.getElementById('username').value)
        self.password = str(self.js.document.getElementById('password').value)
        db = json.load(open('database.json', 'r'))

        if self.username in db:
            # get saved usernames and passwords and check if they coincide with given username and password
            for i in range(len(db)):
                keys = list(db.keys())
                user = keys[i]
                pwd = db[user]['password']
                if user == self.username and pwd == self.password:
                    # redirect to set user data url and send data to authenticate
                    id = rand_id()
                    self.js.window.location.href = request.url_root + '../setuserdata?username=' + self.username + '&password=' + self.password + '&id=' + id
            # catch error
            self.js.window.alert('password errata')
        else:
            # catch error
            self.js.window.alert("l'utente selezionato non esiste")
    # singin function
    def signin(self):
        # initialize variables and check if username exists, else gives error
        self.username = str(self.js.document.getElementById('username').value)
        self.password = str(self.js.document.getElementById('password').value)
        db = json.load(open('database.json', 'r'))
        if self.username not in db:
            # create a new username and save it
            db[self.username] = {'password': self.password}
            with open('database.json', 'w') as jsonFile:
                jsonFile.write(json.dumps(db, indent=4))
            # redirect to setuserdata url and send data to authenticate
            id = rand_id()
            self.js.window.location.href = request.url_root + '../setuserdata?username=' + self.username + '&password=' + self.password + '&id=' + id
        else:
            self.js.window.alert("lo username esiste gia'")
    def logout(self):
        # initialize variables and check if username exists and the given password is correct
        # else gives error
        self.username = str(self.js.localStorage.getItem('username'))
        self.password = str(self.js.localStorage.getItem('password'))
        db = json.load(open('database.json', 'r'))

        if db[self.username] and db[self.username]['password'] == self.password:
            # redirect to removeuserdata url and send data to authenticate
            id = rand_id()
            self.js.window.location.href = request.url_root + 'removeuserdata?username=' + self.username + '&password=' + self.password + '&id=' + id
        else:
            self.js.window.alert("c'e stato un errore durante il logout")
    def deleteAccount(self):
        # intialize variables and check if username exists and the given password is correct,
        # else gives error
        self.username = str(self.js.localStorage.getItem('username'))
        self.password = str(self.js.localStorage.getItem('password'))
        db = json.load(open('database.json', 'r'))

        if db[self.username] and db[self.username]['password'] == self.password:
            # delete the user from the database and
            # redirect to removeuserdata url and data to authenticate
            with open('database.json', 'w') as f:
                del db[self.username]
                f.write(json.dumps(db, indent=4))
            id = rand_id()
            self.js.window.location.href = request.url_root + '../removeuserdata?username=' + self.username + '&password=' + self.password + '&id=' + id
        else:
            self.js.window.alert("c'e stato un errore durante l'eliminazione dell'account")
    # get username and password from localStorage
    def getItem(self, data):
        # get data from localStorage sent by the client and save it in global variables
        global username, password, done
        username = data[0] if data[0] != None else ''
        password = data[1] if data[1] != None else ''
        done = 1
    def deleteSong(self, username, password, url):
        db = json.load(open('database.json'))

        if db[username]:
            if db[username]['password'] == password:
                if db[username]['songs']:
                    if db[username]['songs'][url]:
                        with open('database.json', 'w') as f:
                            del db[username]['songs'][url]
                            f.write(json.dumps(db, indent=4))
                    else:
                        self.js.window.alert("l'utente non ha salvato la canzone selezionata")
                else:
                    self.js.windiw.alert("l'utente non ha canzoni")
            else:
                self.js.window.alert("la password e' sbagliata")
        else:
            self.js.window.alert("l'utente non esiste")
# initialize index url
@app.route('/')
def index():
    # add context to the app, so the app can access to the html file  and render them
    with app.app_context():
        # load a script to client that send username and password got from localStorage
        # to the server and wait until the operation is concluded
        global username, password, done
        yield App.render(GET_USER_DATA)
        while done == 0:
            pass
        done = 0
        # check if username and password exist from localStorage, else gives login page
        if username != '' and password != '':
            # check if username from cookie exist in database, else fives login page
            db = json.load(open('database.json', 'r'))
            if username in db:
                # get saved usernames and passwords from database and check if they coincide with localStorage's
                # username and password in order to acces to the app, else gives login page
                for i in range(len(db)):
                    keys = list(db.keys())
                    user = keys[i]
                    pwd = db[user]['password']
                    if user == username and pwd == password:
                        yield App.render(render_template('/app/index.html'))
                        raise StopIteration
                yield REDIRECT_LOGIN_PAGE
                raise StopIteration
            else:
                yield REDIRECT_LOGIN_PAGE
                raise StopIteration
        else:
            yield REDIRECT_LOGIN_PAGE
            raise StopIteration

# initialize login url
@app.route('/login')
def login():
    # add context to the app, so the app can access to the html file  and render them
    with app.app_context():
        # load a script to client that send username and password got from localStorage
        # to the server and wait until the operation is concluded
        global username, password, done
        yield App.render(GET_USER_DATA)
        while done == 0:
            pass
        done = 0
        # check if username and password exist from localStorage, else gives login page
        if username != '' and password != '':
            # check if username from cookie exist in database, else gives login page
            db = json.load(open('database.json', 'r'))
            if username in db:
                # get saved usernames and passwords from database and check if they coincide with localStorage's
                # username and password in order to acces to the app, else gives login page
                for i in range(len(db)):
                    keys = list(db.keys())
                    user = keys[i]
                    pwd = db[user]['password']
                    if user == username and pwd == password:
                        yield REDIRECT_APP_PAGE
                        raise StopIteration
                yield App.render(render_template('/login/index.html'))
                raise StopIteration
            else:
                yield App.render(render_template('/login/index.html'))
                raise StopIteration
        else:
            yield App.render(render_template('/login/index.html'))
            raise StopIteration

# initialize signin url
@app.route('/signin')
def signin():
    # add context to the app, so the app can access to the html file  and render them
    with app.app_context():
        # load a script to client that send username and password got from localStorage
        # to the server and wait until the operation is concluded
        global username, password, done
        yield App.render(GET_USER_DATA)
        while done == 0:
            pass
        done = 0
        # check if username and password exist from localStorage, else gives signin page
        if username != '' and password != '':
            # check if username from cookie exist in database, else gives signin page
            db = json.load(open('database.json', 'r'))
            if username in db:
                # get saved usernames and passwords from database and check if they coincide with localStorage's
                # username and password in order to acces to the app, else gives signin page
                for i in range(len(db)):
                    keys = list(db.keys())
                    user = keys[i]
                    pwd = db[user]['password']
                    if user == username and pwd == password:
                        yield REDIRECT_APP_PAGE
                        raise StopIteration
                yield App.render(render_template('/signin/index.html'))
                raise StopIteration
            else:
                yield App.render(render_template('/signin/index.html'))
                raise StopIteration
        else:
            yield App.render(render_template('/signin/index.html'))
            raise StopIteration

# initialize cookie url
@app.route('/setuserdata')
def setuserdata():
    # request query values and check if 'id' exist in that list
    args = request.args
    ip = request.environ['REMOTE_ADDR']
    if not 'id' in args.keys():
        return REDIRECT_LOGIN_PAGE
    with open('id.json', 'r') as f:
        f = json.load(f)
        if f[ip]:
            # check if the random id and the query id coincide and then, if it is true,
            # create localStorage items and redirect to the app page, else redirect to login page
            if args['id'] == f[ip]:
                username = args['username']
                password = args['password']
                res = make_response(f"""
                    <script>
                        localStorage.setItem('username', '{username}');
                        localStorage.setItem('password', '{password}');
                        location.href = location.protocol + "//" + location.host;
                    </script>
                """)
                rand_id()
                return res
            else:
                return REDIRECT_LOGIN_PAGE
        else:
            return REDIRECT_LOGIN_PAGE
        
@app.route('/removeuserdata')
def removeuserdata():
    # get args and client ip and check if the 'id' is in the args, else redirect login page
    args = request.args
    ip = request.environ['REMOTE_ADDR']
    if not 'id' in args.keys():
        return REDIRECT_LOGIN_PAGE
    # load the id database and check if the client ip is saved, else redirect login page
    with open('id.json', 'r') as f:
        f = json.load(f)
        if f[ip]:
            # check if the random id and the query id coincide and then, if it is true,
            # remove localStorage items and redirect to the login page, else redirect to login page without doing nothing
            if args['id'] == f[ip]:
                res = make_response(f"""
                    <script>
                        localStorage.removeItem('username');
                        localStorage.removeItem('password');
                        location.href = location.protocol + "//" + location.host + "/login";
                    </script>
                """)
                rand_id()
                return res
            else:
                return REDIRECT_LOGIN_PAGE
        else:
            return REDIRECT_LOGIN_PAGE
        
@app.route('/get_videos')
def get_videos():
    # open the database
    args = request.args
    db = json.load(open('database.json', 'r'))
    data = []

    # check if the 'songs' element exists in the database and
    # if the client password is the same as the user saved password
    if args['username'] and db[args['username']]['password'] == args['password']:
        if 'songs' in db[username] and db[username]["password"] == password:
            # put data of every video saved in the database into an array
            # and append it to a multi-dimensional array
            # and then return data
            for video in db[username]['songs']:
                tempData = []
                tempData.append(video)
                tempData.append(db[username]['songs'][video]['author'])
                tempData.append(db[username]['songs'][video]['title'])
                tempData.append(db[username]['songs'][video]['formats'])
                data.append(tempData)
            return data
    else:
        return ''

@app.route('/get_video_info')
def getvideoinfo():
    # get args and open the database
    args = request.args
    db = json.load(open('database.json', 'r'))

    # check if the username exists and check if the given password is correct
    if args['username'] and db[args['username']]['password'] == args['password']:
        # get every url and format from args checking if they exists
        for i in range(-1, len(args) - 2):
            if args[f'url{i}'] and args[f'format{i}']:
                url = args[f'url{i}']
                format = args[f'format{i}']
                #pytube section
    else:
        return ''

@app.route('/get_url_data')
def geturldata():
    # get args and open the database
    args = request.args
    db = json.load(open('database.json', 'r'))

    # check if the username exists and check if the given password is correct
    if args['username'] and db[args['username']]['password'] == args['password']:
        # get every url and format from args checking if they exists
        try:
            yt = YouTube(args['url'])
            author = yt.author
            title = yt.title
            return {"author": author, "title": title}
        except Exception:
            return ''
    else:
        return ''

@app.route('/get_video_urls')
def getvideourls():
    args = request.args
    db = json.load(open('database.json'))

    if args['username'] and db[args['username']]['password'] == args['password']:
        #try:
        urls = []
        for i in range(1, int((len(args) - 2) / 2 + 1)):
            mime_type = args['format' + str(i)].split(' ')[0]
            res = args['format' + str(i)].split(' ')[1]
            audio = False if len(args['format' + str(i)].split(' ')) == 3 else True
            yt = YouTube(args['url' + str(i)])
            videos = yt.streams.filter(mime_type = mime_type)
            if videos[0].type == 'video':
                videos = videos.filter(res = res)
            else:
                videos = videos.filter(bitrate = res)
            if len(videos) == 2:
                urls.append([videos[0].url if audio == True else videos[1].url, videos[0].mime_type if audio == True else videos[1].mime_type])
            else:
                urls.append([videos[0].url, videos[0].mime_type])
        return urls
        #except Exception as e:
            #print(e)
            #return ''
    else:
        return ''
    
@app.route('/video')
def video():
    with app.app_context():
        args = request.args
        url = ''
        i = 0
        mime_type = args['mime_type']
        extension = 'm4a' if mime_type == 'audio/mp4' else mime_type.replace('video/', '').replace('audio/', '')
        for arg in args:

            print(arg, '\n')
            if arg != 'mime_type':
                if i > 0:
                    url = url + '&' + arg + '=' + args[arg]
                    i = i + 1
                else:
                    url = url + args[arg]
                    i = i + 1
        headers = {
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "accept-language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
            "cache-control": "max-age=0",
            "if-modified-since": "Mon, 13 Nov 2023 14:00:23 GMT",
            "range": "bytes=0-1000000000000000",
            "sec-ch-ua": "\"Not_A Brand\";v=\"8\", \"Chromium\";v=\"120\", \"Google Chrome\";v=\"120\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "none",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "x-client-data": "CJO2yQEIpLbJAQipncoBCL6EywEIk6HLAQiFoM0BCKHuzQEIjO/NAQiD8M0BCJHyzQEY9snNARin6s0B"
        }
        
        #response = requests.get(url, headers = headers)
        chunk_size = 10*1024
        #print(divide(response.content, chunk_bytes))
        #r = requests.get(url, headers = headers, stream = True
        r = requests.head(url, headers = headers)
        total_size = int(r.headers.get('content-length', 0))

        with VideoFileClip(url) as video:
            duration = video.duration

        response_headers = {
        'Content-Type': mime_type,
        'Content-Length': total_size,
        'Accept-Ranges': 'bytes',
        }
        r = requests.get(url, headers = headers, stream = True)
        return Response(r.iter_content(chunk_size = chunk_size), headers = response_headers)
        #return Response(generate(url, headers, chunk_size), mimetype = mime_type)
        # Verifica che la richiesta sia andata a buon fine
        #return Response(BytesIO(divide(response.content, chunk_bytes)), mimetype=mime_type)

if __name__ == '__main__':
    app.run(debug=True)