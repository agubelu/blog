TeX is not a bug-free software
---

A short rant on the importance of spending a bit of time writing good error messages to save our users a lot of time.

---

There are, in my opinion, many things to like about Rust, from the language's design to the ecosystem and community around it. But there is one feature that, to me, stands out. A feature that is very widely acclaimed, and that single-handedly prevents your first interactions with the borrow checker from being a painful ordeal:

It has exceptionally clear and useful compilation error messages.

For instance, let's consider this simple program, which reads a file from a certain path and outputs how many lines in it have more than 120 characters:

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

![An example of an error message from the Rust compiler](/entries/assets/rust-compiler-error.webp)

It turns out that `read_to_string().unwrap()` creates a `String`, and `.lines()` borrows from that string to create an iterator over its lines. But that `String` isn't stored anywhere, so it's dropped immediately afterwards. As a consequence, the lines iterator stops being valid as the `String` it references has been freed from memory, so it can't be used. Even if you're completely unfamiliar with Rust and didn't understand a word of what I just said, the compiler is *literally* showing you the change you can make to fix it.

This error tells you exactly what's wrong, why it's wrong, suggests a fix, and points you towards more related information should you need it. It is an excellent error message.

This is not by chance. It comes as a result of the Rust compiler's team policy of treating unclear errors as bugs. This may sound radical at first, but it makes a lot of sense from a logical standpoint:

- If great error messages are acclaimed as a *feature* then, conversely, poor error messages should be considered a bug; and
- Error messages are part of a software. Their goal is to tell you, the user, exactly what went wrong and how to remedy it if possible. If part of a software isn't achieving its purpose, that's definitely a bug.

And this leads us to today's topic. I recently found out that TeX, the software at the core of LaTeX (the typesetter that lets PhD students trade mental health for fancy equations), [is considered bug-free](https://lwn.net/Articles/726208/) because of how infrequently new bugs are found, [especially as of recent](https://www.tug.org/TUGboat/tb42-1/tb130knuth-tuneup21.pdf).

I beg to differ, for a very simple reason: **It has absolutely horrendous error messages.**

Sure, there may be worse offenders, somewhere. I don't do a lot of C++, so I haven't been blessed with those wonderful template errors. But I'm sure it must be close.

For the sake of illustration, I'll be using LaTeX. I know they are not the same, but since LaTeX is essentially a bunch of macros on top of TeX, and error messages come from the TeX processor (plus almost no-one uses plain TeX), I think my point will still stand.

Let's make the simplest of LaTeX documents:

```tex
\documentclass{article}

\begin{document}
Hello, world!
\end{document}
```

Sure enough, everything compiles. Let's cause a bit of trouble by adding a very dangerous piece of text: an underscore.

```tex
\documentclass{article}

\begin{document}
Please reach me at name_surname@domain.com
\end{document}
```

Whoops! Something turned red and your email looks a bit funky. Let's see what the compiler has to say:

```txt
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

Ok, sure, I'm being a bit difficult. This is the whole compiler log. But it *is* what you get if you run `pdflatex yourfile.tex` (compare it to Rust's error, which is what you get by running `cargo run`). Let's assume that you're using Overleaf, TeX studio or any other tool that shows you only the revelant errors:

```txt
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

It is still not particularly useful, since it's talking about math symbols and external fonts and whatnot. If you're experienced with LaTeX, you'll already know that the issue is that underscores must be escaped with a backslash like `\_`, since otherwise it's used for subscripts, which LaTeX expects to find only inside math mode. Good luck finding that out from this error!

(And, by the way, you would be forgiven for thinking that, if `\_` escapes an underscore, then `\\` escapes a backslash. But no, that terminates the current line, what you're looking for in that case is `\textbackslash`. The TeX family is full of such inconsistencies that would make PHP blush, but that's a different topic.)

Armed with the newfound knowledge that math mode is required for some symbols, plus the fact that, like Markdown, LaTeX requires an empty line to introduce a newline, you try to create a multi-line equation:

```tex
\begin{equation}
2^3 = \frac{16}{2} =

8
\end{equation}
```

Your efforts are rewarded with:

```txt
<inserted text> 
                $
l.8 
    
I've inserted a begin-math/end-math symbol since I think
you left one out. Proceed, with fingers crossed.

! Display math should end with $$.
<to be read again> 
                   \tex_par:D 
l.8 
    
The `$' that I just saw supposedly matches a previous `$$'.
So I shall assume that you typed `$$' both times.

! You can't use `\eqno' in horizontal mode.
\eqno ->\@kernel@eqno 
                      \aftergroup \ignorespaces 
l.10 \end{equation}
                   
Sorry, but I'm not programmed to handle this case;
I'll just pretend that you didn't ask for it.
If you're in the wrong mode, you might be able to
return to the right one by typing `I}' or `I$' or `I\par'.

! Missing $ inserted.
<inserted text> 
                $
l.10 \end{equation}
                   
I've inserted something that you may have forgotten.
(See the <inserted text> above.)
With luck, this will get me unwedged. But if you
really didn't forget anything, try typing `2' now; then
my insertion and my current dilemma will both disappear.

! Display math should end with $$.
<to be read again> 
                   \endgroup 
l.10 \end{equation}
                   
The `$' that I just saw supposedly matches a previous `$$'.
So I shall assume that you typed `$$' both times.
```

You'll have to admit that at least the compiler is funny. But no matter how many `$` or `$$` you try to sprinkle in, it won't work. The issue is that... empty lines are not allowed in equation mode. It's just maddening that you have to look it up somewhere because the associated error is utterly useless.

(How do you insert a newline in an equation then, you ask? You can't. You simply can't, without resorting to using external packages, or just two equations back to back.)

As all LaTeX <del>victims</del> users know, it only gets worse. In a moderately sized document, it's not unusual to suddenly have >200 errors in random places because of a minor syntax issue. At this point, I'm just afraid to know how the TeX processor works inside.

Having been exposed to Rust and LaTeX together, and their corresponding error messages, has made me much more acutely aware of how gracefully the software I write should handle invalid states, and how it should communicate such events to its users. I honestly believe that our industry should strongly move towards widely adopting the "unclear errors are bugs" policy, as it would massively improve a facet of UX that's often overlooked or seen as a chore by us programmers.