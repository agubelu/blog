How we teach front-end development with vanilla JS
---

Or, a proposal on how to organize vanilla JS code.

## Some context

When I was a PhD student, I had to take on some teaching duties. Luckily for me, I ended up in the two introductory courses to information systems, which essentially map to back-end and front-end development. They were both very fun and rewarding to teach, but also very important to get right, since the local market in Spain focuses heavily on web development, so most of our students will work on a web information system as their first job after graduating.

Right at the time when I joined, they were undergoing some changes as they were pretty outdated. The back-end course focused mostly on introducing students to requirements, relational databases and SQL, which never go out of fashion. We added a few units introducing REST and we [built a tool](https://github.com/DEAL-US/Silence) to help them quickly deploy CRUD APIs on top of their existing databases. It resulted in a nicely cohesive course where students go through the whole process of turning requirements into a conceptual model, then into a relational model and a database, and finally building a back-end served by that database.

However, front-end was a completely different beast. The legacy course consisted on implementing the web application using vanilla PHP, with design patterns (and especially a lack thereof) that left a lot to be desired in terms of code quality. Without any useful guidance about how to organize their code, our students were doing the only thing they could: some delicious spaghetti intertwining everything -database access logic, business logic and presentation logic- everywhere, all at once.

In true programmer fashion, we decided to discard all legacy materials and start from a clean slate. Students would be given a REST back-end they would be familiar with thanks to the previous course, and we would teach them how to make a front-end that connects to it via REST requests. With this high-level idea in mind, and after some debate, we decided to teach them to implement it using as much vanilla JS as possible. The reasons for avoiding teaching any major frameworks essentially narrowed down to:

- We thought it was better to introduce them to some basic concepts that would then be familiar when they have to use any specific framework.

- The resulting learning materials would become stale very quickly due to the fast-paced trends in the JS world, or simply due to framework updates.

There was a problem, though. None of us had heard of, or could find, any remotely standardized way to organize vanilla JS for a web app, let alone one simple enough for people who had just learned the basics of JS just a couple of weeks beforehand. But we really didn't want to repeat the same mistake of not giving students clear guidelines to structure their codebase.

So we came up with a code structure that has worked reasonably well for us. It borrows inspiration from MVC architectures and the idea of components, so it serves the dual purpose of organizing code and planting some intuitions on the students' heads that will be useful when they're properly introduced to those concepts later on.

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

The different folders inside the `js/` main folder contain different specialized modules, which will be detailed in the following sections. Then, a single JS file is created for every HTML page, which will serve as the *controller* for that page.

## API modules

The API JS modules serve as the *model* of the application. Their role is to encapsulate all REST requests needed to interact with the back-end and retrieve or modify objects.

We provide a common JS module with general utilities for all other API modules, and then we generate one JS module per domain class. In a teaching context, this almost always is a 1:1 mapping with database tables.

```text
📁web-app
├─ 📁js
│  ├─ 📁api
│  │  ├─ 📄common.js
│  │  ├─ 📄photos.js
│  │  └─ [...]
[...]
```

The `common.js` module provides shared configuration for all other API modules, like the base URL. It also sets up a header to send the user's session token in all requests. 

```js
import { sessionManager } from '../utils/session.js';

const BASE_URL = "/api/v1";

const requestOptions = {
    headers: { Token: sessionManager.getToken() },
};

export { BASE_URL, requestOptions };
```

Then, the class-specific API modules provide methods for all back-end endpoints. For example, this is the `photos.js` module:

```js
import { BASE_URL, requestOptions } from './common.js';

const photosAPI = {

    /** Gets all Photos */
    getAll: async function() {
        let response = await axios.get(`${BASE_URL}/photos`, requestOptions);
        return response.data;
    },

    /**  Gets an entry from 'Photos' by its primary key */
    getById: async function(photoId) {
        let response = await axios.get(`${BASE_URL}/photos/${photoId}`, requestOptions);
        return response.data;
    },

    /** Creates a new entry in 'Photos' */
    create: async function(formData) {
        let response = await axios.post(`${BASE_URL}/photos`, formData, requestOptions);
        return response.data;
    },

    /** Updates an existing entry in 'Photos' by its primary key */
    update: async function(formData, photoId) {
        let response = await axios.put(`${BASE_URL}/photos/${photoId}`, formData, requestOptions);
        return response.data;
    },

    /** Deletes an existing entry in 'Photos' by its primary key */
    delete: async function(photoId) {
        let response = await axios.delete(`${BASE_URL}/photos/${photoId}`, requestOptions);
        return response.data;
    },
};

export { photosAPI };
```

The methods in these modules always have the same structure, the only difference being the parameters they receive depending on the operation they perform. We found that this consistency helps students understand what's going on and encourages them to expand them with new methods if needed.

I also mentioned that we *generate* them, because this simplicity has the advantage of making them almost trivial to autogenerate from an API spec. In fact, this whole JS file was autogenerated by [our back-end tool](https://github.com/DEAL-US/Silence) from an existing `Photos` table in the database.

Some careful readers will have noticed that we use [axios](https://github.com/axios/axios) for the API requests despite our intended goal of using only vanilla JS. We compromised here for the sake of clarity: we wanted our students to clearly see that a request is being made, without going too low-level on how that's implemented. This is the only external JS library that we use, and in our experience, the decreased cognitive and coding load in comparison with using `fetch()` helped them understand the whole thing better.

## Rendering modules

We can get things from our back-end. Great. Now we need a way to display them in our application.

However, we don't always want to display the same element the same way. A photo, for instance, can be displayed as a small part of a gallery, or as a larger element if we want to see its details, and so it needs different HTML representations depending on context.

This is when what we called *renderers* come into play. A renderer receives an object from the back-end and provides different HTML representations for that object. If you twist the concept enough, it could fit into the *View* part of MVC, but it's really more similar to a component: a generic template that can be reused in many different places.

In our web apps, we have again one renderer per relevant domain class:

```text
📁web-app
├─ 📁js
│  ├─ [...]
│  ├─ 📁renderers
│  │  ├─ 📄photos.js
│  │  ├─ 📄users.js
│  │  └─ [...]
[...]
```

The way we create renderers is pretty simple. We ask our students to write standard HTML to represent something until they're happy with how it looks, and then abstract away the specific details. For example, in the case of `renderers/photos.js`:

```js

import { parseHTML } from "/js/utils/parseHTML.js";

const photosRenderer = {
    asThumbnail: function (photo) {
        let html = `<div class="card">
                    <a href="view_photo.html?photoId=${photo.photoId}">
                        <div class="ratio ratio-1x1">
                            <img src="${photo.url}" class="card-img-top photo-image" 
                                 alt="${photo.description}">
                        </div>
                    </a>
                    <div class="card-body">
                        <h5 class="card-title">${photo.title}</h5>
                        <p class="card-text">${photo.description}</p>
                    </div>
                </div>`;
        
        let card = parseHTML(html);
        return card;
    },

    asDetails: function (photo) {
        let html = `<div>
            <h2>${photo.title}</h2>
            <h4>${photo.description}</h4>
            <p>
                Uploaded by <a href="profile.html">
                    @${photo.username}
                    <img src="${photo.avatarUrl}"
                         alt="Profile picture" class="profile-picture rounded-circle">
                </a> on ${photo.date}
            </p>
            <img src="${photo.url}" alt="${photo.description}" class="img-fluid">
        </div>`;
        let details = parseHTML(html);
        return details;
    }
};

export { photosRenderer };
```

This has all the usual benefits of components: if you want to change how all thumbnails look across your application, there is only sgf f gsfsg f hgkjdhg sj kgdhj ksdhg.

[TODO] 
[TODO] 
[TODO] 
[TODO] 
[TODO] 
[TODO] 
[TODO] 

Renderers are also composable: you can use them inside other renderers. For example, suppose a renderer module for a gallery of photos, `renderers/gallery.js`:

```js
import { parseHTML } from "/js/utils/parseHTML.js";
import { photosRenderer } from "/js/renderers/photos.js";

const galleryRenderer = {
    asThumbnailGallery: function (photos) {
        let gallery = parseHTML('<div class="row text-center"></div>');

        for (let photo of photos) {
            let col = parseHTML(`<div class="col-md-3"></div>`);
            let card = photosRenderer.asCard(photo);
            col.append(card);
            gallery.append(col);
        }

        return gallery;
    },
};

export { galleryRenderer };
```

This renderer assumes responsibility for managing the general layout of the gallery, while being agnostic about how a picture thumbnail is supposed to look like.