from flask import Flask, request, Response
from flask_cors import CORS, cross_origin
import json
from syncit.delay_checker import DelayChecker
from syncit.constants import Constants
from syncit.sync_checker import SyncChecker
import logging
from logger_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'


@app.route('/check_sync', methods=['POST'])
@cross_origin()
def check_sync():
    """
    Route to check if buffers and subtitles are synced or not.

    Request Params:
        data (list): List of lists conatining [base64_buffer, subtitles] e.g: [[f3b5AAA, 'I went to eat'], [a93KKpr, 'I went to sleep']]

    Returns:
        Boolean: If synced or not.
    """

    logger.info('Checking sync.')
    if(type(request.json) != list or len(request.json) != Constants.SAMPLES_TO_CHECK):
        print(type(request.json), len(request.json))
        return Response(json.dumps({'error': 'Bad request.'}), 400)

    try:
        logger.debug('Request validated, getting json')
        data = request.json
        logger.debug('Recieved json, initating checker')
        checker = SyncChecker(data)
        logger.debug('Check initiated, check is_synced')
        is_synced = checker.check_is_synced()
        logger.debug(
            f'Checked is synced. Result: {is_synced}. Sending response')
        if(is_synced):
            return Response(json.dumps({'is_synced': is_synced}), 200)
        else:
            start = 0
            end = Constants.DELAY_CHECKER_SECTIONS_TIME + Constants.DELAY_RADIUS
            return Response(json.dumps({'is_synced': False, 'send_timestamp': {'start': start, 'end': end}}), 200)

    except Exception as e:
        logger.error(f'Error in check_sync. Error: {e}')
        return Response(json.dumps({'error': 'Internal server error.'}), 500)


@app.route('/check_delay', methods=['POST'])
def check_delay():
    """
    Route to check the delay based on a timestamps.

    Request Params:
        base64str: The buffer encoded as base64.
        timestamp: {start: START, end: END}. Note that this is in comparison to the full video loaded on the client side.
        subtitles: The subtitles of this timestamps.

    Response:
        If delay found:
            'subtitles': SubtitlesFile

        If delay not found:
            'send_timestamps': Next Timestamps
    """
    
    logger.info('Checking delay.')
    if(type(request.json) != dict):
        return Response('Bad Request.', 400)

    base64str = request.json['base64str']
    timestamp = request.json['timestamp']
    subtitles = request.json['subtitles']
    dc = DelayChecker(base64str, timestamp, subtitles)
    delay = dc.check_delay_in_timespan()

    if(delay is None):
        start = timestamp['start'] + Constants.DELAY_CHECKER_SECTIONS_TIME
        end = timestamp['end'] + Constants.DELAY_CHECKER_SECTIONS_TIME
        return Response(json.dumps({'send_timestamp': {'start': start, 'end': end}}), 200)

    else:
        return Response(json.dumps({ 'delay': delay }), 200)


@app.errorhandler(404)
def page_not_found(e):
    return Response('404 not found', 404)
