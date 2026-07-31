const http = require('http');
const { exec } = require('child_process');
const url = require('url');

const PORT = 9001;

const server = http.createServer((req, res) => {
  const queryObject = url.parse(req.url, true).query;
  const host = queryObject.host || '127.0.0.1';

  // Command Injection Vulnerability
  exec(`ping -c 1 ${host}`, (error, stdout, stderr) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end(`STDOUT:\n${stdout}\nSTDERR:\n${stderr}`);
  });
});

server.listen(PORT, () => {
  console.log(`Vulnerable web app listening on port: ${PORT}`);
});
