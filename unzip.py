#!/usr/local/bin/python3
import os
import sys
import zipfile
A_DIR = 0x10

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--encoding', default='cp437')
    parser.add_argument('-l', '--listonly', action='store_const', dest='mode', const='l')
    parser.add_argument('-x', '--extract', action='store_const', dest='mode', const='x')
    parser.add_argument('-r', '--retract', action='store_const', dest='mode', const='r')
    parser.add_argument('file', nargs=1)
    parser.add_argument('pattern', nargs='*', default=['*'])
    opts = parser.parse_args()
    print(opts)
    if not opts.mode:
        if 'unzip' in sys.argv[0]: opts.mode = 'x'
        elif 'rezip' in sys.argv[0]: opts.mode = 'r'
        else:
            print("Unknown mode, listing")
            opts.mode = 'l'
    if opts.mode not in ('l', 'r'):
        print("Not Implemented")
        return
    for arg in opts.file:
        process_file(arg, opts)

def process_file(zfn, opts):
    rzdirs = []
    with zipfile.ZipFile(zfn) as z:
        for r in z.infolist():
            fn = r.filename.encode('cp437').decode(opts.encoding)
            if opts.mode == 'l':
                print(fn)
                continue
            if r.external_attr & A_DIR:
                if opts.mode == 'r': rzdirs.append(r.filename)
                if opts.mode == 'x': os.mkdir(fn)
                continue
            data = z.read(r.filename)
            if opts.mode == 'x':
                print(fn)
                open(fn, 'xb').write(data)
                continue
            if opts.mode == 'r':
                try:
                    rf = open(fn, 'rb')
                except FileNotFoundError:
                    continue
                if data == rf.read():
                    os.unlink(fn)
                    print(fn)
    if opts.mode == 'r':
        for fn in sorted(rzdirs, key = lambda x: -len(x)):
            try:
                os.rmdir(fn)
                print(fn)
            except OSError:
                continue

if __name__ == '__main__':
    main()
