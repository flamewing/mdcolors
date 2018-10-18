## Introduction

This is a Gimp-Python plugin to convert images in Gimp to Sega Mega Drive colors.

## Installation and Usage

Copy `mdcolors.py` to your Gimp plug-ins directory. This directory is:

|OS     |User scripts|System scripts|
|-------|----|----|
|Ubuntu/Linux  |~/.gimp-&lt;version&gt;/plug-ins|/usr/lib/gimp/2.0/plug-ins|
|Windows|C:\\Users\\&lt;user&gt;\\.gimp-&lt;version&gt;\\plug-ins|C:\\Program Files\\GIMP 2\\lib\\gimp\\2.0\\plug-ins|
|MacOSX |~/Library/Application Support/GIMP/&lt;version&gt;/plug-ins|/Applications/GIMP.app/Contents/Resources/lib/gimp/2.0/plug-ins|

Replace `<version>` by your Gimp version. For example, if you are using Gimp 2.8.22, this would be `2.8`.

When you restart Gimp, you should see a new menu under filters:

```
Filters
|
⋮
└── Mega Drive
    ├── Fix Colors...
    └── Palette fade...
```

`Palette fade` is still being developed. As a result, it is disabled and cannot be used.

`Fix Colors` is what you want. You are greeted with 3 choices for source, 3 choices for destination, and a choice of whether to allow shadow/highlight colors or not.

- **Options for source and destination:** For source, it assumes that the input image is close to the given selection. For destination, this is what you want the script to produce.
 - *SonMapEd colors:* These are the colors used by SonMapEd. Each channel (red, green, and blue) is a multiple of 32.
 - *Sonic &amp; Knuckles Collection colors:* These are the colors used by Sonic &amp; Knuckles Collection. Each channel (red, green, and blue) is a multiple of 34.
 - *VDP measurements:* These are based on voltage levels output by the VDP. They are nonlinear, and compressed in the mid-range.
- **Allow shadow/highlight:** If enabled, shadow/highlight colors are accepted in the input and are generated in the output. If disabled, they are converted to the nearest normal color.

The script works in both indexed and RGB images:

- *indexed images:* the script operates directly on the colormap, and runs very quickly. It does *not* deduplicate colormap entries at the end, so you may end up with duplicated entries.
- *RGB images:* the script operates pixel-by-pixel, and may take quite a while to finish for very large images. Usually, it is better to convert the image into an indexed image first, if this can be done losslessly, then run the script.

## Contributing

This script is licensed under MIT license. See LICENSE for a copy of the license.