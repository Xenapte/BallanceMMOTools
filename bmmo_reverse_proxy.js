const http = require('http'),
      fs = require('fs');
const { exit } = require('process');
const { exec } = require('child_process');


// parsing command line arguments

let host = '0.0.0.0', port = 47406, proxyPort = '47400', endPort = '26676', endDomain = 'bmmo.win';

for (let i = 0; i < process.argv.length; i++) {
  const arg = process.argv[i];
  switch (arg) {
    case '-h':
    case '--help':
      console.log('Simple UDP-based BMMO reverse proxy.');
      console.log(`Usage: ${process.argv0} ${process.argv[1]} [OPTION]...`);
      console.log('Options:');
      console.log('\t-h, --help\t Display this help and exit.');
      console.log('\t-H, --host HOST\t Use HOST as the host address. Default: 0.0.0.0.');
      console.log('\t-p, --port PORT\t Use PORT as the binding port. Default: 26675.');
      console.log('\t-P, --proxy-port PORT\t Use PORT as the proxy port. Default: 47400.');
      console.log('\t-d, --domain DOMAIN\t Use DOMAIN as the endpoint domain name. Default: bmmo.win.');
      console.log('\t-E, --end-port PORT\t Use PORT as the endpoint port. Default: 26676.');
      exit(0);
    case '-H':
    case '--host':
      host = process.argv[++i];
      break;
    case '-p':
    case '--port':
      port = Number(process.argv[++i]);
      break;
    case '-d':
    case '--domain':
      endDomain = process.argv[++i];
      break;
    case '-P':
    case '--proxy-port':
      proxyPort = process.argv[++i];
      break;
    case '-E':
    case '--end-port':
      endPort = process.argv[++i];
      break;
    default:
      if (arg.startsWith('-'))
        console.log(`Unknown option: ${arg}`);
  }
}

require('console-stamp')(console, 'yyyy-mm-dd HH:MM:ss.l');

// server actions

const endpointFile = __dirname + '/endpoint.txt';

let endpoint = fs.existsSync(endpointFile) ? fs.readFileSync(endpointFile).toString().trim() : endDomain;

const requestListener = function(req, res) {
  console.log("Accessed", req.url);
  res.setHeader("Content-Type", 'text/plain');
  res.writeHead(200);
  if (req.url.startsWith("/server/")) {
    endpoint = req.url.replace("/server/", "").replace(/[^a-z0-9\.\-]/g, "") + `.${endDomain}`;
    console.log("Switching server to", endpoint);
    const cmd = `echo ${endpoint} > endpoint.txt && screen -S socat -p 1 -X stuff "^C" && sleep 1s && screen -S socat -p 1 -X stuff " date +'[%F %T] switching to ${endpoint}' && socat udp-listen:${proxyPort},fork udp-sendto:${endpoint}:${endPort}^M"`;
    console.log("Command:", cmd);
    exec(cmd, (err, stdout, stderr) => {
      if (err) {
        console.log(err.message);
        // node couldn't execute the command
        return;
      }
    
      // the *entire* stdout and stderr (buffered)
      if (stdout.trim().length != 0)
        console.log(`stdout: ${stdout}`);
      if (stderr.trim().length != 0)
        console.log(`stderr: ${stderr}`);
    });
    res.end("OK");
  }
  else {
    res.end(endpoint);
  }
};

// start server

const server = http.createServer(requestListener);
server.listen(port, host, () => {
  console.log(`Server running on http://${host}:${port}`);
});
