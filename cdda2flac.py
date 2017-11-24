#!/usr/bin/python3

import subprocess,musicbrainzngs,discid,sys,requests,shutil,os,webbrowser
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QLineEdit, QVBoxLayout, QHBoxLayout,
                             QGridLayout, QApplication, QComboBox, QPushButton, QMessageBox, QCheckBox)
from PyQt5.QtGui import QPixmap,QIcon
from PyQt5.QtCore import Qt

musicbrainzngs.set_useragent("python-musicbrainzngs","0.6")
home = os.getenv('HOME')
musicpath = f'{home}/Music'
temppath = f'{home}/.local/tmp/cdda2flac' # WARNING: This directory is destroyed after operation
devices = ('(none selected)','/dev/sr0','/dev/sr1')

class getdisc:

    def __init__(self,drive):
        self.disc = discid.read(drive)

    def getid(self):
        return(self.disc)

    def url(self):
        return(self.disc.submission_url)

    def getlist(self):
        try:
            self.mblist = musicbrainzngs.get_releases_by_discid(self.disc,toc=None,cdstubs=True,\
                                                                includes=["artists","recordings"])

        except:
            self.mblist = False
        
        if self.mblist:
            try: # These things are occasionally missing.
                for i in range(len(self.mblist['disc']['release-list'])):
                    if 'date' not in self.mblist['disc']['release-list'][i]:
                        self.mblist['disc']['release-list'][i]['date'] = '0000'
                    if 'country' not in self.mblist['disc']['release-list'][i]:
                        self.mblist['disc']['release-list'][i]['country'] = 'XX'
            except:
                print('Looks like this is a cdstub.')
            
        return(self.mblist)

    def parse(self,relnum):
        if not self.mblist:
            self.mblist = { 'manual': 'manual' } #lazy bugfix is lazy
        for k in self.mblist:
            if k == 'disc':
                data = self.mblist['disc']['release-list'][relnum]
                self.infodict = { 'artist': data['artist-credit-phrase'], 'album': data['title'], 'discnum': '',\
                                  'multidisc': False, 'date': data['date'], 'relid': data['id'], \
                                  'infotype': 'musicbrainz', 'tracklist': []}

                if int(data['medium-count']) > 1:
                    self.infodict['multidisc'] = True

                for x in data['medium-list']:
                    for y in x['disc-list']:
                        if str(self.disc) == y['id']:
                            self.infodict['discnum'] = x['position']
                dindex = int(self.infodict['discnum']) - 1
                for x in data['medium-list'][dindex]['track-list']:
                    self.infodict['tracklist'].append(x['recording']['title'])
                break
            
            elif k == 'cdstub':
                data = self.mblist['cdstub']
                self.infodict = { 'artist': data['artist'], 'album': data['title'], 'date': '0000',\
                                  'discnum': '1', 'multidisc': False, 'relid': data['id'], \
                                  'infotype': 'cdstub', 'tracklist': []}
                for x in data['track-list']:
                    self.infodict['tracklist'].append(x['title'])
                break

            else:
                self.infodict = { 'artist': 'Artist', 'album': 'Album Title', 'date': '0000', 'discnum': '1',\
                                  'multidisc': False, 'relid': 'helpmeihavenoentryonmusicbrainz',
                                  'infotype': 'manual', 'tracklist': []}
                for x in range(len(self.disc.tracks)):
                    self.infodict['tracklist'].append(f'Track {(x+1):02d}')
                break

        try:
            imageinfo = False
            imagelist = musicbrainzngs.get_image_list(self.infodict['relid'])
            for x in imagelist['images']:
                if x['front']:
                    imageinfo = x
        except Exception as e:
            print(e)

        if os.path.exists(f"{temppath}/{self.infodict['relid']}"):
            shutil.rmtree(f"{temppath}/{self.infodict['relid']}")
        os.makedirs(f"{temppath}/{self.infodict['relid']}")
            
        if imageinfo:
            self.infodict['cover'] = f"{temppath}/{self.infodict['relid']}/cover{imageinfo['image'][-4:]}"
            coverart = open(self.infodict['cover'],'wb')
            coverart.write(musicbrainzngs.get_image_front(self.infodict['relid']))
            coverart.close()
        else:
            self.infodict['cover'] = False
            print("Couldn't find cover art for this release.")
        
        return(self.infodict)
    
class Window(QMainWindow):

    def __init__(self, parent=None):
        super(Window,self).__init__()
        self.widget = main_widget(self)
        self.setCentralWidget(self.widget)
        self.setGeometry(300, 300, 900, 300)
        self.show()
        
