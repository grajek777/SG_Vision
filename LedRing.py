import board
import neopixel
import sys, getopt

def main(argv):
    turn = ''
    bright = 0.1
    try:
        arguments, values = getopt.getopt(argv,"hi:o:",["turn=", "brightness="])
    except getopt.error as err:
        # Output error, and return with an error code
        print (str(err))
        sys.exit(2)
        
    for opt, arg in arguments:
        if opt in ("-t", "--turn"):
            turn = arg
        elif opt in ("-b", "--brightness"):
            bright = arg

    pixels = neopixel.NeoPixel(board.D18, 16, brightness=float(bright))
    if turn == "on":
       pixels.fill((255, 255, 255))
    elif turn == "off":
       pixels.fill((0, 0, 0))

if __name__ == "__main__":
    main(sys.argv[1:])
