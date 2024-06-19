#!/usr/bin/env python3
"""General purpose document formatter for ODT and TXT files.
"""
import os, sys, re
import logging as L
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import string
from subprocess import run

from pathlib import Path
from odfdo import Document

def args_to_replacements(*rep_list, col_sep=r"\t", base_dir="."):
    """We expect a list of strings in the form k=v or k=@v
    """
    # First construct a dict of { k: [*v] }, plus a dict of
    # { filename: [*k] } to keep track of multi-column files.
    res1 = {}
    res2 = {}
    for k, v in (x.split("=", 1) for x in rep_list):

        if v.startswith("@"):
            # We are getting a list from a file
            fn = v[1:]
            res2.setdefault(fn, [])
            col_num = len(res2[fn])
            res2[fn].append(k)

            with open(os.path.join(base_dir, fn)) as vfh:
                v = [ re.split(col_sep, l.rstrip("\n"))[col_num]
                      for l in vfh if l.strip() ]
        else:
            v = [v]
        # We can add multiple values for the same key
        res1.setdefault(k, []).extend(v)

    # Now flip the dict of lists into a list of all possible combinations.
    # Strategy is to start with a single empty dict, then for each list v in
    # res1.values() we take each existing entry in res and clone it to make
    # len(v) copies. Then we put one of the values from v into each of those copies.
    # Repeat until done.
    # To account for multiple columns read from files, this is modified to loop through
    # the values in res2 and only do the clone step once per list, so we don't end up
    # with the product of all the columns.
    res = [{}]
    key_lists = [ [k] for k in res1 if not(any(k in v for v in res2.values())) ]
    key_lists.extend(res2.values())

    for klist in key_lists:
        for rx in res[:]:
            dlist = [ {k: res1[k][n] for k in klist}
                      for n in range(max(len(res1[k]) for k in klist)) ]

            for dx in dlist[1:]:
                res.append(dict(**rx, **dx))
            rx.update(dlist[0])

    return [r for r in res if r]

def sort_outdirs(replacements, template, t2=None, extra=None, check=False, make=False):
    """Make (or simply check) some directories for the outputs.
    """
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

class BaseTemplate:
    formats = dict( _OFORMAT_ = None,
                    _IFORMAT_ = None )

    def __init__(self, template_file, marker='#'):
        self._tfile = template_file
        self._marker = marker
        self.reload()

    @classmethod
    def handles(cls, filename):
        f = cls.formats['_IFORMAT_']
        return filename.endswith(f".{f}")

    def get_fields(self, name_list):
        """Given a list of names to be replaced, see which are in the template
           and which are suffixed. Check for suffix consistency. Returns a dict
           where all values are lists.

           dict( ns_fields = [],
                 s_fields = [],
                 suffixes = [],
                 missing = [] )
        """
        res = dict( ns_fields = [],
                    s_fields = [],
                    suffixes = set(),
                    missing = [] )

        for name in name_list:
            found_ns = False
            found_s = set()

            suffs = self.get_placeholders(name)
            for s in suffs:
                if s:
                    found_s.add(s)
                else:
                    # Basic placeholder
                    found_ns = True

            if found_ns and found_s:
                # This is no good - can only be one or the other.
                raise RuntimeError(f"Field {name} is in template with and without suffixes.")

            if res['suffixes'] and found_s and (found_s != res['suffixes']):
                # There is a conflict
                raise RuntimeError(f"Inconsistent field suffixes in template.")

            # Add this info to the aggregate data structure
            if found_ns:
                res['ns_fields'].append(name)
            elif found_s:
                res['s_fields'].append(name)
            else:
                # Missing things go on ns_fields and missing
                res['ns_fields'].append(name)
                res['missing'].append(name)

            res['suffixes'] = res['suffixes'] or found_s

        # Finally, transform the suffixes into a list, numerically sorted.
        res['suffixes'] = sorted( res['suffixes'],
                                  key = lambda i: int(i.lstrip("-")) )

        return res

