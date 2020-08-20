# first-order-ui
A UI version of AliaksandrSiarohin's [first-order-model](https://github.com/AliaksandrSiarohin/first-order-model). 

Simplifies generating deepfakes with the same process used in the Jupyter Notebook demo [here](https://colab.research.google.com/github/AliaksandrSiarohin/first-order-model/blob/master/demo.ipynb). You may be interested in this if you are generating output videos without the need for significant tweaking (for making Baka Mitai memes, for example.)

(Will test auto-speed-up with ffmpeg bindings later.)

Can optionally be installed with the 800mb checkpoint pre-packaged. See Installing below.

## Troubleshooting
### Output video is too bright
Try changing the filetype of the source image. While .png is recommended (*"This format is loss-less, and it has better i/o performance"*), .jpg and other types will work as well. If you are fine with performing additional post-processing to your video, then you should use a .png image and manually tweak the brightness in a video editor.

Seems related to https://github.com/AliaksandrSiarohin/first-order-model/issues/182.