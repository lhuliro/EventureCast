import http.client

conn = http.client.HTTPSConnection("www.wasgehtapp.de")
payload = ''
headers = {
  'Cookie': 'lv=1747851903; v=1; vc=2'
}
conn.request("GET", "/export.php?mail=ghaith.alshathi.24@nithh.onmicrosoft.com&passwort=Gatetomba90&columns=null", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
