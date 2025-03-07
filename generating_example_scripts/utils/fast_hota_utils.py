import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment

import time
from multiprocessing import Pool

# Suppress the SettingWithCopyWarning
pd.options.mode.chained_assignment = None


from utils.data_obj import CostMatrixData, VideoFrameData, FrameExtractionInputData, HOTA_DATA, HOTA_DATA_PRECURSOR



def compute_cost_per_video_per_frame(ref_dfs: dict[str, pd.DataFrame], comp_dfs: dict[str, pd.DataFrame], n_workers:int=0, class_id: int = None) -> list[CostMatrixData]:
    # video ids are unique as they are keys in the input dictionary
    unique_video_ids = list(set(ref_dfs.keys()).union(set(comp_dfs.keys())))
    
    # ************************************
    # Convert the list[pd.DataFrame] into a list[FrameExtractionInputData]
    # For every dataframe, create a FrameExtractionInputData dataclass which stores just the boxes and ids which exist in that frame
    # ************************************
    st = time.time()
    print('Extracting per-frame boxes for every dataframe')
    # this flattens a list of parameter calls to gisa.extract_per_frame_data into a single 1D list of inputs packaged into a FrameExtractionInputData dataclass
    frame_extraction_work_queue = _linearize_FrameExtractionInputData(ref_dfs, comp_dfs, unique_video_ids)
    # perform the calls to gisa.extract_per_frame_data to extract per-frame data
    video_frame_data = list()
    # perform the work to prepare the cost matrix
    if n_workers > 1 and len(frame_extraction_work_queue) > 1:
        print('  pool working on extract_per_frame_data')
        with Pool(processes=n_workers) as pool:
            results = pool.map(extract_per_frame_data, frame_extraction_work_queue, class_id)
    else:
        print('  single threaded extract_per_frame_data')
        results = [extract_per_frame_data(dat, class_id) for dat in frame_extraction_work_queue]
    for res in results:
        video_frame_data.extend(res)
    print(f"Per-Frame data extraction took: {time.time() - st} seconds")


    # ************************************
    # Convert the list[FrameExtractionInputData] into a list[CostMatrixData]
    # For every FrameExtractionInputData, compute the cost matrix for id assignment within that frame
    # the CostMatrixData stores the video_id and frame number for later reference
    # ************************************
    st = time.time()
    print('Computing cost matrices for every frame')
    # using the per-frame data video_frame_data, compute a cost matrix for each frame
    id_similarity_per_video = dict()
    if n_workers > 1:
        with Pool(processes=n_workers) as pool:
            results = pool.map(compute_id_alignment_similarity, video_frame_data)
    else:
        results = [compute_id_alignment_similarity(dat) for dat in video_frame_data]
    # unpack the sim_results list into a dict of dict
    for res in results:
        if res.video_id not in id_similarity_per_video:
            id_similarity_per_video[res.video_id] = dict()
        id_similarity_per_video[res.video_id][res.frame] = res
    print(f"Per Frame cost calculation took: {time.time() - st} seconds")

    return id_similarity_per_video
    


def jaccard_cost_matrices(matrices_list: list[CostMatrixData]) -> CostMatrixData:
    # Get unique IDs across all matrices
    ref_ids = np.unique(np.concatenate([
        data.i_ids for data in matrices_list
    ]))
    comp_ids = np.unique(np.concatenate([
        data.j_ids for data in matrices_list
    ]))

    ref_lookup = {id_val: idx for idx, id_val in enumerate(ref_ids)}
    comp_lookup = {id_val: idx for idx, id_val in enumerate(comp_ids)}

    # Initialize output matrices with zeros
    shape = (len(ref_ids), len(comp_ids))
    i_counts = np.zeros(shape[0])
    j_counts = np.zeros(shape[1])
    cost_sum = np.zeros(shape, dtype=np.float64)

    # Process each CostMatrixData
    for data in matrices_list:
        ref_idx = np.fromiter((ref_lookup[id_] for id_ in data.i_ids), dtype=int)
        comp_idx = np.fromiter((comp_lookup[id_] for id_ in data.j_ids), dtype=int)

        i_counts[ref_idx] += 1
        j_counts[comp_idx] += 1

        # get a copy of the matrix, normalize the cost values and add to the sum
        cm = normalize_cost_matrix(data.cost_matrix.copy())
        cost_sum[ref_idx[:, np.newaxis], comp_idx[np.newaxis, :]] += cm

    cost_matrix = cost_sum / (i_counts[:, np.newaxis] + j_counts[np.newaxis, :] - cost_sum)

    return CostMatrixData(i_ids=ref_ids, j_ids=comp_ids, cost_matrix=cost_matrix, video_id=None, frame=None)


