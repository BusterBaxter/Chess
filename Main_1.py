"""
TODO
    SOCKETS
        Server needs to send message to the client. Client only sends if recv from server
        handle early closed connections
TODO
    Minimax
        Time deduction for AI
TODO
    function for Main.py for running games
    Clock -> graphics
    Ambient Music and controls
    Option menu for preferences -> writes to preferece file
    Change promotion prompt -> Tkinter
    Coodinates should switch when turn sitches if flip?
    50 move draw?
    Drag pieces?
    reading PGN?
    Overall
    AI - Minimax, alpha beta pruning
    server, multithreading with 2 clients
    960?
    Training, Tutorial??
"""

from Chess_6 import *
standard_game = Standard(Chessboard('codes/FEN/setup.txt'))
KOTH_game = KOTH(Chessboard('codes/FEN/setup.txt'))
random_game = Random_AI(Chessboard('codes/FEN/setup.txt'))
minimax_game = Minimax(Chessboard('codes/FEN/setup.txt'))

#------------------------------------------------------------
# for rank in _game.mode.pieces:
#    for piece in rank:
#        print (piece.__dict__)
# print ('\n\n')

# standard_game.main()
# KOTH_game.main()
# Random_AI_game.main()
# minimax_game.main()
# -------------------------------------------5-----------------

main_done = False
menu = 0
main_clock = pygame.time.Clock()
while not main_done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if menu is 0:
                main_done = True
            else:
                menu = 0

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_0:
                menu = 0
            if event.key == pygame.K_1:
                menu = 1
            if event.key == pygame.K_2:
                menu = 2
            if event.key == pygame.K_3:
                menu = 3
            if event.key == pygame.K_4:
                menu = 4

    if menu is 1:
        try:
            standard_game.main()
            if standard_game.game_end:
                del standard_game
            menu = 0
        except:
            standard_game = Standard(Chessboard('codes/FEN/setup.txt'))

    if menu is 2:
        try:
            KOTH_game.main()
            if KOTH_game.game_end:
                del KOTH_game
            menu = 0
        except:
            KOTH_game = KOTH(Chessboard('codes/FEN/setup.txt'))

    if menu is 3:
        try:
            random_game.main()
            if random_game.game_end:
                del random_game
            menu = 0
        except:
            random_game = Random_AI(Chessboard('codes/FEN/setup.txt'))

    if menu is 4:
        try:
            minimax_game.main()
            if minimax_game.game_end:
                del minimax_game
            menu = 0
        except:
            minimax_game = Minimax(Chessboard('codes/FEN/setup.txt'))

    if menu is 0:
        pygame.draw.rect(screen, (128, 128, 128), ([0, 0], [1800, 1000]))
        pygame.display.flip()

    main_clock.tick(60)

pygame.quit()
print ('Program Complete')
