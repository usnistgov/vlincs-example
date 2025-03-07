#! /usr/bin/env python
"""
A python script to generate a random submission. Currently, it only works
for norms and emotions.
"""
import os, glob,sys
import numpy as np
import pandas as pd
import logging
import argparse
import utils.box_augmentation as ba

logger = logging.getLogger('GENERATING')

def generate_submission_dir(output_dir, leaderboard_name, dataset_name, submission_name):

	final_submission_name = "{}_{}_{}".format(leaderboard_name, dataset_name, submission_name)

	output_submission = os.path.join(output_dir, final_submission_name)

	if not os.path.exists(output_submission):
		print('Creating {}'.format(output_submission))
		os.makedirs( os.path.dirname(output_submission + '/'), mode=0o777, exist_ok=False)
	else:
		print('Directory {} already exists, delete it manualy'.format(output_submission))
		sys.exit(0)

	return output_submission

def load_annotation(annotation_file):
    
    GROUND_TRUTH_COLUMNS = ['frame', 'id', 'bb_left', 'bb_top', 'bb_width', 'bb_height', 'conf', 'class', 'visibility']
    ref_df = pd.read_csv(annotation_file, sep=',', names=GROUND_TRUTH_COLUMNS, skiprows=1)

    return ref_df

def modify_columns(df):

    df["lat"] = np.nan
    df["long"] = np.nan
    df["alt"] =	np.nan

    df = df[['frame', 'id', 'bb_left', 'bb_top', 'bb_width', 'bb_height', 'conf', 'class', "lat", "long", "alt"]]

    return df

def generate_perfect_submission(reference_dir, output_dir, leaderboard_name, dataset_name, submission_name, type):

	output_submission = generate_submission_dir(output_dir, leaderboard_name, dataset_name, submission_name)

	for gt_path in glob.glob(os.path.join(reference_dir,"*/gt.txt")):
		output_file_path = os.path.join(output_submission, "{}.parquet".format(os.path.basename(os.path.dirname(gt_path))))
		gt_df = load_annotation(gt_path)
		final_gt_df = modify_columns(gt_df)
		tracker_df = final_gt_df.copy()
		if type == "perfect":
			pass
		elif type == "random":
			ba.swap_labels(tracker_df, 1, 3)
			ba.drop_detections(tracker_df, 0.25)
			ba.add_random_boxes(tracker_df)
			ba.inject_localization_error(tracker_df, 0.5)
			ba.inject_label_swaps(tracker_df, 0.5)

		final_tracker_df = tracker_df.rename(columns={'frame': 'frame_id', 'id': 'object_id', 'bb_left': 'x', 'bb_top': 'y', 'bb_width': 'w', 'bb_height': 'h', 'class': 'class_id'})
		final_tracker_df.to_parquet(output_file_path, index=False)

def main():
	parser = argparse.ArgumentParser(description='Generate a random norm/emotion submission')
	parser.add_argument('-ref','--reference-dir', type=str, required=True, help='Reference directory')
	parser.add_argument("-o", "--output_dir", type=str, required=True, help="Output directory")
	parser.add_argument("-l", "--leaderboard-name", type=str, required=True, help="Leaderboard name")
	parser.add_argument("-d", "--dataset-name", type=str, required=True, help="Dataset name")
	parser.add_argument("-s", "--submission-name", type=str, required=True, help="Submission name")
	parser.add_argument('-t','--type', type=str, required=True, choices=['perfect','random'], help='Choose submission type')

	args = parser.parse_args()

	generate_perfect_submission(args.reference_dir, args.output_dir, args.leaderboard_name, args.dataset_name, args.submission_name, args.type)

if __name__ == '__main__':
	main()