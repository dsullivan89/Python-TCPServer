# Team: RGB Alphas
# Members: Andrew Hinea, Justin Dinkelbach, Brandon Lee, and David Sullivan
# Date: 10-05-2020

# The server handles clients by creating a new thread each time accept() returns a value
# the client() and handle_client_input() functions are where all the magic happens.

# TODO:
# Input is not handled except for checking if a client is sending the server an exit command
# client is not made. I tested this using telnet.

import sys
import string
import threading
import errno
from socket import *
from time import sleep

class Server:
	keepAlive = True
	# Will accept a shutdown command from client
	def init(self, hostname, port, max_clients):
		self.server_address = (hostname, port)
		# instances have variables created and given values from inside functions like so
		self.connection = socket(AF_INET, SOCK_STREAM)
		self.isRunning = True
		self.max_clients = max_clients
		# Under my settings there is more than 1 thread premade. perhaps on someone
		# else's machine they will have an issue where they can't connect
		# and they get a "server is full" message. 
		# If that's the case then remove self.initial_thread_count from the if statement
		# on line 48
		self.initial_thread_count = threading.activeCount()
		self.connection.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.connection.settimeout(3.0)
		self.connection.bind(self.server_address)
		self.connection.listen(1)
		print('[Server] Listening on port {}.'.format(port))
	def send(self, client, addr):
		no = True # python doesnt like empty function declarations. boo-wahh
	def shutdown(self):
		# the connection variable still exists in self, thats good because
		# its time to clean up before leaving
		self.connection.close()
		self.connection = None
		print('[Server] Shutdown Complete.')
	# This function will just accept new clients.
	# Originally we planned for the main thread to send/recv but oh well :)
	def run(self):
		while Server.keepAlive:
			# This is just elegant. one thread = one client so therefore
			# our number of concurrent clients IS our thread count.
			# We will give excess clients the boot as shown in the else statement
			if threading.activeCount() - self.initial_thread_count < self.max_clients:
				try:
					newConnection, newAddress = self.connection.accept()
				except timeout as t:
					sleep(1)
					print('sleeping')
				else:
					newThread = threading.Thread(target=self.client, name='Thread {} handling {}'.format(threading.activeCount()-1, newAddress), args=(newConnection, newAddress))
					newThread.daemon = True
					newThread.start()
			else:
				newConnection.send("Server is full.".encode())
				newConnection.close()
	def client(self, client_socket, client_address):
		print('[Client {}] has connected.'.format(client_address))
		while True:
			data = self.receive_from(client_socket)
			if not data: 
				print('[Client {}] has disconnected.'.format(client_address))
				break
			elif "exit" in data:	# exit condition is here, life is better that way.
				lock = threading.Lock()
				lock.acquire()
				try:
					Server.keepAlive = False
				finally:
					lock.release()
				break
			else:
				print('[Client {}]: {}'.format(client_address, data))
				# we now go to where we handle the data
				if not self.input_handler(client_socket, data):
					break
		client_socket.close()
		# we are going to use either a switch or if's
		# and process the requests. We find out what
		# we have here and send the response
	def input_handler(self, client_socket, data):
		if data:
			message = data.upper()
			return self.send_to(client_socket, message)
		else:
			print('[Server] data was null')
	def send_to(self, client_socket, data):
		try:
			client_socket.send(data.encode())
			return True
		except error as e:
			print(e)
			return False
	def receive_from(self, client_socket):
		try:
			data = client_socket.recv(1024).decode()
		except error as e:
			print(e)
			return None
		else:
			return data


def main():
	# Create a TCP socket 
	# Notice the use of SOCK_STREAM for TCP packets
	#serverSocket = socket(AF_INET,SOCK_STREAM)
	# Assign IP address and port number to socket
	#serverSocket.bind(('',serverPort))
	#serverSocket.listen(1)
	#print ('The server is ready to receive')
	#while True:
	#	connectionSocket, addr = serverSocket.accept()
	#	sentence = connectionSocket.recv(1024).decode()
	#	capitalizedSentence = sentence.upper()
	#	connectionSocket.send(capitalizedSentence.encode())
	#	connectionSocket.close() 
	server = Server()
	server.init("localhost", 5555, 2)
	server.run()
	server.shutdown()

if __name__ == '__main__':
    main()
