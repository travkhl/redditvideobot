import praw, time, os, re, subprocess
from gtts import gTTS
from html2image import Html2Image
from mutagen.mp3 import MP3
from moviepy.editor import *

fps = 10
html_front = '<html style="background-color: #1a1a1b;"><iframe id="reddit-embed"src="https://www.redditmedia.com'
html_back = '?depth=1&amp;ref_source=embed&amp;ref=share&amp;embed=true&amp;theme=dark" sandbox="allow-scripts allow-same-origin allow-popups" style="border: none; transform-origin: 0% 0%; transform: scale(2);" scrolling="no" width="500" height="500"></iframe></html>'
hti = Html2Image()
subreddit = "askreddit"
language = "en"
new_vid = True

reddit = praw.Reddit(
    client_id="kJjJqx9JWm6eM0QsuyZ3Pw", #put your reddit client_id here
    client_secret="cKNzYrnRYmXM2Eni-aHi60iGQZdUoQ", #put your reddit client secrets here
    password="",
    user_agent="reditmoment", #put your reddit user agent here
    username="",
)


def main():
    """parameters can be tweaked here, (number of posts in a video, number of comments per post, number of replies per comment chain, subreddit to draw from)"""
    dic_list = extract_video_contents(1, 4, 0, subreddit) #maximum uploads per day is 6
    for video_dic in dic_list:
        create_images(video_dic)
        #clean_text(video_dic)
        create_audio(video_dic)
        save_location = str(time.time()).split('.')[0] + ".mp4"
        title = f"{video_dic[list(video_dic.keys())[0]]['title']} (r/{subreddit}) #shorts"
        video = create_video(video_dic, save_location)
        add_audio(video_dic, video, save_location)
        upload(save_location, title)
        cleanup(video_dic)


def extract_video_contents(posts_num = 10, comments_num = 5, replies_num = 1, sub=subreddit):
    """collects [posts] posts and [comments] comments per post"""
    if not new_vid:
        return
    dic_list = []
    fh = open("log.csv", "a+")
    posts = reddit.subreddit(sub).top(time_filter="day", limit=posts_num)
    for post in posts:
        if post.permalink not in fh.read():
            video_dic = {}
            fh.write(f"{post.permalink},")
            video_dic.update({post.permalink: {"title": post.title,
                                               "id": post,
                                               "embed": f"{html_front}{post.permalink}{html_back}",
                                               "comments": []}})
            for comment in post.comments[:comments_num]:
                video_dic[post.permalink]["comments"].append({"id": comment,
                                                              "embed": f"{html_front}{comment.permalink}{html_back}",
                                                              "body": comment.body})
            dic_list.append(video_dic)

    fh.close()
    return dic_list


def create_images(dic):
    '''makes images from the posts and comments in dic'''
    for post in dic:
        html_str_to_png(dic[post]["embed"], f'Q_{dic[post]["id"]}.png')
        dic[post].update({"image_location": f'Q_{dic[post]["id"]}.png'})
        for comment in dic[post]["comments"]:
            html_str_to_png(comment["embed"], f'C_{dic[post]["id"]}{comment["id"]}.png')
            comment.update({"image_location": f'C_{dic[post]["id"]}{comment["id"]}.png'})


def html_str_to_png(html, save_location):
    hti.screenshot(html_str=html, save_as=f"{save_location}", size=(1000, 1500))


def create_audio(dic):
    '''makes TTS audio from text of posts and comments in dic'''
    for post in dic:
        gTTS(text=dic[post]["title"], lang=language, slow=False).save(f"Q_{dic[post]['id']}.mp3")
        dic[post].update({"audio_location": f"Q_{dic[post]['id']}.mp3"})
        dic[post].update({"duration": float(MP3(dic[post]["audio_location"]).info.length)})
        for comment in dic[post]["comments"]:
            gTTS(text=comment["body"], lang=language, slow=False).save(f"CA_{dic[post]['id']}{comment['id']}.mp3")
            comment.update({"audio_location": f"CA_{dic[post]['id']}{comment['id']}.mp3"})
            comment.update({"duration": float(MP3(comment["audio_location"]).info.length)})


def create_video(dic, save_location):
    '''stitches together images saved in dic into a video of length sum(image durations))'''
    clips = []
    for post in dic:
        clips.append(ImageClip(dic[post]["image_location"]).set_duration(dic[post]["duration"]))
        for comment in dic[post]["comments"]:
            clips.append(ImageClip(comment["image_location"]).set_duration(comment["duration"]))
    video = concatenate_videoclips(clips)
    return video


def add_audio(dic, video, save_location):
    """takes audio files and combines them into one clip"""
    video_clip = video
    length = 0
    audio_clips = []
    for post in dic:
        audio_clips.append(AudioFileClip(dic[post]["audio_location"]))
        length += dic[post]["duration"]
        for comment in dic[post]["comments"]:
            audio_clips.append(AudioFileClip(comment["audio_location"]))
            length += comment["duration"]
    combined_audio = concatenate_audioclips(audio_clips)
    video_clip.audio = combined_audio
    video_clip.write_videofile(save_location, fps=fps)


def cleanup(dic):
    """deletes all the asset files"""
    for post in dic:
        os.remove(dic[post]["image_location"])
        os.remove(dic[post]["audio_location"])
        for comment in dic[post]["comments"]:
            os.remove(comment["image_location"])
            os.remove(comment["audio_location"])


def clean_text(dic):
    """removes certain things from the test so the TTS won't read it"""

def upload(save_location, title):
    """uploads the video"""
    try:
        subprocess.run(
            f'python upload_video.py '
            f'--file="{save_location}" '
            f'--title="{title}" ' #edit your title here
            f'--description="" ' #put your description here
            f'--keywords="{subreddit}, reddit" ' #edit your keywords here
            f'--category="20" ' #choose your category here
            f'--privacyStatus="private"' #change your privacy status here
        )
        os.replace(save_location, f"uploaded/{save_location}")
    except Exception as e:
        print(f"{title} not uploaded:\n{e}")



if __name__ == "__main__":
    main()
