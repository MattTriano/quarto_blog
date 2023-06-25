# My Quarto Blog

I do a lot of my work in Jupyter Notebooks. Notebooks can integrate code with descriptive text, images, or $\LaTeX$ equations. Notebooks can be easily converted to `HTML`, which makes them an excellent vehicle for blog posts. I used to use Fast.ai's [fastpages](https://github.com/fastai/fastpages) notebook blogging platform, but Fast.ai deprecated `fastpages` after [Quarto](https://quarto.org/) (the successor to the R-markdown format) emerged. Quarto makes it very convenient to publish notebooks via GitHub-Pages.

## Previewing work locally

After installing `quarto` (you can install it into a conda env; that's what I've done) and [creating a blog](https://quarto.org/docs/websites/website-blog.html), you can preview the blog by:
1. (in a terminal with your `quarto_env` activated) Navigate to your blog's directory
2. Run `quarto preview .`
3. Go to the URL printed in your terminal's output.
