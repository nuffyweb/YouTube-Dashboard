import glob, os
from parsel import Selector
import re

def main():    
    os.chdir("./channels")
    channels = []
    for file in glob.glob("*.html"):
        print(file)
        with open(file, "r", encoding='utf-8') as f:
            html_text = f.read()
            # html_selector = Selector(text=html_text)
            # print(html_selector.css('a').get())
            
            x = re.search(r'"https://www.youtube.com/channel/(.+?)"',html_text)
            channel_id = x.group(1)
            # Kludge to fix not everytime properly finded regexp group
            channel_id = re.sub("/videos", "",channel_id)
            channels.append(channel_id)
    with open('./channels/channels.txt', 'w') as f:
        for channel in channels:
            f.write(f"{channel}\n")

if __name__ == '__main__':
    main()