Ok, next I want to create a "image service" that will have some utilities to describe images uploaded.
Specifically I want to use the `vikhyatk/moondream2` model from transformers.
When an image is received, it is saved but it also used to generate a `caption` with the following model settings:
`{"temperature": 0.25, "max_tokens": 768, "top_p": 0.3}`.

For now the caption will be just console logged.