def compute_id_alignment_similarity(dat: VideoFrameData) -> CostMatrixData:
    """
    Compute alignment costs between reference and comparison frames.
    Optimized for speed using dictionary lookups and np.ix_.
    """

    f_idx = dat.col_names.index('frame')
    id_idx = dat.col_names.index('id')
    # Quick validation using values access
    ref_frames = np.unique(dat.ref_np[:, f_idx])
    comp_frames = np.unique(dat.comp_np[:, f_idx])
    if len(comp_frames) == 0:
        ref_ids = dat.ref_np[:, id_idx]
        comp_ids = dat.comp_np[:, id_idx]
        cost_matrix = np.zeros((len(ref_ids), len(comp_ids)))
        return CostMatrixData(i_ids=ref_ids, j_ids=comp_ids, cost_matrix=cost_matrix, video_id=dat.video_id, frame=dat.frame)
    assert len(ref_frames) == 1 and len(comp_frames) == 1
    assert ref_frames[0] == comp_frames[0]

    # This is reference data, it should never happen, but ... you never know
    # Check for duplicate IDs in reference data
    ref_ids_t = dat.ref_np[:, id_idx]
    unique_ref_ids, ref_counts = np.unique(ref_ids_t, return_counts=True)
    if np.max(ref_counts) > 1:
        duplicate_ids = unique_ref_ids[ref_counts > 1]
        raise ValueError(f'Ground-truth has duplicate IDs in frame {dat.frame}: {duplicate_ids}')

    # TODO how do we want to handle duplicate IDs? and reporting back to performers
    # Check for duplicate IDs in comparison data
    comp_ids_t = dat.comp_np[:, id_idx]
    unique_comp_ids, comp_counts = np.unique(comp_ids_t, return_counts=True)
    if np.max(comp_counts) > 1:
        duplicate_ids = unique_comp_ids[comp_counts > 1]
        raise ValueError(f'Tracker predictions have duplicate IDs in frame {dat.frame}: {duplicate_ids}')

    # Get unique IDs once
    ref_ids = dat.ref_np[:, id_idx]
    comp_ids = dat.comp_np[:, id_idx]

    # Direct numpy array creation for bounding boxes
    box_idx = [dat.col_names.index(col) for col in ['bb_left', 'bb_top', 'bb_width', 'bb_height']]
    bb1 = dat.ref_np[:, box_idx]
    bb2 = dat.comp_np[:, box_idx]

    # Create cost matrix and compute IOUs
    cost_matrix = calculate_box_ious(bb1, bb2, box_format='xywh')

    return CostMatrixData(i_ids=ref_ids, j_ids=comp_ids, cost_matrix=cost_matrix, video_id=dat.video_id, frame=dat.frame)


def extract_per_frame_data(dat: FrameExtractionInputData, class_id: int = None) -> list[VideoFrameData]:
    ref_df = dat.ref_df
    comp_df = dat.comp_df

    cols = ref_df.columns.tolist()

    if class_id is not None:
        # only keep the relevant class
        ref_df = ref_df[ref_df['class'] == class_id]
        comp_df = comp_df[comp_df['class'] == class_id]
    
    # Group by frame
    # return pd.api.typing.DataFrameGroupBy
    ref_frames_df = ref_df.groupby('frame')
    comp_frames_df = comp_df.groupby('frame')

    k1 = set(ref_frames_df.groups.keys())
    k2 = set(comp_frames_df.groups.keys())
    shared_unique_frames = list(k1 | k2)  # union of keys
    shared_unique_frames.sort()

    dat_list = list()
    for frame in shared_unique_frames:
        if frame in ref_frames_df.groups:
            ref_frame_df = ref_frames_df.get_group(frame)
        else:
            ref_frame_df = pd.DataFrame(columns=cols)
        if frame in comp_frames_df.groups:
            comp_frame_df = comp_frames_df.get_group(frame)
        else:
            comp_frame_df = pd.DataFrame(columns=cols)

        # package into dataclass, adding class information
        dat = VideoFrameData(ref_frame_df.values, comp_frame_df.values, dat.video_id, int(frame), class_id, cols)
        dat_list.append(dat)
    return dat_list


