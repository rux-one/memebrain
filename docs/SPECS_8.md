I want you to focus on the frontend now. In `HomeView.vue` component let's add a command palette-style search which will search qdrant for matching memes (by caption). Let's define a threshold of similarity (0.15 by default) which will filter out less fitting images.
Search results are refreshed after each new key is pressed into the search input. (ignore empty query)
Once the search results are available, let's render the list of found images below the search input.
Let's make the search threshold configurable with a default of `0.15` and expose it as a slider or input field below the search bar, with a range from 0.0 to 1.0. The slider should have step size of 0.05.
On the search page, any key stroke outside search (except the slider) should focus the search input.