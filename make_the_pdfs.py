#!/usr/bin/env python
"""Make attendance certs for one of our courses.
"""
import os, sys, re
import logging as L
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import string
from subprocess import run

from pathlib import Path
from odfdo import Document

IN = "form_test1.odt"
OUT = "form_test1_replaced.odt"


def args_to_replacements(rep_list):
    """We expect a list of strings in the form k=v or k=@v
    """
    res = {}
    for k, v in (x.split("=", 1) for x in rep_list):

        if v.startswith("@"):
            # We are getting a list from a file
            with open(v[1:]) as vfh:
                v = [l.rstrip("\n") for l in list(vfh) if l.strip()]
        else:
            v = [v]
        # We can set multiple values for the same key
        res.setdefault(k, []).extend(v)

    # Now flip the dict into a list of all possible combinations.
    res2 = [{}]
    for k, v in res.items():
        for rx in res2[:]:
            for vx in v[1:]:
                res2.append(dict(**{k: vx}, **rx))
            rx.update(**{k: v[0]})

    return [r for r in res2 if r]

def sort_outdirs(replacements, template, t2=None, extra=None, check=False, make=False):

    out_dirs = set()

    for rep in replacements:

        out_dirs.add(myformat(template, rep, extra=extra))

        # If t2, we just want to check it formats OK.
        if t2:
            L.debug(f"Output file -- " + myformat(t2, rep, extra=extra))

    out_dirs = sorted(out_dirs)
    for od in out_dirs:
        if make:
            os.makedirs(od, exist_ok=(not check))
        else:
            if check:
                assert not os.path.exists(od)

    return out_dirs

def myformat(template, adict, extra=None):
    """Format that removes any funny characters from the dict
    """
    sdict = { k: shellize(v)
              for k, v in adict.items() }

    # Add an _ALL_ item which has everything
    sdict['_ALL_'] = "_".join([ sdict[k] for k in sorted(sdict) ])

    # Now add the file format, or whatever.
    sdict.update(extra or ())

    return template.format(**sdict)

def shellize(insane):
    """Sanitizes a non-sane string so it can be a filename.
       Apparently Aspera can't deal with '+' in filenames.
    """
    allowed_chars = string.ascii_letters + string.digits + "_-"

    # Unicode oddities
    odd_chars = '‐‑−¹²³'
    odd_subs  = '---123'

    # Substitutions first
    s = [ char
            if char in allowed_chars
          else odd_subs[odd_chars.find(char)]
            if char in odd_chars
          else {u'+':u'plus', u'*':u'star', u'&':u'and'}[char]
            if char in u'+*&'
          else u"_"
            for char in insane ]

    # Then squash multiple underscores and periods
    idx = len(s) - 1
    while idx > 0:
        if s[idx] in u'._' and s[idx-1] == s[idx]:
            del(s[idx])
        idx -= 1

    # Then remove all "-" from start and finish
    return ''.join(s).strip('-')

class ODTTemplate:
    formats = dict(_OFORMAT_ = "pdf",
                   _IFORMAT_ = "odt" )

    def __init__(self, template_file, marker='#'):

        self._tfile = template_file
        self._marker = marker
        self.reload()

    @classmethod
    def handles(cls, filename):
        f = cls.formats['_IFORMAT_']
        return filename.endswith(f".{f}")

    def search_replace(self, repdict):
        body = self._document.body
        m = self._marker

        for k, v in repdict.items():
            # replace a string in the full document
            body.replace(f"{m}{k}{m}", v)

    def save(self, newname):
        self._document.save(newname, pretty=False)

    def reload(self):
        self._document = Document(self._tfile)

class TXTTemplate:
    formats = dict(_OFORMAT_ = "txt",
                   _IFORMAT_ = "txt" )

    def __init__(self, template_file, marker='#'):
        self._tfile = template_file
        self._marker = marker
        self.reload()

    @classmethod
    def handles(cls, filename):
        f = cls.formats['_IFORMAT_']
        return filename.endswith(f".{f}")

    def search_replace(self, repdict):
        m = self._marker

        for k, v in repdict.items():
            for idx, l in enumerate(self._document):
                # replace a string in the full document
                self._document[idx] = l.replace(f"{m}{k}{m}", v)

    def save(self, newname):
        with open(newname, "w") as fh:
            for l in self._document:
                fh.write(l)

    def reload(self):
        with open(self._tfile) as fh:
            self._document = list(fh)

def main(args):
    # Let's a-go!
    L.basicConfig(level = L.INFO)

    replacements = args_to_replacements(args.replacements)

    # Load the template
    for ttype in (ODTTemplate, TXTTemplate):
        if ttype.handles(args.template):
            document = ttype(args.template)
            break
    else:
        exit("No template handler for args.template")

    # See about (and make) the output directories.
    rep_extra = document.formats
    out_dirs = sort_outdirs( replacements, args.outdir, t2 = args.outfile,
                                                        extra = rep_extra,
                                                        check = True,
                                                        make = True )

    # Generally only replacements['attendee'] would be a list but we'll
    # just support all possible combinations of all the replacements.
    for d in out_dirs:
        L.info(f"Results will be saved to: {d}")

    # Save a mapping of {newname: oldname} for when we do PDF conversions
    conversions = {}

    # Loop through all the output docs to be made
    for rep in replacements:
        # Load the template again!
        document.reload()
        newname = ( Path(myformat(args.outdir, rep, rep_extra)) /
                    myformat(args.outfile, rep, rep_extra) )

        # Modify in place
        document.search_replace(rep)

        conversions[newname] = newname.with_suffix(f".{document.formats['_IFORMAT_']}")
        newname = conversions[newname]

        print(f"Saving: {newname}")
        document.save(newname)


    L.info(f"Saved out {len(replacements)} new files.")

    # Now for the PDF conversions
    if document.formats['_IFORMAT_'] != document.formats['_OFORMAT_']:
        for d in out_dirs:
            all_v = [ v for k, v in conversions.items()
                      if os.path.dirname(k) == d ]

            if not all_v:
                continue

            # v is the source name (.odt) and we should be able to make
            # all the PDFs at once.
            run(["soffice", "--headless", "--convert-to", document.formats['_OFORMAT_'],
                 "--outdir", d,
                 *all_v ],
                check=True, text=True, capture_output=True)

            # If that worked we can remove the ODT files
            for v in all_v:
                os.unlink(v)

        L.info(f"Converted {len(conversions)} files to {document.formats['_OFORMAT_'].upper()}.")

def parse_args(*argv):
    """Usual ArgumentParser
    """
    desc = "Make a directory of PDFs with filled-in fields from a template ODT file"

    parser = ArgumentParser( description = desc,
                             formatter_class = ArgumentDefaultsHelpFormatter )

    parser.add_argument("-t", "--template", required=True,
                        help="ODT or TXT template to load.")
    parser.add_argument("-d", "--outdir", default="{_OFORMAT_}_out",
                        help="Directory for results")
    parser.add_argument("-f", "--outfile", default="{_ALL_}.{_OFORMAT_}",
                        help="Out file name")
    parser.add_argument("replacements", nargs="+")

    args = parser.parse_args(*argv)

    return args

if __name__ == '__main__':
    main(parse_args())