class main_widget(QWidget):

    def __init__(self, parent):
        super(main_widget,self).__init__(parent)

        self.statbar = parent.statusBar()
        self.windowtitle = parent.setWindowTitle
        parent.setWindowIcon(QIcon.fromTheme('audio-x-generic'))
        
        self.rinfo = {}
        self.tracksEdit = []

        self.initUI()


    def initUI(self):

        self.devList = QComboBox()
        self.relList = QComboBox()
        self.coverPix = QLabel()
        
        self.vbox = QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.grid = QGridLayout()
        self.grid.setSpacing(10)
        self.grid.setColumnStretch(0, 0)
        self.grid.setColumnStretch(1, 1)
        self.grid.setColumnStretch(2, 0)
        self.grid.setColumnStretch(3, 2)
        
        self.hbox.addWidget(QLabel('Device'))
        self.hbox.addWidget(self.devList)
        self.hbox.addWidget(QLabel('Release'))
        self.hbox.addWidget(self.relList)

        for dev in devices:
            self.devList.addItem(dev)

        self.vbox.addLayout(self.hbox)
        self.vbox.addLayout(self.grid)
        self.vbox.addStretch()
        self.setLayout(self.vbox)

        self.devList.activated[str].connect(self.devSelect)
        self.relList.activated.connect(self.relSelect)
    
    def devSelect(self,drive):
        if drive != '(none selected)':
            try:
                self.relList.clear()
                self.disc = getdisc(drive)
                self.dinfo = self.disc.getlist()

                if self.dinfo and 'disc' in self.dinfo:
                    for x in self.dinfo['disc']['release-list']:
                        y = f"{x['country']} {x['date'][:4]}: {x['artist-credit-phrase']} - {x['title']}"
                        self.relList.addItem(y)
                else:
                    self.relList.addItem('Be nice and add this to Musicbrainz.')

                self.relSelect(0)
                
            except Exception as e:
                QMessageBox.critical(self,'Error',f'Unable to read {drive}')
                self.initData()
                self.devList.setCurrentIndex(0)
                print(e)
            
    def relSelect(self,relnum):
        self.windowtitle(self.relList.currentText())
        self.initData()
        self.rinfo = self.disc.parse(relnum)

        if self.rinfo['infotype'] == 'cdstub':
            msg = "This data is from a cdstub, not a proper Musicbrainz entry. Would you like to add this disc?"
        elif self.rinfo['infotype'] == 'manual':
            msg = "No information for this disc found. Submit to Musicbrainz?"
        if self.rinfo['infotype'] != 'musicbrainz':
            u = self.disc.url()
            print(u)
            q = QMessageBox.question(self, 'Please help', msg, QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if q == QMessageBox.Yes:
                webbrowser.open_new_tab(u)        
        
        tracklist = self.rinfo['tracklist']

        self.artistEdit = QLineEdit(self.rinfo['artist'])
        self.albumEdit = QLineEdit(self.rinfo['album'])
        self.dateEdit = QLineEdit(self.rinfo['date'])
        self.dateEdit.setMaxLength(10)
        self.discnumEdit = QLineEdit(self.rinfo['discnum'])
        self.discnumEdit.setMaxLength(2)
        self.coverEdit = QLineEdit()
        self.coverEdit.setPlaceholderText("File path or URL")
        self.multiToggle = QCheckBox('Multidisc')
        self.multiToggle.setChecked(self.rinfo['multidisc'])
        
        ripBtn = QPushButton("Make FLAC",self)
        reloadBtn = QPushButton("Reload",self)
        noCovBtn = QPushButton("No Cover",self)
        self.upCovBtn = QPushButton("Ch Cover",self)

        if self.rinfo['cover']:
            self.coverPix.setPixmap(QPixmap(self.rinfo['cover']).scaled(375, 375, Qt.KeepAspectRatio))
            self.update()

        self.grid.addWidget(self.upCovBtn, 13, 0)
        self.grid.addWidget(self.coverEdit, 13, 1)
            
        self.grid.addWidget(QLabel('Artist'), 2, 0)
        self.grid.addWidget(self.artistEdit, 2, 1)
        self.grid.addWidget(QLabel('Album'), 3, 0)
        self.grid.addWidget(self.albumEdit, 3, 1)
        self.grid.addWidget(QLabel('Date'), 4, 0)
        self.grid.addWidget(self.dateEdit, 5, 0)
        self.grid.addWidget(QLabel('Disc #'), 6, 0)
        self.grid.addWidget(self.discnumEdit, 7, 0)
        self.grid.addWidget(self.multiToggle, 8, 0)
        self.grid.addWidget(ripBtn, 10, 0)
        self.grid.addWidget(reloadBtn, 11, 0)
        self.grid.addWidget(noCovBtn, 12, 0)
        self.grid.addWidget(self.coverPix, 4, 1, 9, 1)
        
        for x in range(len(tracklist)):
            tnum = x + 1
            trow = x + 2
            self.tracksEdit.append((QLabel(f'Track {tnum:02d}'),QLineEdit(tracklist[x])))
            self.grid.addWidget(self.tracksEdit[x][0], trow, 2)
            self.grid.addWidget(self.tracksEdit[x][1], trow, 3)

        self.statbar.showMessage('Ready.')
        ripBtn.clicked.connect(self.makeflac)
        reloadBtn.clicked.connect(self.reloadDev)
        noCovBtn.clicked.connect(self.remCover)
        self.upCovBtn.clicked.connect(self.chCover)

    def updateInfo(self):
        self.rinfo['artist'] = self.artistEdit.text()
        self.rinfo['title'] = self.albumEdit.text()
        self.rinfo['date'] = self.dateEdit.text()
        self.rinfo['discnum'] = self.discnumEdit.text()
        self.rinfo['multidisc'] = self.multiToggle.isChecked()
        for x in range(len(self.rinfo['tracklist'])):
            self.rinfo['tracklist'][x] = self.tracksEdit[x][1].text()
        
    def remCover(self):
        self.rinfo['cover'] = False
        self.coverPix.clear()
        self.coverEdit.clear()
        self.update()
        self.statbar.showMessage('Cover removed')

    def chCover(self):
        coverPath = self.coverEdit.text()
        if coverPath != '':
            coverExt = coverPath.split('.')[-1]
            self.rinfo['cover'] = f"{temppath}/{self.rinfo['relid']}/cover.{coverExt}"
            if coverPath[:7] == 'http://' or coverPath[:8] == 'https://':
                f = open(self.rinfo['cover'],'wb')
                r = requests.get(coverPath)
                f.write(r.content)
                f.close()
                r.close()
            else:
                shutil.copy2(coverPath,self.rinfo['cover'])
        self.coverPix.clear()
        self.coverPix.setPixmap(QPixmap(self.rinfo['cover']).scaled(375, 375, Qt.KeepAspectRatio))
        self.update()

    def reloadDev(self):
        dev = self.devList.currentText()
        self.devSelect(dev)
        if self.devList.currentText() == dev:
            self.statbar.showMessage(f'Reloaded {dev}')
        else:
            self.statbar.showMessage(f'Unable to reload {dev}')

    def initData(self):
        for x,y in self.tracksEdit:
            x.clear()
            y.clear()
        self.rinfo.clear()
        self.tracksEdit.clear()
        try:
            self.coverPix.clear()
            self.coverEdit.clear()
        except:
            print("Cover may not have yet been defined.")
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().setParent(None)
        self.update()

    def makeflac(self):
        self.updateInfo()
        drive = self.devList.currentText()
        path = f"{musicpath}/{self.rinfo['artist']}/{self.rinfo['date'][:4]} {self.rinfo['title']}/"
        tracknum = 1
        if os.path.exists(path) and self.rinfo['multidisc'] is False:
            warn = QMessageBox.warning(self, 'warning', f'{path} exists. Remove folder and continue?',\
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if warn == QMessageBox.Yes:
                shutil.rmtree(path)
                os.makedirs(path)
            else:
                return()
        elif os.path.exists(path) and self.rinfo['multidisc'] is True:
            for x in os.listdir(path):
                if x[0] == self.rinfo['discnum']:
                    msg = f'It appear you already attempt to rip this disc to {path}. Please check the folder.' + \
                          '\n\nTo continue anyway, click Yes.'
                    warn = QMessageBox.question(self,'warning',msg,QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                    if warn == QMessageBox.No:
                        return()
                    break
        else:
            os.makedirs(path)
        os.chdir(f"{temppath}/{self.rinfo['relid']}")
        self.statbar.showMessage('Ripping CD to wav...')
        cdda2wav = ['cdda2wav','-vall','-paraopts=proof,c2check','-B','-H','-D',drive]
        subprocess.run(cdda2wav,stdout=sys.stdout,stderr=sys.stdout)
        self.statbar.showMessage('CD Rip complete')
        subprocess.run(['eject',drive])
        print('\a')
        if self.rinfo['cover'] != False and self.rinfo['discnum'] == '1':
            shutil.copy(self.rinfo['cover'],path)
        for x in self.rinfo['tracklist']:
            self.statbar.showMessage(f'Encoding: {x}...')
            if self.rinfo['multidisc'] is True:
                filetrack = f"{self.rinfo['discnum']}_{tracknum:02d}"
            else:
                filetrack = f'{tracknum:02d}'
            flac = ['flac','-8','-s','-o',f"{path}/{filetrack} {x.replace('/','_')}.flac",\
                    '-T',f"ARTIST={self.rinfo['artist']}",\
                    '-T',f"ALBUM={self.rinfo['title']}",'-T',f"DISCNUMBER={self.rinfo['discnum']}",\
                    '-T',f"TITLE={x}",'-T',f'TRACKNUMBER={tracknum}','-T',f"DATE={self.rinfo['date']}",\
                    f"{temppath}/{self.rinfo['relid']}/audio_{tracknum:02d}.wav"]
            subprocess.run(flac,stdout=sys.stdout,stderr=sys.stderr)
            tracknum += 1
        os.chdir(home)
        shutil.rmtree(temppath)
        print("Done.")
        self.statbar.showMessage("Done.")
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    run = Window()
    sys.exit(app.exec_())
