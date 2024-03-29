# Making certificates without hand editing

Nathan had a system using Google docs, but it was problematic and I cannot get into
the account. Grrr.

I'm a Python coder. There must be a way to make this work on my laptop, right?

## Editing PDF with Python

Editing/replacing text in a PDF is not as easy as you would think. We can almost do it by
making the text be a form element, but:

1) The user can then edit the form again in the PDF viewer.
2) The font of editable text cannot be changed (it's always sans-serif).

So that's no good.

## Making the PDF from scratch using, eg. PanDoc

For PDF generation, PanDoc is basically a LaTeX wrapper, and we can't get anything that looks
like a vertificate. Boo.

## Using MS Word mail merge

Word has mail-merge (good) but not in the web version (meh). And I ain't running a Windows VM
just for this.

## Using LibreOffice mail merge

LibreOffice mail merge is doubleplusungood. But...

## Editing ODT with Python

Yes! We can use this example:

https://github.com/tbooth/odfdo/blob/master/recipes/search_and_replace_words.py

Then make a PDF with:

```
soffice --headless --convert-to pdf form_test1_replaced.odt --outdir dir1
```

Let's goooo!
