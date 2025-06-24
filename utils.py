"""
This module provides functions for loading ground truth data and results,
generating random data, and performing various utility tasks.

It includes functions to load ground truth data and results from parquet files,
get video statistics, find missing files, and generate random data for testing purposes.

Functions:
    load_ground_truth: Loads ground truth data from parquet files.
    load_results: Loads results from parquet files.
    get_video_stats: Retrieves video statistics such as frame count, width, and height.
    find_missing_files: Finds missing files by comparing a reference list with a list of filepaths.
    generate_random_data: Generates random data for testing purposes.

"""
import os
import cv2
import os
import cv2
import numpy as np
import random
import pandas as pd



def load_ground_truth(video_name_list: list[str], ground_truth_dirpath: str) -> dict[str, pd.DataFrame]:
    """
    Loads ground truth data from parquet files for a list of video names.

    Args:
        video_name_list (list): A list of video names.
        ground_truth_dirpath (str): The directory path where ground truth files are stored.

    Returns:
        dict: A dictionary where keys are video names and values are pandas DataFrames containing ground truth data.

    Raises:
        SystemExit: If a ground truth file is not found for a video.
    """
    ground_truth = {}

    for video_name in video_name_list:
        video_ground_truth_filepath = os.path.join(ground_truth_dirpath, video_name, 'gt.parquet')
        if os.path.exists(video_ground_truth_filepath):
            ground_truth[video_name] = pd.read_parquet(video_ground_truth_filepath)
        else:
            print(f'Failed to find video ground truth file: {video_ground_truth_filepath}')
            exit(1)
    return ground_truth


def load_results(video_name_list: list[str], results_dirpath: str, column_names: list[str] = None) -> dict[str, pd.DataFrame]:
    """
    Loads results from parquet files for a list of video names.

    Args:
        video_name_list (list): A list of video names.
        results_dirpath (str): The directory path where result files are stored.
        column_names (list, optional): Column names to use if a result file is not found. Defaults to None.

    Returns:
        dict: A dictionary where keys are video names and values are pandas DataFrames containing result data.
    """
    results = {}
    for video_name in video_name_list:
        video_result_filepath = os.path.join(results_dirpath, f'{video_name}.parquet')
        if os.path.exists(video_result_filepath):
            results[video_name] = pd.read_parquet(video_result_filepath)
        else:
            print(f'Failed to find video result file: {video_result_filepath}')
            results[video_name] = pd.DataFrame(columns=column_names)
    return results


def get_video_stats(video_path: str) -> tuple[int, int , int]:
    """
    Retrieves video statistics such as frame count, width, and height.

    Args:
        video_path (str): The path to the video file.

    Returns:
        tuple: A tuple containing the frame count, width, and height of the video.
    """
    cap = cv2.VideoCapture(video_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    return frame_count, width, height


def find_missing_files(reference_list: list[str], filepath_list: list[str]) -> set[str]:
    """
    Finds missing files by comparing a reference list with a list of filepaths.

    Args:
        reference_list: A list of filenames to compare against.
        filepath_list: A list of filepaths to extract filenames from.

    Returns:
        A set of filenames that are present in the reference list but not in the filepath list.
    """
    # Extract filenames from filepaths
    filenames = [os.path.basename(filepath) for filepath in filepath_list]

    # Convert lists to sets for efficient comparison
    reference_set = set(reference_list)
    filename_set = set(filenames)

    # Find items in reference_list that are not in filenames
    missing_files = reference_set.difference(filename_set)

    return missing_files


def generate_random_data(output_dirpath: str, videos_dirpath: str, dataset_name: str, datasets_dict: dict[str, list[str]]) -> None:
    """
    Generates random data for testing purposes. The data is saved into the output_dirpath,
    and creates one random result data per video for a given dataset_name.

    Args:
        output_dirpath: The directory path where the generated parquet files will be saved.
        videos_dirpath: The directory path where the video files are stored.
        dataset_name: The name of the dataset to generate random data for.
        datasets_dict: A dictionary containing the list of video names for each dataset.        

    Returns:
        None
    """
    # Number of random subjects/people into the data
    num_subjects = 10
    valid_extensions = ['.avi', '.mp4']

    video_names = datasets_dict[dataset_name]

    video_filepaths = []

    # Iterate through video directories and build list of valid video files
    for video_dir in os.listdir(videos_dirpath):
        video_dirpath = os.path.join(videos_dirpath, video_dir)

        for video_file in os.listdir(video_dirpath):
            filename, file_extension = os.path.splitext(video_file)

            if file_extension in valid_extensions:
                if filename in video_names:
                    video_filepaths.append(
                        os.path.join(video_dirpath, video_file))

    # Load each video file to get number of frames to randomize the output
    if len(video_names) != len(video_filepaths):
        print(
            f'Error the number of videos ({len(video_filepaths)}) does not match the expected number of videos ({len(video_names)})')
        print(
            f'Missing files: {find_missing_files(video_names, video_filepaths)}')
        exit(1)

    # Generate random data
    for video_filepath in video_filepaths:
        # load the video to get frame metadata
        frame_count, width, height = get_video_stats(video_filepath)

        data = []
        track_ids = list(range(num_subjects))

        for frame in range(frame_count):
            num_subjects_in_frame = np.random.randint(0, num_subjects)
            selected_track_ids = random.sample(track_ids, num_subjects_in_frame)

            for track_id in selected_track_ids:
                class_id = 0
                score = np.random.uniform(0, 1)

                # Generate random bbox
                x = np.random.randint(0, width)
                y = np.random.randint(0, height)
                w = np.random.randint(0, width - x)
                h = np.random.randint(0, height - y)

                # Generate random lat/long/alt
                lat = np.random.randint(-180, 180)
                long = np.random.randint(-180, 180)
                alt = np.random.uniform(-1000, 1000)

                data.append({
                    'frame': frame,
                    'object_id': track_id,
                    'class_id': class_id,
                    'score': score,
                    'x': x,
                    'y': y,
                    'w': w,
                    'h': h,
                    'lat': lat,
                    'long': long,
                    'alt': alt
                })

        df = pd.DataFrame(data)
        filename = os.path.splitext(os.path.basename(video_filepath))[0]

        output_filepath = os.path.join(output_dirpath, f'{filename}.parquet')
        # Ensure output directory exists
        os.makedirs(output_dirpath, exist_ok=True)
        df.to_parquet(output_filepath, index=False)
        print(f'Generated Parquet file for {filename} at {output_filepath}')
