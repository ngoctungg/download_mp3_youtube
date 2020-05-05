from __future__ import unicode_literals
import os
import pickle
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import json
import youtube_dl


class YoutubeMp3:

    def __init__(self,playlist_id,saved_dir):
        super().__init__()
        self.PLAYLIST_ID = playlist_id
        self.DIR = saved_dir
        self.youtube_client = self.get_youtube_client()
        self.playlist_title = self.fetch_playlist_title()

    scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
    # 1 Authorized google api
    def get_youtube_client(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
        api_service_name = "youtube"
        api_version = "v3"
        client_secrets_file = "client_secret_CLIENTID.json"

        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
            client_secrets_file, self.scopes)
        # If local have available credentials
        # If there are not valid, let user login
        if os.path.exists('credentials.pickle'):
            with open('credentials.pickle', 'rb') as credentials_data:
                credentials = pickle.load(credentials_data)
        else:
            credentials = flow.run_console()
            with open('credentials.pickle', 'wb') as credentials_data:
                pickle.dump(credentials, credentials_data)

        youtube = googleapiclient.discovery.build(
            api_service_name, api_version, credentials=credentials)
        return youtube
    
    def fetch_playlist_title(self):
        request = self.youtube_client.playlists().list(
                part='snippet',
                id=self.PLAYLIST_ID,
        )
        response = request.execute()
        title = 'Playlist title'
        for item in response['items']:
            title = item.get('snippet').get('title')
        return title
    # 2 fetch video list from youtube
    def fetch_link_videos(self):
        videos = set()
        next_page_token = None
        # Because each request that get only 50 video
        # and have next page token
        while True:
            request = self.youtube_client.playlistItems().list(
                part='snippet',
                playlistId=self.PLAYLIST_ID,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()
            for video in response.get('items'):
                id = video.get('snippet').get('resourceId').get('videoId')
                link = "https://www.youtube.com/watch?v={}".format(id)
                videos.add(link)

            next_page_token = response.get('nextPageToken')
            if next_page_token is None:
                break     
        return list(videos)
    # 2.1 get list link is already downloaded
    def get_already_downloaded_links(self):
        if os.path.exists(f'{self.DIR}/{self.playlist_title}/links_video.txt'):
            with open(f'{self.DIR}/{self.playlist_title}/links_video.txt', 'r',newline='') as downloaded_links:
                links = []
                for link in downloaded_links.readlines():
                    links.append(link[:-2])
                return links
        return []
    # 3 download video from list
    def download_video(self):
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'progress_hooks':[self.my_hook],
            'outtmpl': f'{self.DIR}/{self.playlist_title}/%(title)s.%(ext)s',
        }

        all_playlist_link = self.fetch_link_videos()
        already_download = self.get_already_downloaded_links()
        # revomve all link is already downloaded
        link_videos = [link for link in all_playlist_link if link not in already_download]

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download(link_videos)
        # Save list videos
        with open(f'{self.DIR}/{self.playlist_title}/links_video.txt', 'w') as downloaded_links:
            for link in all_playlist_link:
                downloaded_links.write(link+'\n')
    
    def my_hook(self,d):
        if d['status'] == 'finished':
            print('Done downloading, now converting ...')

def main():
    playlist_id = 'PLOGQl55w6DU_s7_vjS6yT_AkgZkNbt-dF'
    saved_dir = 'D:\DELL\SpotifySync'
    youtubeMp3 = YoutubeMp3(playlist_id,saved_dir)
    youtubeMp3.download_video()
  


if __name__ == "__main__":
    main()
