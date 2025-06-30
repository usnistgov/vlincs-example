# VLINCS Take-Home Evaluation Submission Example

This branch provides an example for submitting to the **[VLINCS Leaderboard](https://pages.nist.gov/vlincs/)** as part of the **Take-Home** Evaluation. It includes guidance and resources specific to the Take-Home submission process. 

For the main branch of the VLINCS Example repository, which supports the **NIST Video LINCS Evaluation** more broadly, please visit: [https://github.com/usnistgov/vlincs-example/](https://github.com/usnistgov/vlincs-example/).

## Table of Contents<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
      <ul>
        <li><a href="#1-overview">1. Overview</a>
      </li>
        <li><a href="#2-getting-started">2. Getting Started</a>
      </li>
        <li><a href="#3-feature-and-usage">3. Feature and Usage</a>
      <ul>
        <li><a href="#31-generate-random-data">3.1 Generate Random Data</a>
      </li>
        <li><a href="#32-package-submission">3.2 Package Submission</a>
      </li>
        <li><a href="#33-compute-metrics">3.3 Compute Metrics</a>
      </li>
      </ul>
        <li><a href="#4-takehome-submission-protocol">4. Takehome Submission Protocol</a>
      </li>
        <li><a href="#5-appendix">5. Appendix</a>
      <ul>
        <li><a href="#51-system-output-format">5.1 System Output Format</a>
      </li>
    </ul></ul>
    </li>
  </ol>
</details>

## 1. Overview

The `create_submission.py` script is a utility designed to streamline the process of generating, validating, and packaging system outputs for the **[VLINCS Leaderboard](https://pages.nist.gov/vlincs/)**. It offers three core functionalities:

- **Random Data Generation**: Useful for testing and debugging pipelines.
- **Submission Packaging**: Validates outputs and prepares a properly structured `.zip` file for leaderboard submission.
- **Metric Calculation**: If ground truth data is available, performance metrics will be computed using the `reid_hota` library.

This tool supports standardized workflows, ensuring compatibility with NIST’s evaluation infrastructure and reproducibility of results.

---

## 2. Getting Started

To set up the environment and begin using the tool:

### 2.1 Clone the Repository

```bash
# Clone this repository using `git` 
git clone https://github.com/usnistgov/vlincs-example.git
cd vlincs-example
git checkout takehome

# Or pull before use to get latest updates
git pull  # if you've already cloned it
```

### 2.2 Set Up the Environment

Using [Miniforge](https://github.com/conda-forge/miniforge) (recommended), or any Python environment manager like `uv` or `venv`:

```bash
# Create and activate the environment
conda create --name vlincs-example python=3.11
conda activate vlincs-example

# Install dependencies
pip install -r requirements.txt
```

---

## 3. Features and Usage

The script supports three main subcommands:

- `generate`: Creates synthetic data for testing.
- `package`: Validates and archives results for submission.
- `metrics`: Computes performance metrics given ground truth.

### 3.1 Generate Random Data
#### 3.1.1 Description
This command generates synthetic system outputs, simulating realistic data for a given dataset. This is particularly helpful for debugging or validating the end-to-end submission pipeline.

> The output conforms to the **System Output Format** described in [Appendix 5.1](#51-system-output-format).

#### 3.1.2 Usage

To generate random data, use the `generate` command:

```bash
python create_submission.py generate --output_dirpath <output_directory> --videos_dirpath <videos_directory> --dataset_name <dataset_name>
```
* `--output_dirpath`: Directory where generated files will be stored.
* `--videos_dirpath`: Path to the input videos used for synthetic output generation.
* `--dataset_name`: Dataset identifier (e.g., `debug`, `meva-rev2`, etc.).

#### 3.1.3 Example
Generate random data for the "debug" dataset:
```bash
python create_submission.py generate --output_dirpath ./generated_data --videos_dirpath ./videos --dataset_name debug
```
### 3.2 Package Submission
#### 3.2.1 Description
This command validates a submission, optionally computes evaluation metrics, and packages the output files into a ZIP archive suitable for leaderboard submission.

#### 3.2.2 Usage
To package the submission data, use the `package` command:

```bash
python create_submission.py package --results_dirpath <results_directory> --output_dirpath <output_directory> --dataset_name <dataset_name> --output_name <output_name> [--ground_truth_dirpath <ground_truth_directory>]
```
* `--results_dirpath`: Directory containing the system output files.
* `--output_dirpath`: Directory where the `.zip` file will be saved.
* `--dataset_name`: Dataset identifier.
* `--output_name`: Desired name for the ZIP file (without `.zip` extension).
* `--ground_truth_dirpath` *(optional)*: Path to the ground truth data. Required for metric computation.

### 3.3 Compute Metrics

#### 3.3.1 Description
When ground truth data is available, this command computes evaluation metrics for the system output using the `reid_hota` library. The results reflect a subset of metrics displayed on the official leaderboard.

> For the complete list of supported metrics, refer to the [reid_hota GitHub repository](https://github.com/usnistgov/reid_hota) and the [documentation](https://pypi.org/project/reid-hota/).

#### 3.3.2 Usage
To test computing metrics for the submission data, use the `metrics` command (requires access to ground truth):

```bash
python create_submission.py metrics --results_dirpath <results_directory> --ground_truth_dirpath <ground_truth_directory> --dataset_name <dataset_name>
```
* `--results_dirpath`: Path to your system's result files.
* `--ground_truth_dirpath`: Path to the ground truth data.
* `--dataset_name`: Identifier for the dataset being evaluated.

#### 3.3.3 Example
```bash
python create_submission.py metrics --results_dirpath ./submission_data --ground_truth_dirpath ./ground_truth --dataset_name debug
```
---
## 4. Takehome Submission Protocol
For the take-home evaluation, performers must submit their system output via Google Drive using the process described below. Submissions must follow the naming and formatting conventions outlined to ensure compatibility with NIST’s evaluation infrastructure.

**Step 1. Account Setup (One-Time Only)**

1. **Create a Google Drive account**

   - Use "My Drive" (not a Shared Drive) to avoid permission issues.

2. **Register with NIST**

   - Email `vlincs@nist.gov` with the following:
     - **Team Name**: Alphanumeric only.
     - **Google Drive Account Email**
     - **Point of Contact Email**: Official institutional email.

**Step 2. Submission**

1. **Prepare Output Files**

   - Archive `.parquet` files only (no folders).

   ```bash
   zip MyBestSys.zip *.parquet
   ```

2. **Rename Archive**

   ```
   <LeaderboardName>_<DatasetName>_<SubmissionName>.zip
   ```

   Example:

   ```bash
   mv MyBestSys.zip takehome-ta1_meva-rev2_MyBestSys.zip
   ```

3. **Upload & Share**

   - Upload to your registered Google Drive.
   - Share the file with `vlincs@nist.gov`.
   - Unshare the file once the Job Status shows “None”.

> Performers may submit once per month during the self-test period. Contact NIST for the full evaluation schedule.

---

## 5. Appendix

### 5.1 System Output Format
All objects re-identified by the system for a given input video must be included in a single corresponding system output file. If there is no output for a particular video, it indicates that the ReID system did not produce any results.

To handle large volumes of data efficiently, each system output file must be stored in Parquet format (`.parquet` file), which uses a columnar storage structure optimized for performance and scalability. This format is shared across both the **Re-identification (ReID)** and **Geo Location (GeoLoc)** tasks. However, for the ReID task, the last three columns are ignored by the scorer.

Output guidelines:
- One Parquet file per input video.
- If there is no output, no file should be generated.
- The same output format is used for both ReID and GeoLoc tasks, with task-specific interpretation by the scorer.

Table 1 lists the columns defined in the system output for both **ReID** and **GeoLoc** tasks:

| Column Name | Description | Valid Range | Unit |
|-------------|-------------|--------------|------|
| `frame_id`  | a unique identifier assigned to a single video frame | `uint (≥ 0)` | n/a |
| `object_id` | a unique identifier assigned to a specific detected entity—such as a person, vehicle, or object | `uint (≥ 0)` | n/a |
| `x`         | the x-coordinate of the top-left corner of the rectangular bounding box in pixels | `uint (0 to frame_width)` | pixel |
| `y`         | the y-coordinate of the top-left corner of the rectangular bounding box in pixels | `uint (0 to frame_height)` | pixel |
| `w`         | the width of the bounding box in pixels | `uint (0 to frame_width - x)` | pixel |
| `h`         | the height of the bounding box in pixels | `uint (0 to frame_height - y)` | pixel |
| `confidence`| a number between 0 and 1 representing the level of certainty in the prediction, with 0 as complete uncertainty and 1 as absolute certainty. | `float (0.0 to 1.0)` | n/a |
| `class_id`  | a number denoting the class of the object: <br>1 for a person <br>2 for a vehicle <br>3 for a generic object that is neither a person nor a vehicle | `uint (≥ 0)` | n/a |
| `lat`       | the angular distance north or south of the Earth’s equator, measured in degrees and ranging from -90° to 90°, where 0° represents the equator, positive values indicate locations north of the equator, and negative values indicate locations south of the equator. Latitude specifies a location’s position on the globe along the north-south axis. | `double (-90.0 to 90.0)` | degree |
| `long`      | the angular distance east or west of the Prime Meridian, measured in decimal degrees from -180° to 180°, where 0° represents the Prime Meridian, positive values indicate locations to the east, and negative values indicate locations to the west. Longitude defines a location’s position along the east-west axis of the globe. | `double (-180.0 to 180.0)` | degree |
| `alt`       | the height of an object relative to sea level, measured in meters. Positive values indicate elevation above sea level, while negative values indicate positions below sea level. | `float (unbounded)` | meter |

**Table 1: System Output Format for both ReID and GeoLoc tasks**

The tool described above can be used to generate example data in Parquet format. The `utils.py` file includes the `generate_random_data` function, which demonstrates how to package results into a Parquet file.

📌 **Note**: This standardized format ensures efficient data handling and maintains compatibility with the leaderboard scoring system.