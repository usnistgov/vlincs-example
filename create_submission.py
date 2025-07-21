import os
import cv2
import numpy as np
import random
import pandas as pd
from reid_hota import HOTAReIDEvaluator, HOTAConfig
import zipfile

from utils import generate_random_data, load_results, load_ground_truth

datasets_dict = {
    'debug': [
        'vlincs_MS02_MC0002_MCAM318_2018-03-15_15-00-01',
        'vlincs_MS02_MC0002_MCAM310_2018-03-15_15-00-06'
    ]
}

valid_columns_names = ['frame', 'object_id', 'class_id', 'score', 'x', 'y', 'w', 'h', 'lat', 'long', 'alt']


def validate_submission(results_dirpath: str, dataset_name: str) -> None:
    """
    Validates a submission by checking the presence and content of parquet files.

    Args:
        results_dirpath (str): The directory path containing the submission data.
        dataset_name (str): The name of the dataset being validated. i.e. "debug"

    This function checks if the parquet files in the submission directory match the expected filenames for the given dataset.
    It also validates the column names and data types of the parquet files.
    If any validation checks fail, the function prints an error message and exits with a non-zero status code.
    """
    expected_filenames = datasets_dict[dataset_name]
    parquet_filenames = []
    for filename in os.listdir(results_dirpath):
        filename_no_ext, extension = os.path.splitext(filename)
        if extension == '.parquet':
            parquet_filenames.append(filename_no_ext)

            filepath = os.path.join(results_dirpath, filename)
            try:
                df = pd.read_parquet(filepath)
                # Check column names
                if not set(df.columns).issubset(valid_columns_names):
                    invalid_columns = set(df.columns) - \
                        set(valid_columns_names)
                    print(
                        f"Invalid columns found in {filename}: {invalid_columns}")
                    exit(1)

                for col in valid_columns_names:
                    try:
                        pd.to_numeric(df[col], errors='raise')
                    except ValueError:
                        non_numeric_values = df[col][pd.to_numeric(
                            df[col], errors='coerce').isnull()]
                        print(
                            f"Non-numeric values found in column '{col}' of {filename}: {non_numeric_values.unique()}")
                        exit(1)
            except Exception as e:
                print(f"Error reading or validating {filename}: {str(e)}")
                exit(1)

    # Check if all expected filenames are present
    if set(expected_filenames) != set(parquet_filenames):
        missing_filenames = set(expected_filenames) - set(parquet_filenames)
        unexpected_filenames = set(parquet_filenames) - set(expected_filenames)
        if missing_filenames:
            print(f"Missing parquet files: {missing_filenames}")
        if unexpected_filenames:
            print(f"Unexpected parquet files: {unexpected_filenames}")

        if missing_filenames or unexpected_filenames:
            exit(1)


def compute_metrics(results_dirpath: str, ground_truth_dirpath: str, dataset_name: str):    
    """
    Computes the metrics for the given results for a dataset.
    Args:
        results_dirpath (str): The directory path containing the submission data.
        ground_truth_dirpath (str): The directory path containing the ground truth data.
        dataset_name (str): The name of the dataset being evaluated. i.e. "debug"

    This function loads the results and ground truth data, evaluates the HOTA metrics using both IoU and lat/lon similarity,
    and returns the computed metrics as shown on the vlincs leaderboard. Only a subset of the metrics are reported, to view
    additional metrics, modify the code and access the global, per_video, and per_frame data.
    """
    result_ret = {}

    
    try:
        dataset_videos = datasets_dict[dataset_name]

        results_dict = load_results(dataset_videos, results_dirpath, valid_columns_names)
        ground_truth_dict = load_ground_truth(dataset_videos, ground_truth_dirpath)

        iou_config = HOTAConfig(id_alignment_method='global', similarity_metric='iou')
        iou_evaluator = HOTAReIDEvaluator(n_workers=20, config=iou_config)

        iou_evaluator.evaluate(ground_truth_dict, results_dict)
        iou_global_hota_data = iou_evaluator.get_global_hota_data()
        iou_per_video_hota_data = iou_evaluator.get_per_video_hota_data()
        iou_per_frame_hota_data = iou_evaluator.get_per_frame_hota_data()

        computes_latlon_metrics = False
        latlon_global_hota_data = None
        latlon_per_video_hota_data = None
        latlon_per_frame_hota_data = None

        for df in results_dict.values():
            if 'lat' in df.columns and 'lon' in df.columns:
                if (df['lat'].notna() & df['lat'].ne(0)).any() or (df['lon'].notna() & df['lon'].ne(0)).any():
                    computes_latlon_metrics = True
                    break

        if computes_latlon_metrics:
            latlon_config = HOTAConfig(
                id_alignment_method='global', similarity_metric='latlon')
            latlon_evaluator = HOTAReIDEvaluator(
                n_workers=20, config=latlon_config)
            latlon_evaluator.evaluate(ground_truth_dict, results_dict)

            latlon_global_hota_data = latlon_evaluator.get_global_hota_data()
            latlon_per_video_hota_data = latlon_evaluator.get_per_video_hota_data()
            latlon_per_frame_hota_data = latlon_evaluator.get_per_frame_hota_data()

        metric_list = ['IDF1', 'HOTA']

        for metric_name in metric_list:
            metric_result = iou_global_hota_data[metric_name]
            if isinstance(metric_result, np.ndarray):
                metric_result = float(np.average(metric_result).item())
            else:
                metric_result = float(metric_result)

            result_ret[f'iou_{metric_name}'] = metric_result

            if computes_latlon_metrics:
                metric_result = latlon_global_hota_data[metric_name]
                if isinstance(metric_result, np.ndarray):
                    metric_result = float(np.average(metric_result).item())
                else:
                    metric_result = float(metric_result)
                result_ret[f'latlon_{metric_name}'] = metric_result
            else:
                result_ret[f'latlon_{metric_name}'] = 0
        print(f'Metric results: {result_ret}')
    except Exception as e:
        print(f'Failed to compute metrics: {e}')
    
    return result_ret

