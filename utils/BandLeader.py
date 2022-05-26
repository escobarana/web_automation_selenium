from selenium.webdriver import Firefox
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from time import sleep, ctime
from collections import namedtuple
from threading import Thread
from os.path import isfile
import csv

BANDCAMP_FRONTPAGE = 'https://bandcamp.com/'
TrackRec = namedtuple('TrackRec', [
    'title',
    'artist',
    'artist_url',
    'album',
    'album_url',
    'timestamp'  # When you played it
])


class BandLeader:
    """
    Class BandLeader:
    - Initialize a headless browser and navigate to bandcamp
    - Keep a list of available tracks
    - Support finding more track
    - Play, pause, and skip tracks
    - Collects structured information about the currently playing track
    - Keep a 'database' of tracks
    - Save and restore that 'database' to and from disk
    """
    def __init__(self, csv_path: str = None):
        self.database_path = csv_path
        self.database = []

        # Load database from disk if possible
        if isfile(self.database_path):
            with open(self.database_path, newline='') as db_file:
                db_reader = csv.reader(db_file)
                next(db_reader)  # To ignore the header line
                self.database = [TrackRec._make(rec) for rec in db_reader]

        # Create a headless browser
        opts = Options()
        opts.add_argument("--headless")
        self.browser = Firefox(options=opts)
        self.browser.get(BANDCAMP_FRONTPAGE)

        # Track list related state
        self._current_track_number = 1
        self.track_list = []
        self.tracks()

        # State for the database
        self.database = []
        self._current_track_record = None

        # The database maintenance thread
        self.thread = Thread(target=self._maintain)
        self.thread.daemon = True  # Kills the thread with the main process dies
        self.thread.start()

        self.tracks()

    def _maintain(self):
        while True:
            self._update_db()
            sleep(20)  # Check every 20 seconds

    # A new save_db() method
    def save_db(self):
        with open(self.database_path, 'w', newline='') as db_file:
            db_writer = csv.writer(db_file)
            db_writer.writerow(list(TrackRec._fields))
            for entry in self.database:
                db_writer.writerow(list(entry))

    # Finally, add a call to save_db() to your database maintenance method
    def _update_db(self):
        try:
            check = (self._current_track_record is not None
                     and self._current_track_record is not None
                     and (len(self.database) == 0
                          or self.database[-1] != self._current_track_record)
                     and self.is_playing())
            if check:
                self.database.append(self._current_track_record)
                self.save_db()

        except Exception as e:
            print('error while updating the db: {}'.format(e))

    def tracks(self):
        """
        Query the page to populate a list of available tracks.
        """

        # Sleep to give the browser time to render and finish any animations
        sleep(1)

        # Get the container for the visible track list
        discover_section = self.browser.find_element(by=By.CLASS_NAME, value='discover-results')
        left_x = discover_section.location['x']
        right_x = left_x + discover_section.size['width']

        # Filter the items in the list to include only those we can click
        discover_items = self.browser.find_elements(by=By.CLASS_NAME, value='discover-item')
        self.track_list = [t for t in discover_items if left_x <= t.location['x'] < right_x]

        # Print the available tracks to the screen
        for (i, track) in enumerate(self.track_list):
            print('[{}]'.format(i + 1))
            lines = track.text.split('\n')
            print('Album  : {}'.format(lines[0]))
            print('Artist : {}'.format(lines[1]))
            if len(lines) > 2:
                print('Genre  : {}'.format(lines[2]))

    def catalogue_pages(self):
        """
        Print the available pages in the catalogue that are presently
        accessible.
        """
        print('PAGES')
        for e in self.browser.find_elements(by=By.CLASS_NAME, value='item-page'):
            print(e.text)
        print('')

    def more_tracks(self, page='next'):
        """
        Advances the catalogue and repopulates the track list. We can pass in a number
        to advance any of the available pages.
        """

        next_btn = [e for e in self.browser.find_elements(by=By.CLASS_NAME, value='item-page')
                    if e.text.lower().strip() == str(page)]

        if next_btn:
            next_btn[0].click()
            self.tracks()

    def play(self, track=None):
        """
        Play a track. If no track number is supplied, the presently selected track
        will play.
        """
        if track is None:
            self.browser.find_element(by=By.CSS_SELECTOR, value='playbutton').click()
        elif type(track) is int and len(self.track_list) >= track >= 1:
            self._current_track_number = track
            self.track_list[self._current_track_number - 1].click()

        sleep(0.5)
        if self.is_playing():
            self._current_track_record = self.currently_playing()

    def play_next(self):
        """
        Plays the next available track
        """
        if self._current_track_number < len(self.track_list):
            self.play(self._current_track_number + 1)
        else:
            self.more_tracks()
            self.play(1)

    def pause(self):
        """
        Pauses the playback
        """
        self.play()

    def is_playing(self):
        """
        Returns `True` if a track is presently playing
        """
        play_btn = self.browser.find_element(by=By.CSS_SELECTOR, value='playbutton')
        return play_btn.get_attribute('class').find('playing') > -1

    def currently_playing(self):
        """
        Returns the record for the currently playing track,
        or None if nothing is playing
        """
        try:
            if self.is_playing():
                title = self.browser.find_element(by=By.CSS_SELECTOR, value='title').text
                album_detail = self.browser.find_element(by=By.CSS_SELECTOR, value='.detail-album > a')
                album_title = album_detail.text
                album_url = album_detail.get_attribute('href').split('?')[0]
                artist_detail = self.browser.find_element(by=By.CSS_SELECTOR, value='.detail-artist > a')
                artist = artist_detail.text
                artist_url = artist_detail.get_attribute('href').split('?')[0]
                return TrackRec(title, artist, artist_url, album_title, album_url, ctime())

        except Exception as e:
            print('there was an error: {}'.format(e))

        return None
