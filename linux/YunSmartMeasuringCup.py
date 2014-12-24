# Update Python path to include libraries on SD card.
import sys
sys.path.append('/mnt/sda1/python-packages')

# Import system libraries.
import socket
import time

# Import flask library.
from flask import *


# Port the YunServer instance is listening on for connections.
YUN_SERVER_PORT = 5678

# Create flask application.
app = Flask(__name__)


# Generator function to connect to the YunServer instance and send
# all data received from it to the webpage as HTML5 server sent events.
def yunserver_sse():
	try:
		# Connect to YunServer instance that's listening on localhost.
		soc = socket.create_connection(('localhost', 5678))
		socfile = soc.makefile()
		while True:
			# Get data from server.
			line = socfile.readline()
			# Stop if the server closed the connection.
			if not line:
				raise StopIteration
			# Send the data to the web page in the server sent event format.
			yield 'data: {0}\n\n'.format(line)
			# Sleep so the CPU isn't consumed by this thread.
			time.sleep(0)
	except socket.error:
		# Error connecting to socket. Raise StopIteration to quit.
		raise StopIteration


@app.route('/measurements')
def measurements():
	return Response(yunserver_sse(), mimetype='text/event-stream')

@app.route('/')
def root():
	return render_template('index.html')


if __name__ == '__main__':
	# Create a server listening for external connections on the default
	# port 5000.  Enable debug mode for better error messages and live
	# reloading of the server on changes.  Also make the server threaded
	# so multiple connections can be processed at once (very important
	# for using server sent events).
	app.run(host='0.0.0.0', debug=True, threaded=True)