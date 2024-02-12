How we teach front-end development using vanilla JS
---

Or, a proposal on how to structure JS code for simple web apps.

## Some context

During my time as a PhD student, I had to take on some teaching duties. I ended up teaching the two introductory courses to information systems, which essentially map to back-end and front-end development. They were both very fun and rewarding to teach, but also very important to teach well since the local market in Spain focuses very heavily on web development, so most of our students will work on a web information system as their first job after graduating.

At the time when I joined, they were undergoing some changes as they were pretty outdated. The back-end course focused mostly on introducing students to requirements, relational databases and SQL, which never go out of fashion. We added a few units introducing REST and we [built a tool](https://github.com/DEAL-US/Silence) to help them quickly deploy CRUD APIs on top of their existing databases. It resulted in a nicely cohesive course where students go through the whole process of turning requirements into a conceptual model, then into a relational model and a database, and finally building a REST back-end served by that database.

However, the front-end course was a completely different beast. The legacy one consisted of implementing the web application using vanilla PHP, with design patterns (and especially a lack thereof) that left a lot to be desired in terms of quality. So, without any useful guidance about how to organize their code, our students were doing the only thing they could: some delicious spaghetti intertwining everything —database access logic, business logic and presentation logic— everywhere.

In true programmer fashion, we decided to discard all legacy materials and re-design the course from a clean slate. We settled down on providing students with an existing back-end (which they would be familiar with thanks to the previous course), and teaching them how to make a front-end that connects to it via REST requests. With this high-level idea in mind, and after some debate, we decided to teach them to implement it using as much vanilla JS as possible. The reasons for avoiding teaching any major frameworks essentially narrowed down to:

- We thought it was better to introduce them to some basic concepts that would then be familiar when they have to use any specific framework.

- The resulting learning materials would become stale very quickly due to the fast-paced trends in the JS world, or simply due to framework updates.

There was a problem, though. None of us had heard of, or could find, any remotely standardized way to organize vanilla JS for a web app, let alone one simple enough for second-year students who had just learned the basics of JS just a couple of weeks beforehand. But we really didn't want to repeat the same mistake of not giving students clear guidelines on how to structure their codebase, so we came up with a code structure for this particular purpose.

This structure borrows inspiration from MVC architectures and the idea of components, so it serves the dual purpose of organizing code and also planting some intuitions on the students' brains that will be useful when they're properly introduced to those concepts in later courses.

## App structure

Ignoring unrelated elements like CSS, the general folder structure for our web apps looks like this:

```text
📁web-app
├─ 📁js
│  ├─ 📁api
│  ├─ 📁libs
│  ├─ 📁renderers
│  ├─ 📁utils
│  ├─ 📁validators
│  ├─ 📄some_page.js
│  └─ 📄other_page.js
├─ 📄some_page.html
└─ 📄other_page.html
```

The sub-folders inside `js/` contain different specialized modules, which will be detailed in the following sections. For the sake of example, let's assume we're building a simple photo gallery, and that there is an existing back-end that provides basic CRUD endpoints for photos.

## API modules

The API modules serve as the *model* of the application. Their role is to encapsulate all REST requests needed to interact with the back-end and retrieve or modify objects.

The `api/` folder contains a common module, `api/common.js`, with general utilities for all other API modules. Then, we generate one JS module per domain class. In a teaching context, this is almost always a 1:1 mapping with database tables:


```text
📁web-app
├─ 📁js
│  ├─ 📁api
│  │  ├─ 📄common.js
│  │  ├─ 📄photos.js
│  │  └─ [...]
[...]
```

The `common.js` module provides shared configuration for all other API modules, like the base URL. It also allows us to centralize shared options and headers for all requests, for example, to send things like session tokens:

```js
"use strict";
import { sessionManager } from "/js/utils/session.js";

const BASE_URL = "/api/v1";

const requestOptions = {
    headers: { Token: sessionManager.getToken() },
};

export { BASE_URL, requestOptions };
```

In this case, session tokens are handled by `sessionManager`, a [utility module](#bonus-utility-modules).

Then, the class-specific API modules provide wrapper methods for all back-end endpoints. For example, this is the `photos.js` module:

```js
"use strict";
import { BASE_URL, requestOptions } from "./common.js";

const photosAPI = {

    /** Gets all Photos */
    getAll: async function() {
        let response = await axios.get(`${BASE_URL}/photos`, requestOptions);
        return response.data;
    },

    /**  Gets an entry from 'Photos' by its primary key */
    getByID: async function(photoID) {
        let response = await axios.get(`${BASE_URL}/photos/${photoID}`, requestOptions);
        return response.data;
    },

    /** Creates a new entry in 'Photos' */
    create: async function(formData) {
        let response = await axios.post(`${BASE_URL}/photos`, formData, requestOptions);
        return response.data;
    },

    /** Updates an existing entry in 'Photos' by its primary key */
    update: async function(formData, photoID) {
        let response = await axios.put(`${BASE_URL}/photos/${photoID}`, formData, requestOptions);
        return response.data;
    },

    /** Deletes an existing entry in 'Photos' by its primary key */
    delete: async function(photoID) {
        let response = await axios.delete(`${BASE_URL}/photos/${photoID}`, requestOptions);
        return response.data;
    },
};

export { photosAPI };
```

The methods in these modules always have the same structure, the only difference being the parameters they receive depending on the operation they perform. We found that this consistency helps students understand what's going on and encourages them to expand them with new methods if needed.

I also mentioned that we *generate* these class-specific API modules. This is because the wrapper methods are almost trivial to autogenerate from an API spec. In fact, the whole JS module above was autogenerated by [our back-end tool](https://github.com/DEAL-US/Silence) from an existing `Photos` table in our database.

You, a careful reader, will have noticed that we use [axios](https://github.com/axios/axios) for the API requests despite our intended goal of using only vanilla JS. We compromised here for the sake of clarity: we wanted our students to clearly see that a request is being made, without going too low-level on how that's implemented. This is the only external JS library that we use, and in a teaching context, we thought that the resulting code is more straightforward than using the native `fetch()` function.

## Rendering modules

We can communicate with our back-end, great. Now, we need a way to display the things we fetch from it in our web app.

From our experience, this task was another hotspot for messy code. To provide a standardized way of doing it, we came up with what we called _renderers_. A renderer is a JS module that takes an object retrieved from the back-end, and provides different HTML representations for that object. This has two main advantages:

- It centralizes the styling of the different domain elements, and
- It decouples the data representation from its possible visual representations (for example, a photo can be displayed as a thumbnail inside a gallery, or as a larger element if we want to see its details).

And so, without uttering the word _component_, we managed to introduce students to a basic concept of modern web design without tying ourselves down to a specific framework.

In our web apps, we again have one renderer per relevant domain class:

```text
📁web-app
├─ 📁js
│  ├─ [...]
│  ├─ 📁renderers
│  │  ├─ 📄photos.js
│  │  └─ [...]
[...]
```

The way we create these is pretty simple. We tell our students to write standard HTML to represent something until they're happy with how it looks, and then abstract away the specific details into a JS renderer. For example, here is a possible renderer for photos, which provides representations for a photo as a thumbnail or as an extended view:

```js
"use strict";
import { parseHTML } from "/js/utils/parseHTML.js";

const photosRenderer = {
    asThumbnail: function(photo) {
        let html = `<div class="thumbnail">
                        <a href="view_photo.html?id=${photo.photoID}">
                            <img src="${photo.url}" alt="${photo.description}">
                        </a>
                        <div class="thumb-body">
                            <h5 class="photo-title">${photo.title}</h5>
                            <p class="photo-desc">${photo.description}</p>
                        </div>
                    </div>`;

        return parseHTML(html);
    },

    asDetails: function(photo) {
        let html = `<div>
            <h2>${photo.title}</h2>
            <h4>${photo.description}</h4>
            <p>
                Uploaded by
                <a href="view_profile.html?id=${photo.userID}">
                    @${photo.username}
                </a>
            </p>
            <img src="${photo.url}" alt="${photo.description}">
        </div>`;

        return parseHTML(html);
    }
};

export { photosRenderer };
```

Here, `parseHTML` is another [utility](#bonus-utility-modules) that we provide students with, which simply transforms an HTML string into a DOM object.

Renderers are, of course, highly composable. For example, let's build a renderer for a gallery of photo thumbnails, `/js/renderers/gallery.js`, using a basic Bootstrap layout:

```js
"use strict";
import { parseHTML } from "/js/utils/parseHTML.js";
import { photosRenderer } from "/js/renderers/photos.js";

const galleryRenderer = {
    asThumbnailGrid: function(photos) {
        let gallery = parseHTML('<div class="row text-center"></div>');

        for (let photo of photos) {
            let col = parseHTML(`<div class="col-md-3"></div>`);
            let thumbnail = photosRenderer.asThumbnail(photo);
            col.append(thumbnail);
            gallery.append(col);
        }

        return gallery;
    },
};

export { galleryRenderer };
```

This new renderer assumes responsibility for managing the general layout of the photo gallery, while being agnostic about how a picture thumbnail is supposed to look like. We also encourage students to create renderers for other commonly used elements throughout their app, like error/information messages.

## Validation modules

Form validation is another popular source of spaghetti code among students, as they tend to just plop it in wherever. To try to combat this, we encourage them to do it using validation modules, whose role is simply to receive `FormData` objects and return a list of associated validation errors.

Similarly to the previous ones, we create one validation module per class, which contain validation functions for all forms regarding that class:

```text
📁web-app
├─ 📁js
│  ├─ [...]
│  ├─ 📁validators
│  │  ├─ 📄photos.js
│  │  └─ [...]
[...]
```

The validation module for photos could look like this:

```js
"use strict";
const photosValidator = {

    validateCreation: function(formData) {
        let errors = [];

        let title = formData.get("title");
        let url = formData.get("url");

        if (title === null || title.length === 0) {
            errors.push("The photo must have a title");
        }

        if (url === null || !url.match(/^https?:/)) {
            errors.push("The photo must have a valid image URL");
        }

        return errors;
    },
};

export { photosValidator };
```

This is a simple validation, but the idea is also simple. The goal is, again, to help them keep everything tidy and organized. From our experience, we've seen that this encourages students to write more complex and exhaustive validations. A common source of pain for them used to be implementing validations that involve API requests; after we started doing things this way, I saw many of my students turning their validation functions `async` and doing API requests inside them before I even got to teaching them that.

## Bringing everything together

By now, we have all the building blocks we need to build an actual page for our web app. All that remains is to orchestrate the specific logic for every individual page.

To do this, we create a JS file for every HTML page in our application, with the same name. For example, let's build our `index.html`, in which we'll show a gallery with all of our pictures. The responsible for bringing this page to life (its _controller_, if you will) is `js/index.js`, which could look like this:

```js
"use strict";
import { photosAPI } from "/js/api/photos.js";
import { photosValidator } from "/js/validators/photos.js";
import { galleryRenderer } from "/js/renderers/gallery.js";

function main() {
    loadGallery();
}

async function loadGallery() {
    let photos = await photosAPI.getAll();
    let gallery = galleryRenderer.asThumbnailGrid(photos);
    let galleryContainer = document.getElementById("card-gallery");
    galleryContainer.append(gallery);
}

document.addEventListener("DOMContentLoaded", main);
```

Creating and registering a `main()` function reduces friction with their pre-existing programming knowledge and, I think, helps students visualize the execution flow more clearly. At this point, the process of retrieving and displaying elements from the API becomes fairly streamlined: request the elements, renderize them, and place them in the appropriate container. Other elements can then be loaded in parallel thanks to the functions being `async`.

The logic for handling forms also becomes remarkably similar every time: the controller registers a function to deal with the form's `submit` event, which uses the relevant validator to check for errors, and either send it via a POST/PUT request using the `api` modules, or displaying these errors to the user:

```js
"use strict";
import { photosAPI } from "/js/api/photos.js";
import { alertRenderer } from "/js/renderers/alerts.js";

function main() {
    let photoForm = document.getElementById("form-photo-upload");
    photoForm.onsubmit = handleSubmitPhoto;
}

function handlePhotoSubmit(event) {
    event.preventDefault();

    let formData = new FormData(event.target);
    let errors = photosValidator.validateCreation(formData);

    if (errors.length === 0) {
        await photosAPI.create(formData);
        window.location.href = "index.html";
    } else {
        // Display `errors` in a useful way using a renderer.
    }
}

document.addEventListener("DOMContentLoaded", main);

```

## Closing thoughts

I had a lot of fun during my four years teaching web development. It's a particularly rewarding course because students get instant visual feedback on all the work they do, and that has a huge impact in keeping their motivation high throughout the semester. I like to think that the most valuable thing we were able to provide to them, rather than the technicalities of things like *how to make an AJAX request with JS*, was these guidelines on how to organize scalable volumes of JS code.

Of course, this structure isn't flawless, and in many cases it's a bit coupled to other parts of our tech stack. I decided to share it in the hopes that it's useful to some devs or teachers out there. My hope is that, as our former students advance in their careers and move on to higher responsibility positions, they use it a starting point for even better code structures, and that we contributed to making some codebases, somewhere, a bit nicer.

## Bonus: utility modules

There are a couple of extra modules that I mentioned briefly before which provide some related utilities. We included them in our project templates for students to use freely. However, I always tried to allocate some time to briefly explain why and how they work.

The first one is `parseHTML.js`, which turns a string containing HTML into a DOM object:

```js
"use strict";

function parseHTML(str) {
    let tmp = document.implementation.createHTMLDocument();
    tmp.body.innerHTML = str;
    return tmp.body.children[0];
}

export { parseHTML };
```

This is an adaptation of [YouMightNotNeedJQuery's](https://youmightnotneedjquery.com/) replacement for `$.parseHTML()`, with the added restriction of allowing only one root node in the string.

Finally, there's `sessions.js`. This is an object with a collection of utility methods for handling and storing login data, logouts, invalidating them when they expire and so on. What the `login()` method expects is tightly coupled to [the tool that we use for our back-ends](https://github.com/DEAL-US/Silence), but besides that, I don't think that anything here is particularly remarkable. I'll include it in all its glory simply to make this blog post fully self-contained:

```js
"use strict";

// Time in seconds during which the session token is valid
const TOKEN_VALIDITY_TIME = 86400;

const sessionManager = {

    login: function (sessionToken, userData) {
        localStorage.setItem("sessionToken", sessionToken);
        localStorage.setItem("sessionTokenTime", new Date().getTime());
        localStorage.setItem("loggedUserData", JSON.stringify(userData));
    },

    logout: function () {
        localStorage.removeItem("sessionToken");
        localStorage.removeItem("sessionTokenTime");
        localStorage.removeItem("loggedUserData");
    },

    getToken: function () {
        let token = localStorage.getItem("sessionToken");

        // Logout if the token has expired
        if (token !== null) {
            let currentDate = new Date().getTime();
            let tokenDate = localStorage.getItem("sessionTokenTime");
            let diff = currentDate - tokenDate;

            if (diff > TOKEN_VALIDITY_TIME * 1000) {
                console.error("The session has expired, logging out.");
                this.logout();
                token = null;
            }
        }

        return token;
    },

    isLogged: function () {
        return this.getToken() !== null;
    },

    getLoggedUser: function () {
        return JSON.parse(localStorage.getItem("loggedUserData"));
    },

    getLoggedId: function () {
        return this.isLogged() ? this.getLoggedUser().userId : null;
    }
};

export { sessionManager };
```