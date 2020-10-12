import socket
import threading

class Server:
	def init(self, host_name, port, max_clients):
		self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		server_address = (host_name, port)
		self.listen_socket.bind(server_address)
		self.listen_socket.listen(max_clients)

		self.socket_username_dictionary = {}
		self.socket_list = []

		print("Server listening on {}:{}".format(host_name, port))

	def broadcast(self, message):
		for client in self.socket_list:
			client.send(message)

	def handle_client(self, client_socket):
		while True:
			try:
				message = client_socket.recv(1024)
				self.broadcast(message)
			except:
				# remove and close the client.
				index = self.socket_list.index(client_socket)
				self.socket_list.remove(index)
				client_socket.close()
				user_name = self.socket_username_dictionary[client_socket]
				self.broadcast('{} has left'.format(user_name).encode())
				self.socket_username_dictionary.remove(client_socket)
				break
	def receive_clients(self):
		while True:
			# accept connection
			client_socket, client_address = self.listen_socket.accept()
			print("{} has connected.".format(client_address))

			client_socket.send("req_username".encode())
			user_name = client_socket.recv(1024).decode()
			self.socket_username_dictionary[client_socket] = user_name
			self.socket_list.append(client_socket)

			# broadcast nickname
			print("{} is now {}".format(client_address, user_name))
			self.broadcast("{} has joined.".format(user_name).encode())
			client_socket.send("Connected to server.".encode())

			# begin new client thread
			thread = threading.Thread(target=self.handle_client, args=(client_socket,))
			thread.start()
	def shutdown(self):
		self.listen_socket(close)

def main():
	server = Server()
	server.init("localhost", 5555, 2)
	server.receive_clients()
	server.shutdown()

if __name__ == '__main__':
	main()
