#!/usr/bin/env bash

reference_dir=$1
output_dir=$2
submission_type=$3
leaderboard_name=$4
dataset_name=$5
submission_name=$6

if [ -f ${output_dir}/${leaderboard_name}_${dataset_name}_${submission_name}.zip ]; then
    rm ${output_dir}/${leaderboard_name}_${dataset_name}_${submission_name}.zip
fi

python3 generating_example_scripts/generate_test_submission.py \
    -ref ${reference_dir} \
    -o ${output_dir} \
    -t ${submission_type} \
    -l ${leaderboard_name} \
    -d ${dataset_name} \
    -s ${submission_name}

cd ${output_dir}/${leaderboard_name}_${dataset_name}_${submission_name} && zip ../${leaderboard_name}_${dataset_name}_${submission_name}.zip *
cd .. && rm -rf ${leaderboard_name}_${dataset_name}_${submission_name}