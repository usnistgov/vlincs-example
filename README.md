# Create Submission Script
This branch explains how to submit to the [VLINCS Leaderboard](https://pages.nist.gov/vlincs/) for __take home__ evaluation.

## Overview

The `create_submission.py` script is a utility tool designed to facilitate the creation and packaging of submissions for the VLINCs leaderboard. It provides two primary functions: generating random data for testing purposes and packaging submission data into a compatible zip file. If ground truth data is provided, then metric calculation can be computed.

## Features

*   **Data Generation**: The script can generate random data based on the provided dataset name and video directory.
*   **Submission Packaging**: It validates the submission data, computes metrics if ground truth data is provided, and packages the submission into a zip file.

## Getting Started
* Clone this repository using `git` (or pull before use to get latest updates)
* Download [miniforge](https://github.com/conda-forge/miniforge) (also can be installed using uv or python venv)
* `conda create --name vlincs-example python=3.11`
* `conda activate vlincs-example`
* `pip install -r requirements.txt`

## Usage

The `create_submission.py` script is used via the command line and supports two main commands: `generate` and `package`.

### Generate Random Data

To generate random data, use the `generate` command:

```bash
python create_submission.py generate --output_dirpath <output_directory> --videos_dirpath <videos_directory> --dataset_name <dataset_name>
```

*   `--output_dirpath`: The directory where the generated data will be saved.
*   `--videos_dirpath`: The directory containing the video data.
*   `--dataset_name`: The name of the dataset being generated (e.g., "debug").

### Package Submission

To package the submission data, use the `package` command:

```bash
python create_submission.py package --results_dirpath <results_directory> --output_dirpath <output_directory> --dataset_name <dataset_name> --output_name <output_name> [--ground_truth_dirpath <ground_truth_directory>]
```

*   `--results_dirpath`: The directory containing the submission data.
*   `--output_dirpath`: The directory where the packaged submission will be saved.
*   `--dataset_name`: The name of the dataset being submitted (e.g., "debug").
*   `--output_name`: The name of the output zip file.
*   `--ground_truth_dirpath`: (Optional) The directory containing the ground truth data. If provided, the script will compute metrics.

## Example Usage

1.  Generate random data for the "debug" dataset:

 ```bash
python create_submission.py generate --output_dirpath ./generated_data --videos_dirpath ./videos --dataset_name debug
```

2.  Package the submission data:

```bash
python create_submission.py package --results_dirpath ./submission_data --output_dirpath ./output --dataset_name debug --output_name my_submission --ground_truth_dirpath ./ground_truth
```

By following these steps and using the provided commands, you can effectively utilize the `create_submission.py` script to generate random data and package your submissions for the VLINCs leaderboard.


# System Output Format for Re-identification (ReID) and Geo Location (GeoLoc) Tasks

All objects re-identified by the system for a given input video file should be in the same system output file. If there is no output for a given input video, it means no output from the ReID system.

Due to the data volume, each system output file must be stored as a Parquet file to facilitate efficient storage and retrieval. Parquet stores data in a columnar format. Both the ReID and GeoLoc tasks use the same system output format. However, the scorer will ignore the last three columns for the ReID task. Table 1 lists the columns defined for the system output:

| Column Name | Description                                                                                        | Valid Range                      | Unit   |
| ----------- | ---- | ---- | ------ |
| frame    | A number representing the unique frame number in which the object appears                          | `int >= 0`                       | n/a    |
| object_id   | A number representing the unique identifier of the predicted object                                | `int >= 0`                       | n/a    |
| class_id    | A number denoting the class of the object: 1 for a person, 2 for a vehicle, 3 for a generic object | `int >= 0`                       | n/a    |
| score        | A number between 0 and 1 representing the level of certainty in the prediction                     | `0 <= float <= 1.0`              | n/a    |
| x           | A number representing the x-coordinate of the top-left point of the bounding box in pixels         | `0 <= int <= frame_width`        | pixel  |
| y           | A number representing the y-coordinate of the top-left point of the bounding box in pixels         | `0 <= int <= frame_height`       | pixel  |
| w           | A number representing the width of the bounding box in pixels                                      | `0 <= int <= (frame_width - x)`  | pixel  |
| h           | A number representing the height of the bounding box in pixels                                     | `0 <= int <= (frame_height - y)` | pixel  |
| lat         | A decimal number indicating latitude in the UTM map projection system                              | `-90 <= double <= 90`            | degree |
| long        | A decimal number indicating longitude in the UTM map projection system                             | `-180 <= double <= 180`          | degree |
| alt         | A number indicating the altitude in meters relative to sea level                                   | `float`                          | meter  |

Table 1: System Output Format

The tool described above can be used to generate example data in the parquet format. The `utils.py` file implements the function `generate_random_data`, which shows an example of how to package results into a parquet file.

# Takehome Submission Protocol

Performers must use their own Google Drive account from which they will submit their system output. Before making the first submission, they must register their Google Drive account with NIST. Performers can make submissions once NIST has added their Google Drive account.

Below are the steps. Steps 1-2 are only done once for the duration of the program:

1. Create a Google Drive account (from which a performer/team will use to submit their system output). It is recommended that this drive be ‘My Drive’, not a ‘Shared drive’ because some organizations do not allow sharing a file on their institutional shared drive with an account not on the shared drive.
2. Register the Google Drive account with NIST by emailing [vlincs@nist.gov](mailto:vlincs@nist.gov) with the following requested information:
   - Team name (alphanumeric, no special characters, no spaces) \- the performer may be asked to change their team name if it collides with another team.
   - Google Drive account email
   - Point of contact email address (the performer’s official institutional email)
3. Zip up the system output.
   - Using the `package` command, call the `create_submission.py`, as shown above.
   - The resulting zip should contain only a list of parquet files, named based on each video file. There should be no directory or subdirectory.      
4. Zip file naming:  
   - The zip file must be named with the following format: `takehome_<Dataset Name>_<Submission Name>.zip`
   - By using the `create_submission.py`, the utility will name the zip file according to your parameters as described above.
   - The name of the dataset will correspond to what is distributed and live on the leaderboard, as shown under the `takehome` tab on the [VLINCS Leaderboard](https://pages.nist.gov/vlincs/). The `create_submission.py` will be updated as new datasets are added to the leaderboard.
   - `<Submission Name>` is an alpha-numeric, mnemonic name chosen by the performer  
  For example: `takehome_debug_rev2_MyBestSys.zip`, `rev2_MyBestSys` will be displayed as the submission name on the leaderboard.
5. Upload the zip file to the performer’s Google Drive account.
6. Share the zip file with [vlincs@nist.gov](mailto:vlincs@nist.gov).
7. To make a second submission either overwrite the shared file or unshare the file and share the next. 
   - Only one file can be sahred at a time per dataset.
8. To see the Job Status, go to the leaderboard [https://pages.nist.gov/vlincs/](https://pages.nist.gov/vlincs/). There is a Teams/Jobs table that lists the statuses of all the jobs.


Performers are allowed to make as many submissions as needed every month, but are required to submit once per month during the take home period. Please consult the evaluation schedule in the evaluation plan for the take home period. Each submission will be scored with the results displayed to the leaderboard shortly thereafter.
