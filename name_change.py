import os
import re

def rename_files(directory):
    """
    Renames all .mp3 files in the specified directory based on a specific naming convention.
    
    The new file name format is: {company}_q_{quarter}_{year}.mp3
    - 'company', 'quarter', and 'year' are extracted from the original file name.
    - 'company' is assumed to be the first part of the file name.
    - 'year' is identified as a four-digit number in the file name.
    - 'quarter' is identified as a digit following the letter 'q' or 'Q'.
    
    Parameters:
    directory (str): The path to the directory containing .mp3 files to be renamed.
    """
    for filename in os.listdir(directory):
        if filename.endswith(".mp3"):
            # Split the filename into parts based on underscores and periods
            parts = re.split(r'[_\.]', filename)
            company = parts[0]
            year = None
            quarter = None

            # Loop through the parts to find year and quarter
            for i, part in enumerate(parts):
                if re.match(r'\d{4}', part):
                    year = part
                if part.lower() == 'q' and i + 1 < len(parts) and parts[i + 1].isdigit():
                    quarter = f"{parts[i + 1]}"

            # Construct the new file name and rename the file
            new_name = f"{company}_q_{quarter}_{year}.mp3"
            os.rename(os.path.join(directory, filename), os.path.join(directory, new_name))


# Call the function to rename files in the specified directory
rename_files("E:/test_audio/audio")

# Create a list of new file names without the .mp3 extension
new_file_names = []
for filename in os.listdir("E:/test_audio/audio"):
    if filename.endswith(".mp3"):
        new_file_names.append(filename[:-4])

# Write the list of new file names to a text file
with open(os.path.join("E:/test_audio", 'file_names.txt'), 'w') as f:
    f.write(str(new_file_names))
