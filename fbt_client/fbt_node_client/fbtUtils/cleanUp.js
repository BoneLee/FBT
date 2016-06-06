// cleanup.js
// object to capture process exits and call app specific cleanup function...

function noOp() {};
all_fn = [];
exports.registerClean = function a(fn){
  all_fn.push(fn);
  global.log.info("regist cleanup");
};
process.on('exit', 
  function () {
    for (var i = 0; i < all_fn.length; i++) {
      all_fn[i]();
    }
    global.log.info("exit app");
  }
);

// catch ctrl+c event and exit normally
process.on('SIGINT', 
  function () {
    console.log('Ctrl-C...');
    process.exit(2);
    }
  );
/*exports.Cleanup = function Cleanup(callback) {

  // attach user callback to the process event emitter
  // if no callback, it will still exit gracefully on Ctrl-C
  callback = callback || noOp;
  //process.on('cleanup',callback);

  // do app specific cleaning before exiting
  process.on('exit', 
    function () {
      global.log.info("exit app");
      callback();
      }
    );

  // catch ctrl+c event and exit normally
  process.on('SIGINT', 
    function () {
      console.log('Ctrl-C...');
      process.exit(2);
      }
    );
};*/
