#!/usr/bin/env python
"""Make attendance certs for one of our courses.
"""
import os, sys, re
import logging as L
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter

from pathlib import Path
from odfdo import Document

IN = "form_test1.odt"
OUT = "form_test1_replaced.odt"


def search_replace(document, repdict):
    body = document.body

    for k, v in repdict.items():
        # replace a string in the full document
        body.replace(f"#{k}#", v)

def args_to_replacements(rep_list):
    """We expect a list of strings in the form k=v or k=@v
    """
    res = {}
    for k, v in (x.split("=", 1) for x in rep_list):

        if v.startswith("@"):
            # We are getting a list from a file
            with open(v[1:]) as vfh:
                v = [l.rstrip("\n") for l in list(v) if l.strip()]
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

def sort_outdirs(replacements, template, t2=None, check=False, make=False):

    out_dirs = set()

    for rep in replacements:
        out_dirs.add(myformat(template, rep))

        # If t2, we just want to check it formats OK.
        if t2:
            L.debug(f"Output file -- " + myformat(t2, rep))

    out_dirs = sorted(out_dirs)
    for od in out_dirs:
        if make:
            os.makedirs(od, exist_ok=(not check))
        else:
            if check:
                assert not os.path.exists(od)

    return out_dirs

def myformat(template, adict):
    """Format that removes any funny characters from the dict
    """
    sdict = { k: shellize(v)
              for k, v in adict.items() }

    return template.format(sdict)

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


def main(args):
    # Let's a-go!
    L.basicConfig(level = L.INFO)

    replacements = args_to_replacements(args.replacements)

    # Load the template
    document = Document(args.template)

    # See about (and make) the output directories.
    out_dirs = sort_outdirs(replacements, args.outdir, args.outfile, check=True, make=True)

    # Generally only replacements['attendee'] would be a list but we'll
    # just support all possible combinations of all the replacements.
    for d in out_dirs:
        L.info("Results will be saved to: {d}")

    for repdict in replacements:
        # Load the template again!
        document = Document(args.template)
        newname = File(myformat(args.outdir, rep)) / myformat(args.outfile, rep)

        # Modify in place
        search_replace(document, repdict)

        print(f"Saving: {newname}")
        document.save(newname, pretty=False)


    L.info("Saved out {len(replacements)} new files.")

    # TODO - convert to PDF afterwards
    if args.outfile.endswith(".pdf"):
        FIXME

def parse_args(*argv):
    """Usual ArgumentParser
    """
    desc = "Make a bunch of certificates from a template ODT file"

    parser = ArgumentParser( description = desc,
                             formatter_class = ArgumentDefaultsHelpFormatter )

    parser.add_argument("-t", "--template", default="templates/default.odt",
                        help="ODT template to load.")
    parser.add_argument("-d", "--outdir", default="certs_{COURSE}_{DATE}",
                        help="Directory for results")
    parser.add_argument("-f", "--outfile", default="{COURSE}_{ATTENDEE}.pdf",
                        help="Out file name")
    parser.add_argument("replacements", nargs="+")

    args = parser.parse_args(*argv)

    return args

if __name__ == '__main__':
    main(parse_args())
