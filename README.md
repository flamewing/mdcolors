[![CodeFactor](https://www.codefactor.io/repository/github/flamewing/mdcolors/badge)](https://www.codefactor.io/repository/github/flamewing/mdcolors)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/flamewing/mdcolors.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/flamewing/mdcolors/alerts/)

## Introduction

This is a Gimp Python-Fu plugin to convert images in Gimp to Sega Mega Drive colors.

## Installation and Usage

You need to have Python 2.7.x installed (Gimp for Windows comes with it), and you need to install the `enum34` package. In Linux and MacOSX, you can install the package by issuing the following command in a terminal:

```
pip install enum34
```

In Windows, you will need to download it manually. Go to [this page](https://pypi.org/project/enum34/#files), download the latest zip file (`enum34-1.1.6.zip`, at the time of this writing) and extract it somewhere. Then find the `enum` directory, and copy it to one of the locations listed below for Windows.

Copy `mdcolors.py` to your Gimp plug-ins directory. This directory is:

|OS     |User scripts|System scripts|
|-------|----|----|
|Ubuntu/Linux  |<pre>~/.gimp-&lt;version&gt;/plug-ins</pre>|<pre>/usr/lib/gimp/2.0/plug-ins</pre>|
|MacOSX |<pre>~/Library/Application Support/GIMP/&lt;version&gt;/plug-ins</pre>|<pre>/Applications/GIMP.app/Contents/Resources/lib/gimp/2.0/plug-ins</pre>|
|Windows|<pre>C:\\Users\\&lt;user&gt;\\.gimp-&lt;version&gt;\\plug-ins</pre>|<pre>C:\\Program Files\\GIMP 2\\lib\\gimp\\2.0\\plug-ins</pre>|

Replace `<version>` by your Gimp version. For example, if you are using Gimp 2.8.22, this would be `2.8`. Due to issues in tiles, Gimp 2.9 and 2.10 are currently not supported for RGB images.

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
