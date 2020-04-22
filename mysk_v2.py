from http.server import BaseHTTPRequestHandler, HTTPServer
import webbrowser
import json
import requests

subreddits = ["rpan", "AnimalsOnReddit", "distantsocializing", "GlamourSchool", "RedditInTheKitchen", "RedditMasterClasses", "RedditSessions", "talentShow", "TheArtistStudio", "TheGamerLounge", "TheYouShow", "whereintheworld"]
subreddit_selector = b""
for item in subreddits:
    subreddit_selector += bytes("<option value='{0}'>{0}</option>".format(item), encoding="ascii")

doc_start = b"<html><head><style>body { font-family: arial; } h1 { font-family: arial black; } code { display: block; background-color: #e2e2e2; padding: 2px; font-family: 20px;}</style><body>"
doc_end = b"</body></html>"

start_body = b"""<h1>SnooKey</h1><p>Welcome to SnooKey. This program will guide you through the creation of your RPAN stream!<br>Click on the link below and you will be redirected to reddit. Log-in, if you are requested to. Then scroll down to the page you are presented and click 'accept'.</p>"""

callback_body = bytes("""<h1>SnooKey</h1>
<p>Your account token was obtained.<br>Now you should prepare your streaming application.<br><b>The URL you have to stream to:</b><code>rtmp://ingest.redd.it/inbound/</code><br>
The best streaming settings are resolution 1080x1920, scaled down to 720x1280,  FPS: 30</p>
<h3>Stream settings:</h3>
<form id='main' action='/create_stream' method='post'>
<input type='hidden' name='token' id='token'></input>
    <table>
        <tbody>
            <tr>
                <td><b>Stream name:</b></td>
                <td><input type='text' name='stream_name' size="50"></input></td>
            </tr>
            <tr>
                <td><b>Subreddit:</b></td>
                <td><select name='subreddit'>
                    {0}
                    </select>
                </td>
            </tr>
        </tbody>
    </table>
    <p>Get ready to enter your stream key to your streaming application. As soon as you click on Start streaming, you will be presented with your streamer key.</p>
    <input type='submit' value='Start Streaming!'></input></td>
</form>""".format(subreddit_selector), encoding="ascii")
callback_script = b"""<script>
function putToken() {
    var str_to_find = 'access_token=';
    var index = document.location.hash.indexOf(str_to_find);

    var tok = document.location.hash.slice(index+str_to_find.length);
    var amp = '&';

    var tok = tok.slice(0, tok.indexOf(amp));

    var dest = document.getElementById("token");
    dest.value = tok;

    if (dest.value == tok) {
        console.log("Sucessfuly set up token:" + tok);
    }
}
putToken();
</script>
"""

success_body = """<h1>SnooKey</h1><h2>Success!</h2><br><p>You are live! Here is your streamer key:</p><code>{0}</code><br><p>Your url:<a href='{1}'>{1}</a><br>Thank you for using SnooKey. Now you can close the console window.</p>"""
failed_body = """<h1>SnooKey</h1><h2>Broadcast start failed. :(</h2><br><p>Something went wrong!<br>Click&nbsp;<a href='http://localhost:65010/start'>here</a>&nbsp;to try again.</p><h2>Details:</h2><code>Response: {0}</code><p>Json response body:</p><code>{1}</code>"""
pyfailed_body = """<p>Additionaly, here is a Python exception:</p><code></code>"""

invalid_body =  b"""<h1>SnooKey - ERROR :(</h1><p>Something went wrong. Click&nbsp;<a href='http://localhost:65010/start'>here</a>&nbsp;to try again.</p>"""

class SKHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(doc_start)
        if self.path == "/start":
            self.wfile.write(start_body)
            client_id = "ohXpoqrZYub1kg"
            response_type = "token"
            scope = "*"
            callback = "http://localhost:65010/callback"
            state = "SNOOKEY"
            request_url = "https://www.reddit.com/api/v1/authorize?client_id={0}&response_type={1}&redirect_uri={2}&scope={3}&state={4}".format(client_id, response_type, callback, scope, state)

            self.wfile.write(bytes("<a href='{0}'>Click here to start!</a>".format(request_url), encoding="ascii"))
        elif self.path == "/callback":
            self.wfile.write(callback_body)
            self.wfile.write(callback_script)
        else:
            self.wfile.write(invalid_body)
            
        self.wfile.write(doc_end)

    def do_POST(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(doc_start)
        if self.path == "/create_stream":
            pyfailed = False
            clen = int(self.headers["Content-Length"])
            data = self.rfile.read(clen).decode("utf-8")

            kvs = data.split("&")
            ddict = {}
            for kval in kvs:
                k,v = kval.split("=")
                ddict[k] = v
            print(ddict)
            broadcast_endpoint = "https://strapi.reddit.com/r/{0}/broadcasts?title={1}".format(ddict["subreddit"], ddict["stream_name"])
            full_token = "Bearer {0}".format(ddict["token"])

            headers = {
                'User-Agent': 'Project SnooKey/0.3',
                'Authorization': full_token
            }
            
            req = requests.post(broadcast_endpoint, headers=headers)
            print(req.content)
            response = json.loads(str(req.content, encoding="ascii"))
            if req.status_code == 200 and not pyfailed:
                content = sucess_body.format(response["data"]["streamer_key"], response["data"]["post"]["outboundLink"]["url"])
                self.wfile.write(bytes(content, encoding="ascii"))
            else:
                content = failed_body.format(str(req.status_code), str(req.content, encoding="ascii").replace("\n", "<br>"))
                self.wfile.write(bytes(content, encoding="ascii")) 
        else:
            self.wfile.write(invalid_body)
            
        self.wfile.write(doc_end)
        

serv = HTTPServer(("localhost", 65010), SKHandler)
webbrowser.open("http://localhost:65010/start")
print("SNOOKEY")
print("A webbrowser window should open in a few seconds. Do not close this window until you are told to do so.")
serv.serve_forever()
