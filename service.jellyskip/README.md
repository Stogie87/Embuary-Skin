# Jellyskip

Jellyskip is a Kodi service that interacts with the Jellyfin Media Segments API to provide a button for skipping media segments such as intros and outros. This tool enhances your media watching experience by allowing you to easily skip unwanted segments with a single click.

For example use [intro-skipper](https://github.com/intro-skipper/intro-skipper) jellyfin addon to create intro segments for your media files.
Then install this addon in Kodi alongside [jellyfin kodi](https://github.com/jellyfin/jellyfin-kodi) addon to skip the intro segments.


## Usage


<details> 
  <summary>Presents a button to skip media segments (e.g., intro, outro)</summary>
    <img src="https://i.imgur.com/hL62YyN.png" alt=""/>
</details>

## Requirements
- *Jellyfin Server 10.10.0* or later (with Media Segments API enabled)
- Manually or automatically created media segments in Jellyfin (e.g., intro, outro)
- *Jellyfin-Kodi* addon installed and configured
- Jellyfin instance reachable from Kodi

## Installation

1. Download the addon code (the repository zip).
2. Place the `service.jellyskip` folder in your Kodi `addons` directory.
3. (Re)start Kodi.
4. Enable/Install the addon.
5. Enjoy!

## Usage

Once installed, Jellyskip will automatically detect media segments from Jellyfin and present a button to skip these segments during playback.

## Inspiration

This project was inspired (and code was taken from) by the following repositories and projects:

- [service.upnext (Jellyfin hack)](https://github.com/qwerty12/service.upnext/)
- [service.upnext (original repo)](https://github.com/im85288/service.upnext)
- [jellyfin-kodi](https://github.com/jellyfin/jellyfin-kodi)
- [Titan Bingie Skin Mod for Button Design](https://forum.kodi.tv/showthread.php?tid=355993)

## Roadmap

Depending on whether this feature is ported to the Jellyfin-Kodi addon or any other addon, this project may be deprecated.
The current version is very simple and includes the following planned improvements:

- Settings to define which segments to present a button for, skip delays, etc.
- Bug fixes
- Code cleanup

## Potential Issues

**Tested using native paths only and on Kodi Version 21.2! Experience may vary on other versions**

**Quickly thrown together, proof of concept!**

## License

This project is licensed under the GNU General Public License, v2. See the `LICENSE` file for more details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## Contact

For any questions or issues, please open an issue on GitHub.
