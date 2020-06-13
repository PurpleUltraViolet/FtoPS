# FtoPS

Interpreter for [Fountain](https://www.fountain.io) screenplay markup language
outputting to PostScript.

By default it reads from stdin and outputs to stdout, so it can be invoked
through `python ftops.py < <input file> > <output file>` or, it can be invoked
as `python ftops.py [input file] [output file]`

The input files can be in any encoding, but do not use characters that are
outside the latin1 characterset.

## What isn't supported

 - Dual Dialogue
 - Lyrics
 - Emphasis formatting

## Why PostScript?

Because I couldn't wrap my head around PDF.

## Installation Instructions

Install with `python -m pip install ftops`, then run with `ftops`
