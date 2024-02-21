Why is it so hard to link (and style) SVGs in HTML?
---

The year is 2024. We have language models that can code, shitty AI-generated content everywhere, and still no flying cars. But a problem that should be trivial to solve is surprisingly annoying: why is there no easy way to link the contents of an `<svg>` tag?

---

A few days ago, I was working on making my blog and my homepage as lightweight as possible. One of the changes I made was getting rid of FontAwesome icons, and replacing them with the more permissive and modular [FeatherIcons](https://feathericons.com/), which provides all icons as individual SVGs. My problems started with this bad boy:

<center><img src="assets/github-blue.svg"></center>

I wanted to use it as a link to GitHub for my projects, so it was going to be reused. The obvious answer is to store it somewhere and link it with an `<img>` tag:

```html
<img src="/img/icons/github.svg">
```

Great, that works. However, I have slightly different colors for links in the light and dark themes, and I'd like the icon's color to be consistent with them. A quick Google search later, I found out that [you can use CSS to change the stroke color](https://developer.mozilla.org/en-US/docs/Web/SVG/Tutorial/Fills_and_Strokes) of an `<svg>`. Exactly what I needed! I wonder if it works for `<img>` as well?

```html
<img src="/img/icons/github.svg" class="icon-link">
```
```css
.icon-link {
    stroke: var(--link);
}
```

...no luck. It looks like it only works for `<svg>`. Oh well:
```html
<svg src="/img/icons/github.svg" class="icon-link"></svg>
```

Wait, what? `<svg>` doesn't support linked content? Am I really supposed to repeat this N times?

```html
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
class="feather feather-github icon-link">
    <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37
    3.37 0 0 0-.94-2.61c3.14-.35 6.44-1.54 6.44-7A5.44
    5.44 0 0 0 20 4.77 5.07 5.07 0 0 0 19.91 1S18.73.65
    16 2.48a13.38 13.38 0 0 0-7 0C6.27.65 5.09 1 5.09
    1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78c0
    5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22">
    </path>
</svg>
```

It works as intended now, but it's just not great for page size, maintainability, readability, or just general sanity.

Come on, there has to be a way. Another search and one [StackOverflow visit](https://stackoverflow.com/questions/34121832/how-do-i-link-an-svg-file-in-my-html) later, I learned that using `<object>` may do the trick:

```html
<object class="icon-link" type="image/svg+xml" data="/img/icons/github.svg"></object>
```
```css
.icon-link svg {
    stroke: var(--link);
}
```

Still doesn't work. It turns out that `<object>` creates a whole new document inside it, where my CSS rules have no power. Fine, I'll have to include the rule inside the svg file, which [is allowed](https://developer.mozilla.org/en-US/docs/Web/SVG/Element/style):

```html
<object type="image/svg+xml" data="/img/icons/github.svg"></object>
```
```html
<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"
class="feather feather-github">
    <style>
        path {
            stroke: var(--link);
        }
    </style>
    <path>[...]</path>
</svg>
```

The result of this ridiculously convoluted contraption is:

![`--link is not defined`](assets/style_error_svg.png)

My CSS variables, defined in `:root`, also have no business being in scope in this whole new realm defined by `<object>`. I suppose I could define the link colors there as well, but they would be redundant and I'd need to remember to change them there too in the future, which I probably won't.

I gave up and gave them a shade of blue somewhere in the middle of both themes.

---

Why is this such a painful ordeal? I'd love to be told otherwise and learn the correct way, because this seemed ridiculous for what should have been a simple change. If you know a better approach, by all means let me know and I'd be more than happy to update this post to share it.