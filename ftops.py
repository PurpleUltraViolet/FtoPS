import sys
import re

ELEMENT_TYPES = {'scene': (1.5, 1), 'action': (1.5, 1), 'char': (3.5, 1),
    'paren': (3, 3), 'dialogue': (2.5, 2.5), 'trans': (5.5, 1)}

class ScreenplayElement:
    def reformat(self):
        stxt = self.txt.split('\n')
        shouldbreak = False
        for i, s in enumerate(stxt):
            if shouldbreak: break
            if len(s) > self.width * 10:
                for x in range(int(self.width * 10 - 1), 0, -1):
                    if(s[x].isspace()):
                        stxt[i] = s[:x] + '\n' + s[x + 1:]
                        self.txt = '\n'.join(stxt)
                        self.reformat()
                        shouldbreak = True
                        break
                else:
                    stxt[i] = stxt[i][:int(self.width * 10 - 2)] + '-\n' + \
                        stxt[i][int(self.width * 10 - 2):]
                    self.txt = '\n'.join(stxt)
                    self.reformat()
                    shouldbreak = True
                    

    def __init__(self, txt, t):
        self.txt = txt
        self.t = t
        self.lmargin, self.rmargin = ELEMENT_TYPES[t]
        self.width = 8.5 - self.lmargin - self.rmargin
        self.reformat()

def main():
    ofile = None
    ifile = None

    if(len(sys.argv) < 2):
        ifile = sys.stdin
    else:
        try:
            ifile = open(sys.argv[1], 'r')
        except:
            print('Failed to open input file ' + sys.argv[1], file=sys.stderr)
            return 1

    if(len(sys.argv) < 3):
        ofile = sys.stdout
    else:
        try:
            ofile = open(sys.argv[2], 'w')
        except:
            print('Failed to open output file ' + sys.argv[2], file=sys.stderr)
            return 1

    ifile.close()
    ofile.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
