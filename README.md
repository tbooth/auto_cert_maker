# Making certificates without hand editing

Nathan had a system using Google docs, but it was problematic and I cannot get into
the account. Grrr.

I'm a Python coder. There must be a way to make this work on my laptop, right?

## Yes, it works now

To make a batch of certificates (or anything else)...

1. Check the template ODT (script defaults to `templates/default.odt`)
1. Put the list of names into a simple text file, one per line
1. Run the script

```
$ python3 make_the_certs.py COURSE="Linux for Genomics" ATTENDEE="@attendees/names.txt"
```

You will want to replace all the placeholders in the template with something or else the
placeholders will just be left there.

## Making labels etc?

The current version replaces all the instances of a given placeholder in a document, then converts
that document to PDF. It just repeats this for every combination of placeholders (normally you
will only have one which is a list and the rest are fixed).

This is no good for a sheet of labels or badges, but I could extend it to work with labels. My
idea is:

1. Instead of #PLACEHOLDER# use #PLACEHOLDER-0#, #PLACEHOLDER-1# etc.
2. If such replacements are made, these will consume items from the list (rather than just
   replacing all occurrences in the doc with the same item).
3. In this case, the output file names will contain "batch{b}\_{n}" where `b` is the batch size
   and n is the doc number.
4. We have an option to combine all the docs using pdftools.

Yeah that could be fun. But it falls down if we need to replace two items, like #NAME# and
#INSTITUTE#. Then we'd need to load two columns from the file and replace them in lock step.

Maybe NAME="@[0]foo.csv" INSTITUTE="@[1]foo.csv", or we could even imply that if the same file is
referenced twice we are reading columns from it. But this starts to get complex to code. So yeah.

## Original notes and approaches

### Editing PDF with Python

Editing/replacing text in a PDF is not as easy as you would think. We can almost do it by
making the text be a form element, but:

1) The user can then edit the form again in the PDF viewer.
2) The font of editable text cannot be changed (it's always sans-serif).

So that's no good.

### Making the PDF from scratch using, eg. PanDoc

For PDF generation, PanDoc is basically a LaTeX wrapper, and we can't get anything that looks
like a vertificate. Boo.

### Using MS Word mail merge

Word has mail-merge (good) but not in the web version (meh). And I ain't running a Windows VM
just for this.

### Using LibreOffice mail merge

LibreOffice mail merge is doubleplusungood. But...

### Editing ODT with Python

Yes! We can use this example:

https://github.com/tbooth/odfdo/blob/master/recipes/search_and_replace_words.py

Then make a PDF with:

```
soffice --headless --convert-to pdf form_test1_replaced.odt --outdir dir1
```

Let's goooo!
