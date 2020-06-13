import sys
import re

ELEMENT_TYPES = {'scene': (1.5, 1), 'action': (1.5, 1), 'char': (3.5, 1),
    'paren': (3, 3), 'dialogue': (2.5, 2.5), 'trans': (5.5, 1),
    'center': (1.5, 1)}

class ScreenplayElement:
    def reformat(self):
        stxt = list(map(str.lstrip, self.txt.split('\n')))
        # Wrap words, if fails insert hyphen
        shouldbreak = False
        for i, s in enumerate(stxt):
            if shouldbreak: break
            if len(s) > self.width * 10:
                for x in range(int(self.width * 10) - 1, -1, -1):
                    if s[x].isspace():
                        stxt[i] = s[:x] + '\n' + s[x + 1:]
                        self.txt = '\n'.join(stxt)
                        self.reformat()
                        shouldbreak = True
                        break
                    elif s[x] == '-':
                        stxt[i] = s[:x + 1] + '\n' + s[x + 1:]
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

    # Title page
    tpagetxt = f.split('\n\n')[0]
    tpagekeyr = re.compile(r'([^:]+):\s*(.*)')
    tpagevalr = re.compile(r'(?:\s{3,}|\t)(.+)')

    tpage = {}
    tpageit = iter(tpagetxt.split('\n'))
    try:
        line = next(tpageit)
        while True:
            keymatch = tpagekeyr.match(line)
            if not keymatch:
                break
            key, value = keymatch.groups()
            if value:
                tpage.setdefault(key, []).append(value.strip())
                line = next(tpageit)
            else:
                for line in tpageit:
                    valmatch = tpagevalr.match(line)
                    if not valmatch:
                        break
                    tpage.setdefault(key, []).append(valmatch[1].strip())
                else:
                    break
    except StopIteration:
        pass

    for key in tpage:
        tpage[key] = '\n'.join(tpage[key])

    if tpage != {}:
        f = '\n\n'.join(f.split('\n\n')[1:])

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

    while f[0].isspace():
        f = f[1:]

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
        elif (re.match(sceneregex, nsf0.lower()) != None and len(sf) > 1 and
                sf[1] == ''):
            if nsf0[0] == '.' or nsf0[0] == '\\':
                nsf0 = nsf0[1:].lstrip()
            elements.append(ScreenplayElement(nsf0.upper(), 'scene'))
        # Transition
        elif ((nsf0.upper() == nsf0 and nsf0[-3:] == 'TO:' and used != [] and
                used[-1] == '' and len(sf) > 1 and sf[1] == '')
                or (nsf0[0] == '>' and nsf0[-1] != '<')):
            if (nsf0[0] == '>' and nsf0[-1] != '<') or nsf0[0] == '\\':
                nsf0 = nsf0[1:].lstrip()
            elements.append(ScreenplayElement(nsf0, 'trans'))
        # Character
        elif (nsf0[0] == '@' or (re.sub(charextremover, '', nsf0.upper()) ==
                re.sub(charextremover, '', nsf0) and len(sf) > 1 and
                sf[1] != '' and used != [] and used[-1] == '' and
                nsf0[0].isalpha())):
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

    return tpage, elements