def calculate_box_ious(bboxes1: np.ndarray, bboxes2: np.ndarray, box_format='xywh'):
    """
    Calculates the IOU (intersection over union) between two arrays of boxes using vectorized operations.

    Args:
        bboxes1: Array of shape (N, 4) containing first set of bounding boxes
        bboxes2: Array of shape (M, 4) containing second set of bounding boxes
        box_format: Format of input boxes - either 'xywh' (x, y, width, height) or
                   'x0y0x1y1' (x_min, y_min, x_max, y_max) (alias 'xyxy')
        normalize: Whether to normalize IOUs

    Returns:
        Array of shape (N, M) containing pairwise IOU values
    """
    # Convert to x0y0x1y1 format if needed - avoid unnecessary operations
    if box_format == 'xywh':
        # Create views instead of copies where possible
        boxes1 = np.empty_like(bboxes1)
        boxes2 = np.empty_like(bboxes2)

        # Compute coordinates directly
        np.copyto(boxes1[:, :2], bboxes1[:, :2])
        np.copyto(boxes2[:, :2], bboxes2[:, :2])
        boxes1[:, 2:] = bboxes1[:, :2] + bboxes1[:, 2:]
        boxes2[:, 2:] = bboxes2[:, :2] + bboxes2[:, 2:]
    elif box_format in ('x0y0x1y1', 'xyxy'):
        # Use direct references instead of copying
        boxes1, boxes2 = bboxes1, bboxes2
    else:
        raise ValueError(f'Unsupported box format: {box_format}')

    # Pre-compute box areas once
    boxes1_area = (boxes1[:, 2] - boxes1[:, 0]) * (boxes1[:, 3] - boxes1[:, 1])
    boxes2_area = (boxes2[:, 2] - boxes2[:, 0]) * (boxes2[:, 3] - boxes2[:, 1])

    # Compute intersection coordinates efficiently
    # Use min/max operations on specific axes for better performance
    left = np.maximum(boxes1[:, None, 0], boxes2[None, :, 0])
    top = np.maximum(boxes1[:, None, 1], boxes2[None, :, 1])
    right = np.minimum(boxes1[:, None, 2], boxes2[None, :, 2])
    bottom = np.minimum(boxes1[:, None, 3], boxes2[None, :, 3])

    # Calculate intersection area - avoid creating temporary arrays
    width = np.maximum(0, right - left)
    height = np.maximum(0, bottom - top)
    intersection = width * height

    # Calculate union directly
    union = boxes1_area[:, None] + boxes2_area[None, :] - intersection

    # Constant for numerical stability - single definition
    epsilon = 1e-8

    # Compute IOUs
    ious = np.divide(intersection, np.maximum(union, epsilon))

    return ious


def normalize_cost_matrix(cost_matrix: np.ndarray) -> np.ndarray:
    epsilon = 1e-8

    # Compute row and column sums once
    row_sums = np.sum(cost_matrix, axis=1, keepdims=True)
    col_sums = np.sum(cost_matrix, axis=0, keepdims=True)

    # Calculate denominator and normalize in one step where possible
    denom = row_sums + col_sums - cost_matrix
    # Pre-compute the maximum denominator with epsilon
    np.maximum(denom, epsilon, out=denom)
    # Perform division in-place
    np.divide(cost_matrix, denom, out=cost_matrix)

    return cost_matrix



def _linearize_FrameExtractionInputData(ref_dfs, comp_dfs, unique_video_ids) -> list[FrameExtractionInputData]:
    data_prep_work_queue = list()
    for video_id in unique_video_ids:
        if video_id in ref_dfs and video_id in comp_dfs:
            ref_df = ref_dfs[video_id]
            comp_df = comp_dfs[video_id]

            data_prep_work_queue.append(FrameExtractionInputData(ref_df, comp_df, video_id))
    return data_prep_work_queue



