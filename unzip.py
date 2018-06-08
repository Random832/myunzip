#!/usr/local/bin/python3
import os
import sys
import zipfile
import glob
import fnmatch
A_DIR = 0x10


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--encoding', default='cp437')
    parser.add_argument('-l', '--listonly', action='store_const', dest='mode', const='l')
    parser.add_argument('-x', '--extract', action='store_const', dest='mode', const='x')
    parser.add_argument('-r', '--retract', action='store_const', dest='mode', const='r', help='Remove extracted files. Use --dry-run to print a list of files that would be removed.')
    parser.add_argument('-d', '--destdir', type=str)
    parser.add_argument('-o', '--overwrite', action='store_const', dest='omode', const=True)
    parser.add_argument('-n', '--never-overwrite', action='store_const', dest='omode', const=False)
    parser.add_argument('zipfile', nargs=1, help='May be a wildcard. Suppress with --no-wildzip.')
    parser.add_argument('file', nargs='*', default=None, help='May be wildcards. Suppress with --no-wildfile.')
    parser.add_argument('--no-wildzip', dest='wildzip', action='store_false', help=argparse.SUPPRESS)
    parser.add_argument('--no-wildfile', dest='wildfile', action='store_false', help=argparse.SUPPRESS)
    parser.add_argument('--dry-run', action='store_true', help=argparse.SUPPRESS)  # rezip only
    opts = parser.parse_args()
    if not opts.mode:
        if 'unzip' in sys.argv[0]:
            opts.mode = 'x'
        elif 'rezip' in sys.argv[0]:
            opts.mode = 'r'
        else:
            print("Unknown mode, listing")
            opts.mode = 'l'
    for arg in opts.zipfile:
        if opts.wildzip:
            if not arg.endswith('.zip'):
                yn = input("Did you mean %s*.zip? " % arg)
                if yn[:1].lower() == 'y':
                    arg = arg + '*.zip'
            for aarg in glob.glob(arg):
                process_file(aarg, opts)
        else:
            process_file(arg, opts)


def process_file(zfn, opts):
    rzdirs = set()

    def mkdir(dn):
        if not dn: return
        if opts.mode == 'x' and not os.path.isdir(dn):
            os.makedirs(dn)
        elif opts.mode == 'r':
            rzdirs.add(dn)

    def confirm(dfn):
        if opts.omode is not None:
            return opts.omode
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
            if opts.encoding != 'cp437':
                # zipfile module gives us no hooks for this
                try:
                    fn = r.filename.encode('cp437').decode(opts.encoding)
                except UnicodeEncodeError:
                    print("Warning: could not decode %r as cp437" % r.filename)
                    fn = r.filename
            else:
                # Simpler logic, and can't screw up.
                fn = r.filename
            # Be paranoid about path traversal components
            parts = os.path.normpath(fn).split(os.sep)
            for i, part in enumerate(parts):
                if (i, part) == (0, ''): parts[i] = 'ROOT'
                elif part == '..': parts[i] = 'UP'
            fn = os.sep.join(parts)
            if opts.file:
                if opts.wildfile:
                    for spec in opts.file:
                        if fnmatch.fnmatch(fn, spec):
                            break
                    else:
                        continue
                else:
                    if fn not in opts.file:
                        continue
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
                    if not oyes:
                        continue
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
                    if not opts.dry_run:
                        os.unlink(dfn)
                    print(fn)
                continue
    if opts.mode == 'r':
        for fn in sorted(rzdirs, key=lambda x: -len(x)):
            if opts.dry_run:
                # TODO check for empty directory
                if os.path.isdir(fn):  # what about symlinks
                    print(fn)
                    continue
            else:
                try:
                    os.rmdir(fn)
                    print(fn)
                except OSError:
                    continue


if __name__ == '__main__':
    main()
