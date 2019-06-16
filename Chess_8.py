from pprint import pprint
from math import *
import pygame
import random
import copy
import time
import sys

from threading import Thread
import socket as s
import select
import errno
import pickle
pygame.init()


class Chessboard: #The chessboard class is the class that handles all information of the pieces relative to one another

    cord = [[letter+str(num) for letter in 'abcdefgh'] for num in range(8, 0, -1)] #coordinate system
    valid_nums = [i for i in range(8)] #valid positions on the board (0-7)
    #grid is 2D list of rect objects used to determine what piece was clicked. 8x8 grid, 1 rect for each square
    grid = [[pygame.Rect(112.5*i, 112.5*j, 112.5, 112.5) for i in range(8)] for j in range(8)]

    def __init__(self, file_name): #constructor
        self.FEN = self.get_FEN(file_name, 0).replace('/', ' ').split(' ') #gets FEN from a file.
        self.pieces, self.turn = self.read_FEN(self.FEN) #reads the FEN and stores important information
        if self.turn is -1: #if it is currently black's turn and the user has the board flip feature enabled,
            Chessboard.flip(self) #the board is flipped
        self.init_king() #setting attributes - see function

    def get_FEN(self, file_name, line = None): #gets FEN from a file
        with open(file_name, 'r') as read_file:
            text = []
            while True:
                FEN = read_file.readline().replace('\n', '')
                if FEN == '':
                    break
                text.append(FEN)
        if line is None:
            return text
        else:
            return text[line]

    def read_FEN(self, FEN): #interprets FEN
        pieces = [] #2D list of Piece subclass objects
        for index_1, item_1 in enumerate(FEN): #nested loop
            x = 0
            rank = [] #each list element in the 2D list represents a rank on the chessboard
            if index_1 < 8: #only 8 elements (Piece objects) in each nested list
                for index_2, item_2 in enumerate(item_1):
                    if item_2.isalpha(): #in FEN, a letter represents a piece, if it is a letter:
                        if item_2.isupper(): #uppercase letters are white pieces
                            col = 1
                        else:
                            col = -1 #lowercase letters are black pieces

                        if item_2.lower() == 'p': #Depending on the FEN letter...
                            rank.append(Pawn(self, (index_1, index_2 + x), col))
                            
                        elif item_2.lower() == 'n': #a corresponding Piece object is created...
                            rank.append(Knight(self, (index_1, index_2 + x), col))
                            
                        elif item_2.lower() == 'b': #with attributes: the Chessboard object...
                            rank.append(Bishop(self, (index_1, index_2 + x), col))
                            
                        elif item_2.lower() == 'r': #position in the list(and conversly the board)...
                            rank.append(Rook(self, (index_1, index_2 + x), col, True))
                            
                        elif item_2.lower() == 'q': #and colour. The Chessboard object is an attribute...
                            rank.append(Queen(self, (index_1, index_2 + x), col))
                            
                        elif item_2.lower() == 'k': #so that pieces can reference each other through the shared...
                            rank.append(King(self, (index_1, index_2 + x), col, None, None)) #Chessboard object
                    else: #if the current character is not a letter, it's a number that represents the number of...
                        for _ in range(int(item_2)): #empty spaces between pieces. Empty spaces are added to the rank...
                            rank.append(Empty(self, (index_1, index_2 + x), None)) #depending on the number in the FEN
                            x += 1
                        x -= 1
                pieces.append(rank)
        if FEN[8] == 'w': #the FEN also indicates who's turn it is
            turn = 1
        else:
            turn = -1
        return pieces, turn #the 2D list and who's turn it is are both returned

    def write_FEN(self):
        FEN = ''
        empty_spaces = 0
        codes = ['p', 'n', 'b', 'r', 'q', 'k']
        for rank in self.pieces:
            for piece in rank:
                if piece.code is not None:
                    if empty_spaces is not 0:
                        FEN += str(empty_spaces)
                        empty_spaces = 0

                    if piece.colour is 1:
                        FEN += codes[piece.code].upper()
                    else:
                        FEN += codes[piece.code]
                else:
                    empty_spaces += 1
            if empty_spaces is not 0:
                FEN += str(empty_spaces)
                empty_spaces = 0
            FEN += '/'
        FEN = FEN.strip('/')
        return FEN

    def init_king(self):
        self.white_king = self.get_king_pos(1) #gets position of both kings
        self.black_king = self.get_king_pos(-1)
        self.white_king = self.pieces[self.white_king[0]][self.white_king[1]] #getting both King objects
        self.black_king = self.pieces[self.black_king[0]][self.black_king[1]]
        if 'K' in self.FEN[9]: #reads castling availability from FEN
            self.white_king.has_moved = False #sets attributes for king and rook
            self.pieces[7][7].has_moved = False #these attributes --> True once they move and castling is not available
        if 'Q' in self.FEN[9]:
            self.white_king.has_moved = False #process is repeated for all 4 castling possibilities
            self.pieces[7][0].has_moved = False
        if 'k' in self.FEN[9]:
            self.black_king.has_moved = False
            self.pieces[0][7].has_moved = False
        if 'q' in self.FEN[9]:
            self.black_king.has_moved = False
            self.pieces[0][0].has_moved = False

        self.white_king.check = self.white_king.is_check(self.pieces, list(self.white_king.pos)) #see if king is in check
        self.black_king.check = self.black_king.is_check(self.pieces, list(self.black_king.pos)) #and sets check attribute

    def get_king_pos(self, colour): #finds the position of the king given the colour of the king
        for index_1, rank in enumerate(self.pieces):
            for index_2, piece in enumerate(rank):
                if piece.code is 5 and piece.colour is colour:
                    return [index_1, index_2]

    @staticmethod
    def my_copy(board):
        new_board = []
        for rank in board:
            rank_list = []
            for piece in rank:
                if piece.code is 0:
                    piece = Pawn(piece.board, piece.pos, piece.colour)
                elif piece.code is 1:
                    piece = Knight(piece.board, piece.pos, piece.colour)
                elif piece.code is 2:
                    piece = Bishop(piece.board, piece.pos, piece.colour)
                elif piece.code is 3:
                    piece = Rook(piece.board, piece.pos, piece.colour, piece.has_moved)
                elif piece.code is 4:
                    piece = Queen(piece.board, piece.pos, piece.colour)
                elif piece.code is 5:
                    piece = King(piece.board, piece.pos, piece.colour, piece.check, piece.has_moved)
                else:
                    piece = Empty(piece.board, piece.pos, None)
                rank_list.append(piece)
            new_board.append(rank_list)

        # for rank in board:
        #     for piece in rank:
        #         piece.board = new_board
        return new_board

    @staticmethod
    def flip(self): #flips 'the board'. reverses the ranks, every piece in the rank, and rewrites the pos attribute of each piece
        self.pieces = self.pieces[::-1] #flips each ranks position in 2D list
        for rank in range(len(self.pieces)):
            self.pieces[rank] = self.pieces[rank][::-1] #flips position pieces in each rank
        for index_1 in range(len(self.pieces)):
            for index_2 in range(len(self.pieces[index_1])):
                self.pieces[index_1][index_2].pos = (index_1, index_2) #position attributes of every pieces is changed

    @staticmethod
    def evaluate(board, colour):
        val = 0
        for rank in board:
            for piece in rank:
                if piece.colour is colour:
                    val += (piece.value + piece.good_positions[piece.pos[0]][piece.pos[1]])
                elif piece.colour is colour * -1:
                    val -= (piece.value + piece.good_positions[7 - piece.pos[0]][7 - piece.pos[1]])

        return val

    def temp_move(self, pos, move):
        captured_piece = None
        if self.pieces[move[0]][move[1]].colour is not None:
            captured_piece = self.pieces[move[0]][move[1]]
            self.pieces[move[0]][move[1]] = Empty(self, self.pieces[move[0]][move[1]].pos, None)
        self.pieces[pos[0]][pos[1]], self.pieces[move[0]][move[1]] = \
            self.pieces[move[0]][move[1]], self.pieces[pos[0]][pos[1]]
        self.pieces[pos[0]][pos[1]].pos, self.pieces[move[0]][move[1]].pos = \
            self.pieces[move[0]][move[1]].pos, self.pieces[pos[0]][pos[1]].pos
        return pos, move, captured_piece

    def temp_unmove(self, move, pos, captured_piece):
        self.pieces[pos[0]][pos[1]], self.pieces[move[0]][move[1]] = \
            self.pieces[move[0]][move[1]], self.pieces[pos[0]][pos[1]]
        self.pieces[pos[0]][pos[1]].pos, self.pieces[move[0]][move[1]].pos = \
            self.pieces[move[0]][move[1]].pos, self.pieces[pos[0]][pos[1]].pos

        if captured_piece is not None:
            self.pieces[pos[0]][pos[1]] = captured_piece


class Pieces: #there aren't really any Piece objects. Every object is an object of a subclass inheriting from this class

    def __init__(self, board, pos, colour):
        self.pos = pos #position, index of 2D list
        self.board = board #Chessboard object
        self.colour = colour #1 or -1 based on the colour of the piece

    @staticmethod
    def get_cord(self = None, pos = None): #converts to coordinate values. Easier to read and thus, troubleshoot
        if self is not None:
            pos = self.pos
            cord = Chessboard.cord[pos[0]][pos[1]]
            return cord
        elif pos is not None:
            cord = Chessboard.cord[pos[0]][pos[1]]
            return cord


