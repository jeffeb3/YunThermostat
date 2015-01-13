#!/usr/bin/env python

import threading
import Queue
import collections
import logging
from bottle import Bottle, response, template

# The intention is to allow a connection to a log via a local http server.
# I'd like it to use bottle _or_ flask, if possible.
#

class SseLogHandler(logging.Handler):
    ''' Handler to send sse events. '''

    def __init__(self,
                 queueMaxSize=32):
        logging.Handler.__init__(self)

        self._history = collections.deque(maxlen=queueMaxSize)
        self._lock = threading.RLock()
        self._clients = []

    @staticmethod
    def log_view():
        """
        Return an example web page that could be used to render the log messages.

        Use with a normal text formatter for best results.

        Connect to your bottle server like this:
        app.route('/log_view','GET',SseLogHandler.log_view)
        """
        return """
            <!DOCTYPE html>

            <meta charset="utf-8" />

            <title>Server Sent Event Log Test</title>
            <script src="http://code.jquery.com/jquery-1.11.2.min.js"></script>
            <script src="http://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.js"></script>
            <link rel="stylesheet" href="http://code.jquery.com/mobile/1.4.5/jquery.mobile-1.4.5.min.css">
            <script language="javascript" type="text/javascript">

                // Create server sent event connection.
                var server = new EventSource('/logs');

                function write(data)
                {
                    $("#log").append('<p>' + data + '</p>');
                };

                server.onmessage = function(e)
                {
                    // Update measurement value.
                    write(e.data);
                };

                server.onopen = function(e)
                {
                    write('Connected.');
                };

                server.onerror = function(e)
                {
                    write('Disconnected.');
                };

            </script>

            <div data-role="collapsible" data-collapsed="false" data-theme="b">
                <h1>Log</h1>
                <div id="log"></div>
            </div>

            </html>
            """

    def logs(self):
        """
        Returns a server sent event stream of log messages.

        Connect to your bottle server like this:
        app.route('/logs','GET',sseHandler.logs)

        Connect your browser to http://<server>:<port>/log_view
        """
        response.content_type = 'text/event-stream'

        q = Queue.Queue(10) # Should never be more than 1.
        with self._lock:
            # return the history upto this point.
            for record in self._history:
                yield 'data:' + '\ndata:'.join(self.format(record).split('\n')) + '\n\n'
            # add a q for this client.
            self._clients.append(q)

        while True:    # TODO Make this based on some kind of while alive event.
            try:
                # only look for one seconds, because we are hoping to escape
                # this loop with something logical.
                data = q.get(True, 1.0)
                yield 'data:' + '\ndata:'.join(self.format(data).split('\n')) + '\n\n'
            except Queue.Empty:
                continue

        with self._lock:
            self._clients.remove(q)
        raise StopIteration

    def enqueue(self, record):
        """
        Enqueue a record.

        The base implementation uses :meth:`~queue.Queue.put_nowait`. You may
        want to override this method if you want to use blocking, timeouts or
        custom queue implementations.

        :param record: The record to enqueue.
        """
        with self._lock:
            self._history.append(record)
            for q in self._clients:
                try:
                    q.put_nowait(record)
                except Queue.Full:
                    # there is no room on the queue, lets remove one, and enqueue again.
                    discard = q.get_nowait()
                    # if this method fails with Full, then too bad.
                    q.put_nowait(record)

    def prepare(self, record):
        """
        Prepares a record for queuing. The object returned by this method is
        enqueued.

        The base implementation formats the record to merge the message
        and arguments, and removes unpickleable items from the record
        in-place.

        You might want to override this method if you want to convert
        the record to a dict or JSON string, or send a modified copy
        of the record while leaving the original intact.

        :param record: The record to prepare.
        """
        # The format operation gets traceback text into record.exc_text
        # (if there's exception data), and also puts the message into
        # record.message. We can then use this to replace the original
        # msg + args, as these might be unpickleable. We also zap the
        # exc_info attribute, as it's no longer needed and, if not None,
        # will typically not be pickleable.
        self.format(record)
        record.msg = record.message
        record.args = None
        record.exc_info = None
        return record

    def emit(self, record):
        """
        Emit a record.

        Writes the LogRecord to the queue, preparing it for pickling first.

        :param record: The record to emit.
        """
        try:
            self.enqueue(self.prepare(record))
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)

if __name__ == '__main__':
    import time

    class LogLoop(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.daemon = True

        def run(self):
            while True:
                log.warn('warning')
                time.sleep(1)

    sse_handler = SseLogHandler(queueMaxSize=100)
    log = logging.getLogger() # root logger
    log.setLevel(logging.DEBUG)
    log.addHandler(sse_handler)
    sse_handler.setFormatter(logging.Formatter('%(asctime)s: %(message)s'))

    lthread = LogLoop()
    lthread.start()

    # set up a web server
    app = Bottle()
    app.route('/','GET',SseLogHandler.log_view)
    app.route('/logs','GET',sse_handler.logs)

    try:
        import pastey
        log.info('running with paste')
        app.run(debug=True, server='paste')
    except ImportError:
        try:
            import gevent
            log.info('running with gevent')
            app.run(debug=True, server='paste')
        except ImportError:
            log.info('running with bottle, only one page can be viewed at a time')
            app.run(debug=True)
    