import os
import hashlib
import json
import concurrent.futures


# Specify the directory to scan
directory = 'train_wav'
max_workers = 10  # Change this value to control the number of threads used


# Initialize an empty dictionary to store the file data
file_data_dict = {}


# Define a function to calculate the hash value for a file
def calculate_hash(file_path):
    with open(file_path, "rb") as f:
        file_bytes = f.read()
        hash_value = hashlib.sha256(file_bytes).hexdigest()
    return (file_path, hash_value)


# Use a list comprehension to generate the file paths
audio_files = [os.path.join(root, filename)
               for root, dirs, files in os.walk(directory)
               for filename in files
               if filename.endswith(('.mp3', '.wav'))]


# Calculate the hash of each audio file in parallel
with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
    futures = [executor.submit(calculate_hash, file_path) for file_path in audio_files]
    for future in concurrent.futures.as_completed(futures):
        file_path, hash_value = future.result()
        if hash_value in file_data_dict:
            file_data_dict[hash_value].append({"name": os.path.basename(file_path), "filepath": file_path})
        else:
            file_data_dict[hash_value] = [{"name": os.path.basename(file_path), "filepath": file_path}]


# Serialize the dictionary to a JSON file
matching_files = [{"hash": k, "filenames": v} for k, v in file_data_dict.items() if len(v) > 1]
with open("matching_files.json", "w") as f:
    json.dump(matching_files, f, indent=4, sort_keys=True)


print('Matching files saved to matching_files.json')