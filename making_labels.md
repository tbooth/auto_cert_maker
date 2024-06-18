Well the label making mode is too much fun, so I'm coding it up.

Here we go:

1) I'll make this work in text mode or ODT mode. Makes tesing a lot easier.

I'll wrap the required functionality into two classes, TXTTemplate and ODTTemplate.

2) Add a test. Done

3) When adding columns from a file, we need to keep track of if a file is referenced twice,
and if so get the next column. Then for those columns we need to generate in lock step, not a
product.

Need to add a separator argument to this. Default is r"\t".

4) Then I can post-process the args_to_replacements() output to get replacements for each
document where there are multiple placeholders on a page. How to do this? Well I could ask for
the repeats per page as an argument. But no, let's make it template dependent.

For each replacement key, see how many placeholders are in the doc. If there is more than one,
collect the suffixes. The set of suffixes must be the same for every instance*. And it's an error
to see, say, #FOO# and #FOO-1# in the same doc.

---
MEEP

FOO
BAR-1
BAZ-1

FOO
BAR-2
BAZ-2
---

*Well I could combine the sets but then some things would never appear.

So now if I have 6 replacement dicts I want to make 3 outputs. But what if there are two values
of MEEP? Do I need to make 4 documents?

MEEP=A      MEEP=A      MEEP=A      MEEP=B      MEEP=B      MEEP=B
FOO=fixed   FOO=fixed   FOO=fixed   FOO=fixed   FOO=fixed   FOO=fixed
BAR=1       BAR=2       BAR=3       BAR=1       BAR=2       BAR=3
BAZ=1       BAZ=2       BAZ=3       BAZ=1       BAZ=2       BAZ=3

Traslates to:

MEEP=A      MEEP=A      ...and ditto for MEEP=B
FOO=fixed   FOO=fixed
BAR-1=1     BAR-1=3
BAR-2=1     BAz-1=3
BAZ-1=2
BAZ-2=2

So right, when aggregating we need to ensure that all the non-suffix fields are the same. If
they are not, make a partial output. It feels like I should resolve what are lists at the time
of args_to_replacements(). What happens if I try to feed in junk here?

MEEP-1
FOO-1
BAR-1
BAZ-1

MEEP-2
FOO-2
BAR-2
BAZ-2

This is fine, the MEEP and FOO just expand over the available items. As a bonus, I can use this
way to force all the slots to be used - I'll get three pages not four with MEEP=A and MEEP=B on
the same one (but I can't use {MEEP} or {FOO} in the doc name). There is no reason to use FOO-1 and
FOO-2 here.

MEEP-1
FOO
BAR-1
BAZ

MEEP-2
FOO
BAR-2
BAZ

OK what happens here? We see there is a clash on BAZ so there will be 6 docs made, but this
is valid:

FOO=fixed
BAZ=1
BAR-1=1
BAR-2=1
MEEP-1=A
MEEP-2=B

So, when aggregating and checking that all the fields are the same, rather than:

"see if the non-suffix fields fields match and, if not, start a new page"

We have:

"select the next result where all the non-suffix fields match. if none, start a new page"

This algo is getting very over-engineered, but I do like a robust solution. And it should be fun
to code. As an equivalent to "selecting the next result" I could sort the rep list by non-suffix
fields first. But then I want to avoid re-arranging anything unless I have to. So maybe not.
Actually, this is not a sorting problem but a batching problem...

OK, let us code. I'll use the above as test examples. I need a method for both templates that
returns the non-suffix fields and the suffix fields and the suffixes. Maybe do that first.

---

I think I did it. Need to test on some combinations of things, and fix the filenames so that
\_ALL\_ is resonable and also I can get the page number in the file name. And 'pdfunite' will
allow me to concatenate the files if I desire.

Cool. Will likely put this on public GitHub at some point.
