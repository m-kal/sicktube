# Sicktube

## Notes

## Usage

**Download/Process URLs**

The main command for Sicktube is `run`, which will load the appropriate config file and process all sections and all urls.

    sicktube run -h
    usage: sicktube.py [-h] [--config CONFIG]

    Process urls from configuration files

    optional arguments:
      -h, --help       show this help message and exit
      --config CONFIG  Location of the settings configuration file (default: None)

**Dump Configuration**

Use the `config` command to print the global and per-section resolved config settings. This is useful to determine if config files are properly overriding global defaults.

    sicktube config -h
    usage: sicktube.py [-h] [--config CONFIG]

    Dumps/prints the configuration file

    optional arguments:
      -h, --help              show this help message and exit
      --config CONFIG         Location of the settings configuration file (default: None)

**Test Email Configuration**

Post-run emails can be enabled through the `email.enable` config setting. Use the `email` command to send a test message to validate the email server settings are correct.

    sicktube email -h
    usage: sicktube.py [-h] [--config CONFIG] [--from-addr FROM_ADDR]
                   [--to-addr TO_ADDR] [--msg MSG] [--subject SUBJECT]

    Email yourself a test message to check if the email options are configured correctly

    optional arguments:
      -h, --help              show this help message and exit
      --config CONFIG         Location of the settings configuration file (default: None)
      --from-addr FROM_ADDR   Test sender's email address (default: admin@localhost)
      --to-addr TO_ADDR       Test recipient's email address (default: admin@localhost)
      --msg MSG               Test email message (default: This is a test message sent for Sicktube)
      --subject SUBJECT       Test email message subject (default: [Sicktube] Test configuration email)

**Dump Metadata Query Results**

The `metadata` command will print (or save to file) the metadata returned based on a URL. This is useful to debug an individual video or playlist returning unexpected metadata values.

    sicktube metadata -h
    usage: sicktube.py [-h] [--save-as SAVE_AS] [--config CONFIG] url

    Dumps/prints metadata for a url, useful for testing

    positional arguments:
      url                     URL to extract metadata for

    optional arguments:
      -h, --help              show this help message and exit
      --save-as SAVE_AS       Save the metadata to a file rather than printing to stdout (default: None)
      --config CONFIG         Location of the settings configuration file (default: None)

## Installation

For Windows, the appropriate dirs are:

* **Video Saver**: `Anywhere you want`
* **Plex-Agent**: `C:\Users\<username>\AppData\Local\Plex Media Server\Plug-ins\`
* **Plex-Scanner**: `C:\Users\<username>\AppData\Local\Plex Media Server\Scanners\Movies\`
* **Plex imported libs**: `M:/Plex/Resources/Plug-ins-ee6e505/Scanners.bundle/Contents/Resources/Common`

## Configuration

The configuration files and settings are hierarchically structured with from global to section. Each section to backup can have individual settings deviating from global settings. This is done by retrieving setting values from most specific to least specific, such that `defaults < cfg _global < cfg section`.

Default configuration preferences can be set in the main module source. Each section declared in `settings.cfg` (or specified with the `--config` CLI arg) can apply sections-specific settings.

### Sicktub Settings

| Settings ID | Default Value | Description |
|:--|:--|:--|
| cache-metadata | True | Downloads `.info.json` files into a `.metadata-cache` subfolder |
| dir.root | A | B |
| file.template.name | youtube_dl.DEFAULT_OUTTMPL | `<download-dir>/<output-template>` |
| dir.extractor.prefix | False | Puts the extractor before the video section, `[...]/<extractor>/[section]/[...]` |
| dir.extractor.postfix | False | Puts the extractor after the video section, `[...]/[section]/<extractor>/[...]` |

### Plex Metadata Agent Settings (DefaultPrefs.json)

The Plex metadata agent has several preferences for importing data into the Plex server. These can be found in the `DefaultPrefs.json` file as well as in the Plex media server web client at `Settings > Server > Agents`.

| Settings ID | Default Value | Description |
|:--|:--|:--|
| config.fullpath | `c:/sicktube/settings.cfg` | Full file system path to the configuration file for Sicktube used to generate the directory |
| file.metadata.cache.prefer | True | Attempt to use local metadata cache files (`*.info.json`) to expedite metadata import |
| file.metadata.cache.force-rebuild | False | Rebuilds missing metadata cache files if it is missing |

### Youtube-DL Settings

Youtube-dl settings several defaults set based on expected behavior

| Setting ID | Default Value | Description |
|:--|:--|:--|
| format | 'bestvideo+bestaudio' | Caching assumes we want best quality to transcode later |
| skip_download | True | Skips downloading the video file but will download the .info.json file |
| simulate | True | Skips downloading the video and the .info.json file |
| writeinfojson | True | Don't write out the info.json file |
| quiet | False | Don't spam the console with debug info |
| ffmpeg_location | c:/ffmpeg/bin | Location of FFMPEG |
| ignoreerrors | True | Supresses errors |

*Note: Update this to be generic in the future*

# Roadmap

* [x] Start with a scanner for existing folders and convert my manual process to a daemon running in python
* [x] Scan those folders using youtube-dl and taking the metadata (not downloading the files) and feed it into plex
* [ ] Common source for saver, scanner, and agent
* [x] Configuration checking
* [ ] Create a channel to browse the configuration URLs for the existing folders
* [ ] Convert the browsing to existing folders to browsing youtube/other-sites and on access, check for local cache else play and cache in background
* [x] Publish for github

# Mini Task List

* [ ] Add missing youtube metadata
* [x] Add metadata test function
* [x] Add url-to-metadata static method to get metadata from `webpage_url`
* [x] Add config dump cli method
* [ ] Video file rename changes may cause issue looking up `.info.json` files *// can make this a hard-no*
* [ ] Instantiate a video-saver at PlexAgent initialization/Start() *// needed for per-section settings*
* [ ] Configure a` .metadata-cache` folder and setting?
* [ ] Configurare an archives file? *// maybe have [...]/.metadata-cache/archive.log*
* [x] Enable email
* [x] Ensure email gets config param and loads settings for email addrs and ports
