# Team: RGB Alphas
# Members: Andrew Hinea, Justin Dinkelbach, Brandon Lee, and David Sullivan
# Date: 10-05-2020

# The server handles clients by creating a new thread each time accept() returns a value
# the client() and handle_client_input() functions are where all the magic happens.

# TODO:
# Input is not handled except for checking if a client is sending the server an exit command
# client is not made. I tested this using telnet.

import sys
import time
import string
import threading
import errno
from socket import *
from time import sleep

# avoid race conditions by giving each set of data its own wittle house.
class Client:
	def init(self, client_socket, client_address):
		self.client_socket = client_socket
		self.client_address = client_address
		self.user_name = ""
	def get_UserName():
		while True:
			fromClient = self.receive_from(client_socket)
			if "req_username" in fromClient:
				user_name = fromClient.split(' ')[1].rstrip("\n")
				if user_name in self.socket_username_dictionary:
					self.send_to(client_socket, "ack_denied\n")
					print('[Client {}] picked an invalid username.'.format(client_address))
				else:

					self.socket_username_dictionary[client_socket] = user_name
					self.send_to(client_socket, "ack_username\n")
					self.user_name = user_name
					print('[Client {}] is now {}.'.format(client_address, user_name))
					break
class Server:
	keepAlive = True
	# Will accept a shutdown command from client
	def init(self, hostname, port, max_clients):
		self.server_address = (hostname, port)
		# instances have variables created and given values from inside functions like so
		self.connection = socket(AF_INET, SOCK_STREAM)
		self.isRunning = True
		self.max_clients = max_clients
		self.socket_username_dictionary = {}
		self.socket_list = []
		self.thread_list = []
		# Under my settings there is more than 1 thread premade. perhaps on someone
		# else's machine they will have an issue where they can't connect
		# and they get a "server is full" message. 
		# If that's the case then remove self.initial_thread_count from the if statement
		# on line 48
		self.initial_thread_count = threading.activeCount()
		self.connection.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.connection.settimeout(3.0)
		self.connection.bind(self.server_address)
		self.connection.listen(max_clients)
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
				else:
					# creating a thread with a cool name
					# and passing argument(s).
					newThread = threading.Thread( 				\
						target=self.client_main, 					\
						name= 'Thread {} handling {}'.			\
							format(threading.activeCount()-1, 	\
							newAddress), args=\
								(newConnection, newAddress))
					newThread.daemon = True
					self.thread_list.append(newThread)
					newThread.start()
			else:
				try:
					newConnection, newAddress = self.connection.accept()
					newConnection.send("Server is full.".encode())
				except timeout as t:
					sleep(1)
				finally:
					newConnection.close()
		for thread in self.thread_list:
			thread.join()
	def client_main(self, client_socket, client_address):
		# set up username
		# client_socket.settimeout(30.0)
		matchFound = False
		user_name = "{}".format(client_address)
		user_name_wrapper = [user_name]
		self.client_init(client_socket, client_address, user_name_wrapper)
		user_name = user_name_wrapper[0]
		while True:
			if self.getClientCount() >= 2:
				if not matchFound:
					print("Match found for: {}".format(user_name))
					self.send_to(client_socket, "att_match_found\n")
					matchFound = True
				print("Waiting for data from: {}".format(user_name))
				data = self.receive_from(client_socket)
				# exit condition is here, life is better that way.
				if data:
					if "auth_shutdown" in data:
						# set run flag false
						lock = threading.Lock()
						lock.acquire()
						try:
							Server.keepAlive = False
						finally:
							lock.release()
						# say bye
						toClient = "Goodbye!"
						self.send_to(client_socket, toClient)
						break
					else:
						self.input_handler(client_socket, data, user_name)
		self.send_to(client_socket, "Unexpected goodbye?")
		self.socket_list.remove(client_socket)
		client_socket.close()
		# we are going to use either a switch or if's
		# and process the requests. We find out what
		# we have here and send the response
	def client_init(self, client_socket, client_address, user_name):
		# Greet the new client.
		print('[Client {}] has connected.'.format(client_address))
		while True:
			fromClient = self.receive_from(client_socket)
			if "req_username" in fromClient:
				user_name[0] = fromClient.split(' ')[1]
				lock = threading.Lock()
				lock.acquire()
				try:
					existingName = self.socket_username_dictionary.get(client_socket, None)
					# TODO
					# This doesn't check for unique names! :(
					if existingName != None:
						self.send_to(client_socket, "req_denied\n")
						print('[Client {}] picked an invalid username.'.format(client_address))
					else:
						self.socket_username_dictionary[client_socket] = user_name[0]
						self.socket_list.append(client_socket)
						print('[Client {}] is now {}.'.format(client_address, user_name[0]))
						self.send_to(client_socket, "ack_username\n")
						break
				finally:
					lock.release()
	# unused...
	def get_username(self, client_socket, client_address):
		name = ""
		lock = threading.Lock()
		lock.acquire()
		try:
			if client_socket in self.socket_username_dictionary:
				name = self.socket_username_dictionary[client_socket]
				return name
			else:
				name = "Client {}".format(client_address)
				return name
		finally:
			lock.release()	
	def getClientCount(self):
		lock = threading.Lock()
		lock.acquire()
		try:
			connected_clients = len(self.socket_list)
		finally:
			lock.release()
			return connected_clients
	def input_handler(self, client_socket, data, user_name):
		lock = threading.Lock()
		lock.acquire()
		try:
			print('[{}]: {}'.format(user_name, data))
			message = data.upper()
			self.send_to(client_socket, message)
		finally:
			lock.release()
	def send_to(self, client_socket, data):
		lock = threading.Lock()
		lock.acquire()
		try:
			client_socket.send(data.encode())
			return True
		except error as e:
			#print(e)
			# print("{}: Sending() has a race condition.".format(self.user_name))
			return False
		finally:
			lock.release()
	def receive_from(self, client_socket):
		lock = threading.Lock()
		lock.acquire()
		try:
			data = client_socket.recv(1024).decode().rstrip("\n")
			return data
		except error as e:
			#print("Receive: {}".format(e))
			# print("{}: Receiving has a race condition.".format(self.user_name))
			return None
		finally:
			lock.release()


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
	server.init("192.168.1.117", 5555, 2)
	server.run()
	server.shutdown()

if __name__ == '__main__':
    main()
