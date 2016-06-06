
require('./douban').getInfo('до╬╘', function get(info){
          if(info)
          {
            console.log(info.id);
            console.log(info.mlink);
          }
        });