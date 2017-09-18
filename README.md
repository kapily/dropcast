# dropcast
Simple script to generate a podcast feed using MP3s in your Dropbox 

Requirements:
- podgen
- taglib

You can pip install those.

For taglib, you'll need to install it via brew or other means

--

Usage

1. Create a folder named "Podcast" in your Dropbox folder.
2. Create a file, `global_config.json` file in the root of the "Podcast" folder. That only contains the following
3. Run like this: `python dropcast.py --dir="/Users/kapil/Dropbox (Personal)/Podcasts"`


## global_config.json
```
{
    "dropbox_link": "https://www.dropbox.com/sh/...."
}

```
For the value of "dropbox_link", copy it from right click -> "Copy Dropbox Link"

## config.json (optional)
By default, we use the folder name as the title, and an empty description. If you want to set
something else instead, create a `config.json` file in that folder and do it there
```
{
    "Title": "My Custom Title",
    "description": "My description here"
}

```


---

Code Overview