def generate_data(args):
    """
    Generates random data for testing purposes.

    Args:
        args: An object containing the necessary arguments.
            - output_dirpath: The directory path where the generated data will be saved.
            - videos_dirpath: The directory path containing the video data.
            - dataset_name: The name of the dataset being generated.            

    This function generates random data based on the provided arguments and saves it to the specified output directory.
    """
    output_dirpath = args.output_dirpath
    videos_dirpath = args.videos_dirpath
    dataset_name = args.dataset_name    

    generate_random_data(output_dirpath, videos_dirpath, dataset_name, datasets_dict)


def package_submission(args):
    """
    Packages the submission data into a zip file that is compatible with the vlincs leaderboard.

    Args:
        args: An object containing the necessary arguments.
            - results_dirpath: The directory path containing the submission data.
            - output_dirpath: The directory path where the packaged submission will be saved.
            - dataset_name: The name of the dataset being submitted.
            - output_name: The name of the output zip file.
            - ground_truth_dirpath: The directory path containing the ground truth data.

    This function validates the submission data, computes metrics if ground truth data is provided,
    and packages the submission data into a zip file. This zip can then be shared using Google Drive 
    for submission into the vlincs leaderboard.
    """
    results_dirpath = args.results_dirpath
    output_dirpath = args.output_dirpath
    dataset_name = args.dataset_name
    output_name = args.output_name
    ground_truth_dirpath = args.ground_truth_dirpath

    validate_submission(results_dirpath, dataset_name)

    if ground_truth_dirpath is not None:
        compute_metrics(results_dirpath, ground_truth_dirpath, dataset_name)

    # Zip up all files
    output_filepath = os.path.join(
        output_dirpath, f"takehome_{dataset_name}_{output_name}.zip")
    with zipfile.ZipFile(output_filepath, 'w') as zip_file:
        for filename in os.listdir(results_dirpath):
            file_path = os.path.join(results_dirpath, filename)
            if os.path.isfile(file_path) and filename.endswith('.parquet'):
                zip_file.write(file_path, filename)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Create Submission')
    subparsers = parser.add_subparsers(dest='command')

    # Subparser for generating random data
    generate_parser = subparsers.add_parser(
        'generate', help='Generate random data')
    generate_parser.add_argument('--output_dirpath', type=str, required=True, help='Path to the output directory')
    generate_parser.add_argument('--videos_dirpath', type=str, required=True, help='Path to the videos directory')
    generate_parser.add_argument('--dataset_name', type=str, required=True, choices=datasets_dict.keys(), help='Name of the dataset')    
    generate_parser.set_defaults(func=generate_data)

    # Subparser for packaging
    package_parser = subparsers.add_parser('package', help='Package the results')
    package_parser.add_argument('--results_dirpath', type=str, required=True, help='Path to the results directory')
    package_parser.add_argument('--output_dirpath', type=str, required=True, help='Path to the output directory')
    package_parser.add_argument('--dataset_name', type=str, required=True, choices=datasets_dict.keys(), help='Name of the dataset')
    package_parser.add_argument('--output_name', type=str, required=True, help='Name of the output submission')
    package_parser.add_argument('--ground_truth_dirpath', type=str, default=None, help='Path to the ground truth directory')
    package_parser.set_defaults(func=package_submission)

    # Subparser for computing metrics
    metrics_parser = subparsers.add_parser('metrics', help='Compute metrics')
    metrics_parser.add_argument('--results_dirpath', type=str, required=True, help='Path to the results directory')
    metrics_parser.add_argument('--ground_truth_dirpath', type=str, required=True, help='Path to the ground truth directory')
    metrics_parser.add_argument('--dataset_name', type=str, required=True, choices=datasets_dict.keys(), help='Name of the dataset')
    metrics_parser.set_defaults(func=lambda args: compute_metrics(args.results_dirpath, args.ground_truth_dirpath, args.dataset_name))

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