def _compute_pre_hota(sim_cost_matrix, global_cost_matrix, perform_match_per_frame=False) -> HOTA_DATA_PRECURSOR:

    lcl_ref_ids = sim_cost_matrix.i_ids
    lcl_comp_ids = sim_cost_matrix.j_ids
    video_id = sim_cost_matrix.video_id
    frame = sim_cost_matrix.frame
    gt_to_tracker_id_map = global_cost_matrix.ref2comp_id_map

    hota_pre_data = HOTA_DATA_PRECURSOR(video_id, frame)

    # Calculate the total number of dets for each gt_id and tracker_id.
    for ref_id in lcl_ref_ids:
        hota_pre_data.ref_id_counts.add_at(ref_id, 1)
    for comp_id in lcl_comp_ids:
        hota_pre_data.comp_id_counts.add_at(comp_id, 1)

    if perform_match_per_frame:
        if len(lcl_ref_ids) == 0 or len(lcl_comp_ids) == 0:
            match_ref_ids, match_comp_ids = [], []
        else:
            lcl_ref_idx = np.array([global_cost_matrix.ref_id2idx(id) for id in lcl_ref_ids])
            lcl_comp_idx = np.array([global_cost_matrix.comp_id2idx(id) for id in lcl_comp_ids])
            score_mat = global_cost_matrix.cost_matrix[lcl_ref_idx[:, np.newaxis], lcl_comp_idx[np.newaxis, :]]
            score_mat = score_mat * sim_cost_matrix.cost_matrix

            match_rows, match_cols = linear_sum_assignment(-score_mat)
            match_ref_ids = lcl_ref_ids[match_rows]
            match_comp_ids = lcl_comp_ids[match_cols]
    else:
        if len(lcl_ref_ids) == 0 or len(lcl_comp_ids) == 0:
            match_ref_ids, match_comp_ids = [], []
        else:
            # Extract matches relevant to this frame
            frame_matches_id = []
            for i, gt_id in enumerate(lcl_ref_ids):
                if gt_id in gt_to_tracker_id_map.keys():
                    matched_tracker_id = gt_to_tracker_id_map[gt_id]
                    if matched_tracker_id in lcl_comp_ids:
                        frame_matches_id.append((gt_id, matched_tracker_id))

            if frame_matches_id:
                match_ref_ids, match_comp_ids = zip(*frame_matches_id)
            else:
                match_ref_ids, match_comp_ids = [], []

    # Convert to numpy arrays
    match_ref_ids = np.array(match_ref_ids)
    match_comp_ids = np.array(match_comp_ids)
    matched_similarity_vals = [sim_cost_matrix.get_cost(i, j) for i, j in zip(match_ref_ids, match_comp_ids)]
    matched_similarity_vals = np.array(matched_similarity_vals)
    if np.any(np.isnan(matched_similarity_vals)):
        print(f"NaN value in matched_similarity_vals for video {sim_cost_matrix.video_id} frame {sim_cost_matrix.frame}")
        print(f"sim_cost_matrix.i_ids: {sim_cost_matrix.i_ids}")
        print(f"sim_cost_matrix.j_ids: {sim_cost_matrix.j_ids}")
        print(f"sim_cost_matrix.cost_matrix: {sim_cost_matrix.cost_matrix}")
        raise ValueError("NaN value in matched_similarity_vals")
    
    # Calculate and accumulate basic statistics
    for a, alpha in enumerate(HOTA_DATA.array_labels):
        actually_matched_mask = matched_similarity_vals >= alpha - np.finfo('float').eps
        alpha_match_ref_ids = match_ref_ids[actually_matched_mask]
        alpha_match_comp_ids = match_comp_ids[actually_matched_mask]
        sub_match_sim_vals = matched_similarity_vals[actually_matched_mask]
        num_matches = len(alpha_match_ref_ids)

        hota_pre_data.TP[a] += num_matches
        hota_pre_data.FN[a] += len(lcl_ref_ids) - num_matches
        hota_pre_data.FP[a] += len(lcl_comp_ids) - num_matches

        if num_matches > 0:
            for k in range(len(alpha_match_ref_ids)):
                ref_id = int(alpha_match_ref_ids[k])
                comp_id = int(alpha_match_comp_ids[k])
                hota_pre_data.LocA[a] += float(sub_match_sim_vals[k])
                hota_pre_data.matches_counts[a].add_at(ref_id, comp_id, 1)    

    return hota_pre_data