class ODTTemplate(BaseTemplate):
    formats = dict( _OFORMAT_ = "pdf",
                    _IFORMAT_ = "odt" )

    def search_replace(self, repdict):
        body = self._document.body
        m = self._marker

        for k, v in repdict.items():
            # replace a string in the full document
            body.replace(f"{m}{k}{m}", v)

    def get_placeholders(self, ph):
        """Given a single placeholder, return a list of all the times
           the placeholder is found in the doc, in the form of a list of
           suffix strings. Suffix may be empty.
        """
        body_text = self._document.body.text_content
        m = re.escape(self._marker) # normally a '#'

        return [ mo.group(1)
                 for mo in re.finditer(f"{m}{ph}(-\d+)?{m}", body_text) ]

    def save(self, newname):
        self._document.save(newname, pretty=False)

    def reload(self):
        self._document = Document(self._tfile)

class TXTTemplate(BaseTemplate):
    formats = dict( _OFORMAT_ = "txt",
                    _IFORMAT_ = "txt" )

    def search_replace(self, repdict):
        m = self._marker

        for k, v in repdict.items():
            for idx, l in enumerate(self._document):
                # replace a string in the full document
                self._document[idx] = l.replace(f"{m}{k}{m}", v)

    def get_placeholders(self, ph):
        """Given a single placeholder, return a list of all the times
           the placeholder is found in the doc, in the form of a list of
           suffix strings. Suffix may be empty
        """
        m = re.escape(self._marker) # normally a '#'

        return [ mo.group(1)
                 for l in self._document
                 for mo in re.finditer(f"{m}{ph}(-\d+)?{m}", l) ]

    def save(self, newname):
        with open(newname, "w") as fh:
            for l in self._document:
                fh.write(l)

    def reload(self):
        with open(self._tfile) as fh:
            self._document = list(fh)

def munge_replacements(reps_list, fields_spec):
    """This function combines the rep_list (a list of {placeholder: x} dicts) with the fields_spec
       to merge groups of compatible entries into a single page.
    """
    if not fields_spec['suffixes']:
        # No combining to be done
        return reps_list

    # First we need to batch the reps_list based upon fields_spec['ns_fields']
    # Things in the list can only go on the same page if all the values for these
    # keys are identical.
    batches = {}
    for rep in reps_list:
        batch_key = tuple(rep.get(k) for k in fields_spec['ns_fields'])
        batches.setdefault(batch_key, []).append(rep)

    # Now we can group the items in each batch based on fields_spec['suffixes']
    res = []
    sub_batch_size = len(fields_spec['suffixes'])
    for batch in batches.values():
        for sub_batch_n in range(0, len(batch), sub_batch_size):
            sub_batch = batch[sub_batch_n:(sub_batch_n+sub_batch_size)]

            # One sub batch will now be an item in the result (ie. a page to format)
            page = {k: sub_batch[0][k] for k in fields_spec['ns_fields']}
            res.append(page)

            for suf, rep in zip(fields_spec['suffixes'], sub_batch):
                for k in fields_spec['s_fields']:
                    page[k+suf] = rep[k]

    return res

def main(args):
    # Let's a-go!
    L.basicConfig(level = L.INFO)

    # Load any lists of items to be inserted into placeholders
    replacements = args_to_replacements(*args.replacements)

    # Load the template
    for ttype in (ODTTemplate, TXTTemplate):
        if ttype.handles(args.template):
            document = ttype(args.template)
            break
    else:
        exit("No template handler for args.template")

    # Now to support templates with multiple items per page:
    replacements = munge_replacements( replacements,
                                       document.get_fields(replacements[0].keys()) )

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
    parser.add_argument("replacements", nargs="+",
                        help="Replacements as PLACEHOLDER=text or PLACEHOLDER=@file.tsv")

    args = parser.parse_args(*argv)

    return args

if __name__ == '__main__':
    main(parse_args())
