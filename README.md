# dropcast

Simple script to generate a podcast feed using MP3s in your Dropbox 

### Requirements:
- podgen
- taglib
- gflags
- pytz

You can pip install those.

However, for taglib, you'll need to install it via brew or other means since it requires native libraries

----------------

## Usage

1. Create a folder named "Podcast" in your Dropbox folder.
2. Create a file, `global_config.json` file in the root of the "Podcast" folder. That only contains the following
3. Run like this: `python dropcast.py --dir="/Users/kapil/Dropbox (Personal)/Podcasts"`

After running, the file `feed.rss` will be created in each folder that contains a music file.

One subsequent runs, the file `README.txt` will also be created that contains a shared link to `feed.rss`. The README file isn't created on the first run due to a race condition (until Dropbox uploads the `feed.rss` file, we have no way of getting a link for that file). That's why that file is added on subsequent runs.

## global_config.json (required)
```
{
    "dropbox_link": "https://www.dropbox.com/sh/...."
}

```
For the value of "dropbox_link", copy it from right click -> "Copy Dropbox Link"

## Adding Images (optional)

Just add an image to the same folder of the podcast (title doesn't matter) and it will be automatically be added as the podcast's image
If more than one image is provided, one will be arbitrarily chosen.

## config.json (optional)

By default, we use the folder name as the title, and an empty description. If you want to set something else instead, create a `config.json` file in that folder and do it there

```
{
    "Title": "My Custom Title",
    "description": "My description here"
}

```

------------

Other Notes

- run `py.test` to run tests
- didn't use Dropbox API because there's no way to list a shared link folder via the API so had to resolve to scraping
