#!/usr/bin/env python
# coding: utf-8

# In[43]:


import os
import re

def rename_files(directory):
    processed_files = {}
    new_file_names = []

    for filename in os.listdir(directory):
        if filename.endswith(".mp3"):
            parts = re.split(r'[_\.]', filename)
            company = parts[0]
            year = None
            quarter = None

            for i, part in enumerate(parts):
                if re.match(r'\d{4}', part):
                    year = part
                if part.lower() == 'q' and i + 1 < len(parts) and parts[i + 1].isdigit():
                    quarter = f"{parts[i + 1]}"

            new_name = f"{company}_q_{quarter}_{year}.mp3"
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_name))


# In[44]:


rename_files("E:/test_audio")


# In[45]:


new_file_names = []
for filename in os.listdir("E:/test_audio"):
    if filename.endswith(".mp3"):
        new_file_names.append(filename[:-4])
with open(os.path.join("E:/test_audio", 'file_names.txt'), 'w') as f:
        f.write(str(new_file_names))

