# Team: RGB Alphas
# Members: Andrew Hinea, Justin Dinkelbach, Brandon Lee, and David Sullivan
# Date: 10-05-2020

# The server handles clients by creating a new thread each time accept() returns a value
# the client() and handle_client_input() functions are where all the magic happens.

import sys
import time
import string
import threading
import errno
from socket import *
from time import sleep

class Server:
	# Will accept a shutdown command from client
	keepAlive = True
	
	def init(self, hostname, port, max_clients):
		self.server_address = (hostname, port)
		self.max_clients = max_clients

		self.socket_username_dictionary = {}
		self.socket_list = []
		self.thread_list = []

		# Create the socket and set some options.
		self.listen_socket = socket(AF_INET, SOCK_STREAM)
		try:
			self.listen_socket.bind(self.server_address)
		except:
			self.listen_socket.close()
			self.listen_socket = socket(AF_INET, SOCK_STREAM)
			self.listen_socket.bind(self.server_address)

		self.listen_socket.listen(max_clients + 1) # the +1 is to give a rejection message and close
		self.listen_socket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.listen_socket.settimeout(3.0)
	
		print('[Server] Listening on port {}.'.format(port))

	def broadcast(self, message):
		for client in self.socket_list:
			client.send(message)

	def shutdown(self):
		# the connection variable still exists in self, thats good because
		# its time to clean up before leaving
		self.listen_socket.close()
		self.listen_socket = None
		print('[Server] Shutdown Complete.')
	# This function will just accept new clients.
	# Originally we planned for the main thread to send/recv but oh well :)
	def run(self):
		while Server.keepAlive:
			if len(self.socket_list) < self.max_clients:
				try:
					client_socket, client_address = self.listen_socket.accept()
					print("{} has connected.".format(client_address))
				except:
					continue

				client_socket.send("req_username".encode())
				user_name = client_socket.recv(1024).decode()
				self.socket_username_dictionary[client_socket] = user_name
				self.socket_list.append(client_socket)

				# broadcast nickname
				print("{} is now {}".format(client_address, user_name))
				self.broadcast("{} has joined.".format(user_name).encode())
				# client_socket.send("Connected to server.".encode())

				if(len(self.socket_list) == 2):
					s1 = self.socket_list[0]
					n1 = self.socket_username_dictionary[s1]
					s2 = self.socket_list[1]
					n2 = self.socket_username_dictionary[s2]
					self.broadcast("Client X: {} received before Client Y: {}".format(n1,n2))

				# begin new client thread
				thread = threading.Thread(target=self.client_main, 		   \
						name='Thread {} handling {}'.format(threading.activeCount()-1, client_address), 
						args= (client_socket,)) 				  \
				
				self.thread_list.append(thread)
				thread.daemon = True
				thread.start()
			else:
				try:
					client_socket, client_address = self.listen_socket.accept()
					client_socket.send("Server is full. Queue unavailable".encode())
					client_socket.send("req_shutdown".encode())
					client_socket.close()
				except:
					continue

		for thread in self.thread_list:
			thread.join

	def client_main(self, client_socket):
		matchFound = False

		while True:
			try:
				message = client_socket.recv(1024)
				# if we didnt handle the message then it's
				# a chat message and we broadcast it.
				if message:
					# check exit conditions:
					if "auth_shutdown" in message:
						self.begin_shutdown()
						self.broadcast("req_shutdown".encode())
						break
					elif "exit" in message or not message:
						break
					elif True: # matchFound			<-- Here guys
							self.broadcast(message)
			except:
				break
			
			# enable / disable mesages based on occupancy.
			if self.get_client_count() >= 2:
				matchFound = True
			else:
				matchFound = False

		client_socket.send("req_shutdown")
		self.remove_client(client_socket)

	def remove_client(self, client_socket):
		lock = threading.Lock()
		lock.acquire()
		try:
			# remove and close the client.
			self.socket_list.remove(client_socket)
			client_socket.close()
			user_name = self.socket_username_dictionary[client_socket]
			self.broadcast('{} has left'.format(user_name).encode())
			self.socket_username_dictionary.pop(client_socket)
		finally:
			lock.release()

	def begin_shutdown(self):
		lock = threading.Lock()
		lock.acquire()
		try:
			Server.keepAlive = False
		finally:
			lock.release()

		# we are going to use either a switch or if's
		# and process the requests. We find out what
		# we have here and send the response
	def get_client_count(self):
		lock = threading.Lock()
		lock.acquire()
		try:
			count = len(self.socket_list)
		finally:
			lock.release()
			return count

	def input_handler(self, input):
		pass

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
	server = Server()
	server.init("192.168.1.117", 5555, 2)
	server.run()
	server.shutdown()

if __name__ == '__main__':
    main()
