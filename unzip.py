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
    parser.add_argument('-d', '--destdir', type=str)
    parser.add_argument('-o', '--overwrite', action='store_const', dest='omode', const=True)
    parser.add_argument('-n', '--never-overwrite', action='store_const', dest='omode', const=False)
    parser.add_argument('file', nargs=1)
    parser.add_argument('pattern', nargs='*', default=['*'])
    opts = parser.parse_args()
    if not opts.mode:
        if 'unzip' in sys.argv[0]: opts.mode = 'x'
        elif 'rezip' in sys.argv[0]: opts.mode = 'r'
        else:
            print("Unknown mode, listing")
            opts.mode = 'l'
    for arg in opts.file:
        process_file(arg, opts)

def process_file(zfn, opts):
    rzdirs = set()
    def mkdir(dn):
        if opts.mode == 'x' and not os.path.isdir(dn):
            os.makedirs(dn)
        elif opts.mode == 'r':
            rzdirs.add(dn)
    def confirm(dfn):
        if opts.omode is not None: return opts.omode
        inp = input("Overwrite %r? " % dfn).lower()
        if inp == 'y':
            return True
        elif inp == 'a':
            opts.omode = True
            return True
        elif inp == 'x':
            opts.omode = False
            return False
        else:
            return False
    with zipfile.ZipFile(zfn) as z:
        if opts.destdir:
            mkdir(opts.destdir)
        for r in z.infolist():
            rfn = r.filename
            fn = rfn.encode('cp437').decode(opts.encoding)
            if opts.mode == 'l':
                print(fn)
                continue
            if opts.destdir:
                dfn = os.path.join(opts.destdir, fn)
            else:
                dfn = fn
            if r.external_attr & A_DIR:
                mkdir(dfn)
                continue
            if opts.mode == 'x':
                mkdir(os.path.dirname(dfn))
                oyes = False
                if os.path.exists(dfn):
                    oyes = confirm(dfn)
                    if not oyes: continue
                print(fn)
                wf = open(dfn, 'wb' if oyes else 'xb')
                wf.write(z.read(r.filename))
                continue
            if opts.mode == 'r':
                mkdir(os.path.dirname(dfn))
                try:
                    rf = open(dfn, 'rb')
                except FileNotFoundError:
                    continue
                if z.read(r.filename) == rf.read():
                    os.unlink(dfn)
                    print(fn)
                continue
    if opts.mode == 'r':
        for fn in sorted(rzdirs, key = lambda x: -len(x)):
            try:
                os.rmdir(fn)
                print(fn)
            except OSError:
                continue

if __name__ == '__main__':
    main()
