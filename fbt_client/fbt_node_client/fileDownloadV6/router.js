var utils = require('../fbtUtils/fbtUtils');

function route(handle, pathname, response, request) {
  if (typeof handle[pathname] === 'function') {
    handle[pathname](request, response);
  } else {
    global.log.info("No request handler found for " + pathname);
    response.writeHead(404, {"Content-Type": "text/html"});
    response.write("404 Not found");
    response.end();
  }
}

exports.route = route;
