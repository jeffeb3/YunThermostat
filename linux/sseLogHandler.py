#!/usr/bin/env python

import logutils.queue as lq
import Queue
import threading
from bottle import Bottle, response, template

# The intention is to allow a connection to a log via a local http server.
# I'd like it to use bottle _or_ flask, if possible.
#

class SseWebLoop(threading.Thread):
    def __init__(self, web):
        threading.Thread.__init__(self)
        self.web = web
        self.daemon = True

    def run(self):
        self.web.run(debug=False, quiet=True)

class SseLogHandler(lq.QueueHandler):
    ''' Handler to send sse events. '''

    def __init__(self,
                 bottleApp=None,
                 queueMaxSize=32):
        lq.QueueHandler.__init__(self, Queue.Queue(queueMaxSize))
        
        self.web = bottleApp
        self.webLoop = None
        if self.web is None:
            self.web = Bottle()
            self.webLoop = SseWebLoop(self.web)
            self.webLoop.start()

        self.web.route('/log_view', 'GET', self.log_view)
        self.web.route('/logs', 'GET', self.logs)

    def log_view(self):
        return """
                <!DOCTYPE html>

                <meta charset="utf-8" />

                <title>Server Sent Event Log Test</title>

                <script language="javascript" type="text/javascript">

                    // Create server sent event connection.
                    var server = new EventSource('/logs');

                    function write(data)
                    {
                        document.myform.outputtext.value += data
                        document.myform.outputtext.scrollTop = document.myform.outputtext.scrollHeight;
                    };

                    server.onmessage = function(e)
                    {
                        // Update measurement value.
                        write(e.data + '\\n');
                    };

                    server.onopen = function(e)
                    {
                        write('Connected.\\n');
                    };

                    server.onerror = function(e)
                    {
                        write('Disconnected.\\n');
                    };

                </script>

                <form name="myform">
                    <p>
                        <textarea name="outputtext" rows="60" cols="80"></textarea>
                    </p>
                </form>

                </html>
                """

    def logs(self):
        response.content_type = 'text/event-stream'
        while True:    # TODO Make this based on some kind of while alive event.
            try:
                # only look for one seconds, because we are hoping to escape
                # this loop with something logical.
                data = self.queue.get(True, 1)
                text = 'data:' + '\ndata:'.join(self.format(data).split('\n')) + '\n\n'
                yield text
            except Queue.Empty:
                continue

        print 'exited logs loop'
        raise StopIteration

    def enqueue(self, record):
        """
        Override the QueueHandler to make it clean records out if they are full.

        The client of the SSE server may not be connected for a while, but we
        still want them to get some of the previous results. by making sure the
        events get onto the queue, even if full, we will ensure that the only
        information stored in the queue is recent.
        """
        try:
            lq.QueueHandler.enqueue(self, record)
        except Queue.Full:
            # there is no room on the queue, lets remove one, and enqueue again.
            discard = self.queue.get_nowait()
            # if this method fails with Full, then too bad.
            lq.QueueHandler.enqueue(self, record)

if __name__ == '__main__':
    import logging
    import time
    import signal

    sse_handler = SseLogHandler(queueMaxSize=10)

    log = logging.getLogger()
    log.addHandler(sse_handler)

    sse_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))

    while True:
        log.warn('warning')
        time.sleep(1)
