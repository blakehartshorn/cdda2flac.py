# cdda2flac.py
The world didn't need another cd ripper, but I apparently did.

![in kde plasma](https://www.blakedrinks.beer/github-images/cdda2flac.png)

There is plenty of this kind of junk out there, but I have a very specific way of doing things, so I tend to write my own scripts for ripping CDs. In this particular case, I was planning to rip my entire CD collection to my server and move it into storage, so I decided this would be a good opportunity to learn GUI design via PyQt. I chose this framework as I've been a devout KDE user for a very long time.

The goals here were as follows:
* Use proper cdda2wav, NOT IceDav or cdparanoia, as it currently features libparanoia and newer c2check features, making it superior to either of the common utilities currently shipping with Fedora or Debian.
* Use Flac only. If I wanted to listen to lossy media, I'd use the streaming service I pay for so the artists can get royalties.
* Use Musicbrainz for cd lookup, as it is the only grammatically correct solution as far as case in titles go (this drives me absolutely crazy).

Similarly, the prequisites are as follows:
* Python 3.6+
* PyQt 5+ (probably easily backportable to PyQt4, nothing spectactular was used.)
* [musicbrainzngs](http://python-musicbrainzngs.readthedocs.io/en/v0.6/) 0.6
* [discid](https://pypi.python.org/pypi/discid)
* [cdrtools](http://cdrtools.sourceforge.net/private/cdrecord.html) 3.0+ (NOT cdrkit/icedav/cdparanoia)
* [flac](http://www.xiph.org/flac/)

As of Fedora 27, I used pip3 to install all the aforementioned Python libraries.

Usage is straight forward, just run the python script. There are no command line options. Console output is relatively verbose if you launch it from a terminal window. I went through 300+ CDs with this before uploading it, so most of the necessary error handling should be in place.

There are a few options toward the top of the script you might be interested in messing with:

    musicbrainzngs.set_useragent("python-musicbrainzngs","0.6")
    home = os.getenv('HOME') 
    musicpath = f'{home}/Music'
    temppath = f'{home}/.local/tmp/cdda2flac' # WARNING: This directory is destroyed after operation 
    devices = ('(none selected)','/dev/sr0','/dev/sr1')

The "Multidisc" checkbox will append {discnum}_ before the track number of the filenames and allow multiple discs to coexist in one folder. Cover art can be manually provided from a local path or a URL, if Musicbrainz either does not have it or provides something less to your liking. 

Anyway, learning Qt was fun. 
