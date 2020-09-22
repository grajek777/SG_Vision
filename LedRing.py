import board
import neopixel
import sys, getopt

def main(argv):
    turn = ''
    pixels = neopixel.NeoPixel(board.D18, 16, brightness=0.1)
    try:
        arguments, values = getopt.getopt(argv,"hi:o:",["turn="])
    except getopt.error as err:
        # Output error, and return with an error code
        print (str(err))
        sys.exit(2)
        
    for opt, arg in arguments:
        if opt in ("-t", "--turn"):
            turn = arg

    if turn == "on":
       pixels.fill((255, 255, 255))
    elif turn == "off":
       pixels.fill((0, 0, 0))

if __name__ == "__main__":
    main(sys.argv[1:])
