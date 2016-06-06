var DownloadState = {
    DOWNLOAD_OVER: 0,
    DOWNLOADING: 1,
    CANCELED: 2,
    PAUSED: 3,
    DOWNLOAD_ERR: 4,
    ALREADY_COMPLETE: 5
};

exports.DownloadState = DownloadState;
exports.BLOCK_SIZE = 1024;
var BLOCK_IN_PART = 64;
exports.partsize = BLOCK_IN_PART * exports.BLOCK_SIZE;
exports.forwardServerAddr = 'http://211.149.223.98:8099';
exports.seed = 0xAAAA;

