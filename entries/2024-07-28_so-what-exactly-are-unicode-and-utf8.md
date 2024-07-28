So... what exactly are Unicode and UTF-8?
---
I recently finished what I thought would be [a quick project to pass a weekend](https://github.com/agubelu/json-parse) and turned out to be a deeper rabbit hole than expected. Most of the unexpected pain points came from handling Unicode and UTF-8, and the main takeaway for me was a clearer understanding of what they are and how they work.

So, with this newfound knowledge, I think I'm ready to answer some questions that almost every single programmer has asked themselves at some point: What's Unicode? What's UTF-8? Which one should I use? Does the last question even make sense? Let's find out!

## A bit of history

It's the 1960s, we have recently invented computers, and someone thought it would be a good idea to make computers able to store and display text. The problem was, of course, that computers read and write bytes, while we humans read and write characters.

A possible solution? Let's create a translation table (an **encoding**) to map byte values to human characters, and vice-versa. When the computer reads a byte, it will check that table to decide which character to print. When the human types a character, it will do the reverse operation to decide which byte to store. Lo and behold, the famous ASCII encoding was born:

<center>

```plaintext
     0     1     2     3     4     5     6     7     8     9
     ┌─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬─────┐
 00X │ NUL │ SOH │ STX │ ETX │ EOT │ ENQ │ ACK │ BEL │ BS  │ TAB │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 01X │ LF  │ VT  │ FF  │ CR  │ SO  │ SI  │ DLE │ DC1 │ DC2 │ DC3 │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 02X │ DC4 │ NAK │ SYN │ ETB │ CAN │ EM  │ SUB │ ESC │ FS  │ GS  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 03X │ RS  │ US  │     │  !  │  "  │  #  │  $  │  %  │  &  │  '  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 04X │  (  │  )  │  *  │  +  │  ,  │  -  │  .  │  /  │  0  │  1  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 05X │  2  │  3  │  4  │  5  │  6  │  7  │  8  │  9  │  :  │  ;  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 06X │  <  │  =  │  >  │  ?  │  @  │  A  │  B  │  C  │  D  │  E  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 07X │  F  │  G  │  H  │  I  │  J  │  K  │  L  │  M  │  N  │  O  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 08X │  P  │  Q  │  R  │  S  │  T  │  U  │  V  │  W  │  X  │  Y  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 09X │  Z  │  [  │  \  │  ]  │  ^  │  _  │  `  │  a  │  b  │  c  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 10X │  d  │  e  │  f  │  g  │  h  │  i  │  j  │  k  │  l  │  m  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┤
 11X │  n  │  o  │  p  │  q  │  r  │  s  │  t  │  u  │  v  │  w  │
     ├─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┼─────┴─────┘
 12X │  x  │  y  │  z  │  {  │  |  │  }  │  ~  │ DEL │            
     └─────┴─────┴─────┴─────┴─────┴─────┴─────┴─────┘            
```
</center>

The values increase from left to right and from top to bottom, starting at 0 and finishing at 127. The first 32 characters, and the last one, are control characters and don't really have a stand-alone visual representation. Curiously, although ASCII used whole bytes to represent values, it doesn't use the most significant bit, and so it only defines 128 different characters.

As an example, the sequence of characters `Hello` would be ASCII-encoded as the values `72 101 108 108 111` in decimal, or the byte sequence `0x48 0x65 0x6C 0x6C 0x6F` in hex.

This particular solution, however, has its shortcomings. For starters, the fact that English isn't the only language on the planet, and Latin isn't the only alphabet. This led to the development of a plethora of alternative, language-specific encodings, commonly referred to as **extended ASCII**[^1].

Extended ASCII encodings generally took advantage of the fact that ASCII only used 7 bits. They left the original 128 characters unchanged while using the remaining 128 spaces for alternative characters. This meant that text written in the Latin alphabet was generally more encoding-resilient, since `0x48` still mapped to `H` in most encodings. But non-latin characters, which used the second half of the encoding space, would show up as gibberish when using the wrong encoding (And which one was the right encoding? Good luck guessing!).

Some difficulties remained. For instance, it was impossible to represent many multilingual texts, since most encodings still used 8 bits and barely had enough space for the Latin alphabet and an alternative one. And let's not talk about pictographic languages like Chinese or Japanese, with way more than 2<sup>8</sup> characters. The technicalities and history of encoding these languages deserves its own blog post.

## Introducing... Unicode!

By the early 1990s it was evident that this had become an interoperability hell, and efforts were being made to resolve the matter of text encoding once and for all. This led to the introduction and widespread adoption of Unicode.

What's Unicode, you ask? It's essentially a world-wide effort to create a single, huge encoding table that encompasses all alphabets, symbols, emojis, and whatnot. While most of the encodings we discussed before had room for 256 characters (although some were 16-bit and allowed for <nobr>65 536</nobr> characters), Unicode is way larger and allocates enough space for <nobr>1 114 112</nobr> possible characters[^2][^3].

For the sake of interoperability, the first 128 values in Unicode map to the same characters as ASCII. This means that `Hello` still maps to the values `0x48 0x65 0x6C 0x6C 0x6F`. But Unicode-encoded text can also represent `Д` (`0x0414`), `是` (`0x662F`) and `💩` (`0x1F4A9`).

To answer our first question, Unicode is *the* global encoding table, with a value associated to every character used on Earth. It is also, conceptually, a remarkable global standardization effort.

## What about UTF-8?

Let's back up a bit. Before, I mentioned that Unicode has a total of <nobr>1 114 112</nobr> possible values. Those values are abstract numbers, but our computers must represent them somehow.

The smallest power of 2 bits able to hold the maximum Unicode value is 32 bits (or 4 bytes, the usual size for an `int`[^4]). So, we could represent Unicode-encoded text using 4 bytes per character, with those 4 bytes directly holding the Unicode value of said character. Simple, isn't it?

Such a representation is called UTF-32. Here, the 32 means that the smallest amount of space that it will use to store any Unicode value is 32 bits. But that is also the *maximum* amount of space required to store any Unicode value, and so UTF-32 is a **fixed-length** representation, with all characters taking exactly 32 bits.

This binary representation is simple, but not very efficient. Remember when I mentioned that the first 128 Unicode values map to the same characters as ASCII? Using a 4-byte representation for ASCII-only text is wildly inefficient, as the first 3 bytes of every character will always be `0x00 0x00 0x00`, a 75% waste of space.

This is where **variable-length** representations come to the rescue. Broadly speaking, UTF-16 uses 2 bytes when the Unicode value fits in 16 bits[^5], and 4 bytes otherwise. And UTF-8 can use either 1, 2, or 4 bytes per value, using only as much space as needed. Since ASCII characters have very low Unicode values, they comfortably fit in 8 bits, and so their UTF-8 binary representation is exactly the same as in early-day ASCII. Isn't that cool?

To recap and answer our second question: the UTF family defines different ways to represent Unicode values as physical bytes. Or, if you prefer, the other way around: UTF specifies how to turn a sequence of bytes into a sequence of numeric values, and Unicode dictates which character corresponds to each value. The most popular of them all is UTF-8 because it's the most space-efficient.

By the way, I didn't mention that the U in UTF stands for Unicode. In fact, the whole thing means **Unicode Transformation Format**. So, no matter which UTF format you choose, the Unicode encoding will be used to turn values into characters and vice-versa. There's no "Unicode vs UTF-8", they are two complementary layers of the encoding process:

<center>

```plaintext
[Raw binary]
01001000 01101001 00100000 11110000 10011111 10010001 10001011

    ^      
    | UTF-8
    v      

[Unicode values]
72 105 32 128075

      ^        
      | Unicode
      v        

[Characters]
Hi 👋
```

</center>

Note how the first 3 characters (`Hi␣`) take one byte each, while the waving emoji takes 4 bytes. That's UTF-8's variable-length encoding in action.

And that's all for today! I hope that, if anything, this made you aware of the huge standardization and coordination effort it takes so that we can display the 💩 emoji in all its glory, regardless of device and language.

[^1]: Extended ASCII isn't a specific encoding of it's own. It's the name commonly given to the whole family of language-specific, ASCII-based encodings that showed up afterwards.

[^2]: Yes, this number is oddly specific and not a power of 2. It has to do with the way the Unicode space is [internally organized](https://en.wikipedia.org/wiki/Plane_(Unicode)). As of writing this post, Unicode defines 149,813 characters, which accounts for only ~13% of the available space, including [a bunch of characters with unknown meaning](https://www.youtube.com/watch?v=tfk3dgpAals).

[^3]: I am aware that the proper Unicode term is *code point* and not *character*. But leveraging the common conception of *character* gets the points across, and I don't want to engage on a philosophical discussion on what a *character* even is.

[^4]: By the way, this is the reason why Rust's `char` is 32 bits wide, so that it can hold any possible Unicode value.

[^5]: I'd like to emphasize that this is a simplification. The details are a bit more complicated and require allocating some space for meta-information, since otherwise the 4-byte value `0x12345678` would be indistinguishable from the sequence of 2-byte values `0x1234 0x5678`.