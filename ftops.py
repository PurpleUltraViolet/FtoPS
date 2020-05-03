import sys
import re

ELEMENT_TYPES = {'scene': (1.5, 1), 'action': (1.5, 1), 'char': (3.5, 1),
    'paren': (3, 3), 'dialogue': (2.5, 2.5), 'trans': (5.5, 1),
    'center': (1.5, 1)}

class ScreenplayElement:
    def reformat(self):
        stxt = self.txt.split('\n')
        # Wrap words, if fails insert hyphen
        shouldbreak = False
        for i, s in enumerate(stxt):
            if shouldbreak: break
            if len(s) > self.width * 10:
                for x in range(int(self.width * 10), 0, -1):
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

def readfile(ifile):
    f = ifile.read()
    # Remove boneyard
    f = re.sub(r'^/\*.*?[^\\]\*/', r'', f, flags=re.DOTALL)
    f = re.sub(r'([^\\])/\*.*?[^\\]\*/', r'\1', f, flags=re.DOTALL)
    # Clean up linebreaks so there's no more than one blank line at any point
    f = re.sub('\n{3,}', '\n\n', f)
    # Remove sections and synopses
    f = re.sub('\n#.*', '', f)
    f = re.sub('(?:\n|^)=(?!==).*', '', f)
    # Remove notes
    f = re.sub(r'^\[\[.*?[^\\]\]\]', r'', f, flags=re.DOTALL)
    f = re.sub(r'([^\\])\[\[.*?[^\\]\]\]', r'\1', f, flags=re.DOTALL)
    # Remove markdown formatting
    f = re.sub(r'^[\*_]+(.*?[^\\])[\*_]+', r'\1', f)
    f = re.sub(r'([^\\])[\*_]+(.*?[^\\])[\*_]+', r'\1\2', f)
    f = re.sub(r'[\\](.)', r'\1', f)

    elements = []
    sf = f.split('\n')
    used = []
    sceneregex = re.compile(r'^(\.[^\.]|int|ext|est|int\./ext|int/ext|i/e)')
    charextremover = re.compile(r'\(.*\)$')
    while len(sf) > 0:
        osf0 = sf[0].rstrip()
        nsf0 = osf0.lstrip()
        if nsf0 == '':
            elements.append(ScreenplayElement('', 'action'))
        # Scene heading
        elif re.match(sceneregex, nsf0.lower()) != None and sf[1] == '':
            if nsf0[0] == '.' or nsf0[0] == '\\':
                nsf0 = nsf0[1:].lstrip()
            elements.append(ScreenplayElement(nsf0.upper(), 'scene'))
        # Transition
        elif (nsf0.upper() == nsf0 and nsf0[-3:] == 'TO:' and used != [] and
                used[-1] == '' and sf[1] == '') or (nsf0[0] == '>' and
                nsf0[-1] != '<'):
            if (nsf0[0] == '>' and nsf0[-1] != '<') or nsf0[0] == '\\':
                nsf0 = nsf0[1:].lstrip()
            elements.append(ScreenplayElement(nsf0, 'trans'))
        # Character
        elif (nsf0[0] == '@' or (re.sub(charextremover, '', nsf0.upper()) ==
                re.sub(charextremover, '', nsf0) and sf[1] != '' and
                used != [] and used[-1] == '')):
            if nsf0[0] == '@' or nsf0[0] == '\\':
                nsf0 = nsf0[1:].lstrip()
            elements.append(ScreenplayElement(nsf0, 'char'))
        # Parenthetical
        elif (nsf0[0] == '(' and nsf0[-1] == ')' and elements != [] and
                (elements[-1].t == 'char' or elements[-1].t == 'dialogue')):
            elements.append(ScreenplayElement(nsf0, 'paren'))
        # Dialogue
        elif elements != [] and (elements[-1].t == 'char' or
                elements[-1].t == 'paren'):
            sf[0] = sf[0].lstrip().rstrip()
            if sf[0][0] == '\\':
                nsf0 = nsf0[1:].lstrip()
            d = sf[0]
            used.append(sf.pop(0))
            while sf[0] != '' and (sf[0][0] != '(' and sf[0][0] != ')'):
                sf[0] = sf[0].lstrip().rstrip()
                if sf[0][0] == '\\':
                    nsf0 = nsf0[1:].lstrip()
                d += '\n' + sf[0]
                used.append(sf.pop(0))
            sf.insert(0, used.pop())
            elements.append(ScreenplayElement(d, 'dialogue'))
        # Centered
        elif nsf0[0] == '>' and nsf0[-1] == '<':
            nsf0 = nsf0[1:-1].lstrip().rstrip()
            elements.append(ScreenplayElement(nsf0, 'center'))
        # Action
        else:
            if osf0[0] == '\\' or osf0[0] == '!':
                osf0 = osf0[1:]
            elements.append(ScreenplayElement(osf0, 'action'))

        used.append(sf.pop(0))

    return elements

def elementstops(elements):
    ps = (b'%!PS-Adobe-3.0\n'
          b'/Courier findfont\n'
          b'0 dict copy begin\n'
          b'/Encoding ISOLatin1Encoding def\n'
          b'/Courier-latin /FontName def\n'
          b'currentdict end\n'
          b'dup /FID undef\n'
          b'/Courier-latin exch definefont pop\n'
          b'/Courier-latin 12 selectfont\n'
          b'%%Page: 1 1\n')
    line = 0
    page = 1
    for element in elements:
        if element.t == 'action' and element.txt == '===':
            page += 1
            ps += b'showpage\n%%Page: ' + str(page).encode('latin_1') + b' ' \
                  + str(page).encode('latin_1') + b'\n'
            line = 0
            continue
        if element.txt == '':
            line += 1
            continue
        for l in element.txt.split('\n'):
            ps += str(int(element.lmargin * 72)).encode('latin_1') + b' ' \
                  + str(708 - line * 12).encode('latin_1') \
                  + b' moveto\n(' + l.encode('latin_1') + b') show\n'
            line += 1
    ps += b'showpage\n'
    return ps

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
        ofile = sys.stdout.buffer
    else:
        try:
            ofile = open(sys.argv[2], 'wb')
        except:
            print('Failed to open output file ' + sys.argv[2], file=sys.stderr)
            return 1

    elements = readfile(ifile)
    ofile.write(elementstops(elements))

    ifile.close()
    ofile.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
