"use strict";(self.webpackChunkdocumentation=self.webpackChunkdocumentation||[]).push([[7353],{3031:e=>{e.exports=JSON.parse('{"archive":{"blogPosts":[{"id":"building-a-dashboard","metadata":{"permalink":"/Security-Cam/blog/building-a-dashboard","editUrl":"https://github.com/infinitel8p/Security-Cam/edit/main/documentation/blog/2024-07-20-dashboard.mdx","source":"@site/blog/2024-07-20-dashboard.mdx","title":"Building a dashboard","description":"Building a dashboard","date":"2024-07-20T00:00:00.000Z","tags":[{"inline":true,"label":"development","permalink":"/Security-Cam/blog/tags/development"},{"inline":false,"label":"Dashboard","permalink":"/Security-Cam/blog/tags/dashboard","description":"Web Interface related posts."},{"inline":false,"label":"Server","permalink":"/Security-Cam/blog/tags/server","description":"Web Interface related posts."},{"inline":true,"label":"refine","permalink":"/Security-Cam/blog/tags/refine"}],"readingTime":0.77,"hasTruncateMarker":true,"authors":[{"name":"Ludovico Ferrara","title":"Maintainer of Security-Cam","url":"https://github.com/infinitel8p","imageURL":"https://avatars.githubusercontent.com/u/50703696?s=400&u=761df587f17316eb28a4768b8092ec4dbc137f1c&v=4","key":"ludo"}],"frontMatter":{"slug":"building-a-dashboard","title":"Building a dashboard","authors":"ludo","tags":["development","dashboard","server","refine"]},"unlisted":false,"nextItem":{"title":"The start of something new","permalink":"/Security-Cam/blog/welcome"}},"content":"### Building a dashboard\\n\\nToday i started building a dashboard for our project by following JavaScript Mastery\'s [tutorial](https://youtu.be/6a3Dz8gwjdg) after struggling to decide on a design and layout.\\nI figured I\'ll learn something new by using the Refine Framework and see where this goes.\\nThe plan for now is to rebuild the dashboard from the video to get a better understanding of the Refine Framework and how it works.\\n\\n\x3c!--truncate--\x3e\\n\\nAfter that I\'ll start working on the actual dashboard for our project (probably by changing the components and some other stuff).\\nThe video seems promising and I\'m excited to see how it will turn out.\\n\\nThe first issue i\'ve encountered is (hopefully) only a minor dependency issue with the `AuthBindings` import.\\n\\n```tsx\\nimport { AuthBindings } from \\"@refinedev/core\\";\\n```\\n\\nIt seems like the import is deprecated so i hope it will be an easy fix.\\n\\n```c\\n\'AuthBindings\' is deprecated.ts(6385)\\n```\\n\\nWe\'ll see how it goes."},{"id":"welcome","metadata":{"permalink":"/Security-Cam/blog/welcome","editUrl":"https://github.com/infinitel8p/Security-Cam/edit/main/documentation/blog/2024-07-19-welcome.mdx","source":"@site/blog/2024-07-19-welcome.mdx","title":"The start of something new","description":"Welcome on our journey","date":"2024-07-19T00:00:00.000Z","tags":[{"inline":false,"label":"Hello","permalink":"/Security-Cam/blog/tags/hello","description":"Hello World!"}],"readingTime":0.43,"hasTruncateMarker":true,"authors":[{"name":"Ludovico Ferrara","title":"Maintainer of Security-Cam","url":"https://github.com/infinitel8p","imageURL":"https://avatars.githubusercontent.com/u/50703696?s=400&u=761df587f17316eb28a4768b8092ec4dbc137f1c&v=4","key":"ludo"},{"name":"Lennert Pfundtner","title":"Front End Engineer","url":"https://github.com/KrokoNinja","imageURL":"https://avatars.githubusercontent.com/u/79910460?v=4","key":"lenni"}],"frontMatter":{"slug":"welcome","title":"The start of something new","authors":["ludo","lenni"],"tags":["hello"]},"unlisted":false,"prevItem":{"title":"Building a dashboard","permalink":"/Security-Cam/blog/building-a-dashboard"}},"content":"### Welcome on our journey\\n\\nWe mark the 19th of July 2024, the day we start to rebuild this project.  \\nAfter a long time of inactivity, we decided to start from scratch and rebuild most of the stuff we already did.\\nWe are excited to see where this journey will take us.  \\nThis blog will be the place where we share our progress and thoughts (In case we become some famous dudes in the future).\\n\\n```py\\nprint(\\"Hello World\\")\\n```\\n\\n\x3c!--truncate--\x3e\\n\\n<button onClick={() => alert(\\"button clicked!\\")}>Click me!</button>"}]}}')}}]);