class King(Pieces):

    def __init__(self, board, pos, colour, check, has_moved):
        super().__init__(board, pos, colour)
        self.code = 5  # number representing the piece
        self.value = 900  # value of the piece
        self.check = check #if the king is in check
        self.has_moved = has_moved #if the king has moved (used for castling)
        #these attributes are changed in the Chessboard class' init_king() method
        self.good_positions = [[-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
                               [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
                               [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
                               [-3.0, -4.0, -4.0, -5.0, -5.0, -4.0, -4.0, -3.0],
                               [-2.0, -3.0, -3.0, -4.0, -4.0, -3.0, -3.0, -2.0],
                               [-1.0, -2.0, -2.0, -2.0, -2.0, -2.0, -2.0, -1.0],
                               [ 2.0,  2.0,  0.0,  0.0,  0.0,  0.0,  2.0,  2.0 ],
                               [ 2.0,  3.0,  1.0,  0.0,  0.0,  1.0,  3.0,  2.0 ]]

    def get_moves(self): #return a list of legal moves the king object has
        moves = [(self.pos[0] + 1, self.pos[1] + 1),
                 (self.pos[0] - 1, self.pos[1] - 1),
                 (self.pos[0] + 1, self.pos[1] - 1),
                 (self.pos[0] - 1, self.pos[1] + 1),
                 (self.pos[0] + 1, self.pos[1] + 0),
                 (self.pos[0] - 1, self.pos[1] + 0),
                 (self.pos[0] + 0, self.pos[1] + 1),
                 (self.pos[0] + 0, self.pos[1] - 1)]
        #king has 8 possible locations to move to
        #new list is created of only the moves that: are on the board, not the same colour piece, and dont result in check
        moves = [(x, y) for (x, y) in moves if x in Chessboard.valid_nums and y in Chessboard.valid_nums \
                 and self.board.pieces[x][y].colour is not self.colour
                 and self.is_check(self.board.pieces, [x, y]) is False]

        #if the king hasn't moved yet, castling is considered
        if self.has_moved is False:
            if flip and self.colour is -1:
                rook = self.board.pieces[7][0]
                if rook.code is 3 and rook.has_moved is False and rook.colour is -1:
                    x = 0 #the above checks if the black rook is in the right location and hasn't moved
                    while True:
                        if self.is_check(self.board.pieces, [self.pos[0], self.pos[1] + x]) is True:
                            break #none of the spaces the king is in can be in danger
                        x -= 1
                        if self.is_check(self.board.pieces, [self.pos[0], self.pos[1] + x]) is True \
                                or self.board.pieces[self.pos[0]][self.pos[1] + x].colour is not None:
                            break #the spaces between the rook and king must also be free
                        if x is -2: #if conditions are satisfied...
                            moves.append((self.pos[0], self.pos[1] - 2)) #castling is added as a move

                rook = self.board.pieces[7][7]
                if rook.code is 3 and rook.has_moved is False and rook.colour is -1:
                    x = 0
                    while True:
                        if self.is_check(self.board.pieces, [self.pos[0], self.pos[1] + x]) is True:
                            break
                        x += 1
                        if self.is_check(self.board.pieces, [self.pos[0], self.pos[1] + x]) is True \
                                or self.board.pieces[self.pos[0]][self.pos[1] + x].colour is not None:
                            break
                        if x is 2 and self.board.pieces[self.pos[0]][self.pos[1] + 3].colour is None:
                            moves.append((self.pos[0], self.pos[1] + 2))
            else:
                if self.colour is 1:
                    rook = self.board.pieces[7][7]
                else:
                    rook = self.board.pieces[0][7]
                if rook.code is 3 and rook.has_moved is False:
                    x = 0
                    while True:
                        if self.is_check(self.board.pieces, [self.pos[0], self.pos[1] + x]) is True:
                            break
                        x += 1
                        if self.is_check(self.board.pieces, [self.pos[0], self.pos[1] + x]) is True \
                        or self.board.pieces[self.pos[0]][self.pos[1] + x].colour is not None:
                            break
                        if x is 2:
                            moves.append((self.pos[0], self.pos[1] + 2))

                if self.colour is 1:
                    rook = self.board.pieces[7][0]
                else:
                    rook = self.board.pieces[0][0]
                if rook.code is 3 and rook.has_moved is False:
                    x = 0
                    while True:
                        if self.is_check(self.board.pieces, [self.pos[0], self.pos[1] + x]) is True:
                            break
                        x -= 1
                        if self.is_check(self.board.pieces, [self.pos[0], self.pos[1] + x]) is True \
                        or self.board.pieces[self.pos[0]][self.pos[1] + x].colour is not None:
                            break
                        if x is -2 and self.board.pieces[self.pos[0]][self.pos[1] -3].colour is None:
                            moves.append((self.pos[0], self.pos[1] - 2))
        return moves

    def is_check(self, board, pos): #determines if the king is in check
        for rank in board:
            for piece in rank:
                if piece.colour is self.colour * -1: #considers all pieces of the opposite colour
# ----------------------------------------------------------------------------------------------------------------------
                    if piece.code is 0: #if the piece is a pawn, its capturing moves are generated...
                        if flip: #and checks (no pun intended) to see if the king's pos is in the moves
                            Chessboard.flip(self.board)
                            [pos[0], pos[1]] = [7 - pos[0], 7 - pos[1]]
                            if pos in [[piece.pos[0] - 1, piece.pos[1] - 1], [piece.pos[0] - 1, piece.pos[1] + 1]]:
                                Chessboard.flip(self.board)
                                [pos[0], pos[1]] = [7 - pos[0], 7 - pos[1]]
                                return True
                            Chessboard.flip(self.board)
                            [pos[0], pos[1]] = [7 - pos[0], 7 - pos[1]]
                        else:
                            if piece.colour is 1:
                                if pos in [[piece.pos[0] - 1, piece.pos[1] - 1], [piece.pos[0] - 1, piece.pos[1] + 1]]:
                                    return True
                            else:
                                if pos in [[piece.pos[0] + 1, piece.pos[1] - 1], [piece.pos[0] + 1, piece.pos[1] + 1]]:
                                    return True
# ----------------------------------------------------------------------------------------------------------------------
                    if piece.code is 1: #generates moves for the knight and does the same thing
                        moves = [[piece.pos[0] - 2, piece.pos[1] + 1],
                                 [piece.pos[0] - 2, piece.pos[1] - 1],
                                 [piece.pos[0] - 1, piece.pos[1] + 2],
                                 [piece.pos[0] - 1, piece.pos[1] - 2],
                                 [piece.pos[0] + 2, piece.pos[1] + 1],
                                 [piece.pos[0] + 2, piece.pos[1] - 1],
                                 [piece.pos[0] + 1, piece.pos[1] + 2],
                                 [piece.pos[0] + 1, piece.pos[1] - 2]]

                        moves = [[x, y] for [x, y] in moves if x in Chessboard.valid_nums and y in Chessboard.valid_nums]
                        if pos in moves:
                            return True
# ----------------------------------------------------------------------------------------------------------------------
                    if piece.code is 2:
                        moves = []
                        x = 1
                        while True: #incrementally generates moves for the bishop
                            if piece.pos[0] + x > 7 or piece.pos[1] + x > 7:
                                break #if the move is not on the board, or it reaches its own colour piece, no more moves are generated
                            moves.append([piece.pos[0] + x, piece.pos[1] + x])
                            if board[piece.pos[0] + x][piece.pos[1] + x].colour is piece.colour * -1 \
                            and board[piece.pos[0] + x][piece.pos[1] + x].code is not 5 \
                            or board[piece.pos[0] + x][piece.pos[1] + x].colour is piece.colour:
                                break #if the move results in a capture, no more moves are generated
                            x += 1
                        x = 1
                        while True: #the process is continued for all 4 directions
                            if piece.pos[0] - x < 0 or piece.pos[1] - x < 0:
                                break
                            moves.append([piece.pos[0] - x, piece.pos[1] - x])
                            if board[piece.pos[0] - x][piece.pos[1] - x].colour is piece.colour * -1 \
                            and board[piece.pos[0] - x][piece.pos[1] - x].code is not 5 \
                            or board[piece.pos[0] - x][piece.pos[1] - x].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[0] + x > 7 or piece.pos[1] - x < 0:
                                break
                            moves.append([piece.pos[0] + x, piece.pos[1] - x])
                            if board[piece.pos[0] + x][piece.pos[1] - x].colour is piece.colour * -1 \
                            and board[piece.pos[0] + x][piece.pos[1] - x].code is not 5 \
                            or board[piece.pos[0] + x][piece.pos[1] - x].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[0] - x < 0 or piece.pos[1] + x > 7:
                                break
                            moves.append([piece.pos[0] - x, piece.pos[1] + x])
                            if board[piece.pos[0] - x][piece.pos[1] + x].colour is piece.colour* -1 \
                            and board[piece.pos[0] - x][piece.pos[1] + x].code is not 5 \
                            or board[piece.pos[0] - x][piece.pos[1] + x].colour is piece.colour:
                                break
                            x += 1
                        if pos in moves:
                            return True
# ----------------------------------------------------------------------------------------------------------------------
                    if piece.code is 3:
                        moves = []
                        x = 1
                        while True: #same process as the bishop except for the rook
                            if piece.pos[0] + x > 7:
                                break
                            moves.append([piece.pos[0] + x, piece.pos[1]])
                            if board[piece.pos[0] + x][piece.pos[1]].colour is piece.colour * -1 \
                            and board[piece.pos[0] + x][piece.pos[1]].code is not 5 \
                            or board[piece.pos[0] + x][piece.pos[1]].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[1] + x > 7:
                                break
                            moves.append([piece.pos[0], piece.pos[1] + x])
                            if board[piece.pos[0]][piece.pos[1] + x].colour is piece.colour * -1 \
                            and board[piece.pos[0]][piece.pos[1] + x].code is not 5 \
                            or board[piece.pos[0]][piece.pos[1] + x].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[0] - x < 0:
                                break
                            moves.append([piece.pos[0] - x, piece.pos[1]])
                            if board[piece.pos[0] - x][piece.pos[1]].colour is piece.colour * -1 \
                            and board[piece.pos[0] - x][piece.pos[1]].code is not 5 \
                            or board[piece.pos[0] - x][piece.pos[1]].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[1] - x < 0:
                                break
                            moves.append([piece.pos[0], piece.pos[1] - x])
                            if board[piece.pos[0]][piece.pos[1] - x].colour is piece.colour * -1 \
                            and board[piece.pos[0]][piece.pos[1] - x].code is not 5 \
                            or board[piece.pos[0]][piece.pos[1] - x].colour is piece.colour:
                                break
                            x += 1
                        if pos in moves:
                            return True
# ----------------------------------------------------------------------------------------------------------------------
                    if piece.code is 4:
                        moves = []
                        x = 1
                        while True:
                            if piece.pos[0] + x > 7 or piece.pos[1] + x > 7:
                                break
                            moves.append([piece.pos[0] + x, piece.pos[1] + x])
                            if board[piece.pos[0] + x][piece.pos[1] + x].colour is piece.colour * -1 \
                            and board[piece.pos[0] + x][piece.pos[1] + x].code is not 5 \
                            or board[piece.pos[0] + x][piece.pos[1] + x].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[0] - x < 0 or piece.pos[1] - x < 0:
                                break
                            moves.append([piece.pos[0] - x, piece.pos[1] - x])
                            if board[piece.pos[0] - x][piece.pos[1] - x].colour is piece.colour * -1 \
                            and board[piece.pos[0] - x][piece.pos[1] - x].code is not 5 \
                            or board[piece.pos[0] - x][piece.pos[1] - x].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[0] + x > 7 or piece.pos[1] - x < 0:
                                break
                            moves.append([piece.pos[0] + x, piece.pos[1] - x])
                            if board[piece.pos[0] + x][piece.pos[1] - x].colour is piece.colour * -1 \
                            and board[piece.pos[0] + x][piece.pos[1] - x].code is not 5 \
                            or board[piece.pos[0] + x][piece.pos[1] - x].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[0] - x < 0 or piece.pos[1] + x > 7:
                                break
                            moves.append([piece.pos[0] - x, piece.pos[1] + x])
                            if board[piece.pos[0] - x][piece.pos[1] + x].colour is piece.colour * -1 \
                            and board[piece.pos[0] - x][piece.pos[1] + x].code is not 5 \
                            or board[piece.pos[0] - x][piece.pos[1] + x].colour is piece.colour:
                                break
                            x += 1
                        x = 1
#--------------------------------------------------------------------------------------BISHOP TO ROOK
                        while True:
                            if piece.pos[0] + x > 7:
                                break
                            moves.append([piece.pos[0] + x, piece.pos[1]])
                            if board[piece.pos[0] + x][piece.pos[1]].colour is piece.colour * -1 \
                            and board[piece.pos[0] + x][piece.pos[1]].code is not 5 \
                            or board[piece.pos[0] + x][piece.pos[1]].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[1] + x > 7:
                                break
                            moves.append([piece.pos[0], piece.pos[1] + x])
                            if board[piece.pos[0]][piece.pos[1] + x].colour is piece.colour * -1 \
                            and board[piece.pos[0]][piece.pos[1] + x].code is not 5 \
                            or board[piece.pos[0]][piece.pos[1] + x].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[0] - x < 0:
                                break
                            moves.append([piece.pos[0] - x, piece.pos[1]])
                            if board[piece.pos[0] - x][piece.pos[1]].colour is piece.colour * -1 \
                            and board[piece.pos[0] - x][piece.pos[1]].code is not 5 \
                            or board[piece.pos[0] - x][piece.pos[1]].colour is piece.colour:
                                break
                            x += 1
                        x = 1
                        while True:
                            if piece.pos[1] - x < 0:
                                break
                            moves.append([piece.pos[0], piece.pos[1] - x])
                            if board[piece.pos[0]][piece.pos[1] - x].colour is piece.colour * -1 \
                            and board[piece.pos[0]][piece.pos[1] - x].code is not 5 \
                            or board[piece.pos[0]][piece.pos[1] - x].colour is piece.colour:
                                break
                            x += 1
                        if pos in moves:
                            return True
# ----------------------------------------------------------------------------------------------------------------------
                    if piece.code is 5: #generates all legal moves for the enemy king
                        moves = [[piece.pos[0] + 1, piece.pos[1] + 1],
                                 [piece.pos[0] - 1, piece.pos[1] - 1],
                                 [piece.pos[0] + 1, piece.pos[1] - 1],
                                 [piece.pos[0] - 1, piece.pos[1] + 1],
                                 [piece.pos[0] + 1, piece.pos[1] + 0],
                                 [piece.pos[0] - 1, piece.pos[1] + 0],
                                 [piece.pos[0] + 0, piece.pos[1] + 1],
                                 [piece.pos[0] + 0, piece.pos[1] - 1]]
                        moves = [[x, y] for [x, y] in moves if x in Chessboard.valid_nums and y in Chessboard.valid_nums]
                        if pos in moves:
                            return True
        return False


class Queen(Pieces):

    def __init__(self, board, pos, colour):
        super().__init__(board, pos, colour)
        self.code = 4
        self.value = 90
        self.good_positions = [[-2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0],
                               [-1.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -1.0],
                               [-1.0,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -1.0],
                               [-0.5,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -0.5],
                               [ 0.0,  0.0,  0.5,  0.5,  0.5,  0.5,  0.0, -0.5],
                               [-1.0,  0.5,  0.5,  0.5,  0.5,  0.5,  0.0, -1.0],
                               [-1.0,  0.0,  0.5,  0.0,  0.0,  0.0,  0.0, -1.0],
                               [-2.0, -1.0, -1.0, -0.5, -0.5, -1.0, -1.0, -2.0]]

    def get_moves(self): #returns a list of legal moves
        king_pos = self.board.get_king_pos(self.colour)
        moves = []
        x = 1

        while True: #each loop checks to see if the move is on the board, if it is blocked by another piece, or a piece is captured
            if self.pos[0] + x > 7 or self.board.pieces[self.pos[0] + x][self.pos[1]].colour is self.colour:
                break #when one of the above occur, no more moves are generated
            moves.append((self.pos[0] + x, self.pos[1])) #moves are incrementally added until the loop is ended
            if self.board.pieces[self.pos[0] + x][self.pos[1]].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[1] + x > 7 or self.board.pieces[self.pos[0]][self.pos[1] + x].colour is self.colour:
                break
            moves.append((self.pos[0], self.pos[1] + x))
            if self.board.pieces[self.pos[0]][self.pos[1] + x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[0] - x < 0 or self.board.pieces[self.pos[0] - x][self.pos[1]].colour is self.colour:
                break
            moves.append((self.pos[0] - x, self.pos[1]))
            if self.board.pieces[self.pos[0] - x][self.pos[1]].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[1] - x < 0 or self.board.pieces[self.pos[0]][self.pos[1] - x].colour is self.colour:
                break
            moves.append((self.pos[0], self.pos[1] - x))
            if self.board.pieces[self.pos[0]][self.pos[1] - x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
 #---------------------------------------------------------------------------------------------------ROOK TO BISHOP
        while True:
            if self.pos[0] + x > 7 or self.pos[1] + x > 7 \
            or self.board.pieces[self.pos[0] + x][self.pos[1] + x].colour is self.colour:
                break
            moves.append((self.pos[0] + x, self.pos[1] + x))
            if self.board.pieces[self.pos[0] + x][self.pos[1] + x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[0] - x < 0 or self.pos[1] - x < 0 \
            or self.board.pieces[self.pos[0] - x][self.pos[1] - x].colour is self.colour:
                break
            moves.append((self.pos[0] - x, self.pos[1] - x))
            if self.board.pieces[self.pos[0] - x][self.pos[1] - x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[0] + x > 7 or self.pos[1] - x < 0 \
            or self.board.pieces[self.pos[0] + x][self.pos[1] - x].colour is self.colour:
                break
            moves.append((self.pos[0] + x, self.pos[1] - x))
            if self.board.pieces[self.pos[0] + x][self.pos[1] - x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[0] - x < 0 or self.pos[1] + x > 7\
            or self.board.pieces[self.pos[0] - x][self.pos[1] + x].colour is self.colour:
                break
            moves.append((self.pos[0] - x, self.pos[1] + x))
            if self.board.pieces[self.pos[0] - x][self.pos[1] + x].colour not in [None, self.colour]:
                break
            x += 1

        final_moves = []
        for move in moves: #a copy of the 2D list of pieces is made, and each move is made in a copy.
            temp = self.board.temp_move(self.pos, move)
            if not self.board.pieces[king_pos[0]][king_pos[1]].is_check(self.board.pieces, king_pos): #checks king safety
                final_moves.append(move)#after the move. If the move is legal, it is added to final list of moves
            self.board.temp_unmove(temp[0], temp[1], temp[2])
        return final_moves


class Rook(Pieces):

    def __init__(self, board, pos, colour, has_moved):
        super().__init__(board, pos, colour)
        self.code = 3
        self.value = 50
        self.has_moved = has_moved #attribute set to False by default but is changed in Chessbaord.init_king()
        self.good_positions = [[ 0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
                               [ 0.5,  1.0,  1.0,  1.0,  1.0,  1.0,  1.0,  0.5],
                               [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
                               [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
                               [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
                               [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
                               [-0.5,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -0.5],
                               [ 0.0,   0.0, 0.0,  0.5,  0.5,  0.0,  0.0,  0.0]]

    def get_moves(self):
        king_pos = self.board.get_king_pos(self.colour)
        moves = []
        x = 1
        while True:
            if self.pos[0] + x > 7 or self.board.pieces[self.pos[0] + x][self.pos[1]].colour is self.colour:
                break
            moves.append((self.pos[0] + x, self.pos[1]))
            if self.board.pieces[self.pos[0] + x][self.pos[1]].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[1] + x > 7 or self.board.pieces[self.pos[0]][self.pos[1] + x].colour is self.colour:
                break
            moves.append((self.pos[0], self.pos[1] + x))
            if self.board.pieces[self.pos[0]][self.pos[1] + x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[0] - x < 0 or self.board.pieces[self.pos[0] - x][self.pos[1]].colour is self.colour:
                break
            moves.append((self.pos[0] - x, self.pos[1]))
            if self.board.pieces[self.pos[0] - x][self.pos[1]].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[1] - x < 0 or self.board.pieces[self.pos[0]][self.pos[1] - x].colour is self.colour:
                break
            moves.append((self.pos[0], self.pos[1] - x))
            if self.board.pieces[self.pos[0]][self.pos[1] - x].colour not in [None, self.colour]:
                break
            x += 1

        final_moves = []
        for move in moves: #a copy of the 2D list of pieces is made, and each move is made in a copy.
            temp = self.board.temp_move(self.pos, move)
            if not self.board.pieces[king_pos[0]][king_pos[1]].is_check(self.board.pieces, king_pos): #checks king safety
                final_moves.append(move)#after the move. If the move is legal, it is added to final list of moves
            self.board.temp_unmove(temp[0], temp[1], temp[2])
        return final_moves


class Bishop(Pieces):

    def __init__(self, board, pos, colour):
        super().__init__(board, pos, colour)
        self.code = 2
        self.value = 32.5
        self.good_positions = [[-2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0],
                               [-1.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0, -1.0],
                               [-1.0,  0.0,  0.5,  1.0,  1.0,  0.5,  0.0, -1.0],
                               [-1.0,  0.5,  0.5,  1.0,  1.0,  0.5,  0.5, -1.0],
                               [-1.0,  0.0,  1.0,  1.0,  1.0,  1.0,  0.0, -1.0],
                               [-1.0,  1.0,  1.0,  1.0,  1.0,  1.0,  1.0, -1.0],
                               [-1.0,  0.5,  0.0,  0.0,  0.0,  0.0,  0.5, -1.0],
                               [-2.0, -1.0, -1.0, -1.0, -1.0, -1.0, -1.0, -2.0]]

    def get_moves(self):
        king_pos = self.board.get_king_pos(self.colour)
        moves = []
        x = 1
        while True:
            if self.pos[0] + x > 7 or self.pos[1] + x > 7 \
            or self.board.pieces[self.pos[0] + x][self.pos[1] + x].colour is self.colour:
                break
            moves.append((self.pos[0] + x, self.pos[1] + x))
            if self.board.pieces[self.pos[0] + x][self.pos[1] + x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[0] - x < 0 or self.pos[1] - x < 0 \
            or self.board.pieces[self.pos[0] - x][self.pos[1] - x].colour is self.colour:
                break
            moves.append((self.pos[0] - x, self.pos[1] - x))
            if self.board.pieces[self.pos[0] - x][self.pos[1] - x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[0] + x > 7 or self.pos[1] - x < 0 \
            or self.board.pieces[self.pos[0] + x][self.pos[1] - x].colour is self.colour:
                break
            moves.append((self.pos[0] + x, self.pos[1] - x))
            if self.board.pieces[self.pos[0] + x][self.pos[1] - x].colour not in [None, self.colour]:
                break
            x += 1
        x = 1
        while True:
            if self.pos[0] - x < 0 or self.pos[1] + x > 7 \
            or self.board.pieces[self.pos[0] - x][self.pos[1] + x].colour is self.colour:
                break
            moves.append((self.pos[0] - x, self.pos[1] + x))
            if self.board.pieces[self.pos[0] - x][self.pos[1] + x].colour not in [None, self.colour]:
                break
            x += 1

        final_moves = []
        for move in moves: #a copy of the 2D list of pieces is made, and each move is made in a copy.
            temp = self.board.temp_move(self.pos, move)
            if not self.board.pieces[king_pos[0]][king_pos[1]].is_check(self.board.pieces, king_pos): #checks king safety
                final_moves.append(move)#after the move. If the move is legal, it is added to final list of moves
            self.board.temp_unmove(temp[0], temp[1], temp[2])
        return final_moves


class Knight(Pieces):

    def __init__(self, board, pos, colour):
        super().__init__(board, pos, colour)
        self.code = 1
        self.value = 30
        self.good_positions = [[-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0],
                               [-4.0, -2.0,  0.0,  0.0,  0.0,  0.0, -2.0, -4.0],
                               [-3.0,  0.0,  1.0,  1.5,  1.5,  1.0,  0.0, -3.0],
                               [-3.0,  0.5,  1.5,  2.0,  2.0,  1.5,  0.5, -3.0],
                               [-3.0,  0.0,  1.5,  2.0,  2.0,  1.5,  0.0, -3.0],
                               [-3.0,  0.5,  1.0,  1.5,  1.5,  1.0,  0.5, -3.0],
                               [-4.0, -2.0,  0.0,  0.5,  0.5,  0.0, -2.0, -4.0],
                               [-5.0, -4.0, -3.0, -3.0, -3.0, -3.0, -4.0, -5.0]]

    def get_moves(self):
        king_pos = self.board.get_king_pos(self.colour)
        moves = [(self.pos[0] - 2, self.pos[1] + 1),
                 (self.pos[0] - 2, self.pos[1] - 1),
                 (self.pos[0] - 1, self.pos[1] + 2),
                 (self.pos[0] - 1, self.pos[1] - 2),
                 (self.pos[0] + 2, self.pos[1] + 1),
                 (self.pos[0] + 2, self.pos[1] - 1),
                 (self.pos[0] + 1, self.pos[1] + 2),
                 (self.pos[0] + 1, self.pos[1] - 2)]

        moves = [(x, y) for (x, y) in moves if x in Chessboard.valid_nums and y in Chessboard.valid_nums \
                 and self.board.pieces[x][y].colour is not self.colour]

        final_moves = []
        for move in moves: #a copy of the 2D list of pieces is made, and each move is made in a copy.
            temp = self.board.temp_move(self.pos, move)
            if not self.board.pieces[king_pos[0]][king_pos[1]].is_check(self.board.pieces, king_pos): #checks king safety
                final_moves.append(move)#after the move. If the move is legal, it is added to final list of moves
            self.board.temp_unmove(temp[0], temp[1], temp[2])
        return final_moves


class Pawn(Pieces):

    def __init__(self, board, pos, colour):
        super().__init__(board, pos, colour)
        self.code = 0
        self.value = 10
        self.passed = False #attribute is changed to True for one turn after making a 2 space move (for en passant)
        self.passant = False #attribute is changed to True for one turn if taking en passant.
        self.good_positions = [[0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0],
                               [5.0,  5.0,  5.0,  5.0,  5.0,  5.0,  5.0,  5.0],
                               [1.0,  1.0,  2.0,  3.0,  3.0,  2.0,  1.0,  1.0],
                               [0.5,  0.5,  1.0,  2.5,  2.5,  1.0,  0.5,  0.5],
                               [0.0,  0.0,  0.0,  2.0,  2.0,  0.0,  0.0,  0.0],
                               [0.5, -0.5, -1.0,  0.0,  0.0, -1.0, -0.5,  0.5],
                               [0.5,  1.0, 1.0,  -2.0, -2.0,  1.0,  1.0,  0.5],
                               [0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0,  0.0]]

    def get_moves(self):
        king_pos = self.board.get_king_pos(self.colour)
        moves = []
        if flip: #flip is a variable that determines whether the board will be flipped after every turn...
        #if flip is enabled, white and black move generation is the same.
            if self.pos[0] > 0: #if the piece can still move up...
                if self.board.pieces[self.pos[0] - 1][self.pos[1]].colour is None: #and there is an empty space above it...
                    moves.append((self.pos[0] - 1, self.pos[1]))#it is added to the list of moves
                    if self.pos[0] is 6 and self.board.pieces[self.pos[0] - 2][self.pos[1]].colour is None: #if it is on the starting rank...
                        moves.append((self.pos[0] - 2, self.pos[1])) #and the spot 2 spaces above is empty, that move is also added

                if self.pos[1] > 0 and self.board.pieces[self.pos[0] - 1][self.pos[1] - 1].colour is None \
                        and self.board.pieces[self.pos[0]][self.pos[1] - 1].code is 0 \
                        and self.board.pieces[self.pos[0]][self.pos[1] - 1].passed: #en passant move generation
                    moves.append((self.pos[0] - 1, self.pos[1] - 1))
                    self.passant = True

                if self.pos[1] < 7 and self.board.pieces[self.pos[0] - 1][self.pos[1] + 1].colour is None \
                        and self.board.pieces[self.pos[0]][self.pos[1] + 1].code is 0 \
                        and self.board.pieces[self.pos[0]][self.pos[1] + 1].passed: #en passant for other side
                    moves.append((self.pos[0] - 1, self.pos[1] + 1))
                    self.passant = True

                if self.pos[1] > 0 and self.board.pieces[self.pos[0] - 1][self.pos[1] - 1].colour is self.colour * -1:
                    moves.append((self.pos[0] - 1, self.pos[1] - 1)) #diagonally capturing
                if self.pos[1] < 7 and self.board.pieces[self.pos[0] - 1][self.pos[1] + 1].colour is self.colour * -1:
                    moves.append((self.pos[0] - 1, self.pos[1] + 1)) #diagonally capturing for other side

            final_moves = []
            for move in moves:  # a copy of the 2D list of pieces is made, and each move is made in a copy.
                temp = self.board.temp_move(self.pos, move)
                if not self.board.pieces[king_pos[0]][king_pos[1]].is_check(self.board.pieces,
                                                                            king_pos):  # checks king safety
                    final_moves.append(move)  # after the move. If the move is legal, it is added to final list of moves
                self.board.temp_unmove(temp[0], temp[1], temp[2])
            return final_moves

        else:
            if self.colour is 1:
                if self.pos[0] > 0:
                    if self.board.pieces[self.pos[0] - 1][self.pos[1]].colour is None:
                        moves.append((self.pos[0] - 1, self.pos[1])) #moving up one space
                        if self.pos[0] is 6 and self.board.pieces[self.pos[0] - 2][self.pos[1]].colour is None:
                            moves.append((self.pos[0] - 2, self.pos[1])) #moving up 2 spaces

                    if self.pos[1] > 0 and self.board.pieces[self.pos[0] - 1][self.pos[1] - 1].colour is None \
                    and self.board.pieces[self.pos[0]][self.pos[1] - 1].code is 0 \
                    and self.board.pieces[self.pos[0]][self.pos[1] - 1].passed:
                        moves.append((self.pos[0] - 1, self.pos[1] - 1)) #en passant
                        self.passant = True

                    if self.pos[1] < 7 and self.board.pieces[self.pos[0] - 1][self.pos[1] + 1].colour is None \
                    and self.board.pieces[self.pos[0]][self.pos[1] + 1].code is 0 \
                    and self.board.pieces[self.pos[0]][self.pos[1] + 1].passed:
                        moves.append((self.pos[0] - 1, self.pos[1] + 1)) #en passant in other direction
                        self.passant = True

                    if self.pos[1] > 0 and self.board.pieces[self.pos[0] - 1][self.pos[1] - 1].colour not in [None, self.colour]:
                        moves.append((self.pos[0] - 1, self.pos[1] - 1)) #capturing move
                    if self.pos[1] < 7 and self.board.pieces[self.pos[0] - 1][self.pos[1] + 1].colour not in [None, self.colour]:

                        moves.append((self.pos[0] - 1, self.pos[1] + 1)) #capturing move for other direction
                final_moves = []
                for move in moves:  # a copy of the 2D list of pieces is made, and each move is made in a copy.
                    temp = self.board.temp_move(self.pos, move)
                    if not self.board.pieces[king_pos[0]][king_pos[1]].is_check(self.board.pieces,
                                                                                king_pos):  # checks king safety
                        final_moves.append(
                            move)  # after the move. If the move is legal, it is added to final list of moves
                    self.board.temp_unmove(temp[0], temp[1], temp[2])
                return final_moves

            elif self.colour is -1:
                if self.pos[0] < 7:
                    if self.board.pieces[self.pos[0] + 1][self.pos[1]].colour is None:
                        moves.append((self.pos[0] + 1, self.pos[1])) #one space
                        if self.pos[0] is 1 and self.board.pieces[self.pos[0] + 2][self.pos[1]].colour is None:
                            moves.append((self.pos[0] + 2, self.pos[1])) #2 spaces

                    if self.pos[1] > 0 and self.board.pieces[self.pos[0] + 1][self.pos[1] - 1].colour is None \
                    and self.board.pieces[self.pos[0]][self.pos[1] - 1].code is 0 \
                    and self.board.pieces[self.pos[0]][self.pos[1] - 1].passed:
                        moves.append((self.pos[0] + 1, self.pos[1] - 1)) #en passant
                        self.passant = True

                    if self.pos[1] < 7 and self.board.pieces[self.pos[0] + 1][self.pos[1] + 1].colour is None \
                    and self.board.pieces[self.pos[0]][self.pos[1] + 1].code is 0 \
                    and self.board.pieces[self.pos[0]][self.pos[1] + 1].passed:
                        moves.append((self.pos[0] + 1, self.pos[1] + 1)) #en passant
                        self.passant = True

                    if self.pos[1] > 0 and self.board.pieces[self.pos[0] + 1][self.pos[1] - 1].colour not in [None, self.colour]:
                        moves.append((self.pos[0] + 1, self.pos[1] - 1)) #capturing
                    if self.pos[1] < 7 and self.board.pieces[self.pos[0] + 1][self.pos[1] + 1].colour not in [None, self.colour]:
                        moves.append((self.pos[0] + 1, self.pos[1] + 1)) #capturing

                final_moves = []
                for move in moves: #a copy of the 2D list of pieces is made, and each move is made in a copy.
                    temp = self.board.temp_move(self.pos, move)
                    if not self.board.pieces[king_pos[0]][king_pos[1]].is_check(self.board.pieces, king_pos): #checks king safety
                        final_moves.append(move)#after the move. If the move is legal, it is added to final list of moves
                    self.board.temp_unmove(temp[0], temp[1], temp[2])
                return final_moves

    def promote(self): #this function promotes a pawn. Only runs when a pawn reaches the edge of the board
        print ('What piece would you like to promote to?')
        while True: #currently blocks the game, will be replaced with a Tkinter dialogue box
            code = int(input()) #the loop waits for the user to input a valid piece to promote to
            if code in [1, 2, 3, 4]:
                break
        if code == 1: #depending on the promotion, a piece is created and replaces the pawn
            self.board.pieces[self.pos[0]][self.pos[1]] = Knight(self.board, self.pos, self.colour)
        if code == 2:
            self.board.pieces[self.pos[0]][self.pos[1]] = Bishop(self.board, self.pos, self.colour)
        if code == 3:
            self.board.pieces[self.pos[0]][self.pos[1]] = Rook(self.board, self.pos, self.colour, True)
        if code == 4:
            self.board.pieces[self.pos[0]][self.pos[1]] = Queen(self.board, self.pos, self.colour)


class Empty(Pieces):

    def __init__(self, board, pos, colour):
        super().__init__(board, pos, colour)
        self.code = None
        self.value = 0


class Game: #This class handles all the game logic

    def __init__(self, mode):
        self.mode = mode #the Chessboard object.
        self.positions = [] #used to keep track of played positions for 3-fold repetition
        self.positions.append(self.mode.write_FEN())
        with open('preferences.txt', 'r') as read_file:
            self.board_theme = read_file.readline().replace('\n', '')
            self.piece_theme = read_file.readline().replace('\n', '')
            self.transparency = int(read_file.readline())
            self.white_time = int(read_file.readline()) #time remaining for each side
            self.black_time = int(read_file.readline())
            self.white_increment = int(read_file.readline()) #the amount of bonus time per turn
            self.black_increment = int(read_file.readline())
            self.AI_turn = int(read_file.readline())
            if self.white_time is 0 or self.black_time is 0:
                self.with_timer = False
                self.time_passed = 0
            else:
                self.with_timer = True

        self.white_images = []
        self.black_images = []
        for i in range(6):
            file_name = 'images/pieces' + self.piece_theme + '/' + 'w' + str(i) + '.png'
            img = pygame.image.load(file_name)
            self.white_images.append(pygame.transform.scale(img, (100, 100)))
            file_name = file_name.replace('w', 'b')
            img = pygame.image.load(file_name)
            self.black_images.append(pygame.transform.scale(img, (100, 100)))
        self.board_image = pygame.image.load('images/boards/board' + self.board_theme + '.png')
        self.highlight = pygame.Surface((113, 113), pygame.SRCALPHA)  # semi-transparent surface is drawn over the board...
        self.highlight.fill((255, 255, 255, self.transparency))  # to show the locations where the selected piece can move

    def main(self):
        self.selected = None #what piece is currently selected
        self.done = False
        clock = pygame.time.Clock()
        self.repetition_count = 0 #counts repeated moves (for 3-fold repetition)
        self.start_time = int(time.monotonic()) #time at start of loop; used to keep track of how much time has passed
        self.game_end = True #used to keep track of how the game was ended. True is a regular exit (win/loss/quit)
        while not self.done:
            self.click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.click = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_0:
                        self.game_end = False
                        self.done = True

            (self.mx, self.my) = pygame.mouse.get_pos()
            self.mb = pygame.mouse.get_pressed()

            # for rank in self.mode.pieces:
            #     for piece in rank:
            #         print (piece.__dict__)
            # print ('\n\n')

            self.selected = self.select()
            self.draw()

            if self.with_timer:
                self.deduct_time(self.mode.turn)

            if self.is_draw(self.mode.turn):
                print ('The game is a draw!')
                time.sleep(2)
                self.done = True
            if self.is_win(self.mode.turn):
                if self.mode.turn is 1:
                    colour = 'BLACK'
                else:
                    colour = 'WHITE'
                print ('The game is won by {}!'.format(colour))
                time.sleep(2)
                self.done = True

            clock.tick(60)

    def change_turn(self): #handles changing the turn
        if flip: #if flip is enabled, then the board is flipped
            Chessboard.flip(self.mode)
        if self.mode.turn is 1: #deducts time
            self.white_time = self.white_time - self.time_passed
        elif self.mode.turn is -1:
            self.black_time = self.black_time - self.time_passed
        self.start_time = int(time.monotonic()) #time passed is reset
        self.add_time(self.mode.turn)
        self.positions.append(self.mode.write_FEN())
        self.mode.turn *= -1 #change turn

    def deduct_time(self, turn):
        self.time_passed = int(time.monotonic()) - self.start_time  # current time - start time = time passed
        if turn is 1:
            timer = self.white_time
            colour = 'WHITE'
        else:
            timer = self.black_time
            colour = 'BLACK'

        minutes = (timer - self.time_passed) // 60
        seconds = (timer - self.time_passed) % 60
        if self.done:
            if self.mode.turn is 1:  # deducts time
                self.white_time = self.white_time - self.time_passed
            elif self.mode.turn is -1:
                self.black_time = self.black_time - self.time_passed
        print ('{} has {}:{:02d} remaining'.format(colour, minutes, seconds))
        if (minutes, seconds) == (0, 0):  # if white has no time left, black wins
            if colour is 'WHITE':
                colour = 'BLACK'
            else:
                colour = 'WHITE'
            print ('The game is won by {}!'.format(colour))
            time.sleep(2)
            self.done = True

    def add_time(self, turn):
        if turn is 1:
            self.white_time += self.white_increment
        else:
            self.black_time += self.black_increment

    @staticmethod #when self is None, king_pos and board are always passed. // checks for stalemate
    def is_stalemate(colour, self = None, king_pos = None, board = None): #if king_pos and board are not supplied...
        if king_pos is None: #they are retrieved through Chessboard (self.mode) methods...
            king_pos = self.mode.get_king_pos(colour) #if this function is called through the Chessboard class...
        if board is None: #there is no need for the self.mode (Chessboard) methods as that information...
            board = self.mode.pieces #is already and is passed into args
        if board[king_pos[0]][king_pos[1]].is_check(board, king_pos) is False:
            for rank in board: # if the king is not in check
                for piece in rank:
                    if piece.colour is colour and piece.get_moves() != []: #and there are no legal moves available
                        return False
            return True

    @staticmethod
    def is_checkmate(colour, self = None, king_pos = None, board = None): #checks for checkmate (no pun intended)
        if king_pos is None:
            king_pos = self.mode.get_king_pos(colour)
        if board is None:
            board = self.mode.pieces
        if board[king_pos[0]][king_pos[1]].is_check(board, king_pos) is True:
            for rank in board: #if the king is in check
                for piece in rank:
                    if piece.colour is colour and piece.get_moves() != []: #and there are no legal moves available
                        return False
            return True
        return False

    def is_win(self, colour):
        if self.is_checkmate(colour, self):
            return True
        return False

    def is_draw(self, colour):
        if self.is_stalemate(colour, self):
            return True
        if self.check_repetition():
            return True
        return False

    def check_repetition(self):
        if self.mode.write_FEN() in self.positions:
            count = self.positions.count(self.mode.write_FEN())
            if count >= 3:
                return True
        return False

    def move(self, index, move):
        piece = self.mode.pieces[index[0]][index[1]]
        if move in piece.get_moves():
            if piece.code is 0 and piece.passant:
                if flip:
                    self.mode.pieces[move[0] + 1][move[1]] = Empty(self.mode,
                                                                   self.mode.pieces[move[0] + 1][move[1]].pos, None)
                else:
                    if piece.colour is 1:
                        self.mode.pieces[move[0] + 1][move[1]] = Empty(self.mode,
                                                                       self.mode.pieces[move[0] + 1][move[1]].pos, None)
                    if piece.colour is -1:
                        self.mode.pieces[move[0] - 1][move[1]] = Empty(self.mode,
                                                                       self.mode.pieces[move[0] - 1][move[1]].pos, None)

            # ---------------------------------------------------------------------------------------------------------------------------------
            if self.mode.pieces[move[0]][move[1]].colour is not None:
                self.mode.pieces[move[0]][move[1]] = Empty(self.mode, self.mode.pieces[move[0]][move[1]].pos, None)

            self.mode.pieces[piece.pos[0]][piece.pos[1]], self.mode.pieces[move[0]][move[1]] = \
                self.mode.pieces[move[0]][move[1]], self.mode.pieces[piece.pos[0]][piece.pos[1]]

            self.mode.pieces[piece.pos[0]][piece.pos[1]].pos, self.mode.pieces[move[0]][move[1]].pos = \
                self.mode.pieces[move[0]][move[1]].pos, self.mode.pieces[piece.pos[0]][piece.pos[1]].pos

            self.change_turn()
            # ---------------------------------------------------------------------------------------------------------------------------------
            for rank in self.mode.pieces:
                for obj in rank:
                    if obj.code is 0:
                        obj.passed = False
                        obj.passant = False
            if piece.code is 0:
                if abs(index[0] - move[0]) is 2:
                    piece.passed = True
                elif piece.pos[0] in [0, 7]:
                    piece.promote()

            if piece.code is 5:
                if piece.colour is 1:
                    x = 7
                else:
                    x = 0
                if flip:
                    x = 7
                    Chessboard.flip(self.mode)

                if flip and piece.colour is -1:
                    if index[1] - move[1] is -2:
                        self.mode.pieces[x][7].pos, self.mode.pieces[x][4].pos = \
                            self.mode.pieces[x][4].pos, self.mode.pieces[x][7].pos
                        self.mode.pieces[x][7], self.mode.pieces[x][4] = self.mode.pieces[x][4], \
                                                                         self.mode.pieces[x][7]
                    elif index[1] - move[1] is 2:
                        self.mode.pieces[x][0].pos, self.mode.pieces[x][2].pos = \
                            self.mode.pieces[x][2].pos, self.mode.pieces[x][0].pos
                        self.mode.pieces[x][0], self.mode.pieces[x][2] = self.mode.pieces[x][2], \
                                                                         self.mode.pieces[x][0]
                else:
                    if index[1] - move[1] is -2:
                        self.mode.pieces[x][7].pos, self.mode.pieces[x][5].pos = \
                            self.mode.pieces[x][5].pos, self.mode.pieces[x][7].pos
                        self.mode.pieces[x][7], self.mode.pieces[x][5] = self.mode.pieces[x][5], \
                                                                         self.mode.pieces[x][7]
                    elif index[1] - move[1] is 2:
                        self.mode.pieces[x][0].pos, self.mode.pieces[x][3].pos = \
                            self.mode.pieces[x][3].pos, self.mode.pieces[x][0].pos
                        self.mode.pieces[x][0], self.mode.pieces[x][3] = self.mode.pieces[x][3], \
                                                                         self.mode.pieces[x][0]
                if flip:
                    Chessboard.flip(self.mode)

            if piece.code is 3 and piece.has_moved is False:
                piece.has_moved = True
            if piece.code is 5 and piece.has_moved is False:
                piece.has_moved = True

    def select(self): #this function handles selction of pieces (and selection of moves)
        for rank in Chessboard.grid:
            for rect in rank:
                if rect.collidepoint(self.mx, self.my) and self.click:
                    x = Chessboard.grid.index(rank)
                    y = rank.index(rect)
                    if self.selected is not None: #if a piece is already selected...
                        self.move((self.selected[0], self.selected[1]), (x, y)) #try to move the piece to the selected location
                        self.selected = None #deselect pieces
                    else:
                        if self.mode.pieces[x][y].colour is self.mode.turn: #can only select the colour corresponding to the turn
                            return x, y
                        else:
                            return None
        return self.selected

    def draw(self):#this function draws the board image, pieces based off the 2D list (attribute of Chessboard object)...
        x, y = 0, 0 #and highlights potential moves and the selected piece
        screen.blit(self.board_image, (x, y))
        x += 6.25
        y += 6.25
        if self.selected is not None:
            screen.blit(self.highlight, (round(self.selected[1]*112.5), round(self.selected[0]*112.5)))
            moves = self.mode.pieces[self.selected[0]][self.selected[1]].get_moves()
            for move in moves:
                screen.blit(self.highlight, (round(move[1]*112.5), round(move[0]*112.5)))
        for rank in self.mode.pieces:
            for piece in rank:
                if piece.colour is 1:
                    screen.blit(self.white_images[piece.code], (x, y))
                elif piece.colour is -1:
                    screen.blit(self.black_images[piece.code], (x, y))
                x += 112.5
            x = 6.25
            y += 112.5
        pygame.display.flip()


class Standard(Game):
    pass


class KOTH(Game): #KOTH is a version of chess in which stalemate and getting the king to one of the 4 central squares is a win

    def is_draw(self, colour):
        pass

    def is_win(self, colour):
        if self.is_stalemate(self.mode.turn, self):
            return True
        if self.is_checkmate(self.mode.turn, self):
            return True

        king_pos = self.mode.get_king_pos(self.mode.turn * -1)
        if king_pos in [[3, 3], [3, 4], [4, 3], [4, 4]]:
            return True


class AI(Game):

    def main(self):
        self.selected = None  # what piece is currently selected
        self.done = False
        clock = pygame.time.Clock()
        self.repetition_count = 0  # counts repeated moves (for 3-fold repetition)
        self.start_time = int(time.monotonic())  # time at start of loop; used to keep track of how much time has passed
        self.game_end = True #tracks how the game is ended. True is a regular exit (win/loss/quit)
        while not self.done:
            self.click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.click = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_0:
                        self.game_end = False
                        self.done = True

            (self.mx, self.my) = pygame.mouse.get_pos()
            self.mb = pygame.mouse.get_pressed()

            # for rank in self.mode.pieces:
            #     for piece in rank:
            #         print (piece.__dict__)
            # print ('\n\n')

            if self.with_timer:
                self.deduct_time(self.mode.turn)

            if self.AI_turn is self.mode.turn:
                self.make_move(self.mode.turn)
            else:
                self.selected = self.select()
            self.draw()

            if self.is_draw(self.mode.turn):
                print ('The game is a draw!')
                time.sleep(2)
                self.done = True
            if self.is_win(self.mode.turn):
                if self.mode.turn is 1:
                    colour = 'BLACK'
                else:
                    colour = 'WHITE'
                print ('The game is won by {}!'.format(colour))
                time.sleep(2)
                self.done = True

            clock.tick(60)


class Random_AI(AI):

    def make_move(self, colour):
        move = self.generate_moves(colour)
        self.move(move[0], move[1])

    def generate_moves(self, colour):
        possible_moves = {}
        for rank in self.mode.pieces:
            for piece in rank:
                if piece.colour is colour:
                    moves = piece.get_moves()
                    if len(moves) is not 0:
                        possible_moves[piece.pos] = moves
        key = random.choice(list(possible_moves.keys()))
        return key, possible_moves[key].pop()


class Minimax(AI):

    def make_move(self, colour):
        move = self.minimax_root(3, colour, self.mode.pieces, True)
        self.move(move[0], move[1])
        # print ('move made')

    def minimax_root(self, depth, colour, board, is_maximizing):
        possible_moves = {}
        for rank in board:
            for piece in rank:
                if piece.colour is colour:
                    moves = piece.get_moves()
                    if len(moves) is not 0:
                        possible_moves[piece.pos] = moves
        best_value = -9999
        best_move = None
        best_piece = None
        pieces = possible_moves.keys()
        for piece in pieces:
            moves = possible_moves[piece]
            for move in moves:
                # print (depth, piece, move)
                temp = self.mode.temp_move(piece, move)
                value = max(best_value, self.minimax(depth - 1, colour*-1, self.mode.pieces, -10000, 10000, not is_maximizing))
                self.mode.temp_unmove(temp[0], temp[1], temp[2])
                if value > best_value:
                    best_value = value
                    best_piece = piece
                    best_move = move

        return best_piece, best_move

    def minimax(self, depth, colour, board, alpha, beta, is_maximizing):
        if depth == 0: #negative eval for odd depth
            return -Chessboard.evaluate(board, colour)
        possible_moves = {}
        for rank in board:
            for piece in rank:
                if piece.colour is colour:
                    moves = piece.get_moves()
                    if len(moves) is not 0:
                        possible_moves[piece.pos] = moves
        pieces = possible_moves.keys()

        if is_maximizing:
            best_value = -9999
            for piece in pieces:
                moves = possible_moves[piece]
                for move in moves:
                    # print (depth, piece, move)
                    temp = self.mode.temp_move(piece, move)
                    best_value = max(best_value, self.minimax(depth - 1, colour * -1, self.mode.pieces, alpha, beta, not is_maximizing))
                    self.mode.temp_unmove(temp[0], temp[1], temp[2])
                    alpha = max(alpha, best_value)
                    if beta <= alpha:
                        return best_value
            return best_value

        elif not is_maximizing:
            best_value = 9999
            for piece in pieces:
                moves = possible_moves[piece]
                for move in moves:
                    # print (depth, piece, move)
                    temp = self.mode.temp_move(piece, move)
                    best_value = min(best_value, self.minimax(depth - 1, colour * -1, self.mode.pieces, alpha, beta, not is_maximizing))
                    self.mode.temp_unmove(temp[0], temp[1], temp[2])
                    beta = min(beta, best_value)
                    if beta <= alpha:
                        return best_value
            return best_value


class Socket:

    def __init__(self, socket, colour):
        self.socket = socket
        self.colour = colour
        self.selected = None


class Server(Game):

    IP = '192.168.1.9' #IP of the local machine that clients will connect to and server will be bound to
    PORT = 1234 #port of local machine
    HEADERSIZE = 10 #buffer for data // see self.recv_msg()

    def __init__(self, mode):
        super().__init__(mode)
        print ('initializing server socket')
        self.server = s.socket(s.AF_INET, s.SOCK_STREAM) #creating socket
        self.server = Socket(self.server, 0)
        self.server.socket.setsockopt(s.SOL_SOCKET, s.SO_REUSEADDR, 1) #configuring socket
        self.server.socket.bind((Server.IP, Server.PORT)) #binding the server to a specific IP and PORT
        self.server.socket.listen(5) #how many connections can be handled (backlogged) at once
        self.connections = [self.server] #List of connections on local machine. 1 server and 2 clients
        print ('server socket intialized')
        while len(self.connections) < 3: #2 players required to play
            self.accept_connection()
        for socket in self.connections:
            socket.selected = None

    def main(self):
        while True:
            client = self.get_client(self.mode.turn)
            msg = self.recv_msg(self.mode.turn) #BLOCKING

            if msg is None:
                self.connections.remove(client)
                self.accept_connection(self.mode.turn)

            else:
                self.mx, self.my = pickle.loads(msg['data'])
                self.handler()

    def handler(self):
        client = self.get_client(self.mode.turn)
        highlight = []
        for rank in Chessboard.grid:
            for rect in rank:
                if rect.collidepoint(self.mx, self.my):
                    x = Chessboard.grid.index(rank)
                    y = rank.index(rect)
                    if client.selected is not None:
                        self.move(client.selected, (x, y))
                        client.selected = None
                        highlight = []
                    else:
                        if self.mode.pieces[x][y].colour is client.colour:
                            client.selected = (x, y)
                            highlight = self.mode.pieces[x][y].get_moves()
                            highlight.append((x, y))
                        else:
                            client.selected = None
                            highlight = []
                    break
        self.send_msg(pickle.dumps(highlight), client.colour)

    def recv_msg(self, colour):
        print ('receiving message from client (colour: {})'.format(colour))
        client = self.get_client(colour)

        try:
            msg_header = client.socket.recv(Server.HEADERSIZE) #BLOCKING
            if not len(msg_header):
                return None
            msg_len = int(msg_header.decode())
            print ('message from client (colour: {}) received'.format(client.colour))
            return {'header': msg_header, 'data': client.socket.recv(msg_len)} #BLOCKING

        except:
            print ('failed to recieve message from client (colour: {})'.format(client.colour))
            return None

    def send_msg(self, msg, colour):
        print ('sending message to client (colour: {})'.format(colour))
        client = self.get_client(colour)

        try:
            msg_header = ('{:<{}}'.format(len(msg), Server.HEADERSIZE)).encode()
            # msg_header = f'{len(msg):<{Server.HEADERSIZE}}'.encode()
            msg = msg_header + msg
            client.socket.send(msg)
            print ('message sent to client (colour: {})'.format(client.colour))
        except:
            print ('failed to send message to client (colour : {})'.format(client.colour))
            return None

    def accept_connection(self, colour = None):
        print ('accepting connection from client')
        client_socket = None
        if len(self.connections) < 3: #no more than 3 connections allowed (one with server, 2 with clients)
            client_socket, client_address = self.server.socket.accept() #allows client to connect to server
            print ('connection from client accepted')
        if not colour:
            if len(self.connections) %2 == 0: #second person to join is Black
                colour = -1
            else:
                colour = 1 #first player to join is White
        client = Socket(client_socket, colour)
        self.connections.append(client) #client's socket added to the list of connections
        print ('client socket (colour: {}) has been added to list of connections'.format(client.colour))
        print('There are now {} connection(s)'.format(len(self.connections)))
        if client.colour is -1:
            Chessboard.flip(self.mode)
        self.send_msg(pickle.dumps(self.mode.pieces), client.colour)
        if client.colour is -1:
            Chessboard.flip(self.mode)

    def get_client(self, colour):
        for socket in self.connections:
            if socket.colour is colour:
                return socket

    def move(self, index, move):
        piece = self.mode.pieces[index[0]][index[1]]
        if move in piece.get_moves():
            if piece.code is 0 and piece.passant:
                if flip:
                    self.mode.pieces[move[0] + 1][move[1]] = Empty(self.mode,
                                                                   self.mode.pieces[move[0] + 1][move[1]].pos, None)
                else:
                    if piece.colour is 1:
                        self.mode.pieces[move[0] + 1][move[1]] = Empty(self.mode,
                                                                       self.mode.pieces[move[0] + 1][move[1]].pos, None)
                    if piece.colour is -1:
                        self.mode.pieces[move[0] - 1][move[1]] = Empty(self.mode,
                                                                       self.mode.pieces[move[0] - 1][move[1]].pos, None)

            # ---------------------------------------------------------------------------------------------------------------------------------
            if self.mode.pieces[move[0]][move[1]].colour is not None:
                self.mode.pieces[move[0]][move[1]] = Empty(self.mode, self.mode.pieces[move[0]][move[1]].pos, None)

            self.mode.pieces[piece.pos[0]][piece.pos[1]], self.mode.pieces[move[0]][move[1]] = \
                self.mode.pieces[move[0]][move[1]], self.mode.pieces[piece.pos[0]][piece.pos[1]]

            self.mode.pieces[piece.pos[0]][piece.pos[1]].pos, self.mode.pieces[move[0]][move[1]].pos = \
                self.mode.pieces[move[0]][move[1]].pos, self.mode.pieces[piece.pos[0]][piece.pos[1]].pos

            self.change_turn()
            # ---------------------------------------------------------------------------------------------------------------------------------
            for rank in self.mode.pieces:
                for obj in rank:
                    if obj.code is 0:
                        obj.passed = False
                        obj.passant = False
            if piece.code is 0:
                if abs(index[0] - move[0]) is 2:
                    piece.passed = True
                elif piece.pos[0] in [0, 7]:
                    piece.promote()

            if piece.code is 5:
                if piece.colour is 1:
                    x = 7
                else:
                    x = 0
                if flip:
                    x = 7
                    Chessboard.flip(self.mode)

                if flip and piece.colour is -1:
                    if index[1] - move[1] is -2:
                        self.mode.pieces[x][7].pos, self.mode.pieces[x][4].pos = \
                            self.mode.pieces[x][4].pos, self.mode.pieces[x][7].pos
                        self.mode.pieces[x][7], self.mode.pieces[x][4] = self.mode.pieces[x][4], \
                                                                         self.mode.pieces[x][7]
                    elif index[1] - move[1] is 2:
                        self.mode.pieces[x][0].pos, self.mode.pieces[x][2].pos = \
                            self.mode.pieces[x][2].pos, self.mode.pieces[x][0].pos
                        self.mode.pieces[x][0], self.mode.pieces[x][2] = self.mode.pieces[x][2], \
                                                                         self.mode.pieces[x][0]
                else:
                    if index[1] - move[1] is -2:
                        self.mode.pieces[x][7].pos, self.mode.pieces[x][5].pos = \
                            self.mode.pieces[x][5].pos, self.mode.pieces[x][7].pos
                        self.mode.pieces[x][7], self.mode.pieces[x][5] = self.mode.pieces[x][5], \
                                                                         self.mode.pieces[x][7]
                    elif index[1] - move[1] is 2:
                        self.mode.pieces[x][0].pos, self.mode.pieces[x][3].pos = \
                            self.mode.pieces[x][3].pos, self.mode.pieces[x][0].pos
                        self.mode.pieces[x][0], self.mode.pieces[x][3] = self.mode.pieces[x][3], \
                                                                         self.mode.pieces[x][0]
                if flip:
                    Chessboard.flip(self.mode)

            if piece.code is 3 and piece.has_moved is False:
                piece.has_moved = True
            if piece.code is 5 and piece.has_moved is False:
                piece.has_moved = True

    def change_turn(self):
        self.send_msg(pickle.dumps(self.mode.pieces), self.mode.turn)
        if flip:
            Chessboard.flip(self.mode)
        self.positions.append(self.mode.write_FEN())
        self.mode.turn *= -1
        self.send_msg(pickle.dumps(self.mode.pieces), self.mode.turn)


class Client:

    def __init__(self):
        print ('initializing client')
        self.client_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.client_socket.connect((Server.IP, Server.PORT))
        self.client_socket.setblocking(True)
        self.board = None
        self.moves = None
        print ('client initialized')

        print ('configuring client')
        with open('preferences.txt', 'r') as read_file:
            self.board_theme = read_file.readline().replace('\n', '')
            self.piece_theme = read_file.readline().replace('\n', '')
            self.transparency = int(read_file.readline())
        self.white_images = []
        self.black_images = []
        for i in range(6):
            file_name = 'images/pieces' + self.piece_theme + '/' + 'w' + str(i) + '.png'
            img = pygame.image.load(file_name)
            self.white_images.append(pygame.transform.scale(img, (100, 100)))
            file_name = file_name.replace('w', 'b')
            img = pygame.image.load(file_name)
            self.black_images.append(pygame.transform.scale(img, (100, 100)))
        self.board_image = pygame.image.load('images/boards/board' + self.board_theme + '.png')
        self.highlight = pygame.Surface((113, 113), pygame.SRCALPHA)
        self.highlight.fill((255, 255, 255, self.transparency))
        print ('client configured')

    def recv_thread(self):
        data = None
        while True:
            msg = self.recv_msg()
            try:
                data = pickle.loads(msg['data'])
            except EOFError as e:
                print ('loading pickle unsuccessful')
                print (e)

            try:
                if type(data[-1]) is tuple or type(data[-1]) is None:
                    self.moves = data
                    self.highlight_moves(self.moves)

                elif type(data[-1]) is list:
                    self.board = data
                    self.draw_board(self.board)
            except:
                self.moves = []
                self.highlight_moves(self.moves)

    def main(self):
        t1 = Thread(target = Client.recv_thread, args = (self,))
        t1.start()
        self.done = False
        while not self.done:
            self.click = False
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.click = True
            (self.mx, self.my) = pygame.mouse.get_pos()
            self.send_mouse_pos()

    def send_mouse_pos(self):
        if self.click:
            # print(self.mx, self.my)
            msg = pickle.dumps((self.mx, self.my))
            # print(msg)
            self.send_msg(msg)

    def send_msg(self, msg):
        print ('sending message to server')
        try:
            msg_header = ('{:<{}}'.format(len(msg), Server.HEADERSIZE)).encode()
            # msg_header = f'{len(msg):<{Server.HEADERSIZE}}'.encode()
            msg = msg_header + msg
            print (msg)
            self.client_socket.send(msg)
            print ('message sent to server')
        except:
            print ('failed to send message to server')
            return None

    def recv_msg(self):
        print ('receiving message from server')
        try:
            msg_header = self.client_socket.recv(Server.HEADERSIZE)  # BLOCKING
            if not len(msg_header):
                print ('disconnected')
                return None
            msg_len = int(msg_header.decode())
            print ('received message from server')
            return {'header': msg_header, 'data': self.client_socket.recv(msg_len)}  # BLOCKING

        except UnicodeDecodeError as e:
            print (e)
            # print ('failed to recieve message from server. Data artifically receieved')
            # return {'data': self.client_socket.recv(4096)}
            return None

        except ValueError as e:
            print (e)
            # print ('failed to recieve message from server. Data artifically receieved')
            # return {'data': self.client_socket.recv(4096)}
            return None

    def draw_board(self, board):
        print ('drawing board')
        x, y = 0, 0
        screen.blit(self.board_image, (x, y))
        x += 6.25
        y += 6.25
        for rank in board:
            for piece in rank:
                if piece.colour is 1:
                    screen.blit(self.white_images[piece.code], (x, y))
                elif piece.colour is -1:
                    screen.blit(self.black_images[piece.code], (x, y))
                x += 112.5
            x = 6.25
            y += 112.5
        pygame.display.flip()
        print ('board drawn')

    def highlight_moves(self, moves):
        print ('highlighting moves')
        self.draw_board(self.board)
        for move in moves:
            screen.blit(self.highlight, (round(move[1] * 112.5), round(move[0] * 112.5)))
        pygame.display.flip()
        print ('moves highlighted')


flip = True
screen = pygame.display.set_mode((900, 900))
pygame.display.set_caption("Chess")