TeX is not a bug-free software
---

There are, in my opinion, many things to like about Rust, from the language's design to the tools and ecosystem around it. But there is one feature that, to me, stands out. One that single-handedly makes understanding and enforcing reference safety through the borrow checker an enlightening learning experience, rather than a painful ordeal:

It has exceptionally clear and useful compilation error messages.

For example, let's consider this simple program, which reads a file from a certain path and outputs how many lines in it have more than 120 characters:

```rs
use std::fs::read_to_string;

fn main() {
    let file_lines = read_to_string("some_file.txt")
        .unwrap() // Assume that it exists and it's readable
        .lines();

    let long_lines = file_lines
        .filter(|line| line.len() > 120)
        .count();

    println!("{long_lines}");
}
```

This code fails to compile. Why? The `rustc` compiler has this to say:

![An example of an error message from the Rust compiler](/entries/assets/rust-compiler-error.png)

It turns out that `read_to_string().unwrap()` creates a `String`, and `.lines()` borrows from that string to create an iterator over its lines. But that `String` isn't stored anywhere, so it's dropped immediately afterwards. As a consequence, the lines iterator stops being valid as the `String` it references has been freed from memory, so it can't be used.

This error tells you exactly what's wrong, why it's wrong, suggests a fix, and points you towards more related information should you need it. It's an excellent error message.

This is not by chance. It comes as a result of the Rust compiler's team policy of treating unclear errors as bugs. This may sound radical at first, but it makes a lot of sense from a logical standpoint:

- If great error messages are acclaimed as a *feature* then, conversely, poor error messages should be considered a bug; and
- Error messages are part of a software. Their goal is to tell you, the user, exactly what went wrong and how to remedy it if possible. If part of a software isn't achieving its purpose, it should reasonably be considered a bug.

And this leads us to today's topic. I recently found out that TeX, the software at the core of LaTeX (the typesetter that lets PhD students trade mental health for fancy equations), [is considered bug-free](https://lwn.net/Articles/726208/) because its last bug report was filed in XXXX.

I beg to differ, for a very simple reason: **It has absolutely terrible error messages.**

Sure, there may be worse ones. Somewhere. I don't do a lot of C++, so I haven't been blessed with those wonderful template errors. But I'm sure it must be close.

Let's make the simplest of LaTeX documents:

```tex
\documentclass{article}

\begin{document}
Hello, world!
\end{document}
```

Sure enough, everything compiles. Let's cause a bit of trouble by adding a very dangerous piece of text: an email

```tex
\documentclass{article}

\begin{document}
Please reach me at name_surname@domain.com
\end{document}
```

Whoops! Something turned red and your email looks a bit funky. Let's see what the compiler has to say:

```
This is pdfTeX, Version 3.141592653-2.6-1.40.22 (TeX Live 2022/dev/Debian) (preloaded format=pdflatex)
 restricted \write18 enabled.
entering extended mode
(./test.tex
LaTeX2e <2021-11-15> patch level 1
L3 programming layer <2022-01-21>
(/usr/share/texlive/texmf-dist/tex/latex/base/article.cls
Document Class: article 2021/10/04 v1.4n Standard LaTeX document class
(/usr/share/texlive/texmf-dist/tex/latex/base/size10.clo))
(/usr/share/texlive/texmf-dist/tex/latex/l3backend/l3backend-pdftex.def)
No file test.aux.
! Missing $ inserted.
<inserted text> 
                $
l.4 Please reach me at name_
                            surname@domain.com
? 
! Missing $ inserted.
<inserted text> 
                $
l.5 \end{document}
                  
? 
[1{/var/lib/texmf/fonts/map/pdftex/updmap/pdftex.map}] (./test.aux) )</usr/shar
e/texlive/texmf-dist/fonts/type1/public/amsfonts/cm/cmmi10.pfb></usr/share/texl
ive/texmf-dist/fonts/type1/public/amsfonts/cm/cmmi7.pfb></usr/share/texlive/tex
mf-dist/fonts/type1/public/amsfonts/cm/cmr10.pfb>
Output written on test.pdf (1 page, 31812 bytes).
Transcript written on test.log.
```

Ok, sure, I'm being a bit difficult. This is the whole compiler log. But it *is* what you get if you run `pdflatex yourfile.tex` (compare it to the Rust error, which is what you get by running `cargo run`).

From now on, let's assume that you're using Overleaf, TeX studio or any other tool that shows you only the revelant errors:

```
<inserted text> 
                $
l.4 Please reach me at name_
                            surname@domain.com
I've inserted a begin-math/end-math symbol since I think
you left one out. Proceed, with fingers crossed.

LaTeX Font Info:    External font `cmex10' loaded for size
(Font)              <7> on input line 4.
LaTeX Font Info:    External font `cmex10' loaded for size
(Font)              <5> on input line 4.
```

It is still not particularly useful, since it's talking about math symbols and external fonts and whatnot. If you're experienced with LaTeX, you'll already know that the issue is that underscores must be escaped by doing `\_`, since otherwise it's used for subscripts, which LaTeX expects to find only inside math mode.

Good luck finding that out from this error if it's your first time!

But let's not be pessimistic. You decide to persevere, and soon enough you're already writing your first scientific paper in LaTeX. One of its strengths is citations, so let's do that:

