# coding: utf-8

import os
import logging
import imghdr
import upyun
from celery import Celery

BUCKETNAME = os.environ['BUCKETNAME']
UPYUN_USERNAME = os.environ['UPYUN_USERNAME']
UPYUN_PASSWORD = os.environ['UPYUN_PASSWORD']

SUCCESS = "SUCCESS"
NOT_EXIST = "NOT_EXIST"
NOT_IMAGE = "NOT_IMAGE"
UPYUN_ERROR = "UPYUN_ERROR"

def log_se(se):
    if not isinstance(se, upyun.UpYunServiceException):
        logging.error("logging error: ", str(se))

    error_msg = "upload failed, Except an UpYunServiceException ..."+ \
                "HTTP Status Code: " + str(se.status) + '\n' + \
                "Error Message:    " + se.msg + "\n"
    logging.error(error_msg)

def log_ce(ce):
    if not isinstance(ce, upyun.UpYunClientException):
        logging.error("logging error: ", str(ce))

    error_msg = "upload failed Except an UpYunClientException ..." + \
                "Error Message: " + ce.msg + "\n"
    logging.error(error_msg)


celery = Celery("tasks", broker='redis://localhost:6379/0')

up = upyun.UpYun(BUCKETNAME, UPYUN_USERNAME, UPYUN_PASSWORD, timeout=30,
                 endpoint=upyun.ED_AUTO)

@celery.task
def upload_image_to_upyun(filepath, filepath_on_upyun):
    """
    :param filepath: 图片的绝对路径
    :param dir_on_upyun: 在upyun 上的存储路径, 例如/static/images/user_icon/a.jpg
    :return: return code
    """
    filepath = os.path.realpath(filepath)
    if not os.path.exists(filepath):
        return NOT_EXIST

    if imghdr.what(filepath) is None:
        return NOT_IMAGE

    with open(filepath, 'rb') as f:
        try:
            up.put(filepath_on_upyun, f, checksum=True)
        except upyun.UpYunServiceException as se:
            log_se(se)
            return UPYUN_ERROR
        except upyun.UpYunClientException as ce:
            log_ce(ce)
            return UPYUN_ERROR
        else:
            logging.info("upload success: %s to %s" %
                         (filepath, filepath_on_upyun))
            return SUCCESS