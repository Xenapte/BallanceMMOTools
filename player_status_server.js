const http = require('http'),
      fs = require('fs');
const { exit } = require('process');


// parsing command line arguments

let host = '0.0.0.0', port = 26675;

let hostFlag = false, portFlag = false;

for (const arg of process.argv) {
  switch (arg) {
    case '-h':
    case '--help':
      console.log('Simple web server to display player status in the server.');
      console.log(`Usage: ${process.argv0} ${process.argv[1]} [OPTION]...`);
      console.log('Options:');
      console.log('\t-h, --help\t Display this help and exit.');
      console.log('\t-H, --host HOST\t Use HOST as the host address. Default: 0.0.0.0.');
      console.log('\t-p, --port PORT\t Use PORT as the binding port. Default: 26675.');
      exit(0);
    case '-H':
    case '--host':
      hostFlag = true;
      break;
    case '-p':
    case '--port':
      portFlag = true;
      break;
    default:
      if (hostFlag)
        host = arg;
      if (portFlag)
        port = Number(arg);
      hostFlag = portFlag = false;
  }
}

// server actions

const requestListener = function(req, res) {
  res.setHeader("Content-Type", 'application/json');
  res.writeHead(200);
  res.end(fs.readFileSync(__dirname + '/player_status.json'));
};

// start server

const server = http.createServer(requestListener);
server.listen(port, host, () => {
  console.log(`Server running on http://${host}:${port}`);
});
