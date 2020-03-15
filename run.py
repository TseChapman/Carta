import sys
import Carta

if __name__ == "__main__":
    argc = len(sys.argv)

    # python run.py          ---- call EN Carta without debug mode
    # python run.py debug    ---- call EN Carta with debug mode
    # python run.py jp       ---- call JP Carta without debug mode
    # python run.py debug jp ---- call JP Carta with debug mode
    debugMode = False
    inJapanese = False

    if (argc > 1):
        if (sys.argv[1].lower() == "debug"):
            debugMode = True
        elif (sys.argv[1].lower() == "jp"):
            inJapanese = True

    if (argc > 2):
        if (sys.argv[2].lower() == "jp"):
            inJapanese = True

    # First Carta means Carta.py, second Carta means class name Carta
    c = Carta.Carta(debugMode, inJapanese)
    c.process()
    c.quit()
