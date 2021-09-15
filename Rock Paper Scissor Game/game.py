class Game:

	# INITIALIZE VARIABLEs #
	def __init__(self, id):
		self.p1Move = False
		self.p2Move = False
		self.ready = False
		self.id = id
		self.moves = [None, None]
		self.wins = [0, 0]
		self.ties = 0

	def get_player_move(self, p):
		return self.moves[p]

	# MOVEMENT INITIATION #
	def play(self, player, move):
		self.moves[player] = move
		if player == 0:
			self.p1Move = True
		else:
			self.p2Move = True

	# CONNECT THE SERVER #
	def connected(self):
		return self.ready

	def bothMove(self):
		return self.p1Move and self.p2Move

	# GAME RULES #
	def winner(self):
		p1 = self.moves[0].upper()[0]
		p2 = self.moves[1].upper()[0]

		winner = -1

		if p1 == "R" and p2 == "S":
			winner = 0
		elif p1 == "S" and p2 == "R":
			winner = 1
		elif p1 == "P" and p2 == "R":
			winner = 0
		elif p1 == "R" and p2 == "P":
			winner = 1
		elif p1 == "S" and p2 == "P":
			winner = 0
		elif p1 == "P" and p2 == "S":
			winner = 1

		return winner

	# RESET GAME #
	def resetMove(self):
		self.p1Move = False
		self.p2Move = False