def elementstops(tpage, elements):
    plmargin = ELEMENT_TYPES['action'][0]
    prmargin = ELEMENT_TYPES['action'][1]
    pwidth = 8.5 - plmargin - prmargin
    ps = (b'%!PS-Adobe-3.0\n'
          b'/Courier findfont\n'
          b'0 dict copy begin\n'
          b'/Encoding ISOLatin1Encoding def\n'
          b'/Courier-latin /FontName def\n'
          b'currentdict end\n'
          b'dup /FID undef\n'
          b'/Courier-latin exch definefont pop\n'
          b'/Courier-latin 12 selectfont\n'
          b'/PageSize [612 792]\n'
          b'%%Page: 1 1\n')
    centertitle = ''
    righttitle = ''
    lefttitle = ''
    try:
        centertitle += tpage['Title'] + '\n'
    except:
        pass
    try:
        centertitle += tpage['Credit'] + '\n'
    except:
        pass
    try:
        centertitle += tpage['Author'] + '\n'
    except:
        try:
            centertitle += tpage['Authors'] + '\n'
        except:
            pass
    try:
        centertitle += tpage['Source'] + '\n'
    except:
        pass
    try:
        lefttitle += tpage['Copyright'] + '\n'
    except:
        pass
    try:
        lefttitle += tpage['Contact'] + '\n'
    except:
        pass
    try:
        lefttitle += tpage['Draft date'] + '\n'
    except:
        pass
    try:
        righttitle += tpage['Notes'] + '\n'
    except:
        pass
    
    page = 1
    lineno = 0
    if centertitle:
        for line in centertitle.split('\n'):
            oline = line
            line = line.replace('\\', '\\\\')
            line = line.replace('(', '\\(')
            line = line.replace(')', '\\)')
            line = line.replace('\\\\(', '\\(')
            line = line.replace('\\\\)', '\\)')
            ps += str(int(((8.5 - (len(oline) / 10)) / 2) * \
                    72)).encode('latin_1') + b' ' + \
                    str((50 - lineno) * 12).encode('latin_1') + b' moveto\n' + \
                    b'(' + line.encode('latin_1') + b') show\n'
            lineno += 1
    lineno = 0
    if lefttitle:
        for line in lefttitle.split('\n')[::-1]:
            line = line.replace('(', '\\(')
            line = line.replace(')', '\\)')
            line = line.replace('\\\\(', '\\(')
            line = line.replace('\\\\)', '\\)')
            ps += str(int(plmargin * 72)).encode('latin_1') + b' ' + \
                    str((6 + lineno) * 12).encode('latin_1') + b' moveto\n' + \
                    b'(' + line.encode('latin_1') + b') show\n'
            lineno += 1
    if righttitle:
        for line in righttitle.split('\n')[::-1]:
            oline = line
            line = line.replace('(', '\\(')
            line = line.replace(')', '\\)')
            line = line.replace('\\\\(', '\\(')
            line = line.replace('\\\\)', '\\)')
            ps += str(int(((plmargin + pwidth) - len(oline) / 10) * 72)) \
                    .encode('latin_1') + b' ' + str((6 + lineno) * 12) \
                    .encode('latin_1') + b' moveto\n' + \
                    b'(' + line.encode('latin_1') + b') show\n'
            lineno += 1

    if centertitle or lefttitle or righttitle:
        page += 1
        ps += b'showpage\n%%Page: ' + str(page).encode('latin_1') + b' ' \
              + str(page).encode('latin_1') + b'\n'

    line = 0
    header = False
    pageno = 1
    skipblank = False
    nextlinepagebreak = False
    for i, element in enumerate(elements):
        element.txt = element.txt.replace('(', '\\(')
        element.txt = element.txt.replace(')', '\\)')
        element.txt = element.txt.replace('\\\\(', '\\(')
        element.txt = element.txt.replace('\\\\)', '\\)')
        if element.t == 'action' and element.txt[:3] == '===':
            nextlinepagebreak = True
        if nextlinepagebreak:
            page += 1
            if header:
                htext = str(pageno) + '.'
                ps += str(int((8.5 - prmargin) * 72 \
                      - len(htext) * 10)).encode('latin_1') \
                      + b' 744 moveto\n(' + htext.encode('latin_1') + b') show\n'
                pageno += 1
            ps += b'showpage\n%%Page: ' + str(page).encode('latin_1') + b' ' \
                  + str(page).encode('latin_1') + b'\n'
            skipblank = True
            line = 0
            nextlinepagebreak = False
        if element.t == 'action' and element.txt[:3] == '===':
            continue
        if element.txt == '':
            if skipblank:
                continue
            line += 1
            continue
        skipblank = False
        if element.t == 'scene':
            header = True
        if element.t == 'center' and element.txt == '(MORE)':
            nextlinepagebreak = True
        if element.t == 'center':
            for l in element.txt.split('\n'):
                ps += str(int((plmargin + ((pwidth - (len(l) * 5 / 36)) / 2)) \
                      * 72)).encode('latin_1') + b' ' \
                      + str(708 - line * 12).encode('latin_1') \
                      + b' moveto\n(' + l.encode('latin_1') + b') show\n'
                line += 1
            continue
        for j, l in enumerate(element.txt.split('\n')):
            if element.t not in {'char', 'paren', 'dialogue', 'scene'}:
                if line >= 52 and len(element.txt.split('\n')) - j <= 57 - line:
                    nextlinepagebreak = True
                if line >= 57:
                    elements.insert(i + 1, ScreenplayElement('\n'.join(
                            element.txt.split('\n')[j:]), element.t))
                    nextlinepagebreak = True
                    break
            elif element.t not in {'char', 'scene'}:
                if line >= 55 and (
                        len(element.txt.split('\n')) - j >= 57 - line
                        or elements[i + 1].t != 'paren'):
                    elements.pop(i)
                    elements.insert(i + 1, ScreenplayElement('(MORE)',
                            'center'))
                    for e in elements[i::-1]:
                        if e.t == 'char':
                            if (len(e.txt.rstrip()) >= 10 and
                                    e.txt.rstrip()[-10:].upper() ==
                                    '\\(CONT\'D\\)'):
                                elements.insert(i + 2,
                                        ScreenplayElement(e.txt, e.t))
                            else:
                                elements.insert(i + 2,
                                        ScreenplayElement(e.txt + ' (CONT\'D)',
                                            e.t))
                            break
                    elements.insert(i + 3, ScreenplayElement('\n'.join(
                            element.txt.split('\n')[j:]), element.t))
                    #elements.insert(i + 4, ScreenplayElement('', 'action'))
                    break
            elif line >= 52:
                    nextlinepagebreak = True
                    elements.insert(i + 1, element)
                    break
            ps += str(int(element.lmargin * 72)).encode('latin_1') + b' ' \
                  + str(708 - line * 12).encode('latin_1') \
                  + b' moveto\n(' + l.encode('latin_1') + b') show\n'
            line += 1
    page += 1
    if header:
        htext = str(pageno) + '.'
        ps += str(int((8.5 - prmargin) * 72 \
              - len(htext) * 10)).encode('latin_1') \
              + b' 744 moveto\n(' + htext.encode('latin_1') + b') show\n'
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

    tpage, elements = readfile(ifile)
    ofile.write(elementstops(tpage, elements))

    ifile.close()
    ofile.close()
    return 0

if __name__ == '__main__':
    sys.exit(main())
